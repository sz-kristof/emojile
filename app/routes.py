from flask import render_template, session, redirect, url_for, flash, request, jsonify, make_response
from . import main 
from . import db
from .models import Riddle, PlayerStats, db, initial_emojis, AVAILABLE_MODES # Ensure initial_emojis is imported
from datetime import datetime, timedelta, date, timezone # Ensure timezone is imported
import uuid
from sqlalchemy import func # Import func for max()
import random

# Define the epoch date (adjust if needed, e.g., your launch date)
# EPOCH_DATE = date(2024, 1, 1) # Example: January 1st, 2024
EPOCH_DATE = date(2025, 5, 5) # Set to today as per your last change

# Define constants (if not already defined elsewhere)
MAX_GUESSES = 3
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"

# --- Helper Functions (if any, like get_or_create_player) ---
# ... (keep existing helper functions) ...

@main.route('/', methods=['GET'])
def index():
    # --- Game Mode Handling ---
    selected_mode = request.args.get('mode', 'Classic')
    if selected_mode not in AVAILABLE_MODES:
        selected_mode = 'Classic'
    # session['selected_mode'] = selected_mode # This is the target mode, active_state_mode tracks session's game state mode
    print(f"[DEBUG] index: Target selected game mode: {selected_mode}")

    # --- Player UUID Handling ---
    player_uuid = session.get('player_uuid')
    if not player_uuid:
        player_uuid = str(uuid.uuid4())
        session['player_uuid'] = player_uuid
        print(f"[DEBUG] index: New player detected, assigning UUID: {player_uuid}")
    else:
        print(f"[DEBUG] index: Existing player detected, UUID: {player_uuid}")

    # --- Date and Riddle Selection ---
    now_utc = datetime.now(timezone.utc)
    effective_date = now_utc.date()

    current_test_offset = request.args.get('test_offset', type=int)
    if current_test_offset is not None:
        effective_date = EPOCH_DATE + timedelta(days=(effective_date - EPOCH_DATE).days + current_test_offset)
        session['test_offset_override'] = current_test_offset # Store override for consistency
        print(f"[DEBUG] index: Applying test offset: {current_test_offset} days. Effective Date: {effective_date}")
    elif session.get('test_offset_override') is not None: # Persist offset from session if no new one in args
        effective_date = EPOCH_DATE + timedelta(days=(effective_date - EPOCH_DATE).days + session.get('test_offset_override'))
        print(f"[DEBUG] index: Using session test offset: {session.get('test_offset_override')}. Effective Date: {effective_date}")


    print(f"[DEBUG] index: Effective Date (UTC based) = {effective_date}")
    
    today_riddle_id = None
    riddle_answer = ""
    category = ""
    current_riddle_obj = None
    target_day_number_for_query = -1 # Default if no riddles

    if not initial_emojis:
        flash("Error: Emoji list is not available. Please initialize the database.", "danger")
    else:
        cycle_length = len(initial_emojis)
        if cycle_length > 0:
            days_diff = (effective_date - EPOCH_DATE).days
            target_day_number_for_query = days_diff % cycle_length
            print(f"[DEBUG] index: Mode '{selected_mode}': Cycle length = {cycle_length}, Target day number for query = {target_day_number_for_query}")
            current_riddle_obj = Riddle.query.filter_by(
                game_mode=selected_mode,
                day_number=target_day_number_for_query
            ).first()

            if current_riddle_obj:
                today_riddle_id = current_riddle_obj.id
                riddle_answer = current_riddle_obj.name
                category = current_riddle_obj.category
                print(f"[DEBUG] index: Found riddle ID {today_riddle_id} ('{riddle_answer}') for mode '{selected_mode}', day_number {target_day_number_for_query}")
            else:
                print(f"[ERROR] index: Could not find riddle for mode '{selected_mode}', day_number {target_day_number_for_query}.")
                flash(f"No riddle available for '{selected_mode}' mode today (Code: RID_NF).", "warning")
        else:
            print(f"[ERROR] index: Cycle length is zero, cannot determine riddle.")
            flash("Emoji list is empty, cannot load riddles.", "danger")

    # --- Initialize template variables ---
    template_vars = {
        'game_over': False, 'is_win': False, 'guessed_letters': [], 'results': [], 
        'incorrect_guesses': 0, 'answer_display': riddle_answer, 'category': category, 
        'current_riddle_id': today_riddle_id, 'day_number': target_day_number_for_query, 
        'selected_mode': selected_mode, 'alphabet': ALPHABET, 'max_guesses': MAX_GUESSES, 
        'stats': get_player_stats_dict(player_uuid), # Assuming get_player_stats_dict fetches all stats
        'avg_incorrect': calculate_avg_incorrect(player_uuid), # Assuming this function exists
        'next_midnight_iso': (datetime.combine(effective_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)).isoformat(),
        'streak_test_mode': request.args.get('streak_test_mode', 'false').lower() == 'true', # from your existing code
        # Vars for pixelated_game.html specific load state
        'is_game_over_on_load': False,
        'is_win_on_load': False,
        'day_number_on_load': target_day_number_for_query,
        'incorrect_guesses_on_load': 0,
        'max_guesses_on_load': MAX_GUESSES,
    }

    effective_date_iso = effective_date.isoformat()
    completed_key_base = f"{selected_mode}_{effective_date_iso}"
    game_completed_today_for_this_mode = session.get(f'completed_{completed_key_base}', False)
    persisted_riddle_id_for_completed_game = session.get(f'riddle_id_{completed_key_base}')

    if game_completed_today_for_this_mode and persisted_riddle_id_for_completed_game == today_riddle_id and today_riddle_id is not None:
        print(f"[DEBUG] index: Loading COMPLETED state for mode '{selected_mode}' on {effective_date_iso}.")
        template_vars['game_over'] = True
        template_vars['is_win'] = session.get(f'is_win_{completed_key_base}', False)
        template_vars['guessed_letters'] = session.get(f'guesses_{completed_key_base}', [])
        template_vars['results'] = session.get(f'results_{completed_key_base}', [])
        template_vars['is_game_over_on_load'] = True # For pixelated template
        template_vars['is_win_on_load'] = template_vars['is_win'] # For pixelated template
    else:
        print(f"[DEBUG] index: Loading ACTIVE or NEW game state for mode '{selected_mode}' on {effective_date_iso}.")
        active_state_mode = session.get('active_state_mode')
        active_state_date_iso = session.get('active_state_date_iso')
        active_state_riddle_id = session.get('riddle_id') # Generic key for active riddle

        needs_active_state_reset = False
        if active_state_mode != selected_mode or \
           active_state_date_iso != effective_date_iso or \
           active_state_riddle_id != today_riddle_id:
            needs_active_state_reset = True
            print(f"[DEBUG] index: Active game state RESETTING. Prior state: mode='{active_state_mode}', date='{active_state_date_iso}', riddle_id='{active_state_riddle_id}'. New: mode='{selected_mode}', date='{effective_date_iso}', riddle_id='{today_riddle_id}'")

        if needs_active_state_reset:
            session.pop('guesses', None)
            session.pop('results', None)
            session.pop('game_over', None)
            session.pop('is_win', None)
            session.pop('share_text', None)
            # These define the context of the generic session keys
            session['active_state_mode'] = selected_mode
            session['active_state_date_iso'] = effective_date_iso
            session['riddle_id'] = today_riddle_id # Set active riddle ID
        
        # Load from generic session keys for active game
        template_vars['game_over'] = session.get('game_over', False)
        template_vars['is_win'] = session.get('is_win', False)
        template_vars['guessed_letters'] = session.get('guesses', [])
        template_vars['results'] = session.get('results', [])
        template_vars['is_game_over_on_load'] = template_vars['game_over'] # For pixelated template
        template_vars['is_win_on_load'] = template_vars['is_win'] # For pixelated template

    template_vars['incorrect_guesses'] = len([res for res in template_vars['results'] if res is False]) # Correctly count False for incorrect
    template_vars['incorrect_guesses_on_load'] = template_vars['incorrect_guesses'] # For pixelated template
    
    # Determine template
    template_name = 'classic_game.html' if selected_mode == 'Classic' else 'pixelated_game.html'
    if selected_mode == 'Pixelated': # Pass specific vars for pixelated template
        template_vars.update({
            'is_game_over_on_load': template_vars['game_over'],
            'is_win_on_load': template_vars['is_win'],
            'day_number_on_load': target_day_number_for_query,
            'incorrect_guesses_on_load': template_vars['incorrect_guesses'],
            'max_guesses_on_load': MAX_GUESSES
        })

    return render_template(template_name, **template_vars)

@main.route('/guess', methods=['POST'])
def make_guess():
    data = request.get_json()
    guess = data.get('guess', '').lower()
    player_uuid = session.get('player_uuid')

    # Retrieve active game context from session
    active_mode = session.get('active_state_mode')
    active_date_iso = session.get('active_state_date_iso')
    current_riddle_id = session.get('riddle_id')

    if not active_mode or not active_date_iso or current_riddle_id is None:
        return jsonify({'success': False, 'error': 'Game session not properly initialized. Please refresh.', 'game_over': True})

    # Check if this specific mode/date game was already completed and persisted
    # This is an additional check to prevent guessing on an already fully completed/persisted game via direct API call
    completed_key_base_for_active_game = f"{active_mode}_{active_date_iso}"
    if session.get(f'completed_{completed_key_base_for_active_game}', False):
        # If riddle ID also matches, then it's definitely completed.
        if session.get(f'riddle_id_{completed_key_base_for_active_game}') == current_riddle_id:
             print(f"[DEBUG] guess: Attempt to guess on already completed and persisted game: mode '{active_mode}', date '{active_date_iso}'")
             return jsonify({
                 'success': False, 
                 'error': 'This game for the day has already been completed.', 
                 'game_over': True,
                 'is_win': session.get(f'is_win_{completed_key_base_for_active_game}', False),
                 'guessed_letters': session.get(f'guesses_{completed_key_base_for_active_game}', []),
                 'results': session.get(f'results_{completed_key_base_for_active_game}', []),
                 'incorrect_guesses': len([r for r in session.get(f'results_{completed_key_base_for_active_game}', []) if r is False])
             })

    riddle = Riddle.query.get(current_riddle_id)
    if not riddle:
        return jsonify({'success': False, 'error': 'Riddle not found. Please refresh.', 'game_over': True})

    answer = riddle.name.lower()
    guesses = session.get('guesses', [])
    results = session.get('results', []) # True for correct position, False for incorrect, None for not guessed

    if session.get('game_over', False): # Check generic game_over for active game
        return jsonify({'success': False, 'error': 'The game is already over.', 'game_over': True, 'is_win': session.get('is_win', False)})

    if not guess.isalpha() or len(guess) != 1:
        return jsonify({'success': False, 'error': 'Invalid guess. Please enter a single letter.'})

    if guess in guesses:
        return jsonify({'success': False, 'error': 'Letter already guessed.'})

    guesses.append(guess)
    is_correct_guess = guess in answer # Simplified: just checks if letter is in answer

    # For hangman-style results (True if letter is in answer, False otherwise)
    # This 'results' list is more about the letters guessed than their positions.
    # The template uses `guessed_letters` to fill in the answer display.
    # Let's keep `results` as a list of booleans indicating if the guess was helpful.
    # For Emojile, a "correct" guess means the letter is in the answer.
    
    current_results_for_display = []
    incorrect_guess_count = 0
    is_win = True

    for char_in_answer in answer:
        if not char_in_answer.isalpha():
            current_results_for_display.append(char_in_answer) # Keep spaces/symbols
        elif char_in_answer in guesses:
            current_results_for_display.append(True) # Letter guessed and in answer
        else:
            current_results_for_display.append(None) # Letter not yet guessed
            is_win = False # If any letter not guessed, not a win

    # Update incorrect guesses: count letters in `guesses` that are not in `answer`
    incorrect_guess_count = len([g for g in guesses if g.isalpha() and g not in answer])
    
    # The `results` list in session should probably track the outcome of each guess attempt
    # For simplicity, let's assume `results` stores the `guesses` list for now,
    # and `incorrect_guesses` is the primary metric.
    # Or, `results` could be a list of True/False for each guess in `guesses`
    # True if guess is in answer, False if not.
    session['results'] = [g_char in answer for g_char in guesses if g_char.isalpha()]


    game_over = False
    if is_win or incorrect_guess_count >= MAX_GUESSES:
        game_over = True
    
    session['guesses'] = guesses
    session['game_over'] = game_over
    session['is_win'] = is_win
    # session['riddle_id'] is already the active riddle_id

    if game_over:
        # Persist the completed state for this specific mode and date
        # active_mode, active_date_iso, current_riddle_id are from the top of this function
        completed_key_base = f"{active_mode}_{active_date_iso}"
        session[f'completed_{completed_key_base}'] = True
        session[f'riddle_id_{completed_key_base}'] = current_riddle_id
        session[f'guesses_{completed_key_base}'] = guesses
        session[f'results_{completed_key_base}'] = session['results'] # Persist the calculated results
        session[f'is_win_{completed_key_base}'] = is_win
        print(f"[DEBUG] guess: Persisted COMPLETED game state for mode '{active_mode}', date '{active_date_iso}'. Win: {is_win}")
        
        # --- Update Player Stats ---
        # (Your existing player stats update logic here)
        # Ensure it uses `player_uuid`, `incorrect_guess_count`, `is_win`
        update_player_stats(player_uuid, incorrect_guess_count, is_win)


    return jsonify({
        'success': True,
        'guessed_letter': guess,
        'is_correct': guess in answer, # Was the specific letter correct?
        'game_over': game_over,
        'is_win': is_win,
        'guesses_left': MAX_GUESSES - incorrect_guess_count,
        'incorrect_guesses': incorrect_guess_count,
        'guessed_letters': guesses, # Send back all guessed letters
        'results': session['results'], # Send back the results of each guess
        'stats': get_player_stats_dict(player_uuid) if game_over else None # Send stats if game over
    })

# Helper function to update player stats (extracted for clarity)
def update_player_stats(player_uuid, incorrect_guesses_for_game, is_win_for_game):
    player_stats = PlayerStats.query.get(player_uuid)
    if not player_stats:
        # This case should ideally be handled by get_or_create_player in index
        print(f"[WARN] update_player_stats: PlayerStats not found for {player_uuid}")
        return

    now_utc = datetime.now(timezone.utc)
    today_date = now_utc.date()
    
    # Ensure last_played_datetime is timezone-aware if comparing with now_utc
    last_played_date = None
    if player_stats.last_played_datetime:
        if player_stats.last_played_datetime.tzinfo is None:
            # If naive, assume UTC (or your app's default timezone)
            # This depends on how last_played_datetime is stored. For safety, let's assume it might be naive.
            # It's better to always store it as timezone-aware UTC.
            last_played_date = player_stats.last_played_datetime.replace(tzinfo=timezone.utc).date()
        else:
            last_played_date = player_stats.last_played_datetime.astimezone(timezone.utc).date()

    # Update total games only if it's a new game for the day or if it's the first game ever
    # This logic might need refinement based on how "game played" is defined.
    # For now, let's assume every call to this function (on game_over) means a game was played.
    player_stats.total_games += 1
    player_stats.total_incorrect += incorrect_guesses_for_game

    # Play Streak
    if last_played_date == today_date - timedelta(days=1):
        player_stats.current_play_streak += 1
    elif last_played_date != today_date: # Reset if not played yesterday or today (and it's a new day)
        player_stats.current_play_streak = 1
    # If last_played_date is today, streak doesn't change until tomorrow.

    if player_stats.current_play_streak > player_stats.longest_play_streak:
        player_stats.longest_play_streak = player_stats.current_play_streak

    # Correct Streak
    if is_win_for_game:
        player_stats.current_correct_streak += 1
    else:
        player_stats.current_correct_streak = 0 # Reset on loss

    if player_stats.current_correct_streak > player_stats.longest_correct_streak:
        player_stats.longest_correct_streak = player_stats.current_correct_streak
    
    player_stats.last_played_datetime = now_utc # Update last played time to now

    try:
        db.session.commit()
        print(f"[DEBUG] update_player_stats: Stats updated for player {player_uuid}")
    except Exception as e:
        db.session.rollback()
        print(f"[ERROR] update_player_stats: Failed to update stats for {player_uuid}: {e}")

# Helper to get stats as dict (you might have this already)
def get_player_stats_dict(player_uuid):
    player_stats = PlayerStats.query.get(player_uuid)
    if player_stats:
        avg_incorrect = (player_stats.total_incorrect / player_stats.total_games) if player_stats.total_games > 0 else 0
        return {
            'total_games': player_stats.total_games,
            'avg_incorrect': avg_incorrect, # Calculate here or pass pre-calculated
            'current_play_streak': player_stats.current_play_streak,
            'longest_play_streak': player_stats.longest_play_streak,
            'current_correct_streak': player_stats.current_correct_streak,
            'longest_correct_streak': player_stats.longest_correct_streak,
            'last_played_datetime_str': player_stats.last_played_datetime.strftime('%Y-%m-%d %H:%M:%S UTC') if player_stats.last_played_datetime else "Never"
        }
    return { # Default for new players or if stats somehow missing
            'total_games': 0, 'avg_incorrect': 0, 'current_play_streak': 0,
            'longest_play_streak': 0, 'current_correct_streak': 0, 'longest_correct_streak': 0,
            'last_played_datetime_str': "Never"
        }

def calculate_avg_incorrect(player_uuid): # Placeholder for your existing logic if separate
    stats = PlayerStats.query.get(player_uuid)
    if stats and stats.total_games > 0:
        return stats.total_incorrect / stats.total_games
    return 0

# --- ADD API Endpoint for Emoji ---
@main.route('/api/get-emoji/<int:riddle_id>')
def get_emoji(riddle_id):
    riddle = Riddle.query.get(riddle_id)
    if riddle:
        return jsonify({'emoji': riddle.emoji})
    else:
        return jsonify({'error': 'Riddle not found'}), 404

# --- ADD NEW ROUTE FOR MORE GAMES PAGE ---
@main.route('/more-games')
def more_games():
    """Renders the page listing available game modes."""
    print("[DEBUG] more_games: Rendering more_games.html")
    # You can add logic here if needed, e.g., fetching descriptions for modes
    return render_template('more_games.html', available_modes=AVAILABLE_MODES)

@main.cli.command("init-db")
def init_db_command():
    """
    Initializes the database with riddles for multiple modes.
    - Each mode cycles through all available emojis.
    - On any given day_number, different modes will have different emojis.
    - Introduces more variation in sequences between modes.
    """
    db.create_all()
    print("Ensured all tables exist (created if necessary).")

    Riddle.query.delete()
    db.session.commit()
    print("Cleared existing riddles.")

    if not initial_emojis:
        print("Error: initial_emojis list is empty. Cannot populate riddles.")
        return

    num_unique_emojis = len(initial_emojis)
    num_modes = len(AVAILABLE_MODES)

    if num_unique_emojis == 0:
        print("Error: The initial_emojis list is empty. No riddles to add.")
        return

    # This warning is still relevant: if you have few emojis, daily uniqueness is hard.
    if num_unique_emojis < num_modes:
        print(f"Warning: Number of unique emojis ({num_unique_emojis}) is less than the number of game modes ({num_modes}).")
        print("This means different game modes WILL have the SAME emoji on the SAME day_number with the current logic.")
        # return # Consider aborting if this is a critical failure condition

    print(f"Populating riddles for {num_unique_emojis} day_numbers, for modes: {', '.join(AVAILABLE_MODES)}...")
    print(f"Each mode will cycle through all {num_unique_emojis} emojis.")

    # Create a base shuffled list of emojis - this is what each mode will draw from
    # but in a different order determined by their mode-specific day mapping.
    # We can just use initial_emojis directly if we apply transformations to day_number.

    # Generate a unique permutation of day numbers for each mode to pick from the emoji list
    # This helps in making the sequence of emojis different for each mode.
    mode_day_permutations = {}
    base_day_indices = list(range(num_unique_emojis))
    for mode_idx, mode_name in enumerate(AVAILABLE_MODES):
        permuted_days = random.sample(base_day_indices, num_unique_emojis)
        mode_day_permutations[mode_name] = permuted_days
        # print(f"Permutation for {mode_name}: {mode_day_permutations[mode_name][:10]}...") # For debugging


    for day_number_iter in range(num_unique_emojis): # This is the actual calendar day sequence (0 to N-1)
        emojis_assigned_this_calendar_day = {} # Tracks {emoji_char: mode_name}

        print(f"Processing Calendar Day (Iteration): {day_number_iter}")

        for mode_idx, mode in enumerate(AVAILABLE_MODES):
            # Determine which emoji to pick for THIS mode on THIS calendar_day_iter
            # We need a strategy that ensures:
            # 1. This mode cycles through all emojis over num_unique_emojis days.
            # 2. This mode's emoji for calendar_day_iter is different from other modes' emojis for calendar_day_iter.

            # Strategy: Each mode has its own "starting point" in the emoji list,
            # and progresses through it. We then check for daily conflicts.

            # Effective emoji index for this mode, before conflict resolution
            # The (mode_idx * some_offset) makes each mode start at a different point
            # in the initial_emojis list for its own "day 0".
            # Let's use a larger, somewhat arbitrary offset that's not too close to num_modes
            # to create more initial separation in sequences.
            # A prime number relative to num_unique_emojis could be good.
            # For simplicity, let's use a mode-specific offset.
            
            mode_specific_start_offset = mode_idx * (num_unique_emojis // num_modes + mode_idx) # Creates some spread

            # The emoji this mode *would* pick for its internal sequence on day_number_iter
            prospective_emoji_idx = (day_number_iter + mode_specific_start_offset) % num_unique_emojis
            
            chosen_riddle_data = None
            
            # Conflict resolution: try to find an emoji not yet used today
            # This loop attempts to ensure daily uniqueness.
            attempts = 0
            original_prospective_idx = prospective_emoji_idx
            while attempts < num_unique_emojis:
                current_check_idx = (original_prospective_idx + attempts) % num_unique_emojis
                candidate_data = initial_emojis[current_check_idx]
                
                if candidate_data['emoji'] not in emojis_assigned_this_calendar_day:
                    chosen_riddle_data = candidate_data
                    emojis_assigned_this_calendar_day[chosen_riddle_data['emoji']] = mode
                    break
                attempts += 1
            
            if not chosen_riddle_data:
                # This should ideally not happen if num_unique_emojis >= num_modes
                # If it does, it means we couldn't find a unique emoji for this mode today.
                print(f"  CRITICAL WARNING on Calendar Day {day_number_iter} for Mode '{mode}': Could not find a unique emoji. Assigning non-unique or skipping.")
                # Fallback: assign the original prospective one, even if it's a duplicate for the day
                # This indicates a flaw if num_unique_emojis < num_modes or very bad luck in small N
                chosen_riddle_data = initial_emojis[original_prospective_idx]
                if chosen_riddle_data['emoji'] in emojis_assigned_this_calendar_day:
                     print(f"    -> Assigned '{chosen_riddle_data['emoji']}' which was already used by '{emojis_assigned_this_calendar_day[chosen_riddle_data['emoji']]}' today.")
                else: # Should not happen if the above if was true
                     emojis_assigned_this_calendar_day[chosen_riddle_data['emoji']] = mode


            riddle = Riddle(
                emoji=chosen_riddle_data['emoji'],
                name=chosen_riddle_data['name'],
                category=chosen_riddle_data['category'],
                day_number=day_number_iter, # This is the actual day_number for the game cycle
                game_mode=mode
            )
            db.session.add(riddle)
            print(f"  Added: Day {day_number_iter} - Mode: {mode} - Emoji: {riddle.emoji} ({riddle.name})")
    
    try:
        db.session.commit()
        print(f"Successfully committed riddles for {num_unique_emojis} day_numbers to the database.")
    except Exception as e:
        db.session.rollback()
        print(f"Error committing riddles: {e}")
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

import uuid  # Ensure this is imported

def get_or_create_player_uuid():
    """
    Retrieves the player's UUID from the session or creates a new one if it doesn't exist.
    """
    if 'player_uuid' not in session:
        # Generate a new UUID and store it in the session
        session['player_uuid'] = str(uuid.uuid4())
        print(f"[INFO] Created new player UUID: {session['player_uuid']}")
    return session['player_uuid']

@main.route('/')
def index():
    player_uuid = get_or_create_player_uuid()
    selected_mode = request.args.get('mode', 'Classic') 

    today_date = date.today()
    day_number = (today_date - EPOCH_DATE).days
    print(f"[DEBUG] index: Mode '{selected_mode}', Day_number = {day_number}")

    riddle = Riddle.query.filter_by(day_number=day_number, game_mode=selected_mode).first()
    template_name = 'pixelated_game.html' if selected_mode == 'Pixelated' else 'classic_game.html'

    # Set current game context for make_guess
    session['active_state_mode'] = selected_mode
    session['active_state_date_iso'] = today_date.isoformat()

    if not riddle:
        # ... (existing no riddle logic - it's mostly fine, ensure it uses template_name)
        # ... (ensure game_config_data is also populated for error page if JS relies on it)
        print(f"[ERROR] index: No riddle found for mode '{selected_mode}', day_number {day_number}.")
        stats = get_player_stats_dict(player_uuid, selected_mode)
        avg_incorrect_val = stats.get('avg_incorrect', 0.0)
        now_utc = datetime.now(timezone.utc)
        midnight_today_utc = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
        next_midnight_utc = midnight_today_utc + timedelta(days=1)
        next_midnight_iso_val = next_midnight_utc.isoformat()
        
        # Simplified game_config_data for error/no-riddle page
        error_game_config_data = {
            "nextMidnightISO": next_midnight_iso_val,
            "isGameOverOnLoad": True, # No game to play
            "isWinOnLoad": False,
            "dayNumberOnLoad": day_number,
            "incorrectGuessesOnLoad": 0,
            "maxGuessesOnLoad": MAX_GUESSES,
            "MAX_GUESSES": MAX_GUESSES,
            "initialRiddleId": None,
            "initialGameMode": selected_mode,
            "answerDisplay": "",
            "makeGuessUrl": url_for('main.make_guess'),
            "getEmojiUrl": None
        }

        return render_template(
            template_name,
            stats=stats,
            selected_mode=selected_mode,
            max_guesses=MAX_GUESSES,
            avg_incorrect=avg_incorrect_val,
            incorrect_guesses=0,
            current_riddle_id=None,
            category="N/A",
            game_over=True, 
            is_win=False,
            answer_display="",
            guessed_letters=[],
            alphabet=list(ALPHABET),
            next_midnight_iso=next_midnight_iso_val,
            current_year=datetime.now().year,
            day_number_on_load=day_number,
            is_game_over_on_load=True,
            is_win_on_load=False,
            incorrect_guesses_on_load=0,
            max_guesses_on_load=MAX_GUESSES,
            error_message=f"No riddle available today for {selected_mode} mode. Please check back tomorrow or run 'flask init-db'.",
            game_config_data=error_game_config_data
        )

    today_iso = today_date.isoformat()

    # Initialize new session structure if not present
    if 'game_states_by_day_mode' not in session:
        session['game_states_by_day_mode'] = {}
    if today_iso not in session['game_states_by_day_mode']:
        session['game_states_by_day_mode'][today_iso] = {}

    game_state_for_current_mode = session['game_states_by_day_mode'][today_iso].get(selected_mode)

    load_this_game_from_session = False
    if game_state_for_current_mode and game_state_for_current_mode.get('riddle_id') == riddle.id:
        load_this_game_from_session = True

    if load_this_game_from_session:
        print(f"[DEBUG] index: Loading existing game state from session for day {day_number}, mode {selected_mode}")
        current_guesses = game_state_for_current_mode.get('guesses', [])
        game_is_over = game_state_for_current_mode.get('game_over', False)
        player_has_won = game_state_for_current_mode.get('is_win', False)
        
        incorrect_count = len([g for g in current_guesses if g not in riddle.name.lower()])
        if game_is_over:
            current_answer_display = ''.join(char if char.isalpha() else ' ' for char in riddle.name)
        else:
            current_answer_display = ''.join(char if char.lower() in current_guesses else '_' if char.isalpha() else ' ' for char in riddle.name)
    else:
        print(f"[DEBUG] index: Initializing new game state for day {day_number}, mode {selected_mode}")
        new_game_state = {
            'riddle_id': riddle.id,
            'guesses': [],
            'game_over': False,
            'is_win': False
        }
        session['game_states_by_day_mode'][today_iso][selected_mode] = new_game_state
        session.modified = True 

        current_guesses = []
        game_is_over = False
        player_has_won = False
        incorrect_count = 0
        current_answer_display = ''.join('_' if char.isalpha() else ' ' for char in riddle.name)

    stats = get_player_stats_dict(player_uuid, selected_mode)
    avg_incorrect_val = stats.get('avg_incorrect', 0.0)
    
    now_utc = datetime.now(timezone.utc)
    midnight_today_utc = datetime(now_utc.year, now_utc.month, now_utc.day, tzinfo=timezone.utc)
    next_midnight_utc = midnight_today_utc + timedelta(days=1)
    next_midnight_iso_val = next_midnight_utc.isoformat()

    game_config_data = {
        "nextMidnightISO": next_midnight_iso_val,
        "isGameOverOnLoad": game_is_over,
        "isWinOnLoad": player_has_won,
        "dayNumberOnLoad": day_number,
        "incorrectGuessesOnLoad": incorrect_count,
        "maxGuessesOnLoad": MAX_GUESSES,
        "MAX_GUESSES": MAX_GUESSES,
        "initialRiddleId": riddle.id,
        "initialGameMode": selected_mode,
        "answerDisplay": current_answer_display,
        "makeGuessUrl": url_for('main.make_guess'),
        "getEmojiUrl": url_for('main.get_emoji', riddle_id=riddle.id)
    }

    return render_template(
        template_name,
        stats=stats,
        selected_mode=selected_mode,
        max_guesses=MAX_GUESSES,
        avg_incorrect=avg_incorrect_val,
        incorrect_guesses=incorrect_count,
        current_riddle_id=riddle.id, # Still useful for template if not using game_config everywhere
        category=riddle.category,
        game_over=game_is_over,
        is_win=player_has_won,
        answer_display=current_answer_display,
        guessed_letters=current_guesses,
        alphabet=list(ALPHABET),
        next_midnight_iso=next_midnight_iso_val,
        current_year=datetime.now().year,
        day_number_on_load=day_number, 
        is_game_over_on_load=game_is_over, 
        is_win_on_load=player_has_won, 
        incorrect_guesses_on_load=incorrect_count, 
        max_guesses_on_load=MAX_GUESSES, 
        game_config_data=game_config_data
    )

@main.route('/guess', methods=['POST'])
def make_guess():
    data = request.get_json()
    guess = data.get('guess', '').lower()
    player_uuid = session.get('player_uuid')

    # Get current game context from session (set by index route)
    active_mode = session.get('active_state_mode')
    active_date_iso = session.get('active_state_date_iso')

    if not active_mode or not active_date_iso:
        return jsonify({'success': False, 'error': 'Game session context not found. Please refresh.', 'game_over': True})

    # Fetch the specific game state for the current mode and date
    game_states_for_day = session.get('game_states_by_day_mode', {}).get(active_date_iso, {})
    current_game_session_state = game_states_for_day.get(active_mode)

    if not current_game_session_state:
        return jsonify({'success': False, 'error': 'Game state not found for this mode/day. Please refresh.', 'game_over': True})

    riddle_id_from_session = current_game_session_state.get('riddle_id')
    if riddle_id_from_session is None:
         return jsonify({'success': False, 'error': 'Riddle ID not found in session state. Please refresh.', 'game_over': True})

    riddle = Riddle.query.get(riddle_id_from_session)
    if not riddle:
        return jsonify({'success': False, 'error': 'Riddle not found. Please refresh.', 'game_over': True})

    answer = riddle.name.lower()
    guesses = current_game_session_state.get('guesses', []) # Get guesses from mode-specific state

    if current_game_session_state.get('game_over', False):
        # Construct response based on the saved game_over state
        response_answer_display = ''.join(char if char.isalpha() else ' ' for char in answer) # Show full answer
        return jsonify({
            'success': False, # Or True, but game is over
            'error': 'The game is already over.',
            'game_over': True,
            'is_win': current_game_session_state.get('is_win', False),
            'answer_display': response_answer_display,
            'guessed_letters': guesses,
            'incorrect_guesses': len([g for g in guesses if g not in answer])
        })

    if not guess.isalpha() or len(guess) != 1:
        return jsonify({'success': False, 'error': 'Invalid guess. Please enter a single letter.'})

    if guess in guesses:
        return jsonify({'success': False, 'error': 'Letter already guessed.'})

    guesses.append(guess)
    # current_game_session_state['guesses'] = guesses # List is modified in-place, but explicit re-assignment is safer if any doubt

    is_win = all(char in guesses or not char.isalpha() for char in answer)
    incorrect_guess_count = len([g for g in guesses if g not in answer])
    game_over = is_win or incorrect_guess_count >= MAX_GUESSES

    # Update the mode-specific session state
    current_game_session_state['game_over'] = game_over
    current_game_session_state['is_win'] = is_win
    current_game_session_state['guesses'] = guesses # Ensure the list is updated back
    session.modified = True # Crucial!

    response_answer_display = ''.join(char if char.lower() in guesses or not char.isalpha() else '_' for char in riddle.name)
    if game_over: # If game just ended, show full answer
        response_answer_display = ''.join(char if char.isalpha() else ' ' for char in riddle.name)
        # Update player stats in DB
        update_player_stats(player_uuid, active_mode, is_win, incorrect_guess_count, date.fromisoformat(active_date_iso))

    return jsonify({
        'success': True,
        'guessed_letter': guess,
        'is_correct': guess in answer,
        'game_over': game_over,
        'is_win': is_win,
        'answer_display': response_answer_display,
        'guessed_letters': guesses,
        'incorrect_guesses': incorrect_guess_count,
        'stats': get_player_stats_dict(player_uuid, active_mode) if game_over else None
    })

# Helper function to update player stats (extracted for clarity)
def update_player_stats(player_uuid, game_mode, is_win_for_game, incorrect_guesses_for_game, game_date_for_streak):
    # Query using the composite primary key (player_uuid, game_mode)
    player_stats = PlayerStats.query.get((player_uuid, game_mode)) 
    if not player_stats:
        # If no stats record exists, create one for this player and game mode
        print(f"[INFO] update_player_stats: First game for player {player_uuid} in mode {game_mode}. Creating PlayerStats record.")
        player_stats = PlayerStats(
            player_uuid=player_uuid,
            game_mode=game_mode, # Ensure game_mode is set when creating new record
            total_games=0,  # Will be incremented to 1 below
            total_incorrect=0, # Will be updated below
            current_play_streak=0, # Initial streak
            longest_play_streak=0,
            current_correct_streak=0,
            longest_correct_streak=0,
            last_played_datetime=None # Will be set to now_utc below
        )
        db.session.add(player_stats)
        # The commit at the end of this function will save the new record.

    now_utc = datetime.now(timezone.utc)
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
    if last_played_date == game_date_for_streak - timedelta(days=1):
        player_stats.current_play_streak += 1
    elif last_played_date != game_date_for_streak: # Reset if not played yesterday or today (and it's a new day for this game)
        player_stats.current_play_streak = 1
    # If last_played_date is game_date_for_streak, streak doesn't change until the next distinct game day.

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
def get_player_stats_dict(player_uuid, game_mode):
    # Query using the composite primary key (player_uuid, game_mode)
    player_stats = PlayerStats.query.get((player_uuid, game_mode))
    if player_stats:
        avg_incorrect = (player_stats.total_incorrect / player_stats.total_games) if player_stats.total_games > 0 else 0.0
        return {
            'total_games': player_stats.total_games,
            'avg_incorrect': avg_incorrect,
            'current_play_streak': player_stats.current_play_streak,
            'longest_play_streak': player_stats.longest_play_streak,
            'current_correct_streak': player_stats.current_correct_streak,
            'longest_correct_streak': player_stats.longest_correct_streak,
            'last_played_datetime': player_stats.last_played_datetime
        }
    # Return default stats if no record exists for the given player and game mode
    return {
        'total_games': 0,
        'avg_incorrect': 0.0,
        'current_play_streak': 0,
        'longest_play_streak': 0,
        'current_correct_streak': 0,
        'longest_correct_streak': 0,
        'last_played_datetime': None
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
            
            # Ensure the stable offset logic is the one that's active:
            mode_specific_start_offset = mode_idx # Classic (idx 0) gets offset 0, Pixelated (idx 1) gets offset 1, etc.

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
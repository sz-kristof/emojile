from flask import render_template, session, redirect, url_for, flash, request, jsonify, make_response
from . import main 
from . import db
from .models import Riddle, PlayerStats # Import models
from datetime import datetime, timedelta, date, timezone # Ensure timezone is imported
import uuid
from sqlalchemy import func # Import func for max()

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
    # --- Player UUID Handling ---
    player_uuid = session.get('player_uuid')
    if not player_uuid:
        player_uuid = str(uuid.uuid4())
        session['player_uuid'] = player_uuid
        print(f"[DEBUG] index: New player detected, assigning UUID: {player_uuid}")
        show_stats_modal = False # Don't show stats modal on first visit
    else:
        print(f"[DEBUG] index: Existing player detected, UUID: {player_uuid}")
        show_stats_modal = request.args.get('stats') == '1'

    # --- Date and Riddle Selection ---
    # Use UTC for consistency
    now_utc = datetime.now(timezone.utc)
    effective_date = now_utc.date() # Default to today UTC

    # --- Testing Offset ---
    current_test_offset = request.args.get('test_offset', type=int)
    streak_test_mode = request.args.get('streak_test_mode', 'false').lower() == 'true'

    if current_test_offset is not None:
        effective_date = effective_date + timedelta(days=current_test_offset)
        print(f"[DEBUG] index: Applying test offset: {current_test_offset} days. Effective Date: {effective_date}")

    print(f"[DEBUG] index: Effective Date (UTC based) = {effective_date}")
    target_day_number = (effective_date - EPOCH_DATE).days
    print(f"[DEBUG] index: Target Day Number = {target_day_number}")

    # Calculate next midnight for countdown timer
    next_midnight_utc = datetime.combine(effective_date + timedelta(days=1), datetime.min.time(), tzinfo=timezone.utc)
    next_midnight_iso = next_midnight_utc.isoformat()
    print(f"[DEBUG] index: Next Midnight ISO = {next_midnight_iso}")

    # --- Player Stats Loading ---
    player_stats = PlayerStats.query.get(player_uuid)
    if not player_stats:
        player_stats = PlayerStats(player_uuid=player_uuid)
        db.session.add(player_stats)
        # Commit immediately if new so it exists for later updates
        try:
            db.session.commit()
            print(f"[DEBUG] index: Created new stats entry in DB for {player_uuid}")
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] index: Failed to create initial stats for {player_uuid}: {e}")
            flash("Error initializing player statistics.", "danger")
            # Handle error appropriately, maybe render an error page or default values
            player_stats = None # Ensure it's None if creation failed
    else:
        print(f"[DEBUG] index: Loaded stats from DB for {player_uuid}")

    # Convert stats to dictionary for template (handle None case)
    player_stats_dict = {
        'total_games': player_stats.total_games if player_stats else 0,
        'total_incorrect': player_stats.total_incorrect if player_stats else 0,
        'current_play_streak': player_stats.current_play_streak if player_stats else 0,
        'longest_play_streak': player_stats.longest_play_streak if player_stats else 0,
        'current_correct_streak': player_stats.current_correct_streak if player_stats else 0,
        'longest_correct_streak': player_stats.longest_correct_streak if player_stats else 0,
        'last_played_date': player_stats.last_played_datetime.date().isoformat() if player_stats and player_stats.last_played_datetime else "Never"
    }


    # --- Find Today's Riddle ---
    today_riddle_id = None
    riddle_answer = ""
    category = ""
    current_riddle_obj = None

    # Find the highest assigned day_number to determine the cycle length
    max_assigned_day_result = db.session.query(func.max(Riddle.day_number)).scalar()

    if max_assigned_day_result is None:
        # Case 1: No riddles have day numbers assigned at all
        print("[ERROR] index: No riddles found with assigned day numbers in the database.")
        flash("No riddles are currently available. Please check back later.", "warning")
    else:
        # Case 2: Riddles exist, determine which one to show
        cycle_length = max_assigned_day_result + 1 # e.g., if max is 48, length is 49 (0-48)
        effective_day_number = target_day_number % cycle_length # Wrap the target day using modulo

        print(f"[DEBUG] index: Max assigned day = {max_assigned_day_result}, Cycle length = {cycle_length}, Effective day number = {effective_day_number}")

        # Try to find the riddle for the effective day number
        current_riddle_obj = Riddle.query.filter_by(day_number=effective_day_number).first()

        if current_riddle_obj:
            today_riddle_id = current_riddle_obj.id
            riddle_answer = current_riddle_obj.name.lower()
            category = current_riddle_obj.category
            print(f"[DEBUG] index: Found riddle ID {today_riddle_id} ('{riddle_answer}') for effective day {effective_day_number} (Target day {target_day_number})")
        else:
            # This case should ideally not happen if day_numbers are sequential from 0
            # But handle it just in case there's a gap or error
            print(f"[ERROR] index: Could not find riddle for effective day number {effective_day_number} even though max assigned day is {max_assigned_day_result}.")
            flash(f"Error loading today's riddle (Code: EFF_DAY_MISS). Please contact support.", "danger")


    # --- Check if Game State needs reset ---
    session_riddle_id = session.get('riddle_id')
    session_test_offset = session.get('test_offset')
    session_streak_test_mode = session.get('streak_test_mode_flag')

    print(f"[DEBUG] index: Checking for reset. Effective Date: {effective_date}")
    print(f"[DEBUG] index: Checking for reset. Today's Riddle ID: {today_riddle_id}, Session Riddle ID: {session_riddle_id}")
    print(f"[DEBUG] index: Checking for reset. Current Offset: {current_test_offset}, Session Offset: {session_test_offset}")
    print(f"[DEBUG] index: Checking for reset. Current Streak Mode: {streak_test_mode}, Session Streak Mode: {session_streak_test_mode}")

    needs_reset = False
    # Reset if today's riddle is different from session, or if test params changed
    if session_riddle_id != today_riddle_id or \
       session_test_offset != current_test_offset or \
       session_streak_test_mode != streak_test_mode:
           needs_reset = True
           print(f"[DEBUG] index: Resetting session due to change in riddle ID or test parameters.")
    # Also reset if there's simply no riddle today (today_riddle_id is None) and session still holds old data
    elif today_riddle_id is None and (session_riddle_id is not None or session.get('guesses')):
           needs_reset = True
           print("[DEBUG] index: Resetting session because no riddle is assigned/found for today.")


    if needs_reset:
        print(f"[DEBUG] index: *** RESETTING SESSION *** for player {player_uuid}")
        # Clear relevant game state parts
        session.pop('guesses', None)
        session.pop('results', None)
        session.pop('game_over', None)
        session.pop('is_win', None)
        session.pop('share_text', None)
        # Store the new state (even if riddle_id is None)
        session['riddle_id'] = today_riddle_id
        session['riddle_answer'] = riddle_answer # Will be "" if today_riddle_id is None
        session['test_offset'] = current_test_offset
        session['streak_test_mode_flag'] = streak_test_mode
        # Store the actual target day number for potential future reference/debugging
        session['last_target_day_number'] = target_day_number
        print(f"[DEBUG] index: Session reset complete. New session riddle_id: {session.get('riddle_id')}, answer: '{session.get('riddle_answer')}'")
        # Redirect after reset to ensure clean state on reload
        # Preserve query parameters in redirect
        redirect_url = url_for('main.index', **request.args)
        return redirect(redirect_url)


    # --- Load Game State (if not reset) ---
    guesses = session.get('guesses', [])
    results = session.get('results', [])
    game_over = session.get('game_over', False)
    is_win = session.get('is_win', False)
    share_text = session.get('share_text', "")

    # --- Define variables needed by the template ---
    guessed_letters = set(g.lower() for g in guesses) # Set of guessed letters
    incorrect_guesses = len([g for g in guesses if g.lower() not in (riddle_answer or "").lower()]) # Count incorrect guesses

    # --- Render Template ---
    answer_display = riddle_answer if riddle_answer else "N/A"
    print(f"[DEBUG] index: Rendering template with riddle_id={today_riddle_id}, category='{category}', answer_display='{answer_display}', next_midnight_iso='{next_midnight_iso}', game_over={game_over}, is_win={is_win}")

    return render_template('index.html',
                           guesses=guesses,
                           results=results,
                           answer_display=answer_display,
                           category=category if category else "N/A",
                           game_over=game_over,
                           is_win=is_win,
                           share_text=share_text,
                           current_riddle_id=today_riddle_id, # Pass the ID (or None)
                           next_midnight_iso=next_midnight_iso,
                           show_stats_modal=show_stats_modal,
                           player_stats=player_stats_dict,
                           streak_test_mode=streak_test_mode,
                           effective_date_str=effective_date.strftime('%Y-%m-%d'),
                           # --- ADDED Variables for Template ---
                           max_guesses=MAX_GUESSES,
                           incorrect_guesses=incorrect_guesses,
                           guessed_letters=guessed_letters,
                           alphabet=ALPHABET,
                           # Pass the calculated day number for the share button
                           day_number=target_day_number,
                           # Pass stats directly for the stats card (avg_incorrect needs calculation)
                           stats=player_stats_dict,
                           avg_incorrect=(player_stats_dict['total_incorrect'] / player_stats_dict['total_games']) if player_stats_dict['total_games'] > 0 else 0
                           )

# ... (rest of your routes: guess, share_image, etc.) ...

# --- ADD API Endpoint for Emoji ---
@main.route('/api/get-emoji/<int:riddle_id>')
def get_emoji(riddle_id):
    riddle = Riddle.query.get(riddle_id)
    if riddle:
        return jsonify({'emoji': riddle.emoji})
    else:
        return jsonify({'error': 'Riddle not found'}), 404

# --- ADD make_guess route if it's missing or incomplete ---
@main.route('/guess', methods=['POST'])
def make_guess():
    # --- Get Player and Riddle ---
    player_uuid = session.get('player_uuid')
    if not player_uuid:
        return jsonify({'success': False, 'error': 'Player session not found.'}), 400

    riddle_id = session.get('riddle_id')
    riddle_answer = session.get('riddle_answer')
    if not riddle_id or riddle_answer is None:
        return jsonify({'success': False, 'error': 'Current riddle not found in session.'}), 400

    # --- Get Guess ---
    guess_data = request.get_json()
    if not guess_data or 'guess' not in guess_data:
        return jsonify({'success': False, 'error': 'Invalid guess data.'}), 400

    guess = guess_data['guess'].lower()
    if not guess.isalpha() or len(guess) != 1:
        return jsonify({'success': False, 'error': 'Invalid guess character.'}), 400

    # --- Load Game State ---
    guesses = session.get('guesses', [])
    game_over = session.get('game_over', False)

    if game_over:
        return jsonify({'success': False, 'error': 'Game is already over.'}), 400

    if guess in [g.lower() for g in guesses]:
        return jsonify({'success': False, 'error': 'Letter already guessed.'}), 400

    # --- Process Guess ---
    guesses.append(guess.upper()) # Store guess (e.g., uppercase)
    session['guesses'] = guesses

    guessed_letters = set(g.lower() for g in guesses)
    incorrect_guesses = len([g for g in guesses if g.lower() not in riddle_answer.lower()])
    is_correct_guess = guess in riddle_answer.lower()

    # Check for win condition
    answer_letters = set(c for c in riddle_answer.lower() if c.isalpha())
    is_win = answer_letters.issubset(guessed_letters)

    # Check for game over condition
    if is_win or incorrect_guesses >= MAX_GUESSES:
        game_over = True
        session['game_over'] = True
        session['is_win'] = is_win

        # --- Update Player Stats ---
        player_stats = PlayerStats.query.get(player_uuid)
        if player_stats:
            now_utc = datetime.now(timezone.utc)
            today_date = now_utc.date()
            last_played_date = player_stats.last_played_datetime.date() if player_stats.last_played_datetime else None

            # Update total games
            player_stats.total_games += 1
            player_stats.total_incorrect += incorrect_guesses # Add incorrect guesses for this game

            # Update play streak
            if last_played_date == today_date - timedelta(days=1):
                player_stats.current_play_streak += 1
            elif last_played_date != today_date: # Reset if not played yesterday or today
                player_stats.current_play_streak = 1 # Start new streak
            # If last_played_date == today_date, streak doesn't change

            if player_stats.current_play_streak > player_stats.longest_play_streak:
                player_stats.longest_play_streak = player_stats.current_play_streak

            # Update correct guess streak
            if is_win:
                player_stats.current_correct_streak += 1
                if player_stats.current_correct_streak > player_stats.longest_correct_streak:
                    player_stats.longest_correct_streak = player_stats.current_correct_streak
            else:
                player_stats.current_correct_streak = 0 # Reset on loss

            player_stats.last_played_datetime = now_utc

            try:
                db.session.commit()
                print(f"[DEBUG] guess: Updated stats for player {player_uuid}")
                # Prepare updated stats for JSON response
                updated_stats_dict = {
                    'total_games': player_stats.total_games,
                    'total_incorrect': player_stats.total_incorrect,
                    'current_play_streak': player_stats.current_play_streak,
                    'longest_play_streak': player_stats.longest_play_streak,
                    'current_correct_streak': player_stats.current_correct_streak,
                    'longest_correct_streak': player_stats.longest_correct_streak,
                    'last_played_datetime_str': player_stats.last_played_datetime.strftime('%Y-%m-%d %H:%M:%S'),
                    'avg_incorrect': (player_stats.total_incorrect / player_stats.total_games) if player_stats.total_games > 0 else 0
                }
            except Exception as e:
                db.session.rollback()
                print(f"[ERROR] guess: Failed to update stats for {player_uuid}: {e}")
                updated_stats_dict = None # Indicate stats update failed
        else:
             print(f"[ERROR] guess: Could not find player stats for {player_uuid} to update.")
             updated_stats_dict = None


        # --- Prepare Response ---
        return jsonify({
            'success': True,
            'guessed_letter': guess,
            'is_correct': is_correct_guess,
            'incorrect_guesses': incorrect_guesses,
            'game_over': game_over,
            'is_win': is_win,
            'stats': updated_stats_dict # Include updated stats if available
        })

    else: # Game not over yet
        return jsonify({
            'success': True,
            'guessed_letter': guess,
            'is_correct': is_correct_guess,
            'incorrect_guesses': incorrect_guesses,
            'game_over': False,
            'is_win': False
        })
from flask import (
    render_template, request, redirect, url_for, flash,
    Blueprint, session, jsonify, make_response # Add make_response
)
from . import db
# Import the new model and UUID library
from .models import Riddle, PlayerStats
import string
from datetime import date, timedelta, datetime, time, timezone # Import timezone
import uuid # Import uuid library

main = Blueprint('main', __name__)
MAX_INCORRECT_GUESSES = 6
EPOCH_DATE = date(2024, 1, 1)
PLAYER_COOKIE_NAME = 'player_uuid'

# --- get_daily_riddle_id function ---
def get_daily_riddle_id(date_to_use=None):
    if date_to_use is None: date_to_use = date.today()
    days_since_epoch = (date_to_use - EPOCH_DATE).days
    # DEBUG: Print date and days
    print(f"[DEBUG] get_daily_riddle_id: Date = {date_to_use}, Days since epoch = {days_since_epoch}")
    all_riddle_ids = [r.id for r in Riddle.query.order_by(Riddle.id).all()]
    # DEBUG: Print IDs found
    print(f"[DEBUG] get_daily_riddle_id: Found IDs = {all_riddle_ids}")
    if not all_riddle_ids:
        print("[DEBUG] get_daily_riddle_id: No IDs found, returning None")
        return None
    riddle_index = days_since_epoch % len(all_riddle_ids)
    selected_id = all_riddle_ids[riddle_index]
    # DEBUG: Print selected ID
    print(f"[DEBUG] get_daily_riddle_id: Index = {riddle_index}, Selected ID = {selected_id}")
    return selected_id

# --- NEW API Endpoint ---
@main.route('/api/get-emoji/<int:riddle_id>')
def get_emoji(riddle_id):
    # Basic security: Check if the requested ID matches the one in the session
    # This prevents users from just iterating through /api/get-emoji/1, /api/get-emoji/2 etc.
    # unless they are on the correct day/test offset for that riddle.
    session_riddle_id = session.get('riddle_id')
    print(f"[DEBUG] API get_emoji: Requested ID = {riddle_id}, Session ID = {session_riddle_id}") # DEBUG API
    if riddle_id != session_riddle_id:
        # Return an empty response or an error if the ID doesn't match the session's current riddle
        return jsonify({"error": "Not authorized or invalid riddle ID"}), 403 # Forbidden

    riddle = Riddle.query.get(riddle_id)
    if riddle:
        return jsonify({"emoji": riddle.emoji})
    else:
        return jsonify({"error": "Riddle not found"}), 404 # Not Found


@main.route('/', methods=['GET'])
def index():
    # --- Get/Set Player UUID ---
    player_uuid_str = request.cookies.get(PLAYER_COOKIE_NAME)
    set_cookie_in_response = False
    if not player_uuid_str:
        player_uuid_str = str(uuid.uuid4())
        set_cookie_in_response = True
        print(f"[DEBUG] index: New player detected, generated UUID: {player_uuid_str}") # DEBUG New Player
    else:
        # Optional: Validate if it looks like a UUID? For now, assume it's okay.
        print(f"[DEBUG] index: Existing player detected, UUID: {player_uuid_str}") # DEBUG Existing Player
        pass

    # --- Determine Effective Date & Test Modes ---
    # Use UTC for consistent day rollover
    now_utc = datetime.now(timezone.utc) # Get current time in UTC
    today_utc = now_utc.date()           # Get current date in UTC

    test_date_override = None
    current_test_offset = request.args.get('day_offset')
    streak_test_mode = request.args.get('streak_test_mode') == 'true' # Check for streak test mode

    try:
        if current_test_offset is not None:
            day_offset = int(current_test_offset)
            test_date_override = EPOCH_DATE + timedelta(days=day_offset)
    except (ValueError, TypeError):
        flash("Invalid 'day_offset' parameter.", "warning")
        current_test_offset = None

    # Use UTC date unless overridden by test mode
    effective_date = test_date_override if test_date_override else today_utc
    # DEBUG: Print effective date
    print(f"[DEBUG] index: Effective Date (UTC based) = {effective_date}")

    # --- Calculate Day Number ---
    day_number = (effective_date - EPOCH_DATE).days + 1 # Add 1 to start from Day 1
    print(f"[DEBUG] index: Day Number = {day_number}") # DEBUG Day Number

    # --- Calculate Next Midnight ---
    # Combine the effective_date with midnight time, then add one day
    next_midnight_dt = datetime.combine(effective_date, time.min, tzinfo=timezone.utc if not test_date_override else None) + timedelta(days=1)
    # Convert to ISO format string for easier JS parsing (and timezone handling)
    next_midnight_iso = next_midnight_dt.isoformat()
    # DEBUG: Print next midnight
    print(f"[DEBUG] index: Next Midnight ISO = {next_midnight_iso}")

    # --- Load Stats from DB ---
    player_stats_record = PlayerStats.query.get(player_uuid_str)
    if player_stats_record:
        print(f"[DEBUG] index: Loaded stats from DB for {player_uuid_str}") # DEBUG DB Load
        stats = {
            'total_games': player_stats_record.total_games,
            'total_incorrect': player_stats_record.total_incorrect,
            'current_play_streak': player_stats_record.current_play_streak,
            'longest_play_streak': player_stats_record.longest_play_streak,
            'current_correct_streak': player_stats_record.current_correct_streak,
            'longest_correct_streak': player_stats_record.longest_correct_streak,
            # Store the actual datetime object now
            'last_played_datetime': player_stats_record.last_played_datetime
        }
        last_played_datetime = stats['last_played_datetime'] # Use directly
    else:
        print(f"[DEBUG] index: No stats in DB for {player_uuid_str}, initializing.") # DEBUG DB Init
        stats = { # Initialize with defaults
            'total_games': 0, 'total_incorrect': 0, 'current_play_streak': 0,
            'longest_play_streak': 0, 'current_correct_streak': 0,
            'longest_correct_streak': 0, 'last_played_datetime': None
        }
        last_played_datetime = None
        # We will create the DB record when the first game ends

    stats_updated_this_request = False # Flag to know if we need to commit DB changes

    # --- Update Daily Streaks (based on DB data) ---
    # This logic runs on page load if the actual day changed, resetting streaks if needed
    # The game-end logic handles the incrementing/resetting based on test mode or real time.
    if not streak_test_mode and last_played_datetime:
        # Make last_played_datetime timezone-aware (assuming it was stored naive as UTC)
        if last_played_datetime.tzinfo is None:
            last_played_datetime = last_played_datetime.replace(tzinfo=timezone.utc)

        if last_played_datetime.date() < effective_date: # Compare dates directly
            yesterday_date = effective_date - timedelta(days=1)
            if last_played_datetime.date() < yesterday_date: # Missed one or more real days
                if stats['current_play_streak'] > 0:
                     stats['current_play_streak'] = 0
                     stats_updated_this_request = True
                if stats['current_correct_streak'] > 0:
                     stats['current_correct_streak'] = 0
                     stats_updated_this_request = True

    # --- Determine Today's Riddle ID ---
    total_riddles = Riddle.query.count()
    if total_riddles == 0:
        today_riddle_id = None
        riddle_answer = ""
        category = "N/A"
        print("[DEBUG] index: No riddles found in DB.") # DEBUG No Riddles
    else:
        day_number_for_id = (effective_date - EPOCH_DATE).days
        today_riddle_id = (day_number_for_id % total_riddles) + 1
        # Fetch the actual riddle object using SQLAlchemy query
        # Replace the incorrect function call:
        # current_riddle_obj = get_riddle_by_id(today_riddle_id) # Use helper
        current_riddle_obj = Riddle.query.get(today_riddle_id) # <<< FIX HERE
        if current_riddle_obj:
            riddle_answer = current_riddle_obj.name.lower() # Store the correct answer for logic
            category = current_riddle_obj.category
        else:
            # Handle case where ID is calculated but riddle doesn't exist (shouldn't happen)
            today_riddle_id = None
            riddle_answer = ""
            category = "Error"
            print(f"[ERROR] index: Riddle object not found for calculated ID {today_riddle_id}") # ERROR Riddle Object Not Found

    # --- Check if Game State needs reset ---
    session_riddle_id = session.get('riddle_id')
    session_test_offset = session.get('test_offset')
    session_streak_test_mode = session.get('streak_test_mode_flag')

    # --- ADD DEBUG PRINTS HERE ---
    print(f"[DEBUG] index: Checking for reset. Effective Date: {effective_date}")
    print(f"[DEBUG] index: Checking for reset. Today's Riddle ID: {today_riddle_id}, Session Riddle ID: {session_riddle_id}")
    print(f"[DEBUG] index: Checking for reset. Current Offset: {current_test_offset}, Session Offset: {session_test_offset}")
    print(f"[DEBUG] index: Checking for reset. Current Streak Mode: {streak_test_mode}, Session Streak Mode: {session_streak_test_mode}")
    # --- END DEBUG PRINTS ---

    if session_riddle_id != today_riddle_id or \
       session_test_offset != current_test_offset or \
       session_streak_test_mode != streak_test_mode:

        # --- ADD DEBUG PRINT HERE ---
        print(f"[DEBUG] index: *** RESETTING SESSION *** for player {player_uuid_str}")
        # --- END DEBUG PRINT ---

        # Reset game state in session
        session['riddle_id'] = today_riddle_id
        session['guessed_letters'] = []
        session['incorrect_guesses'] = 0
        # Ensure the NEW answer is stored in the session after reset
        session['riddle_answer'] = riddle_answer # Use the answer fetched above for today's riddle
        session['test_offset'] = current_test_offset
        session['streak_test_mode_flag'] = streak_test_mode
        session.modified = True
        print(f"[DEBUG] index: Session reset complete. New session riddle_id: {session.get('riddle_id')}, answer: '{session.get('riddle_answer')}'") # DEBUG Session Reset

        # --- Prepare Response for Redirect ---
        # ... (redirect logic remains the same) ...
        response = make_response(redirect(url_for('main.index', day_offset=current_test_offset, streak_test_mode='true' if streak_test_mode else None)))
        if set_cookie_in_response:
            # Set persistent cookie on redirect
            response.set_cookie(PLAYER_COOKIE_NAME, player_uuid_str, max_age=timedelta(days=365*5), httponly=True, samesite='Lax')
            print(f"[DEBUG] index: Setting cookie on redirect for {player_uuid_str}") # DEBUG Cookie Set Redirect
        return response

    # --- Flash Test Mode Messages ---
    if test_date_override:
         flash(f"TEST MODE: Simulating date {test_date_override.isoformat()} (Day Offset: {current_test_offset})", "info")
    if streak_test_mode:
         flash(f"STREAK TEST MODE: Streaks update based on minutes.", "warning")


    # --- Load Current Game State ---
    # ... (load guessed_letters_set, incorrect_guesses, riddle_answer) ...
    guessed_letters_set = set(session.get('guessed_letters', []))
    incorrect_guesses = session.get('incorrect_guesses', 0)
    # *** riddle_answer now holds the emoji name ***
    riddle_answer = session.get('riddle_answer', "")

    # Fetch minimal riddle info needed for display (category, ID)
    category = ""
    # DEBUG: Check ID before fetching category
    print(f"[DEBUG] index: today_riddle_id before fetching category = {today_riddle_id}")
    if today_riddle_id is not None:
        riddle_minimal = Riddle.query.with_entities(Riddle.category).filter_by(id=today_riddle_id).first()
        if riddle_minimal:
            category = riddle_minimal.category
            print(f"[DEBUG] index: Found category '{category}' for ID {today_riddle_id}") # DEBUG Category
        else: # Handle case where ID is invalid
            print(f"[DEBUG] index: Riddle with ID {today_riddle_id} not found in DB for category fetch.") # DEBUG Invalid ID
            flash("Error loading today's riddle details.", "danger")
            session.pop('riddle_id', None)
            session.pop('riddle_answer', None)
            return redirect(url_for('main.index'))
    elif not riddle_answer: # If no ID and no answer, show empty state
         print("[DEBUG] index: No riddle ID and no answer in session, rendering empty state.") # DEBUG Empty State
         # Pass None explicitly for riddle_id here, but still pass next midnight
         # --- Prepare Response for Empty State ---
         response = make_response(render_template('index.html',
                                riddle_id=None,
                                category=None,
                                answer_display="",
                                stats=stats,
                                avg_incorrect=0,
                                streak_test_mode=streak_test_mode,
                                next_midnight_iso=next_midnight_iso # Pass next midnight
                                ))
         if set_cookie_in_response:
             response.set_cookie(PLAYER_COOKIE_NAME, player_uuid_str, max_age=timedelta(days=365*5), httponly=True, samesite='Lax')
             print(f"[DEBUG] index: Setting cookie on empty state render for {player_uuid_str}") # DEBUG Cookie Set Empty
         return response


    if today_riddle_id is None:
        # ... (handle no riddles) ...
        return render_template('index.html', riddle=None, stats=stats, avg_incorrect=0, streak_test_mode=streak_test_mode)

    # Fetch the full riddle object for display (emoji, category)
    current_riddle = Riddle.query.get(today_riddle_id)
    if not current_riddle: # Handle case where ID is invalid somehow
         flash("Error loading today's riddle.", "danger")
         # Clear potentially bad session data
         session.pop('riddle_id', None)
         session.pop('riddle_answer', None)
         # Redirect to try again
         return redirect(url_for('main.index'))


    was_game_over = incorrect_guesses >= MAX_INCORRECT_GUESSES or \
                    (riddle_answer and {char for char in riddle_answer if char.isalpha()}.issubset(guessed_letters_set))

    # --- Commit DB Changes if needed ---
    if stats_updated_this_request:
        try:
            db.session.commit()
            print(f"[DEBUG] index: Committed DB changes for {player_uuid_str}") # DEBUG DB Commit
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] index: Failed to commit DB changes for {player_uuid_str}: {e}") # DEBUG DB Error
            flash("An error occurred saving your statistics.", "danger")


    # --- Prepare Data for Final Template Render ---
    # ... (calculate game_over, avg_incorrect) ...
    game_over = incorrect_guesses >= MAX_INCORRECT_GUESSES or \
                (riddle_answer and {char for char in riddle_answer if char.isalpha()}.issubset(guessed_letters_set))
    avg_incorrect = (stats['total_incorrect'] / stats['total_games']) if stats['total_games'] > 0 else 0
    alphabet = string.ascii_uppercase

    # DEBUG: Print final values being passed to template
    print(f"[DEBUG] index: Rendering template with riddle_id={today_riddle_id}, category='{category}', answer_display='{riddle_answer}', next_midnight_iso='{next_midnight_iso}'")

    # --- Prepare Final Response ---
    response = make_response(render_template('index.html',
                           riddle_id=today_riddle_id,
                           category=category,
                           answer_display=riddle_answer,
                           guessed_letters=guessed_letters_set,
                           alphabet=alphabet,
                           incorrect_guesses=incorrect_guesses,
                           max_guesses=MAX_INCORRECT_GUESSES,
                           game_over=game_over,
                           stats=stats, # Pass the loaded/updated stats dict
                           avg_incorrect=avg_incorrect,
                           streak_test_mode=streak_test_mode,
                           next_midnight_iso=next_midnight_iso,
                           day_number=day_number # <<< ADD THIS
                           ))
    if set_cookie_in_response:
        # Set persistent cookie on final render if needed
        response.set_cookie(PLAYER_COOKIE_NAME, player_uuid_str, max_age=timedelta(days=365*5), httponly=True, samesite='Lax')
        print(f"[DEBUG] index: Setting cookie on final render for {player_uuid_str}") # DEBUG Cookie Set Final Render

    return response

@main.route('/api/make-guess', methods=['POST'])
def make_guess():
    try: # <<< Add outer try block
        # --- 1. Get Player UUID ---
        player_uuid_str = request.cookies.get(PLAYER_COOKIE_NAME)
        if not player_uuid_str:
            return jsonify({'error': 'Player identifier missing. Please refresh.', 'success': False}), 400

        # --- 2. Get Guess from Request Body ---
        data = request.get_json()
        if not data or 'guess' not in data:
            return jsonify({'error': 'Missing guess data.', 'success': False}), 400

        guessed_letter = data['guess'].lower()

        # --- 3. Basic Validation ---
        if not (guessed_letter and len(guessed_letter) == 1 and guessed_letter.isalpha()):
            return jsonify({'error': 'Invalid guess.', 'success': False}), 400

        # --- 4. Load Current Game State from Session ---
        session_riddle_id = session.get('riddle_id')
        riddle_answer = session.get('riddle_answer', "")
        guessed_letters_set = set(session.get('guessed_letters', []))
        incorrect_guesses = session.get('incorrect_guesses', 0)

        if not session_riddle_id or not riddle_answer:
             return jsonify({'error': 'Game state not found in session. Please refresh.', 'success': False}), 400

        # --- 5. Check if Game Already Over or Letter Already Guessed ---
        answer_chars = {char for char in riddle_answer if char.isalpha()}
        was_game_over = incorrect_guesses >= MAX_INCORRECT_GUESSES or answer_chars.issubset(guessed_letters_set)

        if was_game_over:
            return jsonify({'error': 'Game is already over.', 'success': False}), 400
        if guessed_letter in guessed_letters_set:
            return jsonify({'error': 'Letter already guessed.', 'success': False}), 400

        # --- 6. Process the Guess ---
        session['guessed_letters'] = session.get('guessed_letters', []) + [guessed_letter]
        guessed_letters_set.add(guessed_letter)

        is_correct_guess = guessed_letter in riddle_answer
        if not is_correct_guess:
            session['incorrect_guesses'] += 1
            incorrect_guesses += 1

        session.modified = True

        # --- 7. Check for Win/Loss *after* guess ---
        is_win = answer_chars.issubset(guessed_letters_set)
        is_loss = incorrect_guesses >= MAX_INCORRECT_GUESSES
        is_game_now_over = is_win or is_loss

        stats_updated_data = None

        # --- 8. Update Stats in DB if Game Just Ended ---
        if is_game_now_over:
            now_utc = datetime.now(timezone.utc) # Use UTC now
            today_utc = now_utc.date()           # Use UTC today

            current_test_offset = session.get('test_offset', 0)
            streak_test_mode = session.get('streak_test_mode_flag', False)
            # Determine effective date based on test mode or UTC
            effective_date = EPOCH_DATE + timedelta(days=current_test_offset) if current_test_offset else today_utc

            player_stats_record = PlayerStats.query.get(player_uuid_str)
            new_record_created = False
            if not player_stats_record:
                player_stats_record = PlayerStats(player_uuid=player_uuid_str)
                db.session.add(player_stats_record)
                new_record_created = True
                print(f"[DEBUG] make_guess: Preparing new PlayerStats record in DB for {player_uuid_str}")

            # Ensure record exists before accessing attributes
            if player_stats_record:
                stats = {
                    'total_games': player_stats_record.total_games or 0, # Use default if None
                    'total_incorrect': player_stats_record.total_incorrect or 0,
                    'current_play_streak': player_stats_record.current_play_streak or 0,
                    'longest_play_streak': player_stats_record.longest_play_streak or 0,
                    'current_correct_streak': player_stats_record.current_correct_streak or 0,
                    'longest_correct_streak': player_stats_record.longest_correct_streak or 0,
                    'last_played_datetime': player_stats_record.last_played_datetime
                }
                last_played_datetime = stats['last_played_datetime']

                # --- Update stats dictionary ---
                stats['total_games'] += 1
                stats['total_incorrect'] += incorrect_guesses
                # ... (rest of streak logic remains the same) ...
                played_yesterday = False
                is_new_play_period = True
                if last_played_datetime:
                    # ... (streak date comparison logic) ...
                    if streak_test_mode:
                        time_delta = now_utc - last_played_datetime
                        one_minute_ago = now_utc - timedelta(minutes=1)
                        two_minutes_ago = now_utc - timedelta(minutes=2)
                        if last_played_datetime >= one_minute_ago:
                             is_new_play_period = False
                        elif last_played_datetime >= two_minutes_ago:
                             played_yesterday = True
                    else:
                        yesterday_date = effective_date - timedelta(days=1)
                        if last_played_datetime.date() == effective_date:
                            is_new_play_period = False
                        elif last_played_datetime.date() == yesterday_date:
                            played_yesterday = True

                if is_new_play_period:
                    if played_yesterday:
                        stats['current_play_streak'] += 1
                        stats['current_correct_streak'] = stats['current_correct_streak'] + 1 if is_win else 0
                    else:
                        stats['current_play_streak'] = 1
                        stats['current_correct_streak'] = 1 if is_win else 0

                stats['longest_play_streak'] = max(stats['longest_play_streak'], stats['current_play_streak'])
                stats['longest_correct_streak'] = max(stats['longest_correct_streak'], stats['current_correct_streak'])
                stats['last_played_datetime'] = now_utc
                # --- End stats dictionary update ---

                # --- Update the DB Record ---
                player_stats_record.total_games = stats['total_games']
                player_stats_record.total_incorrect = stats['total_incorrect']
                player_stats_record.current_play_streak = stats['current_play_streak']
                player_stats_record.longest_play_streak = stats['longest_play_streak']
                player_stats_record.current_correct_streak = stats['current_correct_streak']
                player_stats_record.longest_correct_streak = stats['longest_correct_streak']
                player_stats_record.last_played_datetime = stats['last_played_datetime']
                print(f"[DEBUG] make_guess: Updating DB record attributes for {player_uuid_str}")

                try:
                    db.session.commit()
                    print(f"[DEBUG] make_guess: Committed DB changes for {player_uuid_str}")
                    stats_updated_data = {
                        'total_games': stats['total_games'],
                        'avg_incorrect': (stats['total_incorrect'] / stats['total_games']) if stats['total_games'] > 0 else 0,
                        'current_play_streak': stats['current_play_streak'],
                        'longest_play_streak': stats['longest_play_streak'],
                        'current_correct_streak': stats['current_correct_streak'],
                        'longest_correct_streak': stats['longest_correct_streak'],
                        'last_played_datetime_str': stats['last_played_datetime'].strftime('%Y-%m-%d %H:%M:%S UTC')
                    }
                except Exception as e_commit:
                    db.session.rollback()
                    print(f"[ERROR] make_guess: Failed to commit DB changes for {player_uuid_str}: {e_commit}")
                    # Return specific error about saving stats
                    return jsonify({'error': 'Game finished, but failed to save stats.', 'success': False, 'game_over': True, 'is_win': is_win}), 500
            else:
                 # This case should ideally not happen if add worked, but handle it
                 print(f"[ERROR] make_guess: PlayerStats record was unexpectedly None for {player_uuid_str} even after attempting add.")
                 return jsonify({'error': 'Internal error processing game end stats.', 'success': False, 'game_over': True, 'is_win': is_win}), 500


        # --- 9. Prepare JSON Response (Success Path) ---
        response_data = {
            'success': True,
            'guessed_letter': guessed_letter,
            'is_correct': is_correct_guess,
            'incorrect_guesses': incorrect_guesses,
            'game_over': is_game_now_over,
            'is_win': is_win if is_game_now_over else None,
            'guessed_letters': list(guessed_letters_set),
            'stats': stats_updated_data
        }
        return jsonify(response_data)

    except Exception as e: # <<< Catch any unexpected error
        # Log the full error traceback for debugging on the server
        print(f"[ERROR] make_guess: Unhandled exception: {e}")
        import traceback
        traceback.print_exc()
        # Return a generic JSON error response
        return jsonify({'error': 'An unexpected server error occurred.', 'success': False}), 500
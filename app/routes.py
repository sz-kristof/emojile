from flask import (
    render_template, request, redirect, url_for, flash,
    Blueprint, session, jsonify, make_response # Add make_response
)
from . import db
# Import the new model and UUID library
from .models import Riddle, PlayerStats
import string
from datetime import date, timedelta, datetime, time
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
    now = datetime.now()
    today = date.today()
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

    effective_date = test_date_override if test_date_override else today
    # DEBUG: Print effective date
    print(f"[DEBUG] index: Effective Date = {effective_date}")

    # --- Calculate Next Midnight ---
    # Combine the effective_date with midnight time, then add one day
    next_midnight_dt = datetime.combine(effective_date, time.min) + timedelta(days=1)
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
    if not streak_test_mode and last_played_datetime and last_played_datetime.date() < effective_date:
        yesterday_date = effective_date - timedelta(days=1)
        if last_played_datetime.date() < yesterday_date: # Missed one or more real days
            if stats['current_play_streak'] > 0:
                 stats['current_play_streak'] = 0
                 stats_updated_this_request = True
            if stats['current_correct_streak'] > 0:
                 stats['current_correct_streak'] = 0
                 stats_updated_this_request = True

    # --- Determine Today's Riddle ID ---
    today_riddle_id = get_daily_riddle_id(date_to_use=effective_date)
    # DEBUG: Print ID returned by function
    print(f"[DEBUG] index: ID from get_daily_riddle_id = {today_riddle_id}")

    # --- Check if Game State needs reset ---
    session_riddle_id = session.get('riddle_id')
    session_test_offset = session.get('test_offset')
    # Also reset if streak test mode changes
    session_streak_test_mode = session.get('streak_test_mode_flag')

    if session_riddle_id != today_riddle_id or \
       session_test_offset != current_test_offset or \
       session_streak_test_mode != streak_test_mode:
        print(f"[DEBUG] index: Resetting game state. Session ID={session_riddle_id}, Today ID={today_riddle_id}, Session Offset={session_test_offset}, Current Offset={current_test_offset}, Session Streak Mode={session_streak_test_mode}, Current Streak Mode={streak_test_mode}") # DEBUG Reset
        # ... (reset game state logic remains the same) ...
        session.pop('guessed_letters', None)
        session.pop('incorrect_guesses', None)
        session['riddle_id'] = today_riddle_id
        session['test_offset'] = current_test_offset
        session['streak_test_mode_flag'] = streak_test_mode # Store current mode
        # ... (load riddle answer, reset incorrect_guesses) ...
        if today_riddle_id is not None:
            current_riddle = Riddle.query.get(today_riddle_id)
            # *** Store the emoji NAME as the answer ***
            session['riddle_answer'] = current_riddle.name.lower() if current_riddle else ""
        else:
             session['riddle_answer'] = ""
        session['incorrect_guesses'] = 0
        session.modified = True
        # Redirect, preserving parameters
        redirect_params = {}
        if current_test_offset is not None: redirect_params['day_offset'] = current_test_offset
        if streak_test_mode: redirect_params['streak_test_mode'] = 'true'
        # --- Prepare Response for Redirect ---
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

    # --- Handle Letter Guess ---
    guessed_letter = request.args.get('guess', '').lower()
    redirect_after_guess = False

    if guessed_letter and len(guessed_letter) == 1 and guessed_letter.isalpha() and \
       guessed_letter not in guessed_letters_set and not was_game_over:

        # ... (add guess to session, update local sets) ...
        if 'guessed_letters' not in session: session['guessed_letters'] = []
        session['guessed_letters'].append(guessed_letter)
        guessed_letters_set.add(guessed_letter)

        is_correct_guess = guessed_letter in riddle_answer
        if not is_correct_guess:
            session['incorrect_guesses'] += 1
            incorrect_guesses += 1

        session.modified = True
        redirect_after_guess = True

        # --- Check for Win/Loss *after* guess ---
        answer_chars = {char for char in riddle_answer if char.isalpha()}
        is_win = answer_chars.issubset(guessed_letters_set)
        is_loss = incorrect_guesses >= MAX_INCORRECT_GUESSES
        is_game_now_over = is_win or is_loss

        # --- Update Stats if game just ended ---
        if is_game_now_over:
            # Load record again (or prepare to create)
            player_stats_record = PlayerStats.query.get(player_uuid_str)
            if not player_stats_record:
                # Create new record if it's the first game ending for this player
                player_stats_record = PlayerStats(player_uuid=player_uuid_str)
                db.session.add(player_stats_record)
                print(f"[DEBUG] index: Creating new PlayerStats record in DB for {player_uuid_str}") # DEBUG DB Create

            # Update stats dictionary first
            stats['total_games'] += 1
            stats['total_incorrect'] += incorrect_guesses

            played_yesterday = False
            is_new_play_period = True

            # Use last_played_datetime directly from stats dict
            if stats['last_played_datetime']:
                # --- Streak Test Mode Logic (Minutes) ---
                # *** CHANGE HERE ***
                if streak_test_mode:
                    time_delta = now - stats['last_played_datetime'] # Use 'now'
                    one_minute_ago = now - timedelta(minutes=1) # Use 'now'
                    two_minutes_ago = now - timedelta(minutes=2) # Use 'now'

                    if stats['last_played_datetime'] >= one_minute_ago:
                         is_new_play_period = False # Played within the last minute, not a new "day"
                    elif stats['last_played_datetime'] >= two_minutes_ago:
                         played_yesterday = True # Played 1-2 minutes ago ("yesterday")
                    # else: played > 2 mins ago (missed a "day") -> handled by is_new_play_period=True

                else:
                    # --- Normal Mode Logic (Days) ---
                    yesterday_date = effective_date - timedelta(days=1)
                    if stats['last_played_datetime'].date() == effective_date:
                        is_new_play_period = False # Already played today
                    elif stats['last_played_datetime'].date() == yesterday_date:
                        played_yesterday = True # Played yesterday

            # --- Update Streaks based on flags ---
            if is_new_play_period:
                if played_yesterday:
                    stats['current_play_streak'] += 1
                    stats['current_correct_streak'] = stats['current_correct_streak'] + 1 if is_win else 0
                else:
                    stats['current_play_streak'] = 1
                    stats['current_correct_streak'] = 1 if is_win else 0
            # else: played within same period, streaks don't change

            stats['longest_play_streak'] = max(stats['longest_play_streak'], stats['current_play_streak'])
            stats['longest_correct_streak'] = max(stats['longest_correct_streak'], stats['current_correct_streak'])

            # Store current datetime as last played (in stats dict)
            stats['last_played_datetime'] = now # Store the datetime object
            stats_updated_this_request = True # Mark for DB update

            # --- Update the DB Record from the stats dict ---
            player_stats_record.total_games = stats['total_games']
            player_stats_record.total_incorrect = stats['total_incorrect']
            player_stats_record.current_play_streak = stats['current_play_streak']
            player_stats_record.longest_play_streak = stats['longest_play_streak']
            player_stats_record.current_correct_streak = stats['current_correct_streak']
            player_stats_record.longest_correct_streak = stats['longest_correct_streak']
            player_stats_record.last_played_datetime = stats['last_played_datetime']
            print(f"[DEBUG] index: Updating DB record for {player_uuid_str}") # DEBUG DB Update

            # Flash message
            if is_win: flash(f"Correct! The answer was '{riddle_answer.upper()}'. 🎉 Come back tomorrow!", 'success')
            else: flash(f"Too many guesses! The answer was '{riddle_answer.upper()}'. 😥 Come back tomorrow!", 'danger')


    # --- Commit DB Changes if needed ---
    if stats_updated_this_request:
        try:
            db.session.commit()
            print(f"[DEBUG] index: Committed DB changes for {player_uuid_str}") # DEBUG DB Commit
        except Exception as e:
            db.session.rollback()
            print(f"[ERROR] index: Failed to commit DB changes for {player_uuid_str}: {e}") # DEBUG DB Error
            flash("An error occurred saving your statistics.", "danger")


    # --- Redirect if a guess was processed ---
    if redirect_after_guess:
        # --- Prepare Response for Redirect ---
        response = make_response(redirect(url_for('main.index', day_offset=current_test_offset, streak_test_mode='true' if streak_test_mode else None)))
        if set_cookie_in_response:
            # Set persistent cookie on redirect
            response.set_cookie(PLAYER_COOKIE_NAME, player_uuid_str, max_age=timedelta(days=365*5), httponly=True, samesite='Lax')
            print(f"[DEBUG] index: Setting cookie on guess redirect for {player_uuid_str}") # DEBUG Cookie Set Guess Redirect
        return response

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
                           next_midnight_iso=next_midnight_iso
                           ))
    if set_cookie_in_response:
        # Set persistent cookie on final render if needed
        response.set_cookie(PLAYER_COOKIE_NAME, player_uuid_str, max_age=timedelta(days=365*5), httponly=True, samesite='Lax')
        print(f"[DEBUG] index: Setting cookie on final render for {player_uuid_str}") # DEBUG Cookie Set Final Render

    return response
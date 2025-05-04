from . import db
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index
from datetime import datetime # Add datetime import

# Define the new Riddle model structure
class Riddle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emoji = db.Column(db.String(10), unique=True, nullable=False) # Store the single emoji character
    name = db.Column(db.String(100), nullable=False) # Official Unicode name
    category = db.Column(db.String(50), nullable=False) # e.g., "Smileys & People"

    def __repr__(self):
        return f'<Riddle {self.emoji} - {self.name}>'

# --- NEW PlayerStats Model ---
class PlayerStats(db.Model):
    # Use a UUID string as the primary key
    player_uuid = db.Column(db.String(36), primary_key=True)
    total_games = db.Column(db.Integer, default=0, nullable=False)
    total_incorrect = db.Column(db.Integer, default=0, nullable=False)
    current_play_streak = db.Column(db.Integer, default=0, nullable=False)
    longest_play_streak = db.Column(db.Integer, default=0, nullable=False)
    current_correct_streak = db.Column(db.Integer, default=0, nullable=False)
    longest_correct_streak = db.Column(db.Integer, default=0, nullable=False)
    # Store last played time as datetime object
    last_played_datetime = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<PlayerStats {self.player_uuid}>'

# Sample list of emojis with names and categories
# (You'll want a much larger list from a reliable source like Unicode CLDR or a library)
initial_emojis = [
    {"emoji": "😀", "name": "Grinning Face", "category": "Smileys & People"},
    {"emoji": "😂", "name": "Face with Tears of Joy", "category": "Smileys & People"},
    {"emoji": "❤️", "name": "Red Heart", "category": "Symbols"},
    {"emoji": "👍", "name": "Thumbs Up", "category": "People & Body"},
    {"emoji": "🤔", "name": "Thinking Face", "category": "Smileys & People"},
    {"emoji": "🍕", "name": "Pizza", "category": "Food & Drink"},
    {"emoji": "🚀", "name": "Rocket", "category": "Travel & Places"},
    {"emoji": "🎉", "name": "Party Popper", "category": "Activities"},
    {"emoji": "🐶", "name": "Dog Face", "category": "Animals & Nature"},
    {"emoji": "🌳", "name": "Deciduous Tree", "category": "Animals & Nature"},
    {"emoji": "🍎", "name": "Red Apple", "category": "Food & Drink"},
    {"emoji": "⚽", "name": "Soccer Ball", "category": "Activities"},
    {"emoji": "💻", "name": "Laptop", "category": "Objects"},
    {"emoji": "📚", "name": "Books", "category": "Objects"},
    {"emoji": "💡", "name": "Light Bulb", "category": "Objects"},
]

def add_initial_riddles():
    """Adds initial emojis to the database if they don't exist."""
    added_count = 0
    for emoji_data in initial_emojis:
        # Check if an emoji with this character already exists
        exists = Riddle.query.filter_by(emoji=emoji_data["emoji"]).first()
        if not exists:
            new_riddle = Riddle(
                emoji=emoji_data["emoji"],
                name=emoji_data["name"],
                category=emoji_data["category"]
            )
            db.session.add(new_riddle)
            added_count += 1

    if added_count > 0:
        db.session.commit()
        print(f"Added {added_count} new initial emojis.")
    else:
        print("No new initial emojis to add (or all already exist).")

# You might need to adjust your init_db command registration if it was separate
# Ensure it calls this updated add_initial_riddles function.
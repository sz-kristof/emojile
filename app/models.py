from . import db
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Index
from datetime import datetime # Add datetime import

# Define the new Riddle model structure
class Riddle(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    emoji = db.Column(db.String(10), nullable=False) # REMOVED unique=True
    name = db.Column(db.String(100), nullable=False) # Official Unicode name
    category = db.Column(db.String(50), nullable=False) # e.g., "Smileys & People"
    # Add a day_number column, indexed for faster lookups
    day_number = db.Column(db.Integer, nullable=True) # Remove unique=True and index=True
    # --- ADD THIS LINE ---
    game_mode = db.Column(db.String(50), nullable=True, server_default='Classic') # Add game_mode

    # --- ADD THIS TABLE ARGS FOR COMPOSITE INDEX ---
    __table_args__ = (
        db.Index('ix_riddle_game_mode_day_number', 'game_mode', 'day_number', unique=True),
        # db.UniqueConstraint('emoji', 'game_mode', name='uq_emoji_game_mode') # <-- REMOVE OR COMMENT OUT THIS LINE
    )
    # --- END ADDED TABLE ARGS ---

    def __repr__(self):
        # Optional: Add game_mode to the representation
        return f'<Riddle {self.emoji} - {self.name} (Mode: {self.game_mode}, Day: {self.day_number})>'

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

AVAILABLE_MODES = ['Classic', 'Pixelated']
# Sample list of emojis with names and categories
# (You'll want a much larger list from a reliable source like Unicode CLDR or a library)
initial_emojis = [
    # Original 15
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
    {"emoji": "😊", "name": "Smiling Face with Smiling Eyes", "category": "Smileys & People"},
    {"emoji": "😍", "name": "Smiling Face with Heart Eyes", "category": "Smileys & People"},
    {"emoji": "🥳", "name": "Partying Face", "category": "Smileys & People"},
    {"emoji": "🥺", "name": "Pleading Face", "category": "Smileys & People"},
    {"emoji": "😭", "name": "Loudly Crying Face", "category": "Smileys & People"},
    {"emoji": "🥶", "name": "Cold Face", "category": "Smileys & People"},
    {"emoji": "🤯", "name": "Exploding Head", "category": "Smileys & People"},
    {"emoji": "🤖", "name": "Robot", "category": "Smileys & People"},
    {"emoji": "👻", "name": "Ghost", "category": "Smileys & People"},
    {"emoji": "👽", "name": "Alien", "category": "Smileys & People"},
    {"emoji": "👋", "name": "Waving Hand", "category": "People & Body"},
    {"emoji": "🙏", "name": "Folded Hands", "category": "People & Body"},
    {"emoji": "👀", "name": "Eyes", "category": "People & Body"},
    {"emoji": "🧠", "name": "Brain", "category": "People & Body"},
    {"emoji": "👑", "name": "Crown", "category": "Objects"},
    {"emoji": "💍", "name": "Ring", "category": "Objects"},
    {"emoji": "💎", "name": "Gem Stone", "category": "Objects"},
    {"emoji": "💰", "name": "Money Bag", "category": "Objects"},
    {"emoji": "🍔", "name": "Hamburger", "category": "Food & Drink"},
    {"emoji": "🍟", "name": "French Fries", "category": "Food & Drink"},
    {"emoji": "🍦", "name": "Soft Ice Cream", "category": "Food & Drink"},
    {"emoji": "🍓", "name": "Strawberry", "category": "Food & Drink"},
    {"emoji": "🥑", "name": "Avocado", "category": "Food & Drink"},
    {"emoji": "🚗", "name": "Automobile", "category": "Travel & Places"},
    {"emoji": "✈️", "name": "Airplane", "category": "Travel & Places"},
    {"emoji": "🏝️", "name": "Desert Island", "category": "Travel & Places"},
    {"emoji": "☀️", "name": "Sun", "category": "Animals & Nature"},
    {"emoji": "🌙", "name": "Crescent Moon", "category": "Travel & Places"}, # Sometimes Nature, sometimes Travel
    {"emoji": "⭐", "name": "Star", "category": "Travel & Places"}, # Sometimes Symbols
    {"emoji": "🔥", "name": "Fire", "category": "Animals & Nature"}, # Sometimes Symbols
    {"emoji": "🎈", "name": "Balloon", "category": "Activities"},
    {"emoji": "🎁", "name": "Wrapped Gift", "category": "Objects"},
    {"emoji": "🌊", "name": "Water Wave", "category": "Travel & Places"}, # Or Nature
    {"emoji": "🌱", "name": "Seedling", "category": "Animals & Nature"},
    {"emoji": "🌍", "name": "Earth Globe Americas", "category": "Travel & Places"},
    {"emoji": "⏰", "name": "Alarm Clock", "category": "Objects"},
    {"emoji": "✨", "name": "Sparkles", "category": "Activities"},
]

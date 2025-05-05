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
    # Add a day_number column, indexed for faster lookups
    day_number = db.Column(db.Integer, unique=True, nullable=True, index=True)

    def __repr__(self):
        return f'<Riddle {self.emoji} - {self.name} (Day {self.day_number})>'

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

def add_initial_riddles():
    """Adds initial emojis and assigns sequential day_numbers if missing."""
    from sqlalchemy import func # Import func for max()

    # Find the maximum assigned day_number in the database
    max_day_num_result = db.session.query(func.max(Riddle.day_number)).scalar()
    next_day_num = (max_day_num_result + 1) if max_day_num_result is not None else 0
    print(f"Starting next day number assignment from: {next_day_num}")

    added_count = 0
    for emoji_data in initial_emojis:
        exists = Riddle.query.filter_by(emoji=emoji_data["emoji"]).first()
        if not exists:
            new_riddle = Riddle(
                emoji=emoji_data["emoji"],
                name=emoji_data["name"],
                category=emoji_data["category"],
                day_number=next_day_num # Assign the next available day number
            )
            db.session.add(new_riddle)
            print(f"  Adding '{emoji_data['name']}' with day_number {next_day_num}")
            next_day_num += 1 # Increment for the next new emoji
            added_count += 1
        # Optional: Assign day_number to existing riddles if they lack one
        # This is better handled by a one-time migration script (see Step 2c)
        # elif exists and exists.day_number is None:
        #     # Handle assigning day_number to existing ones if needed, carefully
        #     pass

    if added_count > 0:
        try:
            db.session.commit()
            print(f"Added {added_count} new initial emojis with day numbers.")
        except Exception as e:
            db.session.rollback()
            print(f"Error adding new emojis: {e}")
    else:
        print("No new initial emojis to add (or all already exist).")

# You might need to adjust your init_db command registration if it was separate
# Ensure it calls this updated add_initial_riddles function.
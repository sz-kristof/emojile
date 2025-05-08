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
    game_mode = db.Column(db.String(50), primary_key=True) # Added: Part of composite PK
    total_games = db.Column(db.Integer, default=0, nullable=False)
    total_incorrect = db.Column(db.Integer, default=0, nullable=False)
    current_play_streak = db.Column(db.Integer, default=0, nullable=False)
    longest_play_streak = db.Column(db.Integer, default=0, nullable=False)
    current_correct_streak = db.Column(db.Integer, default=0, nullable=False)
    longest_correct_streak = db.Column(db.Integer, default=0, nullable=False)
    # Store last played time as datetime object
    last_played_datetime = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f'<PlayerStats {self.player_uuid} Mode: {self.game_mode}>' # Updated repr

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
    {"emoji": "🚀", "name": "Rocket", "category": "Travel & Places"},
    {"emoji": "🎉", "name": "Party Popper", "category": "Activities"},
    {"emoji": "🐶", "name": "Dog Face", "category": "Animals & Nature"},
    {"emoji": "🌳", "name": "Deciduous Tree", "category": "Animals & Nature"},
    {"emoji": "🍎", "name": "Red Apple", "category": "Food & Drink"},
    {"emoji": "⚽", "name": "Soccer Ball", "category": "Activities"},
    {"emoji": "😊", "name": "Smiling Face with Smiling Eyes", "category": "Smileys & People"},
    {"emoji": "😍", "name": "Smiling Face with Heart Eyes", "category": "Smileys & People"},
    {"emoji": "🥳", "name": "Partying Face", "category": "Smileys & People"},
    {"emoji": "🥺", "name": "Pleading Face", "category": "Smileys & People"},
    {"emoji": "😭", "name": "Loudly Crying Face", "category": "Smileys & People"},
    {"emoji": "🥶", "name": "Cold Face", "category": "Smileys & People"},
    {"emoji": "🤯", "name": "Exploding Head", "category": "Smileys & People"},
    {"emoji": "👋", "name": "Waving Hand", "category": "People & Body"},
    {"emoji": "🙏", "name": "Folded Hands", "category": "People & Body"},
    {"emoji": "👀", "name": "Eyes", "category": "People & Body"},
    {"emoji": "🧠", "name": "Brain", "category": "People & Body"},
    {"emoji": "👑", "name": "Crown", "category": "Objects"},
    {"emoji": "💍", "name": "Ring", "category": "Objects"},
    {"emoji": "💎", "name": "Gem Stone", "category": "Objects"},
    {"emoji": "💰", "name": "Money Bag", "category": "Objects"},
    {"emoji": "🍟", "name": "French Fries", "category": "Food & Drink"},
    {"emoji": "🍦", "name": "Soft Ice Cream", "category": "Food & Drink"},
    {"emoji": "🚗", "name": "Automobile", "category": "Travel & Places"},
    {"emoji": "✈️", "name": "Airplane", "category": "Travel & Places"},
    {"emoji": "🏝️", "name": "Desert Island", "category": "Travel & Places"},
    {"emoji": "🌙", "name": "Crescent Moon", "category": "Travel & Places"}, # Sometimes Nature, sometimes Travel
    {"emoji": "🎈", "name": "Balloon", "category": "Activities"},
    {"emoji": "🎁", "name": "Wrapped Gift", "category": "Objects"},
    {"emoji": "🌊", "name": "Water Wave", "category": "Travel & Places"}, # Or Nature
    {"emoji": "🌱", "name": "Seedling", "category": "Animals & Nature"},
    {"emoji": "🌍", "name": "Earth Globe Americas", "category": "Travel & Places"},
    {"emoji": "⏰", "name": "Alarm Clock", "category": "Objects"},
    {"emoji": "✨", "name": "Sparkles", "category": "Activities"},
    {"emoji": "🧿", "name": "Nazar Amulet", "category": "Objects"}, # Culturally specific, might be hard
    {"emoji": "🧩", "name": "Puzzle Piece", "category": "Activities"}, # Abstract concept
    {"emoji": "⚖️", "name": "Balance Scale", "category": "Objects"}, # Represents a concept
    {"emoji": "🎭", "name": "Performing Arts", "category": "Activities"}, # Represents a broader category
    {"emoji": "⏳", "name": "Hourglass Not Done", "category": "Objects"}, # Represents time, process
    {"emoji": "🪬", "name": "Hamsa", "category": "Objects"},
    {"emoji": "✒️", "name": "Black Nib", "category": "Objects"},
    {"emoji": "📜", "name": "Scroll", "category": "Objects"}, # Historical object, less common today
    {"emoji": "🔬", "name": "Microscope", "category": "Objects"}, # Scientific instrument
    {"emoji": "⚗️", "name": "Alembic", "category": "Objects"}, # Less common object, scientific/historical
    {"emoji": "🧮", "name": "Abacus", "category": "Objects"}, # Historical calculating tool
    {"emoji": "🦾", "name": "Mechanical Arm", "category": "People & Body"}, # Sci-fi, specific
    {"emoji": "🪐", "name": "Ringed Planet", "category": "Travel & Places"}, # Specific celestial body
    {"emoji": "⚜️", "name": "Fleur-de-lis", "category": "Symbols"}, # Specific symbol, historical/cultural
    {"emoji": "⚛️", "name": "Atom Symbol", "category": "Symbols"}, # Scientific symbol, abstract
    {"emoji": "⚕️", "name": "Medical Symbol", "category": "Symbols"}, # Caduceus or Rod of Asclepius, specific
    {"emoji": "☯️", "name": "Yin Yang", "category": "Symbols"}, # Philosophical concept
    {"emoji": "⛩️", "name": "Shinto Shrine", "category": "Travel & Places"}, # Specific cultural/religious building
    {"emoji": "🕋", "name": "Kaaba", "category": "Travel & Places"}, # Specific religious building
    {"emoji": "🪔", "name": "Diya Lamp", "category": "Objects"}, # Culturally specific (Hindu, Sikh, Jain festivals)
    {"emoji": "🪆", "name": "Nesting Dolls", "category": "Objects"}, # Matryoshka, culturally specific
    {"emoji": "🕎", "name": "Menorah", "category": "Symbols"}, # Religious candelabrum (Hanukkah)
    {"emoji": "☬", "name": "Khanda", "category": "Symbols"}, # Symbol of Sikhism
    {"emoji": "🕉️", "name": "Om", "category": "Symbols"}, # Sacred sound and spiritual icon in Hinduism
    {"emoji": "☣️", "name": "Biohazard", "category": "Symbols"}, # Warning symbol for biological hazards
    {"emoji": "☢️", "name": "Radioactive", "category": "Symbols"}, # Warning symbol for radiation
    {"emoji": "⚓", "name": "Anchor", "category": "Objects"}, # Nautical device, also symbolizes stability
    {"emoji": "🧫", "name": "Petri Dish", "category": "Objects"}, # Laboratory equipment
    {"emoji": "🧪", "name": "Test Tube", "category": "Objects"}, # Laboratory equipment
    {"emoji": "🪧", "name": "Placard", "category": "Objects"}, # Can be abstract depending on content (not shown)
    {"emoji": "🪪", "name": "Identification Card", "category": "Objects"}, # Represents identity, access
    {"emoji": "🧰", "name": "Toolbox", "category": "Objects"}, # Represents tools, fixing, building
    {"emoji": "🧱", "name": "Brick", "category": "Objects"}, # Represents construction, foundation
    {"emoji": "🧯", "name": "Fire Extinguisher", "category": "Objects"}, # Specific safety device
    {"emoji": "🪜", "name": "Ladder", "category": "Objects"}, # Represents climbing, progress, levels
    {"emoji": "🪩", "name": "Mirror Ball", "category": "Activities"}, # Disco ball, specific to parties/events
    {"emoji": "⚱️", "name": "Funeral Urn", "category": "Objects"},
    {"emoji": "🏺", "name": "Amphora", "category": "Objects"}, # Ancient jar, historical
    {"emoji": "⚰️", "name": "Coffin", "category": "Objects"}, # Specific funereal object
    {"emoji": "🪦", "name": "Headstone", "category": "Objects"}, # Grave marker
    {"emoji": "🩺", "name": "Stethoscope", "category": "Objects"}, # Medical diagnostic tool
    {"emoji": "🦯", "name": "White Cane", "category": "Objects"}, # Mobility aid for visually impaired
    {"emoji": "🪗", "name": "Accordion", "category": "Objects"}, # Musical instrument
    {"emoji": "🪢", "name": "Knot", "category": "Objects"}, # Represents tying, complexity, a bond
    {"emoji": "🪄", "name": "Magic Wand", "category": "Objects"}, # Associated with magic, illusion # Specific cultural/ritual object
    {"emoji": "🪱", "name": "Worm", "category": "Animals & Nature"}, # Can be surprisingly tricky
    {"emoji": "🦠", "name": "Microbe", "category": "Animals & Nature"}, # Scientific, specific
    {"emoji": "🧾", "name": "Receipt", "category": "Objects"}, # Mundane but specific
    {"emoji": "⚙️", "name": "Gear", "category": "Objects"}, # Represents mechanics, process, settings
    {"emoji": "🔗", "name": "Link", "category": "Objects"},
    {"emoji": "🪝", "name": "Hook", "category": "Objects"}, # Simple, but can be abstract (e.g., "hooked on a feeling")
    {"emoji": "🪞", "name": "Mirror", "category": "Objects"}, # Reflection, self, truth
    {"emoji": "🪟", "name": "Window", "category": "Objects"}, # Opportunity, perspective, looking out/in
    {"emoji": "🪠", "name": "Plunger", "category": "Objects"}, # Mundane, specific, problem-solving
    {"emoji": "🪤", "name": "Mouse Trap", "category": "Objects"}, # Deception, capture, a plan
    {"emoji": "🪵", "name": "Wood", "category": "Objects"}, # Natural material, building, basic
    {"emoji": "🛖", "name": "Hut", "category": "Travel & Places"},
    {"emoji": "🔩", "name": "Nut and Bolt", "category": "Objects"},
    {"emoji": "🛗", "name": "Elevator", "category": "Objects"},
    {"emoji": "📯", "name": "Postal Horn", "category": "Objects"}, # Historical communication device
    {"emoji": "🎚️", "name": "Level Slider", "category": "Objects"}, # Audio/control interface element
    {"emoji": "🎛️", "name": "Control Knobs", "category": "Objects"}, # Audio/control interface element
    {"emoji": "🎞️", "name": "Film Frames", "category": "Objects"}, # Component of motion picture film
    {"emoji": "📽️", "name": "Film Projector", "category": "Objects"}, # Device for showing movies (older tech)
    {"emoji": "📼", "name": "Videocassette", "category": "Objects"}, # Retro video recording medium (VHS)
    {"emoji": "🪘", "name": "Long Drum", "category": "Objects"}, # Percussion instrument (e.g., Djembe, Conga)
    {"emoji": "🪕", "name": "Banjo", "category": "Objects"},
    {"emoji": "🥌", "name": "Curling Stone", "category": "Activities"},
    {"emoji": "🛢️", "name": "Oil Drum", "category": "Objects"}, # Industrial container, can represent resources/pollution
    {"emoji": "🔭", "name": "Telescope", "category": "Objects"}, # Scientific instrument for astronomy
    {"emoji": "📡", "name": "Satellite Antenna", "category": "Objects"}, # Communication technology
    {"emoji": "🧷", "name": "Safety Pin", "category": "Objects"}, # Fastening device, can be punk symbol
    {"emoji": "🧹", "name": "Broom", "category": "Objects"},
    {"emoji": "⛓️", "name": "Chains", "category": "Objects"}, # Represents connection, restraint, industry
    {"emoji": "🪚", "name": "Carpentry Saw", "category": "Objects"}, # Tool for cutting wood
    {"emoji": "🪛", "name": "Screwdriver", "category": "Objects"}, # Tool for screws
    {"emoji": "🧭", "name": "Compass", "category": "Objects"}, # Navigation, direction
    {"emoji": "🥽", "name": "Goggles", "category": "Objects"}, # Eye protection, various uses (skiing, swimming, lab)
    {"emoji": "🥼", "name": "Lab Coat", "category": "Objects"}, # Scientific/medical attire
    {"emoji": "🪒", "name": "Razor", "category": "Objects"}, # Shaving tool
    {"emoji": "💈", "name": "Barber Pole", "category": "Objects"}, # Symbol for barbershop
    {"emoji": "♾️", "name": "Infinity", "category": "Symbols"},
    {"emoji": "🧐", "name": "Face With Monocle", "category": "Smileys & People"},
    {"emoji": "🤫", "name": "Shushing Face", "category": "Smileys & People"},
    {"emoji": "🦥", "name": "Sloth", "category": "Animals & Nature"},
    {"emoji": "🦦", "name": "Otter", "category": "Animals & Nature"},
    {"emoji": "🦟", "name": "Mosquito", "category": "Animals & Nature"},
    {"emoji": "🪷", "name": "Lotus", "category": "Animals & Nature"}, # Flower, symbolic
    {"emoji": "🧋", "name": "Bubble Tea", "category": "Food & Drink"},
    {"emoji": "🫕", "name": "Fondue", "category": "Food & Drink"}, # Communal melted cheese/chocolate dish
    {"emoji": "🪁", "name": "Kite", "category": "Activities"},
    {"emoji": "🛎️", "name": "Bellhop Bell", "category": "Objects"}, # Service bell
    {"emoji": "🧳", "name": "Luggage", "category": "Objects"}, # Travel bags
    {"emoji": "🕰️", "name": "Mantelpiece Clock", "category": "Objects"}, # Decorative clock
    {"emoji": "🗜️", "name": "Clamp", "category": "Objects"}, # Tool for holding things tightly
    {"emoji": "🧵", "name": "Thread", "category": "Objects"}, # Used for sewing
    {"emoji": "🪙", "name": "Coin", "category": "Objects"}, # Metal money
    {"emoji": "🔱", "name": "Trident Emblem", "category": "Symbols"},
    {"emoji": "🪃", "name": "Boomerang", "category": "Objects"}, # Throwing tool, returns
    {"emoji": "🪅", "name": "Pinata", "category": "Activities"}, # Festive container broken to release treats
    {"emoji": "🩰", "name": "Ballet Shoes", "category": "Activities"}, # Dance footwear
    {"emoji": "🪴", "name": "Potted Plant", "category": "Animals & Nature"}, # Houseplant
    {"emoji": "🛟", "name": "Ring Buoy", "category": "Objects"}, # Life preserver
    {"emoji": "🫧", "name": "Bubbles", "category": "Objects"}, # Soap bubbles, effervescence
    {"emoji": "🪸", "name": "Coral", "category": "Animals & Nature"}, # Marine invertebrate
    {"emoji": "🦪", "name": "Oyster", "category": "Food & Drink"}, # Shellfish, sometimes contains pearl
    {"emoji": "🫙", "name": "Jar", "category": "Objects"}, # Glass container
    {"emoji": "🫘", "name": "Beans", "category": "Food & Drink"},
    {"emoji": "🐻", "name": "Bear Face", "category": "Animals & Nature"},
    {"emoji": "🐼", "name": "Panda Face", "category": "Animals & Nature"},
    {"emoji": "🐾", "name": "Paw Prints", "category": "Animals & Nature"}, # Animal footprints
    {"emoji": "🐔", "name": "Chicken", "category": "Animals & Nature"}, # Farm bird
    {"emoji": "🦅", "name": "Eagle", "category": "Animals & Nature"}, # Bird of prey
    {"emoji": "🐸", "name": "Frog Face", "category": "Animals & Nature"},
    {"emoji": "🐚", "name": "Spiral Shell", "category": "Objects"}, # Seashell
    {"emoji": "💅", "name": "Nail Polish", "category": "People & Body"}, # Cosmetic for nails
    {"emoji": "🧥", "name": "Coat", "category": "Objects"}, # Outerwear garment
    {"emoji": "🧢", "name": "Billed Cap", "category": "Objects"}, # Hat with a brim
    {"emoji": "🧣", "name": "Scarf", "category": "Objects"}, # Neckwear for warmth
    {"emoji": "👘", "name": "Kimono", "category": "Objects"}, # Traditional Japanese garment
    {"emoji": "🥻", "name": "Sari", "category": "Objects"}, # Garment worn in South Asia
    {"emoji": "🩱", "name": "One-Piece Swimsuit", "category": "Objects"},
    {"emoji": "🩲", "name": "Briefs", "category": "Objects"}, # Men's underwear
    {"emoji": "🩳", "name": "Shorts", "category": "Objects"},
    {"emoji": "👔", "name": "Necktie", "category": "Objects"},
    {"emoji": "👕", "name": "T-Shirt", "category": "Objects"},
    {"emoji": "🦐", "name": "Shrimp", "category": "Food & Drink"}, # Often Food, can be Animal
    {"emoji": "🦑", "name": "Squid", "category": "Animals & Nature"}, # Often Food, can be Animal
    {"emoji": "🐝", "name": "Honeybee", "category": "Animals & Nature"},
    {"emoji": "🐞", "name": "Lady Beetle", "category": "Animals & Nature"}, # Ladybug
    {"emoji": "🦗", "name": "Cricket", "category": "Animals & Nature"}, # Insect
    {"emoji": "🕸️", "name": "Spider Web", "category": "Animals & Nature"},
    {"emoji": "🦂", "name": "Scorpion", "category": "Animals & Nature"},
    {"emoji": "💐", "name": "Bouquet", "category": "Animals & Nature"}, # Bundle of flowers
    {"emoji": "🌸", "name": "Cherry Blossom", "category": "Animals & Nature"},
    {"emoji": "🌹", "name": "Rose", "category": "Animals & Nature"},
    {"emoji": "🌺", "name": "Hibiscus", "category": "Animals & Nature"},
    {"emoji": "🌻", "name": "Sunflower", "category": "Animals & Nature"},
    {"emoji": "🌷", "name": "Tulip", "category": "Animals & Nature"},
    {"emoji": "🌲", "name": "Evergreen Tree", "category": "Animals & Nature"},
    {"emoji": "🌴", "name": "Palm Tree", "category": "Animals & Nature"},
    {"emoji": "🍁", "name": "Maple Leaf", "category": "Animals & Nature"},
    {"emoji": "🍀", "name": "Four Leaf Clover", "category": "Animals & Nature"}, # Symbol of luck
    {"emoji": "🌿", "name": "Herb", "category": "Animals & Nature"},
    {"emoji": "😁", "name": "Beaming Face With Smiling Eyes", "category": "Smileys & People"},
    {"emoji": "🤣", "name": "Rolling On The Floor Laughing", "category": "Smileys & People"},
    {"emoji": "😉", "name": "Winking Face", "category": "Smileys & People"},
    {"emoji": "🥰", "name": "Smiling Face with Hearts", "category": "Smileys & People"},
    {"emoji": "😋", "name": "Face Savoring Food", "category": "Smileys & People"},
    {"emoji": "🤩", "name": "Star-Struck", "category": "Smileys & People"},
    {"emoji": "🤗", "name": "Hugging Face", "category": "Smileys & People"},
    {"emoji": "🤭", "name": "Face With Hand Over Mouth", "category": "Smileys & People"},
    {"emoji": "🤨", "name": "Face With Raised Eyebrow", "category": "Smileys & People"},
    {"emoji": "🙄", "name": "Face With Rolling Eyes", "category": "Smileys & People"},
    {"emoji": "😷", "name": "Face With Medical Mask", "category": "Smileys & People"},
    {"emoji": "😇", "name": "Smiling Face With Halo", "category": "Smileys & People"},
    {"emoji": "🤠", "name": "Cowboy Hat Face", "category": "Smileys & People"},
    {"emoji": "🤡", "name": "Clown Face", "category": "Smileys & People"},
    {"emoji": "🤖", "name": "Robot Face", "category": "Smileys & People"},
    {"emoji": "💩", "name": "Pile Of Poo", "category": "Smileys & People"}, # Humorous
    {"emoji": "😺", "name": "Grinning Cat Face", "category": "Smileys & People"}, # Cat variant
    {"emoji": "🙈", "name": "See-No-Evil Monkey", "category": "Smileys & People"},
    {"emoji": "😃", "name": "Grinning Face With Big Eyes", "category": "Smileys & People"},
    {"emoji": "😄", "name": "Grinning Face With Smiling Eyes", "category": "Smileys & People"},
    {"emoji": "😅", "name": "Grinning Face With Sweat", "category": "Smileys & People"},
    {"emoji": "😆", "name": "Grinning Squinting Face", "category": "Smileys & People"},
    {"emoji": "😎", "name": "Smiling Face With Sunglasses", "category": "Smileys & People"},
    {"emoji": "😘", "name": "Face Blowing A Kiss", "category": "Smileys & People"},
    {"emoji": "😗", "name": "Kissing Face", "category": "Smileys & People"},
    {"emoji": "😙", "name": "Kissing Face With Smiling Eyes", "category": "Smileys & People"},
    {"emoji": "😚", "name": "Kissing Face With Closed Eyes", "category": "Smileys & People"},
    {"emoji": "🙂", "name": "Slightly Smiling Face", "category": "Smileys & People"},
    {"emoji": "😐", "name": "Neutral Face", "category": "Smileys & People"},
    {"emoji": "😑", "name": "Expressionless Face", "category": "Smileys & People"},
    {"emoji": "😶", "name": "Face Without Mouth", "category": "Smileys & People"},
    {"emoji": "😏", "name": "Smirking Face", "category": "Smileys & People"},
    {"emoji": "👾", "name": "Alien Monster", "category": "Smileys & People"},
    {"emoji": "😣", "name": "Persevering Face", "category": "Smileys & People"},
    {"emoji": "😥", "name": "Sad But Relieved Face", "category": "Smileys & People"},
    {"emoji": "😮", "name": "Face With Open Mouth", "category": "Smileys & People"},
    {"emoji": "🤐", "name": "Zipper-Mouth Face", "category": "Smileys & People"},
    {"emoji": "😯", "name": "Hushed Face", "category": "Smileys & People"},
    {"emoji": "😪", "name": "Sleepy Face", "category": "Smileys & People"},
    {"emoji": "😫", "name": "Tired Face", "category": "Smileys & People"},
    {"emoji": "🥱", "name": "Yawning Face", "category": "Smileys & People"},
    {"emoji": "😴", "name": "Sleeping Face", "category": "Smileys & People"},
    {"emoji": "😌", "name": "Relieved Face", "category": "Smileys & People"},
    {"emoji": "😛", "name": "Face With Tongue", "category": "Smileys & People"},
    {"emoji": "😜", "name": "Winking Face With Tongue", "category": "Smileys & People"},
    {"emoji": "😝", "name": "Squinting Face With Tongue", "category": "Smileys & People"},
    {"emoji": "🤤", "name": "Drooling Face", "category": "Smileys & People"},
    {"emoji": "😒", "name": "Unamused Face", "category": "Smileys & People"},
    {"emoji": "😓", "name": "Downcast Face With Sweat", "category": "Smileys & People"},
    {"emoji": "😔", "name": "Pensive Face", "category": "Smileys & People"},
    {"emoji": "😕", "name": "Confused Face", "category": "Smileys & People"},
    {"emoji": "🙃", "name": "Upside-Down Face", "category": "Smileys & People"},
    {"emoji": "🫣", "name": "Face With Peeking Eye", "category": "Smileys & People"},
    {"emoji": "🫡", "name": "Saluting Face", "category": "Smileys & People"},
    {"emoji": "🫥", "name": "Face With Open Eyes and Hand Over Mouth", "category": "Smileys & People"},
    {"emoji": "😲", "name": "Astonished Face", "category": "Smileys & People"},
    {"emoji": "😳", "name": "Flushed Face", "category": "Smileys & People"},
    {"emoji": "🥵", "name": "Hot Face", "category": "Smileys & People"},
    {"emoji": "🥴", 'name': 'Woozy Face', 'category': "Smileys & People"},
    {"emoji": "😵", 'name': 'Dizzy Face', 'category': "Smileys & People"},
    {"emoji": "🤑", "name": "Money-Mouth Face", "category": "Smileys & People"},
    {"emoji": "☹️", "name": "Frowning Face", "category": "Smileys & People"}, # Note: This might render as ☹ by itself
    {"emoji": "🙁", "name": "Slightly Frowning Face", "category": "Smileys & People"},
    {"emoji": "😖", "name": "Confounded Face", "category": "Smileys & People"},
    {"emoji": "😞", "name": "Disappointed Face", "category": "Smileys & People"},
    {"emoji": "😟", "name": "Worried Face", "category": "Smileys & People"},
    {"emoji": "😤", "name": "Face With Steam From Nose", "category": "Smileys & People"},
    {"emoji": "😢", "name": "Crying Face", "category": "Smileys & People"},
    {"emoji": "😦", "name": "Frowning Face With Open Mouth", "category": "Smileys & People"},
    {"emoji": "😧", "name": "Anguished Face", "category": "Smileys & People"},
    {"emoji": "😨", "name": "Fearful Face", "category": "Smileys & People"},
    {"emoji": "😩", "name": "Weary Face", "category": "Smileys & People"},
    {"emoji": "😬", "name": "Grimacing Face", "category": "Smileys & People"},
    {"emoji": "😰", "name": "Anxious Face With Sweat", "category": "Smileys & People"},
    {"emoji": "😱", "name": "Face Screaming In Fear", "category": "Smileys & People"},
    {"emoji": "🤪", "name": "Zany Face", "category": "Smileys & People"},
    {"emoji": "😡", "name": "Pouting Face", "category": "Smileys & People"},
    {"emoji": "😠", "name": "Angry Face", "category": "Smileys & People"},
    {"emoji": "🤬", "name": "Face With Symbols On Mouth", "category": "Smileys & People"},
    {"emoji": "🤒", "name": "Face With Thermometer", "category": "Smileys & People"},
    {"emoji": "🤕", "name": "Face With Head-Bandage", "category": "Smileys & People"},
    {"emoji": "🤢", "name": "Nauseated Face", "category": "Smileys & People"},
    {"emoji": "🤮", "name": "Face Vomiting", "category": "Smileys & People"},
    {"emoji": "🤧", "name": "Sneezing Face", "category": "Smileys & People"},
    {"emoji": "🤥", "name": "Lying Face", "category": "Smileys & People"},
    {"emoji": "🤓", "name": "Nerd Face", "category": "Smileys & People"},
    {"emoji": "😈", "name": "Smiling Face With Horns", "category": "Smileys & People"},
    {"emoji": "👿", "name": "Angry Face With Horns", "category": "Smileys & People"}, # Also known as Imp
    {"emoji": "👹", "name": "Ogre", "category": "Smileys & People"}, # Japanese Ogre
    {"emoji": "👺", "name": "Goblin", "category": "Smileys & People"}, # Japanese Goblin (Tengu)
    {"emoji": "💀", "name": "Skull", "category": "Smileys & People"},
    {"emoji": "☠️", "name": "Skull And Crossbones", "category": "Smileys & People"},
    {"emoji": "👾", "name": "Alien Monster", "category": "Smileys & People"},
    {"emoji": "😸", "name": "Grinning Cat Face With Smiling Eyes", "category": "Smileys & People"},
    {"emoji": "😹", "name": "Cat Face With Tears Of Joy", "category": "Smileys & People"},
    {"emoji": "😻", "name": "Smiling Cat Face With Heart-Eyes", "category": "Smileys & People"},
    {"emoji": "😼", "name": "Cat Face With Wry Smile", "category": "Smileys & People"},
    {"emoji": "😽", "name": "Kissing Cat Face", "category": "Smileys & People"},
    {"emoji": "🙀", "name": "Weary Cat Face", "category": "Smileys & People"},
    {"emoji": "😿", "name": "Crying Cat Face", "category": "Smileys & People"},
    {"emoji": "😾", "name": "Pouting Cat Face", "category": "Smileys & People"},
    {"emoji": "🙉", "name": "Hear-No-Evil Monkey", "category": "Smileys & People"},
    {"emoji": "🙊", "name": "Speak-No-Evil Monkey", "category": "Smileys & People"},
    {"emoji": "👶", "name": "Baby", "category": "Smileys & People"},
    {"emoji": "🧒", "name": "Child", "category": "Smileys & People"}, # Gender-neutral child
    {"emoji": "👦", "name": "Boy", "category": "Smileys & People"},
    {"emoji": "👧", "name": "Girl", "category": "Smileys & People"},
    {"emoji": "🧑", "name": "Adult", "category": "Smileys & People"}, # Gender-neutral adult
    {"emoji": "👨", "name": "Man", "category": "Smileys & People"},
    {"emoji": "👩", "name": "Woman", "category": "Smileys & People"},
    {"emoji": "🧓", "name": "Older Adult", "category": "Smileys & People"},
    {"emoji": "👲", "name": "Man with Skullcap", "category": "Smileys & People"}, # Genius: Man With Gua Pi Mao
    {"emoji": "👳", "name": "Man Wearing Turban", "category": "Smileys & People"},
    {"emoji": "👮", "name": "Police Officer", "category": "Smileys & People"},
    {"emoji": "👷", "name": "Construction Worker", "category": "Smileys & People"},
    {"emoji": "💂", "name": "Guardsman", "category": "Smileys & People"}, # Unicode: Guard
    {"emoji": "👴", "name": "Older Man", "category": "Smileys & People"},
    {"emoji": "👵", "name": "Older Woman", "category": "Smileys & People"},
    {"emoji": "👸", "name": "Princess", "category": "Smileys & People"},
    {"emoji": "🤴", "name": "Prince", "category": "Smileys & People"},
    {"emoji": "👰", "name": "Person With Veil", "category": "Smileys & People"}, # Often Bride
    {"emoji": "🤰", "name": "Pregnant Woman", "category": "Smileys & People"},
    {"emoji": "🤱", "name": "Breast-Feeding", "category": "Smileys & People"},
    {"emoji": "👼", "name": "Baby Angel", "category": "Smileys & People"}, # Unicode: Angel
    {"emoji": "🎅", "name": "Santa Claus", "category": "Smileys & People"},
    {"emoji": "🤶", "name": "Mrs Claus", "category": "Smileys & People"}, # Mother Christmas
    {"emoji": "🦸", "name": "Superhero", "category": "Smileys & People"},
    {"emoji": "🦹", "name": "Supervillain", "category": "Smileys & People"},
    {"emoji": "🧙", "name": "Mage", "category": "Smileys & People"}, # Can be Wizard or Witch
    {"emoji": "🧚", "name": "Fairy", "category": "Smileys & People"},
    {"emoji": "🧛", "name": "Vampire", "category": "Smileys & People"},
    {"emoji": "🧜", "name": "Merperson", "category": "Smileys & People"}, # Merfolk, Mermaid, Merman
    {"emoji": "🧝", "name": "Elf", "category": "Smileys & People"},
    {"emoji": "🧞", "name": "Genie", "category": "Smileys & People"}, # Can be male or female
    {"emoji": "🧟", "name": "Zombie", "category": "Smileys & People"},
    {"emoji": "🙍", "name": "Person Frowning", "category": "Smileys & People"},
    {"emoji": "🙎", "name": "Person Pouting", "category": "Smileys & People"},
    {"emoji": "🙅", "name": "Person Gesturing No", "category": "Smileys & People"},
    {"emoji": "🙆", "name": "Person Gesturing Ok", "category": "Smileys & People"},
    {"emoji": "💁", "name": "Person Tipping Hand", "category": "Smileys & People"}, # Often Information Desk Person
    {"emoji": "🙋", "name": "Person Raising Hand", "category": "Smileys & People"},
    {"emoji": "🙇", "name": "Person Bowing", "category": "Smileys & People"}, # Deeply Bowing
    {"emoji": "🤦", "name": "Person Facepalming", "category": "Smileys & People"},
    {"emoji": "🤷", "name": "Person Shrugging", "category": "Smileys & People"},
    {"emoji": "💆", "name": "Person Getting Massage", "category": "Smileys & People"},
    {"emoji": "💇", "name": "Person Getting Haircut", "category": "Smileys & People"},
    {"emoji": "🚶", "name": "Person Walking", "category": "Smileys & People"},
    {"emoji": "🏃", "name": "Person Running", "category": "Smileys & People"},
    {"emoji": "💃", "name": "Woman Dancing", "category": "Smileys & People"}, # Unicode: Dancer
    {"emoji": "🕺", "name": "Man Dancing", "category": "Smileys & People"},
    {"emoji": "👯", "name": "People With Bunny Ears Partying", "category": "Smileys & People"}, # Often "Woman with Bunny Ears"
    {"emoji": "🧖", "name": "Person in Steamy Room", "category": "Smileys & People"},
    {"emoji": "🧗", "name": "Person Climbing", "category": "Smileys & People"},
    {"emoji": "🧘", "name": "Person in Lotus Position", "category": "Smileys & People"},
    {"emoji": "✍️", "name": "Writing Hand", "category": "People & Body"},
    {"emoji": "👏", "name": "Clapping Hands", "category": "People & Body"},
    {"emoji": "👐", "name": "Open Hands", "category": "People & Body"},
    {"emoji": "🙌", "name": "Raising Hands", "category": "People & Body"}, # Celebration
    {"emoji": "🤲", "name": "Palms Up Together", "category": "People & Body"}, # Offering, prayer
    {"emoji": "🤝", "name": "Handshake", "category": "People & Body"},
    {"emoji": "👣", "name": "Footprints", "category": "People & Body"},
    {"emoji": "👁️‍🗨️", "name": "Eye In Speech Bubble", "category": "People & Body"},
    {"emoji": "💋", "name": "Kiss Mark", "category": "People & Body"},
    {"emoji": "💘", "name": "Heart With Arrow", "category": "Symbols"},
    {"emoji": "💓", "name": "Beating Heart", "category": "Symbols"},
    {"emoji": "💔", "name": "Broken Heart", "category": "Symbols"},
    {"emoji": "💕", "name": "Two Hearts", "category": "Symbols"},
    {"emoji": "💖", "name": "Sparkling Heart", "category": "Symbols"},
    {"emoji": "💗", "name": "Growing Heart", "category": "Symbols"},
    {"emoji": "💙", "name": "Blue Heart", "category": "Symbols"},
    {"emoji": "💚", "name": "Green Heart", "category": "Symbols"},
    {"emoji": "❣", "name": "Heavy Heart Exclamation Mark Ornament", "category": "Symbols"}, # Often just "Heart Exclamation"
    {"emoji": "💞", "name": "Revolving Hearts", "category": "Symbols"},
    {"emoji": "💟", "name": "Heart Decoration", "category": "Symbols"},
    {"emoji": "💌", "name": "Love Letter", "category": "Symbols"}, # Can also be Objects
    {"emoji": "💤", "name": "Zzz", "category": "Symbols"}, # Represents sleeping, boredom
    {"emoji": "💢", "name": "Anger Symbol", "category": "Symbols"}, # Comic book style anger
    {"emoji": "💬", "name": "Speech Balloon", "category": "Symbols"},
    {"emoji": "💭", "name": "Thought Balloon", "category": "Symbols"},
    {"emoji": "🗯️", "name": "Right Anger Bubble", "category": "Symbols"},
    {"emoji": "🕳️", "name": "Hole", "category": "Objects"}, # Listed as Objects on Genius
    {"emoji": "💥", "name": "Collision", "category": "Symbols"}, # Genius: "Collision Symbol"
    {"emoji": "💦", "name": "Sweat Droplets", "category": "Symbols"}, # Genius: "Sweat Droplets"
    {"emoji": "💨", "name": "Dashing Away", "category": "Symbols"}, # Genius: "Dashing Away Symbol"
    {"emoji": "💫", "name": "Dizzy", "category": "Symbols"}, # Genius: "Dizzy Symbol"
    {"emoji": "🤚", "name": "Raised Back Of Hand", "category": "People & Body"},
    {"emoji": "🖐️", "name": "Hand With Fingers Splayed", "category": "People & Body"},
    {"emoji": "✋", "name": "Raised Hand", "category": "People & Body"},
    {"emoji": "🖖", "name": "Vulcan Salute", "category": "People & Body"},
    {"emoji": "🤘", "name": "Sign Of The Horns", "category": "People & Body"},
    {"emoji": "🤙", "name": "Call Me Hand", "category": "People & Body"},
    {"emoji": "👌", "name": "Ok Hand", "category": "People & Body"},
    {"emoji": "👎", "name": "Thumbs Down", "category": "People & Body"},
    {"emoji": "✊", "name": "Raised Fist", "category": "People & Body"},
    {"emoji": "👊", "name": "Oncoming Fist", "category": "People & Body"}, # Also Fisted Hand Sign
    {"emoji": "🤛", "name": "Left-Facing Fist", "category": "People & Body"},
    {"emoji": "🤜", "name": "Right-Facing Fist", "category": "People & Body"},
    {"emoji": "🤟", "name": "Love-You Gesture", "category": "People & Body"},
    {"emoji": "🎽", "name": "Running Shirt With Sash", "category": "Objects"}, # Often "Running Shirt"
    {"emoji": "👠", "name": "High-Heeled Shoe", "category": "Objects"},
    {"emoji": "👡", "name": "Womans Sandal", "category": "Objects"},
    {"emoji": "👢", "name": "Womans Boot", "category": "Objects"},
    {"emoji": "👞", "name": "Mans Shoe", "category": "Objects"}, # Or "Dress Shoe"
    {"emoji": "👟", "name": "Athletic Shoe", "category": "Objects"}, # Or "Sneaker"
    {"emoji": "🥾", "name": "Hiking Boot", "category": "Objects"},
    {"emoji": "🥿", "name": "Flat Shoe", "category": "Objects"},
    {"emoji": "👒", "name": "Womans Hat", "category": "Objects"},
    {"emoji": "🎩", "name": "Top Hat", "category": "Objects"},
    {"emoji": "🎓", "name": "Graduation Cap", "category": "Objects"},
    {"emoji": "⛑️", "name": "Rescue Workers Helmet", "category": "Objects"}, # Or "Helmet with White Cross"
    {"emoji": "🎒", "name": "Backpack", "category": "Objects"}, # Genius: School Satchel
    {"emoji": "👝", "name": "Pouch", "category": "Objects"}, # Or Clutch Bag
    {"emoji": "👛", "name": "Purse", "category": "Objects"},
    {"emoji": "👜", "name": "Handbag", "category": "Objects"},
    {"emoji": "💼", "name": "Briefcase", "category": "Objects"},
    {"emoji": "🏧", "name": "ATM Sign", "category": "Symbols"},
    {"emoji": "🚮", "name": "Litter In Bin Sign", "category": "Symbols"},
    {"emoji": "🚰", "name": "Potable Water", "category": "Symbols"},
    {"emoji": "♿", "name": "Wheelchair Symbol", "category": "Symbols"},
    {"emoji": "🚹", "name": "Mens Room", "category": "Symbols"},
    {"emoji": "🚺", "name": "Womens Room", "category": "Symbols"},
    {"emoji": "🚻", "name": "Restroom", "category": "Symbols"},
    {"emoji": "🚼", "name": "Baby Symbol", "category": "Symbols"},
    {"emoji": "🚾", "name": "Water Closet", "category": "Symbols"},
    {"emoji": "🛂", "name": "Passport Control", "category": "Symbols"},
    {"emoji": "🛄", "name": "Baggage Claim", "category": "Symbols"},
    {"emoji": "🛅", "name": "Left Luggage", "category": "Symbols"},
    {"emoji": "⚠️", "name": "Warning", "category": "Symbols"},
    {"emoji": "🚸", "name": "Children Crossing", "category": "Symbols"},
    {"emoji": "⛔", "name": "No Entry", "category": "Symbols"},
    {"emoji": "🚫", "name": "Prohibited", "category": "Symbols"},
    {"emoji": "🚭", "name": "No Smoking", "category": "Symbols"},
    {"emoji": "🚯", "name": "No Littering", "category": "Symbols"},
    {"emoji": "🚱", "name": "Non-Potable Water", "category": "Symbols"},
    {"emoji": "🚳", "name": "No Bicycles", "category": "Symbols"},
    {"emoji": "🚷", "name": "No Pedestrians", "category": "Symbols"},
    {"emoji": "📵", "name": "No Mobile Phones", "category": "Symbols"},
    {"emoji": "🔞", "name": "No One Under Eighteen", "category": "Symbols"},
    {"emoji": "⬆️", "name": "Up Arrow", "category": "Symbols"},
    {"emoji": "🆗", "name": "OK Button", "category": "Symbols"},
    {"emoji": "🅿️", "name": "P Button", "category": "Symbols"},
    {"emoji": "🆘", "name": "SOS Button", "category": "Symbols"},
    {"emoji": "🆙", "name": "Up! Button", "category": "Symbols"},
    {"emoji": "🆚", "name": "VS Button", "category": "Symbols"},
    {"emoji": "🈁", "name": "Japanese Here Button", "category": "Symbols"},
    {"emoji": "🈂️", "name": "Japanese Service Charge Button", "category": "Symbols"},
    {"emoji": "🈷️", "name": "Japanese Monthly Amount Button", "category": "Symbols"},
    {"emoji": "🈶", "name": "Japanese Not Free Of Charge Button", "category": "Symbols"},
    {"emoji": "🈯", "name": "Japanese Reserved Button", "category": "Symbols"},
    {"emoji": "🉐", "name": "Japanese Bargain Button", "category": "Symbols"},
    {"emoji": "🈹", "name": "Japanese Discount Button", "category": "Symbols"},
    {"emoji": "🈚", "name": "Japanese Free Of Charge Button", "category": "Symbols"},
    {"emoji": "🈲", "name": "Japanese Prohibited Button", "category": "Symbols"},
    {"emoji": "🉑", "name": "Japanese Acceptable Button", "category": "Symbols"},
    {"emoji": "🈸", "name": "Japanese Application Button", "category": "Symbols"},
    {"emoji": "🈴", "name": "Japanese Passing Grade Button", "category": "Symbols"},
    {"emoji": "🈳", "name": "Japanese Vacancy Button", "category": "Symbols"},
    {"emoji": "㊗️", "name": "Japanese Congratulations Button", "category": "Symbols"},
    {"emoji": "㊙️", "name": "Japanese Secret Button", "category": "Symbols"},
    {"emoji": "🈺", "name": "Japanese Open For Business Button", "category": "Symbols"},
    {"emoji": "🈵", "name": "Japanese No Vacancy Button", "category": "Symbols"},
    {"emoji": "🏂", "name": "Snowboarder", "category": "People & Body"},
    {"emoji": "🏌️", "name": "Person Golfing", "category": "People & Body"},
    {"emoji": "🏌️‍♂️", "name": "Man Golfing", "category": "People & Body"},
    {"emoji": "🏌️‍♀️", "name": "Woman Golfing", "category": "People & Body"},
    {"emoji": "🏄", "name": "Person Surfing", "category": "People & Body"},
    {"emoji": "🏄‍♂️", "name": "Man Surfing", "category": "People & Body"},
    {"emoji": "🏄‍♀️", "name": "Woman Surfing", "category": "People & Body"},
    {"emoji": "🚣", "name": "Person Rowing Boat", "category": "People & Body"},
    {"emoji": "🚣‍♂️", "name": "Man Rowing Boat", "category": "People & Body"},
    {"emoji": "🚣‍♀️", "name": "Woman Rowing Boat", "category": "People & Body"},
    {"emoji": "🏊", "name": "Person Swimming", "category": "People & Body"},
    {"emoji": "🏊‍♂️", "name": "Man Swimming", "category": "People & Body"},
    {"emoji": "🏊‍♀️", "name": "Woman Swimming", "category": "People & Body"},
    {"emoji": "⛹️", "name": "Person Bouncing Ball", "category": "People & Body"},
    {"emoji": "⛹️‍♂️", "name": "Man Bouncing Ball", "category": "People & Body"},
    {"emoji": "⛹️‍♀️", "name": "Woman Bouncing Ball", "category": "People & Body"},
    {"emoji": "🏋️", "name": "Person Lifting Weights", "category": "People & Body"},
    {"emoji": "🏋️‍♂️", "name": "Man Lifting Weights", "category": "People & Body"},
    {"emoji": "🏋️‍♀️", "name": "Woman Lifting Weights", "category": "People & Body"},
    {"emoji": "🚴", "name": "Person Biking", "category": "People & Body"},
    {"emoji": "🚴‍♂️", "name": "Man Biking", "category": "People & Body"},
    {"emoji": "🚴‍♀️", "name": "Woman Biking", "category": "People & Body"},
    {"emoji": "🚵", "name": "Person Mountain Biking", "category": "People & Body"},
    {"emoji": "🚵‍♂️", "name": "Man Mountain Biking", "category": "People & Body"},
    {"emoji": "🚵‍♀️", "name": "Woman Mountain Biking", "category": "People & Body"},
    {"emoji": "🏎️", "name": "Racing Car", "category": "Travel & Places"},
    {"emoji": "🏍️", "name": "Motorcycle", "category": "Travel & Places"},
    {"emoji": "🤸", "name": "Person Cartwheeling", "category": "People & Body"},
    {"emoji": "🤸‍♂️", "name": "Man Cartwheeling", "category": "People & Body"},
    {"emoji": "🤸‍♀️", "name": "Woman Cartwheeling", "category": "People & Body"},
    {"emoji": "🤼", "name": "People Wrestling", "category": "People & Body"},
    {"emoji": "🤼‍♂️", "name": "Men Wrestling", "category": "People & Body"},
    {"emoji": "🤼‍♀️", "name": "Women Wrestling", "category": "People & Body"},
    {"emoji": "🤽", "name": "Person Playing Water Polo", "category": "People & Body"},
    {"emoji": "🤽‍♂️", "name": "Man Playing Water Polo", "category": "People & Body"},
    {"emoji": "🤽‍♀️", "name": "Woman Playing Water Polo", "category": "People & Body"},
    {"emoji": "🤾", "name": "Person Playing Handball", "category": "People & Body"},
    {"emoji": "🤾‍♂️", "name": "Man Playing Handball", "category": "People & Body"},
    {"emoji": "🤾‍♀️", "name": "Woman Playing Handball", "category": "People & Body"},
    {"emoji": "🤹", "name": "Person Juggling", "category": "People & Body"},
    {"emoji": "🤹‍♂️", "name": "Man Juggling", "category": "People & Body"},
    {"emoji": "🤹‍♀️", "name": "Woman Juggling", "category": "People & Body"},
    {"emoji": "🍠", "name": "Roasted Sweet Potato", "category": "Food & Drink"},
    {"emoji": "🍢", "name": "Oden", "category": "Food & Drink"},
    {"emoji": "🍣", "name": "Sushi", "category": "Food & Drink"},
    {"emoji": "🍤", "name": "Fried Shrimp", "category": "Food & Drink"},
    {"emoji": "🍥", "name": "Fish Cake With Swirl", "category": "Food & Drink"},
    {"emoji": "🥫", "name": "Canned Food", "category": "Food & Drink"},
    {"emoji": "🍱", "name": "Bento Box", "category": "Food & Drink"},
    {"emoji": "🍘", "name": "Rice Cracker", "category": "Food & Drink"},
    {"emoji": "🍙", "name": "Rice Ball", "category": "Food & Drink"},
    {"emoji": "🍚", "name": "Cooked Rice", "category": "Food & Drink"},
    {"emoji": "🍛", "name": "Curry Rice", "category": "Food & Drink"},
    {"emoji": "🍜", "name": "Steaming Bowl", "category": "Food & Drink"},
    {"emoji": "🍡", "name": "Dango", "category": "Food & Drink"},
    {"emoji": "🥟", "name": "Dumpling", "category": "Food & Drink"},
    {"emoji": "🥠", "name": "Fortune Cookie", "category": "Food & Drink"},
    {"emoji": "🥡", "name": "Takeout Box", "category": "Food & Drink"},
    {"emoji": "🍧", "name": "Shaved Ice", "category": "Food & Drink"},
    {"emoji": "🍨", "name": "Ice Cream", "category": "Food & Drink"},
    {"emoji": "🍩", "name": "Doughnut", "category": "Food & Drink"},
    {"emoji": "🍪", "name": "Cookie", "category": "Food & Drink"},
    {"emoji": "🎂", "name": "Birthday Cake", "category": "Food & Drink"},
    {"emoji": "🍰", "name": "Shortcake", "category": "Food & Drink"},
    {"emoji": "🥧", "name": "Pie", "category": "Food & Drink"},
    {"emoji": "🍫", "name": "Chocolate Bar", "category": "Food & Drink"},
    {"emoji": "🍬", "name": "Candy", "category": "Food & Drink"},
    {"emoji": "🍭", "name": "Lollipop", "category": "Food & Drink"},
    {"emoji": "🍮", "name": "Custard", "category": "Food & Drink"},
    {"emoji": "🍯", "name": "Honey Pot", "category": "Food & Drink"},
    {"emoji": "🍼", "name": "Baby Bottle", "category": "Food & Drink"},
    {"emoji": "🥛", "name": "Glass Of Milk", "category": "Food & Drink"},
    {"emoji": "☕", "name": "Hot Beverage", "category": "Food & Drink"},
    {"emoji": "🍵", "name": "Teacup Without Handle", "category": "Food & Drink"},
    {"emoji": "🍶", "name": "Sake", "category": "Food & Drink"},
    {"emoji": "🍾", "name": "Bottle With Popping Cork", "category": "Food & Drink"},
    {"emoji": "🍷", "name": "Wine Glass", "category": "Food & Drink"},
    {"emoji": "🍸", "name": "Cocktail Glass", "category": "Food & Drink"},
    {"emoji": "🍹", "name": "Tropical Drink", "category": "Food & Drink"},
    {"emoji": "🍺", "name": "Beer Mug", "category": "Food & Drink"},
    {"emoji": "🍻", "name": "Clinking Beer Mugs", "category": "Food & Drink"},
    {"emoji": "🥂", "name": "Clinking Glasses", "category": "Food & Drink"},
    {"emoji": "🥃", "name": "Tumbler Glass", "category": "Food & Drink"},
    {"emoji": "🥤", "name": "Cup With Straw", "category": "Food & Drink"},
    {"emoji": "🥢", "name": "Chopsticks", "category": "Food & Drink"},
    {"emoji": "🌐", "name": "Globe With Meridians", "category": "Travel & Places"},
    {"emoji": "🗺️", "name": "World Map", "category": "Travel & Places"},
    {"emoji": "🗾", "name": "Map Of Japan", "category": "Travel & Places"},
    {"emoji": "🏔️", "name": "Snow-Capped Mountain", "category": "Travel & Places"},
    {"emoji": "⛰️", "name": "Mountain", "category": "Travel & Places"},
    {"emoji": "🌋", "name": "Volcano", "category": "Travel & Places"},
    {"emoji": "🗻", "name": "Mount Fuji", "category": "Travel & Places"},
    {"emoji": "🏕️", "name": "Camping", "category": "Travel & Places"},
    {"emoji": "🏖️", "name": "Beach With Umbrella", "category": "Travel & Places"},
    {"emoji": "🏜️", "name": "Desert", "category": "Travel & Places"},
    {"emoji": "🏞️", "name": "National Park", "category": "Travel & Places"},
    {"emoji": "🏟️", "name": "Stadium", "category": "Travel & Places"},
    {"emoji": "🏛️", "name": "Classical Building", "category": "Travel & Places"},
    {"emoji": "🏗️", "name": "Building Construction", "category": "Travel & Places"},
    {"emoji": "🏘️", "name": "Houses", "category": "Travel & Places"},
    {"emoji": "🏚️", "name": "Derelict House", "category": "Travel & Places"},
    {"emoji": "🏠", "name": "House", "category": "Travel & Places"},
    {"emoji": "🏡", "name": "House With Garden", "category": "Travel & Places"},
    {"emoji": "🏢", "name": "Office Building", "category": "Travel & Places"},
    {"emoji": "🏣", "name": "Japanese Post Office", "category": "Travel & Places"},
    {"emoji": "🏤", "name": "Post Office", "category": "Travel & Places"},
    {"emoji": "🏥", "name": "Hospital", "category": "Travel & Places"},
    {"emoji": "🏦", "name": "Bank", "category": "Travel & Places"},
    {"emoji": "🏨", "name": "Hotel", "category": "Travel & Places"},
    {"emoji": "🏩", "name": "Love Hotel", "category": "Travel & Places"},
    {"emoji": "🏪", "name": "Convenience Store", "category": "Travel & Places"},
    {"emoji": "🏫", "name": "School", "category": "Travel & Places"},
    {"emoji": "🏬", "name": "Department Store", "category": "Travel & Places"},
    {"emoji": "🏭", "name": "Factory", "category": "Travel & Places"},
    {"emoji": "🏯", "name": "Japanese Castle", "category": "Travel & Places"},
    {"emoji": "🏰", "name": "Castle", "category": "Travel & Places"},
    {"emoji": "💒", "name": "Wedding", "category": "Travel & Places"},
    {"emoji": "🗼", "name": "Tokyo Tower", "category": "Travel & Places"},
    {"emoji": "🗽", "name": "Statue Of Liberty", "category": "Travel & Places"},
    {"emoji": "⛪", "name": "Church", "category": "Travel & Places"},
    {"emoji": "🕌", "name": "Mosque", "category": "Travel & Places"},
    {"emoji": "🕍", "name": "Synagogue", "category": "Travel & Places"},
    {"emoji": "⛲", "name": "Fountain", "category": "Travel & Places"},
    {"emoji": "⛺", "name": "Tent", "category": "Travel & Places"},
    {"emoji": "🌁", "name": "Foggy", "category": "Travel & Places"},
    {"emoji": "🌃", "name": "Night With Stars", "category": "Travel & Places"},
    {"emoji": "🏙️", "name": "Cityscape", "category": "Travel & Places"},
    {"emoji": "🌄", "name": "Sunrise Over Mountains", "category": "Travel & Places"},
    {"emoji": "🌅", "name": "Sunrise", "category": "Travel & Places"},
    {"emoji": "🌆", "name": "Cityscape At Dusk", "category": "Travel & Places"},
    {"emoji": "🌇", "name": "Sunset", "category": "Travel & Places"},
    {"emoji": "🌉", "name": "Bridge At Night", "category": "Travel & Places"},
    {"emoji": "♨️", "name": "Hot Springs", "category": "Travel & Places"},
    {"emoji": "🌌", "name": "Milky Way", "category": "Travel & Places"},
    {"emoji": "🚂", "name": "Locomotive", "category": "Travel & Places"},
    {"emoji": "🚃", "name": "Railway Car", "category": "Travel & Places"},
    {"emoji": "🚄", "name": "High-Speed Train", "category": "Travel & Places"},
    {"emoji": "🚅", "name": "Bullet Train", "category": "Travel & Places"},
    {"emoji": "🚆", "name": "Train", "category": "Travel & Places"},
    {"emoji": "🚇", "name": "Metro", "category": "Travel & Places"},
    {"emoji": "🚈", "name": "Light Rail", "category": "Travel & Places"},
    {"emoji": "🚉", "name": "Station", "category": "Travel & Places"},
    {"emoji": "🚊", "name": "Tram", "category": "Travel & Places"},
    {"emoji": "🚝", "name": "Monorail", "category": "Travel & Places"},
    {"emoji": "🚞", "name": "Mountain Railway", "category": "Travel & Places"},
    {"emoji": "🚋", "name": "Tram Car", "category": "Travel & Places"},
    {"emoji": "🚌", "name": "Bus", "category": "Travel & Places"},
    {"emoji": "🚍", "name": "Oncoming Bus", "category": "Travel & Places"},
    {"emoji": "🚎", "name": "Trolleybus", "category": "Travel & Places"},
    {"emoji": "🚐", "name": "Minibus", "category": "Travel & Places"},
    {"emoji": "🚑", "name": "Ambulance", "category": "Travel & Places"},
    {"emoji": "🚒", "name": "Fire Engine", "category": "Travel & Places"},
    {"emoji": "🚓", "name": "Police Car", "category": "Travel & Places"},
    {"emoji": "🚔", "name": "Oncoming Police Car", "category": "Travel & Places"},
    {"emoji": "🚕", "name": "Taxi", "category": "Travel & Places"},
    {"emoji": "🚖", "name": "Oncoming Taxi", "category": "Travel & Places"},
    {"emoji": "🚘", "name": "Oncoming Automobile", "category": "Travel & Places"},
    {"emoji": "🚙", "name": "Sport Utility Vehicle", "category": "Travel & Places"},
    {"emoji": "🚚", "name": "Delivery Truck", "category": "Travel & Places"},
    {"emoji": "🚛", "name": "Articulated Lorry", "category": "Travel & Places"},
    {"emoji": "🚜", "name": "Tractor", "category": "Travel & Places"},
    {"emoji": "🚲", "name": "Bicycle", "category": "Travel & Places"},
    {"emoji": "🛴", "name": "Kick Scooter", "category": "Travel & Places"},
    {"emoji": "🛵", "name": "Motor Scooter", "category": "Travel & Places"},
    {"emoji": "🚏", "name": "Bus Stop", "category": "Travel & Places"},
    {"emoji": "🛣️", "name": "Motorway", "category": "Travel & Places"},
    {"emoji": "🛤️", "name": "Railway Track", "category": "Travel & Places"},
    {"emoji": "🚧", "name": "Construction", "category": "Travel & Places"},
    {"emoji": "⛵", "name": "Sailboat", "category": "Travel & Places"},
    {"emoji": "🛶", "name": "Canoe", "category": "Travel & Places"},
    {"emoji": "🚤", "name": "Speedboat", "category": "Travel & Places"},
    {"emoji": "🛳️", "name": "Passenger Ship", "category": "Travel & Places"},
    {"emoji": "⛴️", "name": "Ferry", "category": "Travel & Places"},
    {"emoji": "🛥️", "name": "Motor Boat", "category": "Travel & Places"},
    {"emoji": "🚢", "name": "Ship", "category": "Travel & Places"},
    {"emoji": "🛩️", "name": "Small Airplane", "category": "Travel & Places"},
    {"emoji": "🛫", "name": "Airplane Departure", "category": "Travel & Places"},
    {"emoji": "🛬", "name": "Airplane Arrival", "category": "Travel & Places"},
    {"emoji": "🚁", "name": "Helicopter", "category": "Travel & Places"},
    {"emoji": "🚟", "name": "Suspension Railway", "category": "Travel & Places"},
    {"emoji": "🚠", "name": "Mountain Cableway", "category": "Travel & Places"},
    {"emoji": "🚡", "name": "Aerial Tramway", "category": "Travel & Places"},
    # Activities
    {"emoji": "🎠", "name": "Carousel Horse", "category": "Activities"},
    {"emoji": "🎡", "name": "Ferris Wheel", "category": "Activities"},
    {"emoji": "🎢", "name": "Roller Coaster", "category": "Activities"},
    {"emoji": "🎪", "name": "Circus Tent", "category": "Activities"},
    # Objects
    {"emoji": "⛽", "name": "Fuel Pump", "category": "Objects"},
    {"emoji": "🚨", "name": "Police Car Light", "category": "Objects"},
    {"emoji": "🚥", "name": "Horizontal Traffic Light", "category": "Objects"},
    {"emoji": "🚦", "name": "Vertical Traffic Light", "category": "Objects"},
    {"emoji": "💺", "name": "Seat", "category": "Objects"},
    {"emoji": "🛰️", "name": "Satellite", "category": "Objects"},
    {"emoji": "🛸", "name": "Flying Saucer", "category": "Objects"},
    {"emoji": "⌛", "name": "Hourglass Done", "category": "Objects"},
    {"emoji": "⌚", "name": "Watch", "category": "Objects"},
    {"emoji": "⏱️", "name": "Stopwatch", "category": "Objects"},
    {"emoji": "⏲️", "name": "Timer Clock", "category": "Objects"},
    {"emoji": "🕛", "name": "Twelve OClock", "category": "Objects"},
    {"emoji": "🕧", "name": "Twelve-Thirty", "category": "Objects"},
    {"emoji": "🕐", "name": "One OClock", "category": "Objects"},
    {"emoji": "🕜", "name": "One-Thirty", "category": "Objects"},
    {"emoji": "🕑", "name": "Two OClock", "category": "Objects"},
    {"emoji": "🕝", "name": "Two-Thirty", "category": "Objects"},
    {"emoji": "🕒", "name": "Three OClock", "category": "Objects"},
    {"emoji": "🕞", "name": "Three-Thirty", "category": "Objects"},
    {"emoji": "🕓", "name": "Four OClock", "category": "Objects"},
    {"emoji": "🕟", "name": "Four-Thirty", "category": "Objects"},
    {"emoji": "🕔", "name": "Five OClock", "category": "Objects"},
    {"emoji": "🕠", "name": "Five-Thirty", "category": "Objects"},
    {"emoji": "🕕", "name": "Six OClock", "category": "Objects"},
    {"emoji": "🕡", "name": "Six-Thirty", "category": "Objects"},
    {"emoji": "🕖", "name": "Seven OClock", "category": "Objects"},
    {"emoji": "🕢", "name": "Seven-Thirty", "category": "Objects"},
    {"emoji": "🕗", "name": "Eight OClock", "category": "Objects"},
    {"emoji": "🕣", "name": "Eight-Thirty", "category": "Objects"},
    {"emoji": "🕘", "name": "Nine OClock", "category": "Objects"},
    {"emoji": "🕤", "name": "Nine-Thirty", "category": "Objects"},
    {"emoji": "🕙", "name": "Ten OClock", "category": "Objects"},
    {"emoji": "🕥", "name": "Ten-Thirty", "category": "Objects"},
    {"emoji": "🕚", "name": "Eleven OClock", "category": "Objects"},
    {"emoji": "🕦", "name": "Eleven-Thirty", "category": "Objects"},
    {"emoji": "🌡️", "name": "Thermometer", "category": "Objects"},
    {"emoji": "🌂", "name": "Closed Umbrella", "category": "Objects"},
    {"emoji": "☂️", "name": "Umbrella", "category": "Objects"},
    {"emoji": "☔", "name": "Umbrella With Rain Drops", "category": "Objects"},
    {"emoji": "⛱️", "name": "Umbrella On Ground", "category": "Objects"},
    # Animals & Nature (Celestial bodies & Weather)
    {"emoji": "🌑", "name": "New Moon", "category": "Animals & Nature"},
    {"emoji": "🌒", "name": "Waxing Crescent Moon", "category": "Animals & Nature"},
    {"emoji": "🌓", "name": "First Quarter Moon", "category": "Animals & Nature"},
    {"emoji": "🌔", "name": "Waxing Gibbous Moon", "category": "Animals & Nature"},
    {"emoji": "🌕", "name": "Full Moon", "category": "Animals & Nature"},
    {"emoji": "🌖", "name": "Waning Gibbous Moon", "category": "Animals & Nature"},
    {"emoji": "🌗", "name": "Last Quarter Moon", "category": "Animals & Nature"},
    {"emoji": "🌘", "name": "Waning Crescent Moon", "category": "Animals & Nature"},
    {"emoji": "🌚", "name": "New Moon Face", "category": "Animals & Nature"},
    {"emoji": "🌛", "name": "First Quarter Moon Face", "category": "Animals & Nature"},
    {"emoji": "🌜", "name": "Last Quarter Moon Face", "category": "Animals & Nature"},
    {"emoji": "☀️", "name": "Sun", "category": "Animals & Nature"},
    {"emoji": "🌝", "name": "Full Moon Face", "category": "Animals & Nature"},
    {"emoji": "🌞", "name": "Sun With Face", "category": "Animals & Nature"},
    {"emoji": "⭐", "name": "Star", "category": "Animals & Nature"},
    {"emoji": "🌟", "name": "Glowing Star", "category": "Animals & Nature"},
    {"emoji": "🌠", "name": "Shooting Star", "category": "Animals & Nature"},
    {"emoji": "☁️", "name": "Cloud", "category": "Animals & Nature"},
    {"emoji": "⛅", "name": "Sun Behind Cloud", "category": "Animals & Nature"},
    {"emoji": "⛈️", "name": "Cloud With Lightning And Rain", "category": "Animals & Nature"},
    {"emoji": "🌤️", "name": "Sun Behind Small Cloud", "category": "Animals & Nature"},
    {"emoji": "🌥️", "name": "Sun Behind Large Cloud", "category": "Animals & Nature"},
    {"emoji": "🌦️", "name": "Sun Behind Rain Cloud", "category": "Animals & Nature"},
    {"emoji": "🌧️", "name": "Cloud With Rain", "category": "Animals & Nature"},
    {"emoji": "🌨️", "name": "Cloud With Snow", "category": "Animals & Nature"},
    {"emoji": "🌩️", "name": "Cloud With Lightning", "category": "Animals & Nature"},
    {"emoji": "🌪️", "name": "Tornado", "category": "Animals & Nature"},
    {"emoji": "🌫️", "name": "Fog", "category": "Animals & Nature"},
    {"emoji": "🌬️", "name": "Wind Face", "category": "Animals & Nature"},
    {"emoji": "🌀", "name": "Cyclone", "category": "Animals & Nature"},
    {"emoji": "❄️", "name": "Snowflake", "category": "Animals & Nature"},
    {"emoji": "☃️", "name": "Snowman", "category": "Animals & Nature"},
    {"emoji": "⛄", "name": "Snowman Without Snow", "category": "Animals & Nature"},
    {"emoji": "☄️", "name": "Comet", "category": "Animals & Nature"},
    {"emoji": "🛑", "name": "Stop Sign", "category": "Symbols"},
    {"emoji": "⚡", "name": "High Voltage", "category": "Symbols"},
    {"emoji": "🎃", "name": "Jack-O-Lantern", "category": "Activities"}, # Can also be Objects/Animals & Nature
    {"emoji": "🎄", "name": "Christmas Tree", "category": "Activities"}, # Can also be Objects/Animals & Nature
    {"emoji": "🎆", "name": "Fireworks", "category": "Activities"},
    {"emoji": "🎇", "name": "Sparkler", "category": "Activities"},
    {"emoji": "🎊", "name": "Confetti Ball", "category": "Activities"},
    {"emoji": "🎋", "name": "Tanabata Tree", "category": "Activities"}, # Can also be Objects
    {"emoji": "🎍", "name": "Pine Decoration", "category": "Objects"}, # Often associated with New Year activity
    {"emoji": "🎎", "name": "Japanese Dolls", "category": "Objects"}, # Associated with Hinamatsuri festival (Activity)
    {"emoji": "🎏", "name": "Carp Streamer", "category": "Activities"}, # Can also be Objects
    {"emoji": "🎐", "name": "Wind Chime", "category": "Objects"}, # Can be associated with summer (Activity)
    {"emoji": "🎑", "name": "Moon Viewing Ceremony", "category": "Activities"}, # Can also be Travel & Places
    {"emoji": "🎀", "name": "Ribbon", "category": "Objects"}, # Often used in gifts/celebrations (Activities)
    # {"emoji": "🎁", "name": "Wrapped Gift", "category": "Objects"}, # Already exists (associated with Activities)
    {"emoji": "🎗️", "name": "Reminder Ribbon", "category": "Objects"}, # Can be Symbols
    {"emoji": "🎟️", "name": "Admission Tickets", "category": "Objects"}, # Associated with Activities
    {"emoji": "🎫", "name": "Ticket", "category": "Objects"}, # Associated with Activities
    {"emoji": "🎖️", "name": "Military Medal", "category": "Objects"}, # Associated with Achievements/Activities
    {"emoji": "🏆", "name": "Trophy", "category": "Objects"}, # Associated with Achievements/Activities
    {"emoji": "🏅", "name": "Sports Medal", "category": "Objects"}, # Associated with Achievements/Activities
    {"emoji": "🏐", "name": "Volleyball", "category": "Activities"},
    {"emoji": "🏈", "name": "American Football", "category": "Activities"},
    {"emoji": "🏉", "name": "Rugby Football", "category": "Activities"},
    {"emoji": "🎾", "name": "Tennis", "category": "Activities"},
    {"emoji": "🎳", "name": "Bowling", "category": "Activities"},
    {"emoji": "🏏", "name": "Cricket Game", "category": "Activities"},
    {"emoji": "🏑", "name": "Field Hockey", "category": "Activities"},
    {"emoji": "🏒", "name": "Ice Hockey", "category": "Activities"},
    {"emoji": "🏓", "name": "Ping Pong", "category": "Activities"},
    {"emoji": "🏸", "name": "Badminton", "category": "Activities"},
    {"emoji": "🥊", "name": "Boxing Glove", "category": "Activities"},
    {"emoji": "🥋", "name": "Martial Arts Uniform", "category": "Activities"}, # Can also be Objects
    {"emoji": "🥅", "name": "Goal Net", "category": "Activities"}, # Can also be Objects
    {"emoji": "⛳", "name": "Flag In Hole", "category": "Activities"},
    {"emoji": "⛸️", "name": "Ice Skate", "category": "Activities"},
    {"emoji": "🎣", "name": "Fishing Pole", "category": "Activities"}, # Can also be Objects
    {"emoji": "🎿", "name": "Skis", "category": "Activities"}, # Can also be Objects
    {"emoji": "🛷", "name": "Sled", "category": "Activities"}, # Can also be Objects
    {"emoji": "🎯", "name": "Direct Hit", "category": "Activities"}, # Bullseye, can be symbol
    {"emoji": "🎱", "name": "Pool 8 Ball", "category": "Activities"}, # Billiards
    {"emoji": "🔮", "name": "Crystal Ball", "category": "Objects"}, # Associated with fortune-telling (Activity)
    {"emoji": "🎮", "name": "Video Game", "category": "Activities"}, # Can also be Objects
    {"emoji": "🕹️", "name": "Joystick", "category": "Objects"}, # Associated with gaming (Activity)
    {"emoji": "🎰", "name": "Slot Machine", "category": "Activities"},
    {"emoji": "🎲", "name": "Game Die", "category": "Activities"}, # Can also be Objects
    {"emoji": "♠️", "name": "Spade Suit", "category": "Symbols"}, # Card game (Activity)
    {"emoji": "♥️", "name": "Heart Suit", "category": "Symbols"}, # Card game (Activity)
    {"emoji": "♦️", "name": "Diamond Suit", "category": "Symbols"}, # Card game (Activity)
    {"emoji": "♣️", "name": "Club Suit", "category": "Symbols"}, # Card game (Activity)
    {"emoji": "♟️", "name": "Chess Pawn", "category": "Symbols"}, # Chess game (Activity)
    {"emoji": "🃏", "name": "Joker", "category": "Symbols"}, # Card game (Activity)
    {"emoji": "🀄", "name": "Mahjong Red Dragon", "category": "Symbols"}, # Mahjong game (Activity)
    {"emoji": "🎴", "name": "Flower Playing Cards", "category": "Symbols"}, # Hanafuda cards (Activity)
    {"emoji": "🖼️", "name": "Framed Picture", "category": "Objects"}, # Art (Activity)
    {"emoji": "🎨", "name": "Artist Palette", "category": "Objects"},
    {"emoji": "🔇", "name": "Muted Speaker", "category": "Objects"},
    {"emoji": "🔈", "name": "Speaker Low Volume", "category": "Objects"},
    {"emoji": "🔉", "name": "Speaker Medium Volume", "category": "Objects"},
    {"emoji": "🔊", "name": "Speaker High Volume", "category": "Objects"},
    {"emoji": "📢", "name": "Loudspeaker", "category": "Objects"},
    {"emoji": "📣", "name": "Megaphone", "category": "Objects"},
    {"emoji": "🔕", "name": "Bell With Slash", "category": "Objects"},
    {"emoji": "🎼", "name": "Musical Score", "category": "Objects"},
    {"emoji": "🎵", "name": "Musical Note", "category": "Symbols"}, # Often used as a symbol for music
    {"emoji": "🎶", "name": "Musical Notes", "category": "Symbols"}, # Often used as a symbol for music
    {"emoji": "🎙️", "name": "Studio Microphone", "category": "Objects"},
    {"emoji": "🎤", "name": "Microphone", "category": "Objects"},
    {"emoji": "🎧", "name": "Headphone", "category": "Objects"},
    {"emoji": "📻", "name": "Radio", "category": "Objects"},
    {"emoji": "🎷", "name": "Saxophone", "category": "Objects"},
    {"emoji": "🎸", "name": "Guitar", "category": "Objects"},
    {"emoji": "🎹", "name": "Musical Keyboard", "category": "Objects"},
    {"emoji": "🎺", "name": "Trumpet", "category": "Objects"},
    {"emoji": "🎻", "name": "Violin", "category": "Objects"},
    {"emoji": "📱", "name": "Mobile Phone", "category": "Objects"},
    {"emoji": "📲", "name": "Mobile Phone With Arrow", "category": "Objects"},
    {"emoji": "☎️", "name": "Telephone", "category": "Objects"}, # Black Telephone
    {"emoji": "📞", "name": "Telephone Receiver", "category": "Objects"},
    {"emoji": "📟", "name": "Pager", "category": "Objects"},
    {"emoji": "📠", "name": "Fax Machine", "category": "Objects"},
    {"emoji": "🔋", "name": "Battery", "category": "Objects"},
    {"emoji": "🔌", "name": "Electric Plug", "category": "Objects"},
    {"emoji": "💻", "name": "Laptop Computer", "category": "Objects"}, # Unicode: Personal Computer
    {"emoji": "🖥️", "name": "Desktop Computer", "category": "Objects"},
    {"emoji": "🖨️", "name": "Printer", "category": "Objects"},
    {"emoji": "⌨️", "name": "Keyboard", "category": "Objects"},
    {"emoji": "🖱️", "name": "Computer Mouse", "category": "Objects"},
    {"emoji": "🖲️", "name": "Trackball", "category": "Objects"},
    {"emoji": "💽", "name": "Computer Disk", "category": "Objects"}, # Minidisc
    {"emoji": "💾", "name": "Floppy Disk", "category": "Objects"},
    {"emoji": "💿", "name": "Optical Disk", "category": "Objects"}, # CD
    {"emoji": "📀", "name": "Dvd", "category": "Objects"},
    {"emoji": "🎥", "name": "Movie Camera", "category": "Objects"},
    {"emoji": "🎬", "name": "Clapper Board", "category": "Objects"},
    {"emoji": "📺", "name": "Television", "category": "Objects"},
    {"emoji": "📷", "name": "Camera", "category": "Objects"},
    {"emoji": "📸", "name": "Camera With Flash", "category": "Objects"},
    {"emoji": "📹", "name": "Video Camera", "category": "Objects"},
    # {"emoji": "📼", "name": "Videocassette", "category": "Objects"}, # Already exists
    {"emoji": "🔍", "name": "Magnifying Glass Tilted Left", "category": "Objects"},
    {"emoji": "🔎", "name": "Magnifying Glass Tilted Right", "category": "Objects"},
    {"emoji": "🕯️", "name": "Candle", "category": "Objects"},
    {"emoji": "💡", "name": "Light Bulb", "category": "Objects"},
    {"emoji": "🔦", "name": "Flashlight", "category": "Objects"}, # Electric Torch
    {"emoji": "🏮", "name": "Red Paper Lantern", "category": "Objects"}, # Izakaya Lantern
    {"emoji": "📔", "name": "Notebook With Decorative Cover", "category": "Objects"},
    {"emoji": "📕", "name": "Closed Book", "category": "Objects"},
    {"emoji": "📖", "name": "Open Book", "category": "Objects"},
    {"emoji": "📗", "name": "Green Book", "category": "Objects"},
    {"emoji": "📘", "name": "Blue Book", "category": "Objects"},
    {"emoji": "📙", "name": "Orange Book", "category": "Objects"},
    {"emoji": "📚", "name": "Books", "category": "Objects"},
    {"emoji": "📓", "name": "Notebook", "category": "Objects"},
    {"emoji": "📒", "name": "Ledger", "category": "Objects"},
    {"emoji": "📃", "name": "Page With Curl", "category": "Objects"},
    # {"emoji": "📜", "name": "Scroll", "category": "Objects"}, # Already exists
    {"emoji": "📄", "name": "Page Facing Up", "category": "Objects"},
    {"emoji": "📰", "name": "Newspaper", "category": "Objects"},
    {"emoji": "🗞️", "name": "Rolled-Up Newspaper", "category": "Objects"},
    {"emoji": "📑", "name": "Bookmark Tabs", "category": "Objects"},
    {"emoji": "🔖", "name": "Bookmark", "category": "Objects"},
    {"emoji": "🏷️", "name": "Label", "category": "Objects"}, # Or Tag
    # {"emoji": "💰", "name": "Money Bag", "category": "Objects"}, # Already exists
    {"emoji": "💴", "name": "Yen Banknote", "category": "Objects"},
    {"emoji": "💵", "name": "Dollar Banknote", "category": "Objects"},
    {"emoji": "💶", "name": "Euro Banknote", "category": "Objects"},
    {"emoji": "💷", "name": "Pound Banknote", "category": "Objects"},
    {"emoji": "💸", "name": "Money With Wings", "category": "Objects"},
    {"emoji": "💳", "name": "Credit Card", "category": "Objects"},
    {"emoji": "💹", "name": "Chart Increasing With Yen", "category": "Symbols"},
    {"emoji": "💱", "name": "Currency Exchange", "category": "Symbols"},
    {"emoji": "💲", "name": "Heavy Dollar Sign", "category": "Symbols"},
    {"emoji": "✉️", "name": "Envelope", "category": "Objects"},
    {"emoji": "📧", "name": "E-Mail", "category": "Objects"}, # Or E-Mail Symbol
    {"emoji": "📨", "name": "Incoming Envelope", "category": "Objects"},
    {"emoji": "📩", "name": "Envelope With Arrow", "category": "Objects"},
    {"emoji": "📤", "name": "Outbox Tray", "category": "Objects"},
    {"emoji": "📥", "name": "Inbox Tray", "category": "Objects"},
    {"emoji": "📦", "name": "Package", "category": "Objects"},
    {"emoji": "📫", "name": "Closed Mailbox With Raised Flag", "category": "Objects"},
    {"emoji": "📪", "name": "Closed Mailbox With Lowered Flag", "category": "Objects"},
    {"emoji": "📬", "name": "Open Mailbox With Raised Flag", "category": "Objects"},
    {"emoji": "📭", "name": "Open Mailbox With Lowered Flag", "category": "Objects"},
    {"emoji": "📮", "name": "Postbox", "category": "Objects"},
    {"emoji": "🗳️", "name": "Ballot Box With Ballot", "category": "Objects"},
    {"emoji": "✏️", "name": "Pencil", "category": "Objects"},
    {"emoji": "🖋️", "name": "Fountain Pen", "category": "Objects"}, # Lower Left Fountain Pen
    {"emoji": "🖊️", "name": "Pen", "category": "Objects"}, # Lower Left Ballpoint Pen
    {"emoji": "🖌️", "name": "Paintbrush", "category": "Objects"}, # Lower Left Paintbrush
    {"emoji": "🖍️", "name": "Crayon", "category": "Objects"}, # Lower Left Crayon
    {"emoji": "📝", "name": "Memo", "category": "Objects"}, # Or Pencil and Paper
    {"emoji": "📁", "name": "File Folder", "category": "Objects"},
    {"emoji": "📂", "name": "Open File Folder", "category": "Objects"},
    {"emoji": "🗂️", "name": "Card Index Dividers", "category": "Objects"},
    {"emoji": "📅", "name": "Calendar", "category": "Objects"},
    {"emoji": "📆", "name": "Tear-Off Calendar", "category": "Objects"},
    {"emoji": "🗒️", "name": "Spiral Notepad", "category": "Objects"},
    {"emoji": "🗓️", "name": "Spiral Calendar", "category": "Objects"},
    {"emoji": "📇", "name": "Card Index", "category": "Objects"},
    {"emoji": "📈", "name": "Chart Increasing", "category": "Objects"}, # Or Chart With Upwards Trend
    {"emoji": "📉", "name": "Chart Decreasing", "category": "Objects"}, # Or Chart With Downwards Trend
    {"emoji": "📊", "name": "Bar Chart", "category": "Objects"},
    {"emoji": "📋", "name": "Clipboard", "category": "Objects"},
    {"emoji": "📌", "name": "Pushpin", "category": "Objects"},
    {"emoji": "📍", "name": "Round Pushpin", "category": "Objects"},
    {"emoji": "📎", "name": "Paperclip", "category": "Objects"},
    {"emoji": "🖇️", "name": "Linked Paperclips", "category": "Objects"},
    {"emoji": "📏", "name": "Straight Ruler", "category": "Objects"},
    {"emoji": "📐", "name": "Triangular Ruler", "category": "Objects"},
    {"emoji": "✂️", "name": "Scissors", "category": "Objects"}, # Black scissors
    {"emoji": "🗃️", "name": "Card File Box", "category": "Objects"},
    {"emoji": "🗄️", "name": "File Cabinet", "category": "Objects"},
    {"emoji": "🗑️", "name": "Wastebasket", "category": "Objects"},
    {"emoji": "🔒", "name": "Locked", "category": "Objects"},
    {"emoji": "🔓", "name": "Unlocked", "category": "Objects"},
    {"emoji": "🔏", "name": "Locked With Pen", "category": "Objects"},
    {"emoji": "🔐", "name": "Locked With Key", "category": "Objects"},
    {"emoji": "🔑", "name": "Key", "category": "Objects"},
    {"emoji": "🗝️", "name": "Old Key", "category": "Objects"},
    {"emoji": "🔨", "name": "Hammer", "category": "Objects"},
    {"emoji": "⛏️", "name": "Pick", "category": "Objects"},
    {"emoji": "⚒️", "name": "Hammer And Pick", "category": "Objects"}, # Or Symbols
    {"emoji": "🛠️", "name": "Hammer And Wrench", "category": "Objects"}, # Or Symbols
    {"emoji": "🗡️", "name": "Dagger", "category": "Objects"}, # Dagger Knife
    {"emoji": "⚔️", "name": "Crossed Swords", "category": "Objects"}, # Or Symbols
    {"emoji": "🔫", "name": "Pistol", "category": "Objects"}, # Water Pistol / Gun
    {"emoji": "🏹", "name": "Bow And Arrow", "category": "Objects"}, # Or Activities
    {"emoji": "🛡️", "name": "Shield", "category": "Objects"},
    {"emoji": "🔧", "name": "Wrench", "category": "Objects"},
    {"emoji": "💉", "name": "Syringe", "category": "Objects"},
    {"emoji": "🛋️", "name": "Couch And Lamp", "category": "Objects"},
    {"emoji": "🚽", "name": "Toilet", "category": "Objects"},
    {"emoji": "🚿", "name": "Shower", "category": "Objects"},
    {"emoji": "🛁", "name": "Bathtub", "category": "Objects"},
    {"emoji": "🛒", "name": "Shopping Cart", "category": "Objects"}, # Or Shopping Trolley
    {"emoji": "🚬", "name": "Cigarette", "category": "Objects"}, # Smoking Symbol
    {"emoji": "🗿", "name": "Moai", "category": "Objects"} # Moyai, can be Travel & Places # Art (Activity)




]

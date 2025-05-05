from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os # Import os for secret key generation

db = SQLAlchemy()
migrate = Migrate()

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure SECRET_KEY is set for flash messages
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.urandom(24)
        print("Warning: SECRET_KEY not set in config, using a temporary random key.")

    db.init_app(app)
    migrate.init_app(app, db)

    # Import and register the blueprint
    from .routes import main as main_blueprint # Import the blueprint
    app.register_blueprint(main_blueprint) # Register it with the app

    with app.app_context():
        from . import models # Import models

    # Modify the command to populate the database without dropping stats
    @app.cli.command("init-db")
    def init_db_command():
        """Ensure tables exist and add new initial riddles without dropping existing data."""
        from .models import add_initial_riddles

        # Create tables if they don't exist (safe for existing data)
        # This will add new tables or columns based on your models if they are missing.
        db.create_all()
        print("Ensured all tables exist (created if necessary).")

        # Add only new emojis from the list in models.py
        add_initial_riddles()
        # The add_initial_riddles function already checks if emojis exist,
        # so it won't duplicate them.

    # Add current_year to template context
    @app.context_processor
    def inject_current_year():
        from datetime import datetime
        return {'current_year': datetime.utcnow().year}

    return app
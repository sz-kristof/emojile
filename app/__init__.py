from flask import Flask, Blueprint
from config import Config
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os # Import os for secret key generation

db = SQLAlchemy()
migrate = Migrate()
main = Blueprint('main', __name__) # Define the blueprint object

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure SECRET_KEY is set for flash messages
    if not app.config.get('SECRET_KEY'):
        app.config['SECRET_KEY'] = os.urandom(24)
        print("Warning: SECRET_KEY not set in config, using a temporary random key.")

    db.init_app(app)
    migrate = Migrate(app, db) # Initialize Migrate here

    # Import and register the blueprint
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    with app.app_context():
        from . import models # Import models

    # Remove or comment out the init-db command defined here
    # @app.cli.command("init-db")
    # def init_db_command():
    #     """Ensure tables exist and add new initial riddles without dropping existing data."""
    #     # from .models import add_initial_riddles # This line causes the error

    #     # Create tables if they don't exist (safe for existing data)
    #     db.create_all()
    #     print("Ensured all tables exist (created if necessary).")

    #     # Add only new emojis from the list in models.py
    #     # add_initial_riddles() # This function call is problematic
    #     print("Riddle initialization is now handled by 'flask main init-db' or the init-db in routes.py.")

    # Add current_year to template context
    @app.context_processor
    def inject_current_year():
        from datetime import datetime
        return {'current_year': datetime.utcnow().year}

    return app
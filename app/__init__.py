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

    # Add a command to populate the database
    @app.cli.command("init-db")
    def init_db_command():
        """Clear existing data and create new tables."""
        from .models import add_initial_riddles
        db.drop_all()
        db.create_all()
        add_initial_riddles()
        print("Initialized the database.")

    # Add current_year to template context
    @app.context_processor
    def inject_current_year():
        from datetime import datetime
        return {'current_year': datetime.utcnow().year}

    return app
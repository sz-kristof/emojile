import os
from datetime import timedelta # <<< Import timedelta

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a_default_secret_key'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///site.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # --- Add these lines for persistent sessions ---
    SESSION_PERMANENT = True
    PERMANENT_SESSION_LIFETIME = timedelta(days=7) # Keep session cookie for 2 days
    # --- End added lines ---
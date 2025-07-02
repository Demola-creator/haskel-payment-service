import os


class Config:
    """Base configuration that uses a local SQLite database."""
    # This will be read from Replit's Secrets tool
    SECRET_KEY = os.environ.get('SECRET_KEY')
    INTERNAL_ADMIN_API_KEY = os.environ.get('INTERNAL_ADMIN_API_KEY')

    # Paystack Config - also stored in Secrets
    PAYSTACK_SECRET_KEY = os.environ.get('PAYSTACK_SECRET_KEY')
    PAYSTACK_API_BASE_URL = 'https://api.paystack.co'

    # This tells the app to use a file named haskel_payment.db as our database
    SQLALCHEMY_DATABASE_URI = 'sqlite:///haskel_payment.db'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

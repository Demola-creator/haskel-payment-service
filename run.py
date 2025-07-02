import os
import enum
import datetime
import requests
import sys
from functools import wraps
from flask import Flask, jsonify, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, init, migrate, upgrade

# --- 1. App & Config Setup ---
app = Flask(__name__)
# Load config from Replit Secrets
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
app.config['INTERNAL_ADMIN_API_KEY'] = os.environ.get('INTERNAL_ADMIN_API_KEY')
app.config['PAYSTACK_SECRET_KEY'] = os.environ.get('PAYSTACK_SECRET_KEY')
app.config['PAYSTACK_API_BASE_URL'] = 'https://api.paystack.co'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///haskel_payment.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# --- 2. Database Initialization ---
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- 3. Database Models ---
class BillingCycle(enum.Enum):
    TERMLY = 'termly'
    SEMESTERLY = 'semesterly'
    SESSIONAL = 'sessional'

class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    price = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), default='NGN', nullable=False)
    billing_cycle = db.Column(db.Enum(BillingCycle), nullable=False)
    features = db.Column(db.JSON, nullable=True)
    is_active = db.Column(db.Boolean, default=True)

class SubscriptionStatus(enum.Enum):
    ACTIVE = 'active'
    PENDING = 'pending'
    EXPIRED = 'expired'
    CANCELED = 'canceled'
    SUSPENDED = 'suspended'

class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    user_public_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False)
    status = db.Column(db.Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING, nullable=False)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    plan = db.relationship('SubscriptionPlan', backref='subscriptions')

class PaymentStatus(enum.Enum):
    PENDING = 'pending'
    SUCCESSFUL = 'successful'
    FAILED = 'failed'

class PaymentTransaction(db.Model):
    __tablename__ = 'payment_transactions'
    id = db.Column(db.Integer, primary_key=True)
    user_public_id = db.Column(db.String(50), nullable=False, index=True)
    subscription_id = db.Column(db.Integer, db.ForeignKey('user_subscriptions.id'))
    amount = db.Column(db.Integer, nullable=False)
    currency = db.Column(db.String(3), nullable=False)
    status = db.Column(db.Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    gateway = db.Column(db.String(50), default='paystack')
    gateway_reference = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, onupdate=db.func.current_timestamp())
    subscription = db.relationship('UserSubscription', backref='transactions')

# --- 4. Payment Gateway Service (Exists but not used by routes in this file) ---
# (Code for this class is omitted for brevity as it's not needed for the fix, but it's safe to leave it in your file)

# --- 5. API Routes ---
@app.route("/api/v1/subscriptions/status/<user_public_id>", methods=['GET'])
def get_subscription_status(user_public_id):
    subscription = UserSubscription.query.filter_by(user_public_id=user_public_id).first()
    if not subscription:
        # For simplicity in this test, we assume a plan exists.
        default_plan = SubscriptionPlan.query.first()
        if not default_plan:
             return jsonify({'status': 'error', 'message': 'No default subscription plan found.'}), 500
        new_subscription = UserSubscription(user_public_id=user_public_id, plan_id=default_plan.id, status=SubscriptionStatus.PENDING)
        db.session.add(new_subscription)
        db.session.commit()
        return jsonify({'status': new_subscription.status.value}), 200
    return jsonify({'status': subscription.status.value}), 200

# --- 6. Main Execution Block ---
        # --- 6. Main Execution Block ---
    if __name__ == '__main__':
            # This checks if you passed an argument like "db_migrate" from the command line
            if len(sys.argv) > 1:
                # We need the app context to run these commands
                with app.app_context():
                    if sys.argv[1] == 'db_init':
                        init()
                        print("Migrations folder initialized.")
                    elif sys.argv[1] == 'db_migrate':
                        migrate(message="Initial models")
                        print("Migration script created.")
                    elif sys.argv[1] == 'db_upgrade':
                        upgrade()
                        print("Database upgraded successfully.")
            else:
                # If no arguments, just run the server
                app.run(host='0.0.0.0', port=5002)
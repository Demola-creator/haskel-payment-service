import os
import sys
import enum
import uuid
import datetime
from functools import wraps
from flask import Flask, jsonify, request, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate, init, migrate, upgrade
import requests

# --- 1. App & Config Setup ---
app = Flask(__name__)
app.config['FLASK_APP'] = os.environ.get('FLASK_APP')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')
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
    is_active = db.Column(db.Boolean, default=True)

class SubscriptionStatus(enum.Enum):
    ACTIVE = 'active'
    PENDING = 'pending'

class UserSubscription(db.Model):
    __tablename__ = 'user_subscriptions'
    id = db.Column(db.Integer, primary_key=True)
    user_public_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False)
    status = db.Column(db.Enum(SubscriptionStatus), default=SubscriptionStatus.PENDING, nullable=False)
    plan = db.relationship('SubscriptionPlan', backref='subscriptions')

# --- 4. API Routes ---
@app.route("/api/v1/subscriptions/status/<user_public_id>", methods=['GET'])
def get_subscription_status(user_public_id):
    subscription = UserSubscription.query.filter_by(user_public_id=user_public_id).first()
    if not subscription:
        default_plan = SubscriptionPlan.query.first()
        if not default_plan: # Create a default plan if none exist
            default_plan = SubscriptionPlan(name="default", price=1000, billing_cycle=BillingCycle.TERMLY)
            db.session.add(default_plan)
            db.session.commit() # Commit to get the ID
        new_subscription = UserSubscription(user_public_id=user_public_id, plan_id=default_plan.id, status=SubscriptionStatus.PENDING)
        db.session.add(new_subscription)
        db.session.commit()
        return jsonify({'status': new_subscription.status.value}), 200
    return jsonify({'status': subscription.status.value}), 200

# --- 5. Main Execution Block ---
if __name__ == '__main__':
    if len(sys.argv) > 1:
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
        app.run(host='0.0.0.0', port=5002)
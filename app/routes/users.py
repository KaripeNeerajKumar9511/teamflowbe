from flask import Blueprint, jsonify
from flask_jwt_extended import verify_jwt_in_request

from app.models.user import User

users_bp = Blueprint("users", __name__)


@users_bp.route("/", methods=["GET"])
def list_users():
    """List all users (useful for assigning tasks). Requires auth."""
    verify_jwt_in_request()
    users = User.query.order_by(User.name).all()
    return jsonify([u.to_dict() for u in users]), 200

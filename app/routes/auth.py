from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, verify_jwt_in_request

from app import db, bcrypt
from app.models.user import User

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}

    # --- Validation ---
    errors = {}
    name = (data.get("name") or "").strip()
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""
    role = data.get("role", "member")

    if not name:
        errors["name"] = "Name is required."
    if not email or "@" not in email:
        errors["email"] = "A valid email is required."
    if len(password) < 6:
        errors["password"] = "Password must be at least 6 characters."
    if role not in ("admin", "member"):
        errors["role"] = "Role must be 'admin' or 'member'."

    if errors:
        return jsonify({"errors": errors}), 422

    # Check duplicate email
    if User.query.filter_by(email=email).first():
        return jsonify({"errors": {"email": "This email is already registered."}}), 409

    # Create user
    hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")
    user = User(name=name, email=email, password_hash=hashed_pw, role=role)
    db.session.add(user)
    db.session.commit()

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    password = data.get("password") or ""

    user = User.query.filter_by(email=email).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, password):
        return jsonify({"error": "Invalid email or password."}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"token": token, "user": user.to_dict()}), 200


@auth_bp.route("/me", methods=["GET"])
def me():
    try:
        verify_jwt_in_request()
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({"user": user.to_dict()}), 200
    except Exception:
        return jsonify({"error": "Not authenticated"}), 401

from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt_identity, verify_jwt_in_request

from app.models.user import User
from app.models.project import Project
from app.models.team_member import TeamMember


def jwt_required_custom(fn):
    """Wrapper that verifies JWT and attaches the current user."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        return fn(*args, **kwargs)
    return wrapper


def get_current_user():
    """Helper to fetch the User object for the logged-in identity."""
    user_id = get_jwt_identity()
    if user_id is None:
        return None
    try:
        return User.query.get(int(user_id))
    except (ValueError, TypeError):
        return None


def admin_required(fn):
    """Only global admins may access this endpoint."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user = get_current_user()
        if not user or user.role != "admin":
            return jsonify({"error": "Admin access required"}), 403
        return fn(*args, **kwargs)
    return wrapper


def project_member_required(fn):
    """
    The calling user must be a member (or owner) of the project
    identified by the `project_id` URL parameter.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user = get_current_user()
        project_id = kwargs.get("project_id")
        project = Project.query.get(project_id)

        if not project:
            return jsonify({"error": "Project not found"}), 404

        is_owner = project.owner_id == user.id
        is_member = TeamMember.query.filter_by(
            project_id=project_id, user_id=user.id
        ).first() is not None

        if not is_owner and not is_member:
            return jsonify({"error": "You are not a member of this project"}), 403

        return fn(*args, **kwargs)
    return wrapper


def project_admin_required(fn):
    """
    The calling user must be the project owner OR have role 'admin'
    in the TeamMember row for this project.
    """
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user = get_current_user()
        project_id = kwargs.get("project_id")
        project = Project.query.get(project_id)

        if not project:
            return jsonify({"error": "Project not found"}), 404

        if project.owner_id == user.id:
            return fn(*args, **kwargs)

        membership = TeamMember.query.filter_by(
            project_id=project_id, user_id=user.id
        ).first()

        if not membership or membership.role != "admin":
            return jsonify({"error": "Project admin access required"}), 403

        return fn(*args, **kwargs)
    return wrapper

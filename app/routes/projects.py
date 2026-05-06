from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app import db
from app.models.project import Project
from app.models.team_member import TeamMember
from app.models.user import User
from app.middleware.auth import (
    get_current_user,
    project_member_required,
    project_admin_required,
)

projects_bp = Blueprint("projects", __name__)


@projects_bp.route("/", methods=["GET"])
@jwt_required()
def list_projects():
    user = get_current_user()

    owned = Project.query.filter_by(owner_id=user.id).all()
    member_of = (
        db.session.query(Project)
        .join(TeamMember, TeamMember.project_id == Project.id)
        .filter(TeamMember.user_id == user.id)
        .all()
    )

    # Merge and deduplicate
    project_map = {p.id: p for p in owned + member_of}
    projects = list(project_map.values())
    return jsonify([p.to_dict() for p in projects]), 200


@projects_bp.route("/", methods=["POST"])
@jwt_required()
def create_project():
    user = get_current_user()
    data = request.get_json() or {}

    name = (data.get("name") or "").strip()
    if not name:
        return jsonify({"errors": {"name": "Project name is required."}}), 422

    project = Project(
        name=name,
        description=(data.get("description") or "").strip(),
        owner_id=user.id,
    )
    db.session.add(project)
    db.session.commit()
    return jsonify(project.to_dict(include_members=True)), 201


@projects_bp.route("/<int:project_id>", methods=["GET"])
@project_member_required
def get_project(project_id):
    """Get full project detail including members and tasks."""
    project = Project.query.get(project_id)
    return jsonify(project.to_dict(include_members=True, include_tasks=True)), 200


@projects_bp.route("/<int:project_id>", methods=["PUT"])
@project_admin_required
def update_project(project_id):
    """Update project name/description. Only project admins or owner."""
    project = Project.query.get(project_id)
    data = request.get_json() or {}

    if "name" in data:
        name = data["name"].strip()
        if not name:
            return jsonify({"errors": {"name": "Name cannot be empty."}}), 422
        project.name = name
    if "description" in data:
        project.description = data["description"].strip()

    db.session.commit()
    return jsonify(project.to_dict()), 200


@projects_bp.route("/<int:project_id>", methods=["DELETE"])
@project_admin_required
def delete_project(project_id):
    """Delete a project. Only owner or project admin."""
    project = Project.query.get(project_id)
    db.session.delete(project)
    db.session.commit()
    return jsonify({"message": "Project deleted."}), 200


# ── Team member management ─────────────────────────────────────────────────────

@projects_bp.route("/<int:project_id>/members", methods=["GET"])
@project_member_required
def list_members(project_id):
    members = TeamMember.query.filter_by(project_id=project_id).all()
    return jsonify([m.to_dict() for m in members]), 200


@projects_bp.route("/<int:project_id>/members", methods=["POST"])
@project_admin_required
def add_member(project_id):
    """Add a user to the project by email. Only project admins."""
    data = request.get_json() or {}
    email = (data.get("email") or "").strip().lower()
    role = data.get("role", "member")

    if not email:
        return jsonify({"errors": {"email": "Email is required."}}), 422
    if role not in ("admin", "member"):
        return jsonify({"errors": {"role": "Role must be 'admin' or 'member'."}}), 422

    target_user = User.query.filter_by(email=email).first()
    if not target_user:
        return jsonify({"error": f"No user found with email '{email}'."}), 404

    project = Project.query.get(project_id)
    if project.owner_id == target_user.id:
        return jsonify({"error": "The project owner is already a member."}), 409

    existing = TeamMember.query.filter_by(
        project_id=project_id, user_id=target_user.id
    ).first()
    if existing:
        return jsonify({"error": "User is already a member of this project."}), 409

    member = TeamMember(project_id=project_id, user_id=target_user.id, role=role)
    db.session.add(member)
    db.session.commit()
    return jsonify(member.to_dict()), 201


@projects_bp.route("/<int:project_id>/members/<int:member_id>", methods=["DELETE"])
@project_admin_required
def remove_member(project_id, member_id):
    """Remove a member from a project."""
    member = TeamMember.query.filter_by(id=member_id, project_id=project_id).first()
    if not member:
        return jsonify({"error": "Member not found."}), 404

    db.session.delete(member)
    db.session.commit()
    return jsonify({"message": "Member removed."}), 200

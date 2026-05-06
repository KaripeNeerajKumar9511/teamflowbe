from datetime import datetime, timezone
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, verify_jwt_in_request

from app import db
from app.models.task import Task, TASK_STATUSES, TASK_PRIORITIES
from app.models.project import Project
from app.models.team_member import TeamMember
from app.models.comment import Comment
from app.middleware.auth import get_current_user, project_member_required

tasks_bp = Blueprint("tasks", __name__)


def _parse_due_date(raw):
    """Parse an ISO date string into a naive datetime or None."""
    if not raw:
        return None
    try:
        # Accept both date-only (YYYY-MM-DD) and full ISO datetime
        if "T" in raw:
            return datetime.fromisoformat(raw.replace("Z", "+00:00"))
        return datetime.strptime(raw, "%Y-%m-%d")
    except ValueError:
        return None


@tasks_bp.route("/project/<int:project_id>", methods=["GET"])
@project_member_required
def list_tasks(project_id):
    """List all tasks for a project, with optional filters."""
    status = request.args.get("status")
    assignee_id = request.args.get("assignee_id", type=int)
    priority = request.args.get("priority")

    query = Task.query.filter_by(project_id=project_id)
    if status:
        query = query.filter_by(status=status)
    if assignee_id:
        query = query.filter_by(assignee_id=assignee_id)
    if priority:
        query = query.filter_by(priority=priority)

    tasks = query.order_by(Task.created_at.desc()).all()
    return jsonify([t.to_dict() for t in tasks]), 200


@tasks_bp.route("/project/<int:project_id>", methods=["POST"])
@project_member_required
@jwt_required()
def create_task(project_id):
    user = get_current_user()
    data = request.get_json() or {}

    # Validation
    errors = {}
    title = (data.get("title") or "").strip()
    status = data.get("status", "todo")
    priority = data.get("priority", "medium")

    if not title:
        errors["title"] = "Task title is required."
    if status not in TASK_STATUSES:
        errors["status"] = f"Status must be one of: {', '.join(TASK_STATUSES)}."
    if priority not in TASK_PRIORITIES:
        errors["priority"] = f"Priority must be one of: {', '.join(TASK_PRIORITIES)}."

    if errors:
        return jsonify({"errors": errors}), 422

    task = Task(
        title=title,
        description=(data.get("description") or "").strip(),
        status=status,
        priority=priority,
        due_date=_parse_due_date(data.get("due_date")),
        project_id=project_id,
        created_by=user.id,
        assignee_id=data.get("assignee_id"),
    )
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201


@tasks_bp.route("/<int:task_id>", methods=["GET"])
@jwt_required()
def get_task(task_id):
    task = Task.query.get_or_404(task_id)
    return jsonify(task.to_dict()), 200


@tasks_bp.route("/<int:task_id>", methods=["PUT"])
@jwt_required()
def update_task(task_id):
    user = get_current_user()
    task = Task.query.get_or_404(task_id)

    # Check membership
    project = task.project
    is_owner = project.owner_id == user.id
    membership = TeamMember.query.filter_by(
        project_id=task.project_id, user_id=user.id
    ).first()
    is_project_admin = is_owner or (membership and membership.role == "admin")
    is_assignee = task.assignee_id == user.id

    if not is_project_admin and not is_assignee and task.created_by != user.id:
        return jsonify({"error": "You don't have permission to update this task."}), 403

    data = request.get_json() or {}

    # Regular members can only change the status
    if not is_project_admin:
        if "status" in data:
            if data["status"] not in TASK_STATUSES:
                return jsonify({"errors": {"status": "Invalid status."}}), 422
            task.status = data["status"]
    else:
        # Admin can change everything
        if "title" in data:
            title = data["title"].strip()
            if not title:
                return jsonify({"errors": {"title": "Title cannot be empty."}}), 422
            task.title = title
        if "description" in data:
            task.description = data["description"].strip()
        if "status" in data:
            if data["status"] not in TASK_STATUSES:
                return jsonify({"errors": {"status": "Invalid status."}}), 422
            task.status = data["status"]
        if "priority" in data:
            if data["priority"] not in TASK_PRIORITIES:
                return jsonify({"errors": {"priority": "Invalid priority."}}), 422
            task.priority = data["priority"]
        if "due_date" in data:
            task.due_date = _parse_due_date(data["due_date"])
        if "assignee_id" in data:
            task.assignee_id = data["assignee_id"]

    task.updated_at = datetime.now(timezone.utc)
    db.session.commit()
    return jsonify(task.to_dict()), 200


@tasks_bp.route("/<int:task_id>", methods=["DELETE"])
@jwt_required()
def delete_task(task_id):
    user = get_current_user()
    task = Task.query.get_or_404(task_id)

    project = task.project
    is_owner = project.owner_id == user.id
    membership = TeamMember.query.filter_by(
        project_id=task.project_id, user_id=user.id
    ).first()
    is_project_admin = is_owner or (membership and membership.role == "admin")

    if not is_project_admin and task.created_by != user.id:
        return jsonify({"error": "You don't have permission to delete this task."}), 403

    db.session.delete(task)
    db.session.commit()
    return jsonify({"message": "Task deleted."}), 200


@tasks_bp.route("/dashboard", methods=["GET"])
@jwt_required()
def dashboard():
    user = get_current_user()

    assigned = Task.query.filter_by(assignee_id=user.id).all()
    overdue = [t for t in assigned if t.is_overdue]

    status_counts = {}
    for status in TASK_STATUSES:
        status_counts[status] = sum(1 for t in assigned if t.status == status)

    return jsonify({
        "total_assigned": len(assigned),
        "overdue_count": len(overdue),
        "status_counts": status_counts,
        "overdue_tasks": [t.to_dict() for t in overdue],
        "recent_tasks": [t.to_dict() for t in assigned[:10]],
    }), 200


@tasks_bp.route("/<int:task_id>/comments", methods=["POST"])
@jwt_required()
def add_comment(task_id):
    """Add a comment (or reply) to a task."""
    user = get_current_user()
    task = Task.query.get_or_404(task_id)
    
    # Verify user is a member of the project
    project = task.project
    membership = TeamMember.query.filter_by(project_id=project.id, user_id=user.id).first()
    if not membership and project.owner_id != user.id:
        return jsonify({"error": "You must be a member of the project to comment."}), 403

    data = request.get_json() or {}
    content = (data.get("content") or "").strip()
    parent_id = data.get("parent_id")

    if not content:
        return jsonify({"error": "Comment content is required."}), 422

    comment = Comment(
        content=content,
        user_id=user.id,
        task_id=task_id,
        parent_id=parent_id
    )
    db.session.add(comment)
    db.session.commit()
    return jsonify(comment.to_dict()), 201


@tasks_bp.route("/comments/<int:comment_id>", methods=["DELETE"])
@jwt_required()
def delete_comment(comment_id):
    """Only the person who created the comment can delete it."""
    user = get_current_user()
    comment = Comment.query.get_or_404(comment_id)

    if comment.user_id != user.id:
        return jsonify({"error": "You can only delete your own comments."}), 403

    db.session.delete(comment)
    db.session.commit()
    return jsonify({"message": "Comment deleted."}), 200

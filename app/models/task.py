from datetime import datetime, timezone
from app import db

# Valid status values for a task
TASK_STATUSES = ("todo", "in_progress", "done", "blocked")
TASK_PRIORITIES = ("low", "medium", "high")


class Task(db.Model):
    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    status = db.Column(db.String(20), nullable=False, default="todo")
    priority = db.Column(db.String(20), nullable=False, default="medium")
    due_date = db.Column(db.DateTime, nullable=True)

    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    # The person who created the task
    created_by = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # The person the task is assigned to (can be null = unassigned)
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    project = db.relationship("Project", back_populates="tasks")
    assignee = db.relationship("User", foreign_keys=[assignee_id], back_populates="assigned_tasks")
    creator = db.relationship("User", foreign_keys=[created_by])
    comments = db.relationship(
        "Comment", backref="task", cascade="all, delete-orphan", lazy="dynamic"
    )

    @property
    def is_overdue(self):
        if self.due_date and self.status != "done":
            return datetime.now(timezone.utc) > self.due_date.replace(tzinfo=timezone.utc)
        return False

    def to_dict(self):
        from app.models.comment import Comment
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "is_overdue": self.is_overdue,
            "project_id": self.project_id,
            "created_by": self.created_by,
            "creator_name": self.creator.name if self.creator else None,
            "assignee_id": self.assignee_id,
            "assignee_name": self.assignee.name if self.assignee else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "comments": [c.to_dict() for c in self.comments.filter_by(parent_id=None).order_by(Comment.created_at.asc()).all()],
        }

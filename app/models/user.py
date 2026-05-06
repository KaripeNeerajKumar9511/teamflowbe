from datetime import datetime, timezone
from app import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # Global role: 'admin' can create projects; 'member' can only be invited
    role = db.Column(db.String(20), nullable=False, default="member")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    owned_projects = db.relationship(
        "Project", back_populates="owner", cascade="all, delete-orphan"
    )
    team_memberships = db.relationship(
        "TeamMember", back_populates="user", cascade="all, delete-orphan"
    )
    assigned_tasks = db.relationship("Task", foreign_keys="Task.assignee_id", back_populates="assignee")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "role": self.role,
            "created_at": self.created_at.isoformat(),
        }

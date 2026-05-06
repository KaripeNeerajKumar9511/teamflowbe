from datetime import datetime, timezone
from app import db


class Project(db.Model):
    __tablename__ = "projects"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.Text, default="")
    owner_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(
        db.DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # Relationships
    owner = db.relationship("User", back_populates="owned_projects")
    members = db.relationship(
        "TeamMember", back_populates="project", cascade="all, delete-orphan"
    )
    tasks = db.relationship(
        "Task", back_populates="project", cascade="all, delete-orphan"
    )

    def to_dict(self, include_members=False, include_tasks=False):
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "owner_id": self.owner_id,
            "owner_name": self.owner.name if self.owner else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "task_count": len(self.tasks),
        }
        if include_members:
            data["members"] = [m.to_dict() for m in self.members]
        if include_tasks:
            data["tasks"] = [t.to_dict() for t in self.tasks]
        return data

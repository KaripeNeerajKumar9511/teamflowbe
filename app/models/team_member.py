from datetime import datetime, timezone
from app import db


class TeamMember(db.Model):
    """
    Represents a user's membership in a project.
    role can be 'admin' (project-level admin) or 'member'.
    """
    __tablename__ = "team_members"

    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    # Role scoped to this project
    role = db.Column(db.String(20), nullable=False, default="member")
    joined_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Unique constraint: one user can only join a project once
    __table_args__ = (
        db.UniqueConstraint("project_id", "user_id", name="uq_project_user"),
    )

    # Relationships
    project = db.relationship("Project", back_populates="members")
    user = db.relationship("User", back_populates="team_memberships")

    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else None,
            "user_email": self.user.email if self.user else None,
            "role": self.role,
            "joined_at": self.joined_at.isoformat(),
        }

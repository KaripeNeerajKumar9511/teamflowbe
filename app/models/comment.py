from datetime import datetime, timezone
from app import db


class Comment(db.Model):
    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    task_id = db.Column(db.Integer, db.ForeignKey("tasks.id"), nullable=False)
    # parent_id allows for nested replies
    parent_id = db.Column(db.Integer, db.ForeignKey("comments.id"), nullable=True)

    # Relationships
    user = db.relationship("User")
    replies = db.relationship(
        "Comment",
        backref=db.backref("parent", remote_side=[id]),
        cascade="all, delete-orphan",
    )

    def to_dict(self):
        return {
            "id": self.id,
            "content": self.content,
            "created_at": self.created_at.isoformat(),
            "user_id": self.user_id,
            "user_name": self.user.name if self.user else "Unknown",
            "task_id": self.task_id,
            "parent_id": self.parent_id,
            "replies": [r.to_dict() for r in self.replies] if not self.parent_id else [],
        }

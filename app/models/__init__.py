# This file makes the models package importable and ensures all
# models are registered with SQLAlchemy before db.create_all() is called.
from app.models.user import User
from app.models.project import Project
from app.models.team_member import TeamMember
from app.models.task import Task
from app.models.comment import Comment

__all__ = ["User", "Project", "TeamMember", "Task", "Comment"]

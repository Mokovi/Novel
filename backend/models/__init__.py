"""ORM model imports — ensures all models are registered on Base.metadata."""

from backend.models.api_plan import ApiPlan, PlanApi, TaskPlanBinding
from backend.models.book import Book
from backend.models.chapter import Arc, Chapter, ChapterVersion, Volume
from backend.models.character import Character, CharacterRelation
from backend.models.event import EventParticipant, WorldEvent
from backend.models.item import Item, ItemOwnershipHistory
from backend.models.model_api import ModelApi
from backend.models.story_line import ChapterCharacter, ChapterStoryLine, StoryLine
from backend.models.user import User

__all__ = [
    "ApiPlan",
    "Arc",
    "Book",
    "Chapter",
    "ChapterCharacter",
    "ChapterStoryLine",
    "ChapterVersion",
    "Character",
    "CharacterRelation",
    "EventParticipant",
    "Item",
    "ItemOwnershipHistory",
    "ModelApi",
    "PlanApi",
    "StoryLine",
    "TaskPlanBinding",
    "User",
    "Volume",
    "WorldEvent",
]

"""Repository for Character and CharacterRelation database operations."""

from typing import Optional

from sqlalchemy.orm import Session

from backend.models.character import Character, CharacterRelation
from backend.schemas.character import (
    CharacterCreate,
    CharacterRelationCreate,
    CharacterRelationUpdate,
    CharacterUpdate,
)


def list_characters(
    db: Session,
    role_type: Optional[str] = None,
    book_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Character]:
    query = db.query(Character)
    if role_type:
        query = query.filter(Character.role_type == role_type)
    if book_id is not None:
        query = query.filter(Character.book_id == book_id)
    return query.order_by(Character.id).offset(skip).limit(limit).all()


def get_character(db: Session, character_id: int) -> Optional[Character]:
    return db.get(Character, character_id)


def create_character(db: Session, data: CharacterCreate) -> Character:
    character = Character(**data.model_dump())
    db.add(character)
    db.commit()
    db.refresh(character)
    return character


def update_character(
    db: Session, character_id: int, data: CharacterUpdate
) -> Optional[Character]:
    character = db.get(Character, character_id)
    if not character:
        return None
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return character
    for key, value in update_data.items():
        setattr(character, key, value)
    db.commit()
    db.refresh(character)
    return character


def delete_character(db: Session, character_id: int) -> bool:
    character = db.get(Character, character_id)
    if not character:
        return False
    db.delete(character)
    db.commit()
    return True


# ── Relations ─────────────────────────────────────────────


def list_relations(db: Session) -> list[CharacterRelation]:
    return db.query(CharacterRelation).all()


def create_relation(db: Session, data: CharacterRelationCreate) -> CharacterRelation:
    relation = CharacterRelation(**data.model_dump())
    db.add(relation)
    db.commit()
    db.refresh(relation)
    return relation


def update_relation(
    db: Session, relation_id: int, data: CharacterRelationUpdate
) -> Optional[CharacterRelation]:
    relation = db.get(CharacterRelation, relation_id)
    if not relation:
        return None
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return relation
    for key, value in update_data.items():
        setattr(relation, key, value)
    db.commit()
    db.refresh(relation)
    return relation


def delete_relation(db: Session, relation_id: int) -> bool:
    relation = db.get(CharacterRelation, relation_id)
    if not relation:
        return False
    db.delete(relation)
    db.commit()
    return True


def get_relations_graph(db: Session, book_id: Optional[int] = None) -> dict:
    """Return relations formatted for Vue Flow: {nodes: [...], edges: [...]}."""
    query = db.query(Character)
    if book_id is not None:
        query = query.filter(Character.book_id == book_id)
    characters = query.all()
    relations = db.query(CharacterRelation).all()

    nodes = [
        {
            "id": str(c.id),
            "type": "character",
            "position": {"x": 0, "y": 0},
            "data": {
                "name": c.name,
                "role_type": c.role_type or "unknown",
                "status": c.status,
            },
        }
        for c in characters
    ]

    edges = [
        {
            "id": str(r.id),
            "source": str(r.character_id_from),
            "target": str(r.character_id_to),
            "type": "smoothstep",
            "data": {
                "relation_type": r.relation_type,
                "description": r.description or "",
            },
        }
        for r in relations
    ]

    return {"nodes": nodes, "edges": edges}

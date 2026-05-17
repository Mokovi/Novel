"""REST endpoints for Character and CharacterRelation CRUD."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.repositories import character_repo
from backend.schemas.character import (
    CharacterCreate,
    CharacterRelationCreate,
    CharacterRelationResponse,
    CharacterRelationUpdate,
    CharacterResponse,
    CharacterUpdate,
)

router = APIRouter(prefix="/api/v1/characters", tags=["characters"])


# ── Relations (must come before /{id} to avoid path conflict) ──


@router.get("/relations", response_model=dict)
def get_relations_graph(db: Session = Depends(get_db)):
    """Get all relations formatted as nodes + edges for Vue Flow."""
    return character_repo.get_relations_graph(db)


@router.post("/relations", response_model=CharacterRelationResponse, status_code=201)
def create_relation(body: CharacterRelationCreate, db: Session = Depends(get_db)):
    """Create a character relation."""
    # Validate both characters exist
    if not character_repo.get_character(db, body.character_id_from):
        raise HTTPException(status_code=404, detail="Source character not found")
    if not character_repo.get_character(db, body.character_id_to):
        raise HTTPException(status_code=404, detail="Target character not found")
    return character_repo.create_relation(db, body)


@router.put("/relations/{relation_id}", response_model=CharacterRelationResponse)
def update_relation(
    relation_id: int,
    body: CharacterRelationUpdate,
    db: Session = Depends(get_db),
):
    """Update a character relation."""
    relation = character_repo.update_relation(db, relation_id, body)
    if not relation:
        raise HTTPException(status_code=404, detail="Relation not found")
    return relation


@router.delete("/relations/{relation_id}", status_code=204)
def delete_relation(relation_id: int, db: Session = Depends(get_db)):
    """Delete a character relation."""
    deleted = character_repo.delete_relation(db, relation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Relation not found")
    return None


# ── Characters ────────────────────────────────────────────


@router.get("", response_model=list[CharacterResponse])
def list_characters(
    role_type: str | None = Query(None, description="Filter by role type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Get characters with optional role type filter and pagination."""
    return character_repo.list_characters(db, role_type=role_type, skip=skip, limit=limit)


@router.post("", response_model=CharacterResponse, status_code=201)
def create_character(body: CharacterCreate, db: Session = Depends(get_db)):
    """Create a new character."""
    return character_repo.create_character(db, body)


@router.get("/{character_id}", response_model=CharacterResponse)
def get_character(character_id: int, db: Session = Depends(get_db)):
    """Get character detail by ID."""
    character = character_repo.get_character(db, character_id)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.put("/{character_id}", response_model=CharacterResponse)
def update_character(
    character_id: int,
    body: CharacterUpdate,
    db: Session = Depends(get_db),
):
    """Update character details."""
    character = character_repo.update_character(db, character_id, body)
    if not character:
        raise HTTPException(status_code=404, detail="Character not found")
    return character


@router.delete("/{character_id}", status_code=204)
def delete_character(character_id: int, db: Session = Depends(get_db)):
    """Delete a character by ID."""
    deleted = character_repo.delete_character(db, character_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Character not found")
    return None

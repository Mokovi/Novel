"""Repository for Location database operations."""

from typing import Optional

from sqlalchemy.orm import Session

from backend.models.location import Location
from backend.schemas.location import LocationCreate, LocationUpdate


def list_locations(
    db: Session,
    book_id: int | None = None,
    location_type: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> list[Location]:
    query = db.query(Location)
    if book_id is not None:
        query = query.filter(Location.book_id == book_id)
    if location_type:
        query = query.filter(Location.location_type == location_type)
    if search:
        query = query.filter(Location.name.ilike(f"%{search}%"))
    return query.order_by(Location.id).offset(skip).limit(limit).all()


def get_location(db: Session, location_id: int) -> Optional[Location]:
    return db.get(Location, location_id)


def create_location(db: Session, data: LocationCreate, book_id: int = 1) -> Location:
    location = Location(**data.model_dump(), book_id=book_id)
    db.add(location)
    db.commit()
    db.refresh(location)
    return location


def update_location(
    db: Session, location_id: int, data: LocationUpdate
) -> Optional[Location]:
    location = db.get(Location, location_id)
    if not location:
        return None
    update_data = data.model_dump(exclude_unset=True)
    if not update_data:
        return location
    for key, value in update_data.items():
        setattr(location, key, value)
    db.commit()
    db.refresh(location)
    return location


def delete_location(db: Session, location_id: int) -> bool:
    location = db.get(Location, location_id)
    if not location:
        return False
    db.delete(location)
    db.commit()
    return True


def bulk_create_locations(
    db: Session, locations_data: list[dict], book_id: int
) -> dict:
    """Create multiple locations in bulk, accumulating errors without interrupting.

    Returns ``{created_count, skipped_count, errors}``.
    """
    created_count = 0
    skipped_count = 0
    errors = []
    for data in locations_data:
        name = data.get("name", "").strip()
        if not name:
            skipped_count += 1
            errors.append("Skipped item with empty name")
            continue
        try:
            location = Location(**data, book_id=book_id)
            db.add(location)
            db.flush()
            created_count += 1
        except Exception as e:
            skipped_count += 1
            errors.append(f"Failed to import '{name}': {e}")
    db.commit()
    return {"created_count": created_count, "skipped_count": skipped_count, "errors": errors}

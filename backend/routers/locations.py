"""REST endpoints for Location CRUD."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.user import User
from backend.routers.deps import get_current_user
from backend.repositories import book_repo, location_repo
from backend.schemas.location import LocationCreate, LocationResponse, LocationUpdate

router = APIRouter(prefix="/api/v1/locations", tags=["locations"])


@router.get("", response_model=list[LocationResponse])
def list_locations(
    book_id: int = Query(..., description="Filter by book ID"),
    location_type: str | None = Query(None, description="Filter by location type"),
    search: str | None = Query(None, description="Search by location name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get locations with optional type filter and pagination."""
    book_repo.get_book_for_user(db, book_id, current_user.id)  # verify access
    return location_repo.list_locations(db, book_id=book_id, location_type=location_type, search=search, skip=skip, limit=limit)


@router.post("", response_model=LocationResponse, status_code=201)
def create_location(
    body: LocationCreate,
    book_id: int = Query(..., description="Book ID to create location under"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new location."""
    book_repo.get_book_for_user(db, book_id, current_user.id)
    return location_repo.create_location(db, body, book_id=book_id)


@router.get("/{location_id}", response_model=LocationResponse)
def get_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get location detail by ID."""
    location = location_repo.get_location(db, location_id)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@router.put("/{location_id}", response_model=LocationResponse)
def update_location(
    location_id: int,
    body: LocationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update location details."""
    location = location_repo.update_location(db, location_id, body)
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    return location


@router.delete("/{location_id}", status_code=204)
def delete_location(
    location_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a location by ID."""
    deleted = location_repo.delete_location(db, location_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Location not found")
    return None


@router.post("/import", response_model=dict)
def import_locations(
    body: dict,
    book_id: int = Query(..., description="Book ID to import locations into"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Bulk import locations from a JSON payload."""
    book_repo.get_book_for_user(db, book_id, current_user.id)
    data_list = body.get("locations", [])
    return location_repo.bulk_create_locations(db, data_list, book_id)

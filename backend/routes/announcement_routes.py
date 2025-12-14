from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import text
from db import get_db
from utils.auth_middleware import get_current_user, require_role

router = APIRouter()

# Pydantic models
class AnnouncementCreate(BaseModel):
    title: str
    content: str
    category: Optional[str] = "info"

class AnnouncementUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None

class AnnouncementResponse(BaseModel):
    id: int
    title: str
    content: str
    category: str
    created_by: str
    created_at: datetime
    updated_at: datetime

@router.get("/announcements", response_model=List[AnnouncementResponse])
async def get_announcements(
    page: int = 1,
    limit: int = 5,
    db: Session = Depends(get_db)
):
    """
    Get announcements with pagination
    - page: page number (default: 1)
    - limit: items per page (default: 5)
    """
    try:
        offset = (page - 1) * limit
        
        query = text("""
            SELECT id, title, content, category, created_by, created_at, updated_at
            FROM announcements
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
        """)
        
        result = db.execute(query, {"limit": limit, "offset": offset})
        announcements = []
        
        for row in result:
            row_dict = dict(row._mapping)
            announcements.append(row_dict)
        
        return announcements
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch announcements: {str(e)}"
        )

@router.get("/announcements/count")
async def get_announcements_count(db: Session = Depends(get_db)):
    """Get total count of announcements"""
    try:
        query = text("SELECT COUNT(*) as count FROM announcements")
        result = db.execute(query)
        count = result.fetchone()[0]
        
        return {"total": count}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to count announcements: {str(e)}"
        )

@router.get("/announcements/{announcement_id}", response_model=AnnouncementResponse)
async def get_announcement(
    announcement_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific announcement by ID"""
    try:
        query = text("""
            SELECT id, title, content, category, created_by, created_at, updated_at
            FROM announcements
            WHERE id = :id
        """)
        
        result = db.execute(query, {"id": announcement_id})
        announcement = result.fetchone()
        
        if not announcement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Announcement not found"
            )
        
        return dict(announcement._mapping)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch announcement: {str(e)}"
        )

@router.post("/announcements", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(
    announcement: AnnouncementCreate,
    current_user: dict = Depends(require_role("administrator")),
    db: Session = Depends(get_db)
):
    """Create a new announcement (admin only)"""
    
    try:
        query = text("""
            INSERT INTO announcements (title, content, category, created_by)
            VALUES (:title, :content, :category, :created_by)
            RETURNING id, title, content, category, created_by, created_at, updated_at
        """)
        
        result = db.execute(query, {
            "title": announcement.title,
            "content": announcement.content,
            "category": announcement.category,
            "created_by": current_user["username"]
        })
        
        new_announcement = result.fetchone()
        db.commit()
        
        return dict(new_announcement._mapping)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create announcement: {str(e)}"
        )

@router.put("/announcements/{announcement_id}", response_model=AnnouncementResponse)
async def update_announcement(
    announcement_id: int,
    announcement: AnnouncementUpdate,
    current_user: dict = Depends(require_role("administrator")),
    db: Session = Depends(get_db)
):
    """Update an announcement (admin only)"""
    
    try:
        # Build dynamic update query
        update_fields = []
        values = {"id": announcement_id}
        
        if announcement.title is not None:
            update_fields.append("title = :title")
            values["title"] = announcement.title
        
        if announcement.content is not None:
            update_fields.append("content = :content")
            values["content"] = announcement.content
        
        if announcement.category is not None:
            update_fields.append("category = :category")
            values["category"] = announcement.category
        
        if not update_fields:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        update_fields.append("updated_at = NOW()")
        
        query = text(f"""
            UPDATE announcements
            SET {', '.join(update_fields)}
            WHERE id = :id
            RETURNING id, title, content, category, created_by, created_at, updated_at
        """)
        
        result = db.execute(query, values)
        updated_announcement = result.fetchone()
        
        if not updated_announcement:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Announcement not found"
            )
        
        db.commit()
        
        return dict(updated_announcement._mapping)
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update announcement: {str(e)}"
        )

@router.delete("/announcements/{announcement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_announcement(
    announcement_id: int,
    current_user: dict = Depends(require_role("administrator")),
    db: Session = Depends(get_db)
):
    """Delete an announcement (admin only)"""
    
    try:
        query = text("DELETE FROM announcements WHERE id = :id RETURNING id")
        result = db.execute(query, {"id": announcement_id})
        deleted = result.fetchone()
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Announcement not found"
            )
        
        db.commit()
        
        return None
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete announcement: {str(e)}"
        )

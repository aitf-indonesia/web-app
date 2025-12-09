from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List
import psycopg2
from db import get_db_connection

router = APIRouter(prefix="/api/chat", tags=["chat_history"])


class ChatMessage(BaseModel):
    role: str
    message: str
    created_at: str


@router.get("/history/{id_domain}")
async def get_chat_history(id_domain: int, username: str) -> List[ChatMessage]:
    """
    Retrieve chat history for a specific user and domain.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT role, message, created_at
            FROM chat_history
            WHERE username = %s AND id_domain = %s
            ORDER BY created_at ASC
        """, (username, id_domain))
        
        rows = cur.fetchall()
        cur.close()
        
        messages = [
            ChatMessage(
                role=row[0],
                message=row[1],
                created_at=row[2].isoformat()
            )
            for row in rows
        ]
        
        return messages
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retrieve chat history: {str(e)}")
    finally:
        if conn:
            conn.close()


@router.post("/history/{id_domain}")
async def save_chat_message(id_domain: int, username: str, role: str, message: str):
    """
    Save a chat message to the database.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO chat_history (username, id_domain, role, message)
            VALUES (%s, %s, %s, %s)
            RETURNING id, created_at
        """, (username, id_domain, role, message))
        
        result = cur.fetchone()
        conn.commit()
        cur.close()
        
        return {
            "id": result[0],
            "created_at": result[1].isoformat(),
            "role": role,
            "message": message
        }
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to save chat message: {str(e)}")
    finally:
        if conn:
            conn.close()


@router.delete("/history/{id_domain}")
async def clear_chat_history(id_domain: int, username: str):
    """
    Clear all chat history for a specific user and domain.
    """
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            DELETE FROM chat_history
            WHERE username = %s AND id_domain = %s
        """, (username, id_domain))
        
        deleted_count = cur.rowcount
        conn.commit()
        cur.close()
        
        return {
            "success": True,
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        if conn:
            conn.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to clear chat history: {str(e)}")
    finally:
        if conn:
            conn.close()

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.db.database import get_db
from app.db.models import Memory

router = APIRouter()
logger = get_logger(__name__)


class CreateMemoryRequest(BaseModel):
    title: str
    content: str
    category: str = "general"
    source_message_id: str | None = None
    source_conversation_id: str | None = None


class MemoryOut(BaseModel):
    id: str
    title: str
    content: str
    category: str
    source_message_id: str | None = None
    source_conversation_id: str | None = None
    created_at: str


def _mem_to_out(mem: Memory) -> MemoryOut:
    return MemoryOut(
        id=mem.id,
        title=mem.title,
        content=mem.content,
        category=mem.category or "general",
        source_message_id=mem.source_message_id,
        source_conversation_id=mem.source_conversation_id,
        created_at=mem.created_at.isoformat(),
    )


@router.post("/memories", response_model=MemoryOut, tags=["memory"])
def create_memory(request: CreateMemoryRequest, db: Session = Depends(get_db)) -> MemoryOut:
    mem = Memory(
        title=request.title,
        content=request.content,
        category=request.category,
        source_message_id=request.source_message_id,
        source_conversation_id=request.source_conversation_id,
    )
    db.add(mem)
    db.commit()
    return _mem_to_out(mem)


@router.get("/memories", response_model=list[MemoryOut], tags=["memory"])
def list_memories(db: Session = Depends(get_db)) -> list[MemoryOut]:
    mems = db.query(Memory).order_by(Memory.created_at.desc()).all()
    return [_mem_to_out(m) for m in mems]


@router.delete("/memories/{memory_id}", tags=["memory"])
def delete_memory(memory_id: str, db: Session = Depends(get_db)) -> dict:
    mem = db.query(Memory).filter(Memory.id == memory_id).first()
    if not mem:
        raise HTTPException(status_code=404, detail="Memory not found")
    db.delete(mem)
    db.commit()
    return {"deleted": True}

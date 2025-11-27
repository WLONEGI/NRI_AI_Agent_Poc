from datetime import datetime
from typing import List, Optional, Any
from pydantic import BaseModel, Field

class MemoryMetadata(BaseModel):
    title: str
    created_at: datetime
    updated_at: datetime
    tags: List[str] = Field(default_factory=list)
    source: Optional[dict] = None
    importance: Optional[str] = "normal"
    version: int = 1

class Memory(BaseModel):
    memory_name: str
    content_markdown: str
    metadata: MemoryMetadata

class SearchResult(BaseModel):
    memory_name: str
    title: str
    score: float
    tags: List[str]
    snippet: str

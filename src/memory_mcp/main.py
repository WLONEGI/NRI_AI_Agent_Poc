from mcp.server.fastmcp import FastMCP
from typing import List, Optional
import sys
import os

# Add src directory to sys.path to allow absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from memory_mcp.storage import MemoryStore
from memory_mcp.search import SearchEngine
from memory_mcp.models import Memory, SearchResult

# Initialize server
mcp = FastMCP("local-memory-store")

# Initialize components
store = MemoryStore()
search_engine = SearchEngine(store)

@mcp.tool()
def write_memory(
    memory_name: str,
    content_markdown: str,
    tags: List[str] = None,
    source_session_id: str = None,
    source_user_id: str = None,
    append: bool = False
) -> str:
    """
    Create or update a memory.
    
    Args:
        memory_name: Unique key for the memory.
        content_markdown: The content of the memory in Markdown.
        tags: Optional list of tags.
        source_session_id: Optional session ID where this memory originated.
        source_user_id: Optional user ID.
        append: If True, append to existing memory instead of overwriting.
    """
    source = {}
    if source_session_id:
        source["session_id"] = source_session_id
    if source_user_id:
        source["user_id"] = source_user_id
    
    memory = store.save_memory(
        name=memory_name,
        content=content_markdown,
        tags=tags,
        source=source if source else None,
        append=append
    )
    return f"Memory '{memory.memory_name}' saved successfully."

@mcp.tool()
def read_memory(memory_name: str) -> str:
    """
    Read a memory by name.
    """
    memory = store.read_memory(memory_name)
    if not memory:
        return f"Memory '{memory_name}' not found."
    
    # Return full content including frontmatter (which is part of the file)
    # or we can reconstruct it. storage.read_memory returns content as read from file.
    # If the file has frontmatter, it's included.
    return memory.content_markdown

@mcp.tool()
def list_memories(
    prefix: str = None,
    tag_filter: List[str] = None,
    limit: int = 50
) -> List[dict]:
    """
    List available memories.
    """
    return store.list_memories(prefix=prefix, tag_filter=tag_filter, limit=limit)

@mcp.tool()
def delete_memory(memory_name: str) -> str:
    """
    Delete a memory.
    """
    success = store.delete_memory(memory_name)
    if success:
        return f"Memory '{memory_name}' deleted."
    else:
        return f"Memory '{memory_name}' not found."

@mcp.tool()
def search_memories(
    query: str,
    top_k: int = 5,
    tag_filter: List[str] = None
) -> List[dict]:
    """
    Search memories by keyword.
    """
    results = search_engine.search(query=query, top_k=top_k, tag_filter=tag_filter)
    return [res.model_dump() for res in results]

def main():
    mcp.run()

if __name__ == "__main__":
    main()

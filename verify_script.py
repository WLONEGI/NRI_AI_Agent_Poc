import sys
import os
from pathlib import Path

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from memory_mcp.storage import MemoryStore
from memory_mcp.search import SearchEngine
from memory_mcp.config import config

def test_memory_flow():
    print("Initializing components...")
    # Use a temporary directory for testing
    config.memory_root = Path("./test_memory_root")
    config.memories_dir = config.memory_root / "memories"
    config.index_path = config.memory_root / "index.yaml"
    config.config_path = config.memory_root / "config.yaml"
    config.logs_dir = config.memory_root / "logs"
    config._ensure_directories()
    
    store = MemoryStore()
    search = SearchEngine(store)

    print("\n1. Testing write_memory...")
    store.save_memory(
        name="test-memory-1",
        content="これはテストメモリです。重要な情報が含まれています。",
        tags=["test", "important"]
    )
    store.save_memory(
        name="test-memory-2",
        content="Pythonでの実装方法について。Janomeを使います。",
        tags=["python", "nlp"]
    )
    print("Memories saved.")

    print("\n2. Testing list_memories...")
    memories = store.list_memories()
    print(f"Found {len(memories)} memories.")
    for m in memories:
        print(f" - {m['memory_name']}: {m['title']}")

    print("\n3. Testing search_memories (query='重要')...")
    results = search.search("重要")
    print(f"Found {len(results)} results.")
    for r in results:
        print(f" - {r.memory_name} (Score: {r.score}): {r.snippet}")

    print("\n3.1 Testing search_memories (query='Python')...")
    results = search.search("Python")
    print(f"Found {len(results)} results.")
    for r in results:
        print(f" - {r.memory_name} (Score: {r.score}): {r.snippet}")

    print("\n4. Testing read_memory...")
    memory = store.read_memory("test-memory-1")
    if memory:
        print(f"Read memory content: {memory.content_markdown[:50]}...")
    else:
        print("Memory not found.")

    print("\n5. Testing delete_memory...")
    store.delete_memory("test-memory-1")
    memories = store.list_memories()
    print(f"Remaining memories: {len(memories)}")

    # Cleanup
    import shutil
    if config.memory_root.exists():
        shutil.rmtree(config.memory_root)
    print("\nTest completed.")

if __name__ == "__main__":
    test_memory_flow()

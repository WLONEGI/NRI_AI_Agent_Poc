import os
import yaml
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Dict
from .config import config
from .models import Memory, MemoryMetadata

class MemoryStore:
    def __init__(self):
        self.index: List[Dict] = []
        self._load_index()

    def _load_index(self):
        if config.index_path.exists():
            try:
                with open(config.index_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    self.index = data.get("items", []) if data else []
            except Exception as e:
                import sys
                sys.stderr.write(f"Error loading index: {e}\n")
                self.index = []
        else:
            self.index = []

    def _save_index(self):
        temp_path = config.index_path.with_suffix(".tmp")
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                yaml.dump({"items": self.index}, f, allow_unicode=True, sort_keys=False)
            temp_path.replace(config.index_path)
        except Exception as e:
            import sys
            sys.stderr.write(f"Error saving index: {e}\n")
            if temp_path.exists():
                temp_path.unlink()

    def _get_memory_path(self, created_at: datetime, slug: str) -> Path:
        year = created_at.strftime("%Y")
        month = created_at.strftime("%m")
        filename = f"{created_at.strftime('%Y%m%d')}-{slug}.md"
        directory = config.memories_dir / year / month
        directory.mkdir(parents=True, exist_ok=True)
        return directory / filename

    def save_memory(self, name: str, content: str, tags: List[str] = None, source: dict = None, append: bool = False) -> Memory:
        now = datetime.now(timezone.utc)
        tags = tags or []
        
        # Check if memory exists
        existing_item = next((item for item in self.index if item["memory_name"] == name), None)
        
        if existing_item:
            # Update existing
            path = config.memory_root / existing_item["path"]
            created_at = existing_item["created_at"]
            if isinstance(created_at, str):
                 created_at = datetime.fromisoformat(created_at)
            
            if append and path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    # Read existing content, skip frontmatter
                    existing_content = f.read()
                    # Simple split by ---
                    parts = existing_content.split("---", 2)
                    if len(parts) >= 3:
                        body = parts[2].strip()
                        content = body + "\n\n" + content
                    else:
                        # Fallback if format is weird
                        content = existing_content + "\n\n" + content

            metadata = MemoryMetadata(
                title=name, # Simple title for now, could be improved
                created_at=created_at,
                updated_at=now,
                tags=tags if tags else existing_item.get("tags", []),
                source=source or existing_item.get("source"),
                version=existing_item.get("version", 1) + 1
            )
        else:
            # Create new
            created_at = now
            path = self._get_memory_path(created_at, name)
            metadata = MemoryMetadata(
                title=name,
                created_at=created_at,
                updated_at=now,
                tags=tags,
                source=source
            )
            existing_item = {
                "memory_name": name,
                "created_at": created_at, # Store as object, yaml dumper handles it? better to isoformat
            }
            self.index.append(existing_item)

        # Update index item
        existing_item.update({
            "title": metadata.title,
            "path": str(path.relative_to(config.memory_root)),
            "created_at": metadata.created_at.isoformat(),
            "updated_at": metadata.updated_at.isoformat(),
            "tags": metadata.tags,
            "version": metadata.version
        })
        self._save_index()

        # Write Markdown file
        frontmatter = {
            "memory_name": name,
            "title": metadata.title,
            "created_at": metadata.created_at.isoformat(),
            "updated_at": metadata.updated_at.isoformat(),
            "source": metadata.source,
            "tags": metadata.tags,
            "version": metadata.version
        }
        
        file_content = "---\n" + yaml.dump(frontmatter, allow_unicode=True, sort_keys=False) + "---\n\n" + content
        
        with open(path, "w", encoding="utf-8") as f:
            f.write(file_content)

        return Memory(memory_name=name, content_markdown=content, metadata=metadata)

    def read_memory(self, name: str) -> Optional[Memory]:
        item = next((i for i in self.index if i["memory_name"] == name), None)
        if not item:
            return None
        
        path = config.memory_root / item["path"]
        if not path.exists():
            return None
            
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Parse frontmatter manually or just return whole content?
        # Requirement says: "front matter を含む Markdown 全文、または本文のみ（仕様としてどちらかに統一）"
        # Let's return whole content for now, but parse metadata for the object
        
        metadata = MemoryMetadata(
            title=item["title"],
            created_at=datetime.fromisoformat(item["created_at"]),
            updated_at=datetime.fromisoformat(item["updated_at"]),
            tags=item.get("tags", []),
            source=item.get("source"),
            version=item.get("version", 1)
        )
        
        return Memory(memory_name=name, content_markdown=content, metadata=metadata)

    def list_memories(self, prefix: str = None, tag_filter: List[str] = None, limit: int = 50) -> List[Dict]:
        results = []
        for item in self.index:
            if prefix and not item["memory_name"].startswith(prefix):
                continue
            if tag_filter:
                item_tags = set(item.get("tags", []))
                if not all(t in item_tags for t in tag_filter):
                    continue
            results.append(item)
            if len(results) >= limit:
                break
        return results

    def delete_memory(self, name: str) -> bool:
        item = next((i for i in self.index if i["memory_name"] == name), None)
        if not item:
            return False
        
        # Physical deletion
        path = config.memory_root / item["path"]
        if path.exists():
            try:
                path.unlink()
            except Exception as e:
                import sys
                sys.stderr.write(f"Error deleting file {path}: {e}\n")
                # Continue to remove from index even if file deletion fails?
                # Maybe better to fail? Let's try to remove from index.
        
        self.index.remove(item)
        self._save_index()
        return True

from typing import List, Dict
from janome.tokenizer import Tokenizer
from .models import SearchResult
from .config import config
from .storage import MemoryStore

class SearchEngine:
    def __init__(self, store: MemoryStore):
        self.store = store
        self.tokenizer = Tokenizer()

    def _tokenize(self, text: str) -> List[str]:
        if not text:
            return []
        return [token.surface for token in self.tokenizer.tokenize(text) if token.part_of_speech.split(',')[0] in ['名詞', '動詞', '形容詞']]

    def search(self, query: str, top_k: int = 5, tag_filter: List[str] = None) -> List[SearchResult]:
        query_tokens = set(self._tokenize(query))
        if not query_tokens:
            return []

        candidates = self.store.list_memories(tag_filter=tag_filter, limit=10000) # Get all for search
        results = []

        for item in candidates:
            # Load full content for search - this might be slow for many files, 
            # but for "thousands" it should be acceptable for a local tool.
            # Optimization: Cache tokens or index them in a separate file.
            # For now, we follow the requirement: "Markdown ファイルを読み込み... トークン化"
            
            memory = self.store.read_memory(item["memory_name"])
            if not memory:
                continue

            # Simple scoring
            score = 0.0
            
            # Title match
            title_tokens = self._tokenize(memory.metadata.title)
            title_matches = sum(1 for t in title_tokens if t in query_tokens)
            score += title_matches * 10.0

            # Content match
            # Remove frontmatter for content search to avoid double counting metadata
            content_body = memory.content_markdown
            if content_body.startswith("---"):
                parts = content_body.split("---", 2)
                if len(parts) >= 3:
                    content_body = parts[2]
            
            content_tokens = self._tokenize(content_body)
            content_matches = sum(1 for t in content_tokens if t in query_tokens)
            score += content_matches * 1.0
            
            # Tags match
            tag_matches = sum(1 for t in memory.metadata.tags if t in query_tokens)
            score += tag_matches * 5.0

            if score > 0:
                # Create snippet
                snippet = self._create_snippet(content_body, query_tokens)
                
                results.append(SearchResult(
                    memory_name=memory.memory_name,
                    title=memory.metadata.title,
                    score=score,
                    tags=memory.metadata.tags,
                    snippet=snippet
                ))

        # Sort by score desc
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _create_snippet(self, content: str, query_tokens: set, length: int = 100) -> str:
        # Find first occurrence of a query token
        best_pos = -1
        for token in query_tokens:
            pos = content.find(token)
            if pos != -1:
                if best_pos == -1 or pos < best_pos:
                    best_pos = pos
        
        if best_pos == -1:
            return content[:length] + "..."
        
        start = max(0, best_pos - 20)
        end = min(len(content), start + length)
        return ("..." if start > 0 else "") + content[start:end] + ("..." if end < len(content) else "")

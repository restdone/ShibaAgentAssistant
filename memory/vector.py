import uuid
from datetime import datetime
from pathlib import Path

import chromadb


class VectorMemory:
    def __init__(self, chroma_path: Path):
        self.client = chromadb.PersistentClient(path=str(chroma_path))
        self._col = None

    @property
    def col(self):
        if self._col is None:
            self._col = self.client.get_or_create_collection(
                name="conversations",
                metadata={"hnsw:space": "cosine"},
            )
        return self._col

    def add_turn(self, role: str, content: str, session_id: str) -> None:
        if not content.strip():
            return
        self.col.add(
            documents=[content],
            metadatas=[{
                "role": role,
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
            }],
            ids=[str(uuid.uuid4())],
        )

    def search(self, query: str, n_results: int = 5) -> list[dict]:
        total = self.col.count()
        if total == 0:
            return []

        results = self.col.query(
            query_texts=[query],
            n_results=min(n_results, total),
            include=["documents", "metadatas", "distances"],
        )

        items = []
        for i, doc in enumerate(results["documents"][0]):
            meta = results["metadatas"][0][i]
            dist = results["distances"][0][i]
            items.append({
                "content": doc,
                "role": meta.get("role", "?"),
                "timestamp": meta.get("timestamp", ""),
                "session_id": meta.get("session_id", ""),
                "score": round(1 - dist, 3),
            })
        return items

    def count(self) -> int:
        return self.col.count()

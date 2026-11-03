from app.core.vectors import search_chunks
from app.models.user import User


def library_excerpts(q: str, user: User) -> str:
    return "\n\n".join(hit.text for hit in search_chunks(q, user.id))

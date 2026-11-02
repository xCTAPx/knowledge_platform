from app.core.vectors import search_chunks
from app.models.user import User


def library_excerpts(q: str, user: User) -> str:
    return "\n\n".join(search_chunks(q, user.id))

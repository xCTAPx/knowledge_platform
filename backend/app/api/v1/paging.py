from typing import Generic, TypeVar

from fastapi import Query
from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    has_more: bool


def page_limit(limit: int = Query(20, ge=1, le=100)) -> int:
    return limit


def sliced(rows: list[T], limit: int) -> tuple[list[T], bool]:
    return rows[:limit], len(rows) > limit

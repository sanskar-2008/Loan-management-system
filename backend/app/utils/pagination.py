from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Page(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


def paginate(query_items: list, total: int, page: int, page_size: int) -> dict:
    return {
        "items": query_items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }

from __future__ import annotations

from litestar import get

from ..dtos import CategoryDTO, CategoryGroupDTO
from ..services import store


@get("/categories")
async def list_categories() -> list[CategoryDTO]:
    return store.list_categories()


@get("/category-groups")
async def list_category_groups() -> list[CategoryGroupDTO]:
    return store.list_category_groups()


category_handlers = [list_categories, list_category_groups]

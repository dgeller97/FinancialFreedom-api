from __future__ import annotations

from litestar import get
from supabase import AsyncClient

from .. import services
from ..dtos import CategoryDTO, CategoryGroupDTO


@get("/categories")
async def list_categories(client: AsyncClient) -> list[CategoryDTO]:
    return await services.list_categories(client)


@get("/category-groups")
async def list_category_groups(client: AsyncClient) -> list[CategoryGroupDTO]:
    return await services.list_category_groups(client)


category_handlers = [list_categories, list_category_groups]

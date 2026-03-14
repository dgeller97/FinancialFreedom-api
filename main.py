from litestar import Litestar, get
from lib.supabase_client import supabase

@get("/")
async def index() -> dict[str, str]:
    return {"message": "Financial Freedom API!"}

@get("/transactions")
async def get_transactions() -> list[dict]:
    # Simple query to test supabase connection
    return await supabase.query("transactions", {"limit": 10})

app = Litestar(route_handlers=[index, get_transactions])
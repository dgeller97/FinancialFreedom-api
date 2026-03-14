import os
import httpx
from dotenv import load_dotenv

load_dotenv()

class SupabaseClient:
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        if not self.url or not self.key:
            print("Warning: SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY not set in environment.")
        
        self.headers = {
            "apikey": self.key,
            "Authorization": f"Bearer {self.key}",
            "Content-Type": "application/json",
            "Accept-Profile": "app",
            "Content-Profile": "app",
            "Prefer": "return=representation"
        }

    async def query(self, table: str, params: dict = None):
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.url}/rest/v1/{table}",
                headers=self.headers,
                params=params
            )
            response.raise_for_status()
            return response.json()

    async def insert(self, table: str, data: dict | list):
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.url}/rest/v1/{table}",
                headers=self.headers,
                json=data
            )
            response.raise_for_status()
            return response.json()

    # Generic request for more complex operations (RPC, etc.)
    async def request(self, method: str, path: str, **kwargs):
        async with httpx.AsyncClient() as client:
            url = f"{self.url}/rest/v1/{path.lstrip('/')}"
            response = await client.request(
                method,
                url,
                headers=self.headers,
                **kwargs
            )
            response.raise_for_status()
            return response.json()

supabase = SupabaseClient()

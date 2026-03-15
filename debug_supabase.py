import asyncio
import os
from supabase import create_async_client, ClientOptions
from dotenv import load_dotenv

load_dotenv()

async def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    print(f"Connecting to {url}")
    
    try:
        supabase = await create_async_client(
            url, 
            key,
            options=ClientOptions(schema="app")
        )
        
        # Test a simple query on the app schema
        res = await supabase.table("accounts").select("*").limit(1).execute()
        print("Success!")
        print(res.data)
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())

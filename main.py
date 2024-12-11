from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
from dotenv import load_dotenv
import aiomysql
import asyncio
import os
import logging

# Load environment variables from .env file
load_dotenv()

app = FastAPI()

# Database configuration
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = int(os.getenv("DB_PORT"))

# Database connection pool
pool = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/api/homepage")
async def get_homepage():
    """
    Retrieves user data from a JSON file.

    Attempts to read and parse user data from 'demo_data/users.json'.
    Returns the data as a JSON response. Handles potential errors like
    file not found, JSON decoding errors, and other unexpected exceptions.
    """
    try:
        # Construct the file path
        file_path = os.path.join("demo_data", "homepage.json")
        print(f"Trying to open file: {file_path}")  # Debugging statement

        # Read and parse the JSON file
        with open(file_path, 'r') as f:
            users = json.load(f)

        # Return the user data
        return JSONResponse(content=users)

    except FileNotFoundError as e:
        print(f"FileNotFoundError: {e}")  # Debugging output
        return JSONResponse(
            content={"error": "File not found. Please ensure 'demo_data/users.json' exists."},
            status_code=404
        )
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")  # Debugging output
        return JSONResponse(
            content={"error": "Error decoding JSON. Ensure the file contains valid JSON data."},
            status_code=400
        )
    except Exception as e:
        print(f"Unexpected error: {e}")  # Debugging output
        return JSONResponse(
            content={"error": f"An unexpected error occurred: {str(e)}"},
            status_code=500
        )

#
# @app.on_event("startup")
# async def startup():
#     global pool
#     logger.info("Creating database connection pool.")
#     pool = await aiomysql.create_pool(
#         host=DB_HOST,
#         port=DB_PORT,
#         user=DB_USER,
#         password=DB_PASSWORD,
#         db=DB_NAME,
#         autocommit=True,
#         loop=asyncio.get_event_loop(),
#     )
#     logger.info("Database connection pool created.")
#
# @app.on_event("shutdown")
# async def shutdown():
#     global pool
#     logger.info("Closing database connection pool.")
#     pool.close()
#     await pool.wait_closed()
#     logger.info("Database connection pool closed.")
#
# class ItemCreate(BaseModel):
#     name: str
#     description: str
#
# class Item(ItemCreate):
#     id: int
#
# @app.get("/")
# async def read_root():
#     return {"message": "Hello, World"}
#
# @app.get("/items/{item_id}", response_model=Item)
# async def read_item(item_id: int):
#     try:
#         async with pool.acquire() as conn:
#             async with conn.cursor() as cur:
#                 await cur.execute("SELECT id, name, description FROM items WHERE id = %s", (item_id,))
#                 result = await cur.fetchone()
#                 if result:
#                     return Item(id=result[0], name=result[1], description=result[2])
#                 else:
#                     raise HTTPException(status_code=404, detail="Item not found")
#     except Exception as e:
#         logger.error(f"Error reading item with id {item_id}: {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")
#
# @app.post("/items", response_model=Item)
# async def create_item(item: ItemCreate):
#     try:
#         async with pool.acquire() as conn:
#             async with conn.cursor() as cur:
#                 await cur.execute("INSERT INTO items (name, description) VALUES (%s, %s)", (item.name, item.description))
#                 item_id = cur.lastrowid
#                 return Item(id=item_id, name=item.name, description=item.description)
#     except Exception as e:
#         logger.error(f"Error creating item: {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")
#
# @app.put("/items/{item_id}", response_model=Item)
# async def update_item(item_id: int, item: ItemCreate):
#     try:
#         async with pool.acquire() as conn:
#             async with conn.cursor() as cur:
#                 await cur.execute("UPDATE items SET name = %s, description = %s WHERE id = %s", (item.name, item.description, item_id))
#                 return Item(id=item_id, name=item.name, description=item.description)
#     except Exception as e:
#         logger.error(f"Error updating item with id {item_id}: {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")
#
# @app.delete("/items/{item_id}")
# async def delete_item(item_id: int):
#     try:
#         async with pool.acquire() as conn:
#             async with conn.cursor() as cur:
#                 await cur.execute("DELETE FROM items WHERE id = %s", (item_id,))
#                 if cur.rowcount == 0:
#                     raise HTTPException(status_code=404, detail="Item not found")
#                 return {"message": "Item deleted"}
#     except Exception as e:
#         logger.error(f"Error deleting item with id {item_id}: {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")
#
#
# @app.get("/items", response_model=list[Item])
# async def read_items(limit: int = Query(10), offset: int = Query(0)):
#     try:
#         async with pool.acquire() as conn:
#             async with conn.cursor() as cur:
#                 await cur.execute("SELECT id, name, description FROM items LIMIT %s OFFSET %s", (limit, offset))
#                 results = await cur.fetchall()
#                 return [Item(id=row[0], name=row[1], description=row[2]) for row in results]
#     except Exception as e:
#         logger.error(f"Error fetching items: {e}")
#         raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

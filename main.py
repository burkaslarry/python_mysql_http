from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import aiomysql
import asyncio
import json
import os
import logging
from contextlib import asynccontextmanager

# Import new modules
from app.routes import crud, csv_routes

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_PORT = os.getenv("DB_PORT")

# Database connection pool
pool = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global pool
    logger.info("Creating database connection pool.")
    try:
        # Only attempt connection if config is present
        if DB_HOST and DB_USER and DB_PASSWORD and DB_NAME:
            pool = await aiomysql.create_pool(
                host=DB_HOST,
                port=int(DB_PORT) if DB_PORT else 3306,
                user=DB_USER,
                password=DB_PASSWORD,
                db=DB_NAME,
                autocommit=True,
            )
            logger.info("Database connection pool created.")
        else:
            logger.warning("Database configuration missing. Database features will not work.")
    except Exception as e:
        logger.error(f"Failed to create database connection pool: {e}")

    yield

    if pool:
        logger.info("Closing database connection pool.")
        pool.close()
        await pool.wait_closed()
        logger.info("Database connection pool closed.")

app = FastAPI(lifespan=lifespan)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include new route modules
app.include_router(crud.router)
app.include_router(csv_routes.router)

@app.get("/api/homepage")
async def get_homepage():
    """
    Retrieves user data from a JSON file.

    Attempts to read and parse user data from 'demo_data/homepage.json'.
    Returns the data as a JSON response. Handles potential errors like
    file not found, JSON decoding errors, and other unexpected exceptions.
    """
    try:
        # Construct the file path
        file_path = os.path.join("demo_data", "homepage.json")
        logger.debug(f"Trying to open file: {file_path}")

        # Read and parse the JSON file
        with open(file_path, 'r') as f:
            users = json.load(f)

        # Return the user data
        return JSONResponse(content=users)

    except FileNotFoundError as e:
        logger.error(f"FileNotFoundError: {e}")
        return JSONResponse(
            content={"error": "File not found. Please ensure 'demo_data/homepage.json' exists."},
            status_code=404
        )
    except json.JSONDecodeError as e:
        logger.error(f"JSONDecodeError: {e}")
        return JSONResponse(
            content={"error": "Error decoding JSON. Ensure the file contains valid JSON data."},
            status_code=400
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JSONResponse(
            content={"error": f"An unexpected error occurred: {str(e)}"},
            status_code=500
        )

class ItemCreate(BaseModel):
    name: str
    description: str

class Item(ItemCreate):
    id: int

@app.get("/")
async def read_root():
    return {"message": "Hello, World"}

@app.get("/items/{item_id}", response_model=Item)
async def read_item(item_id: int):
    if not pool:
        raise HTTPException(status_code=503, detail="Database not configured")
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT id, name, description FROM items WHERE id = %s", (item_id,))
                result = await cur.fetchone()
                if result:
                    return Item(id=result[0], name=result[1], description=result[2])
                else:
                    raise HTTPException(status_code=404, detail="Item not found")
    except Exception as e:
        logger.error(f"Error reading item with id {item_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.post("/items", response_model=Item)
async def create_item(item: ItemCreate):
    if not pool:
        raise HTTPException(status_code=503, detail="Database not configured")
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("INSERT INTO items (name, description) VALUES (%s, %s)", (item.name, item.description))
                item_id = cur.lastrowid
                return Item(id=item_id, name=item.name, description=item.description)
    except Exception as e:
        logger.error(f"Error creating item: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: ItemCreate):
    if not pool:
        raise HTTPException(status_code=503, detail="Database not configured")
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("UPDATE items SET name = %s, description = %s WHERE id = %s", (item.name, item.description, item_id))
                return Item(id=item_id, name=item.name, description=item.description)
    except Exception as e:
        logger.error(f"Error updating item with id {item_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    if not pool:
        raise HTTPException(status_code=503, detail="Database not configured")
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM items WHERE id = %s", (item_id,))
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Item not found")
                return {"message": "Item deleted"}
    except Exception as e:
        logger.error(f"Error deleting item with id {item_id}: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")


@app.get("/items", response_model=list[Item])
async def read_items(limit: int = Query(10), offset: int = Query(0)):
    if not pool:
        raise HTTPException(status_code=503, detail="Database not configured")
    try:
        async with pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT id, name, description FROM items LIMIT %s OFFSET %s", (limit, offset))
                results = await cur.fetchall()
                return [Item(id=row[0], name=row[1], description=row[2]) for row in results]
    except Exception as e:
        logger.error(f"Error fetching items: {e}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    import uvicorn
    # Use environment variable for port, default to 8000
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

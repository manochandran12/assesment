from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import uuid
from datetime import datetime
import string
import random
import re

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class URLShortenRequest(BaseModel):
    url: str
    custom_code: Optional[str] = None
    
    @validator('url')
    def validate_url(cls, v):
        # Add protocol if missing
        if not v.startswith(('http://', 'https://')):
            v = 'https://' + v
        
        # Basic URL validation
        url_pattern = re.compile(
            r'^https?://'  # http:// or https://
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
        
        if not url_pattern.match(v):
            raise ValueError('Invalid URL format')
        return v
    
    @validator('custom_code')
    def validate_custom_code(cls, v):
        if v is not None:
            if len(v) < 3 or len(v) > 20:
                raise ValueError('Custom code must be between 3 and 20 characters')
            if not re.match(r'^[a-zA-Z0-9_-]+$', v):
                raise ValueError('Custom code can only contain letters, numbers, hyphens, and underscores')
        return v

class BulkURLShortenRequest(BaseModel):
    urls: List[str]
    
    @validator('urls')
    def validate_urls(cls, v):
        if len(v) > 50:  # Limit bulk operations
            raise ValueError('Maximum 50 URLs allowed per bulk request')
        if len(v) == 0:
            raise ValueError('At least one URL is required')
        return v

class URLShortenResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_url: str
    short_code: str
    short_url: str
    custom: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    click_count: int = 0

class BulkURLShortenResponse(BaseModel):
    results: List[URLShortenResponse]
    total_processed: int
    errors: List[str] = []

def generate_short_code(length: int = 8) -> str:
    """Generate a random short code of specified length"""
    characters = string.ascii_letters + string.digits
    return ''.join(random.choice(characters) for _ in range(length))

async def check_code_exists(code: str) -> bool:
    """Check if a short code already exists in the database"""
    existing = await db.url_mappings.find_one({"short_code": code})
    return existing is not None

async def create_unique_short_code(length: int = 8, max_attempts: int = 10) -> str:
    """Create a unique short code, trying up to max_attempts times"""
    for _ in range(max_attempts):
        code = generate_short_code(length)
        if not await check_code_exists(code):
            return code
    
    # If we can't generate a unique code, use UUID-based approach
    return str(uuid.uuid4())[:length]

# API Routes
@api_router.post("/shorten", response_model=URLShortenResponse)
async def shorten_url(request: URLShortenRequest):
    """Shorten a single URL with optional custom code"""
    try:
        # Check if custom code is provided and available
        if request.custom_code:
            if await check_code_exists(request.custom_code):
                raise HTTPException(status_code=400, detail=f"Custom code '{request.custom_code}' is already taken")
            short_code = request.custom_code
            is_custom = True
        else:
            short_code = await create_unique_short_code()
            is_custom = False
        
        # Create the URL mapping
        url_mapping = URLShortenResponse(
            original_url=request.url,
            short_code=short_code,
            short_url=f"{os.environ.get('BACKEND_URL', 'http://localhost:8001')}/api/r/{short_code}",
            custom=is_custom
        )
        
        # Save to database
        await db.url_mappings.insert_one(url_mapping.dict())
        
        return url_mapping
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logging.error(f"Error shortening URL: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.post("/shorten-bulk", response_model=BulkURLShortenResponse)
async def shorten_urls_bulk(request: BulkURLShortenRequest):
    """Shorten multiple URLs at once"""
    results = []
    errors = []
    
    for idx, url in enumerate(request.urls):
        try:
            # Validate URL
            url_request = URLShortenRequest(url=url.strip())
            
            # Generate unique short code
            short_code = await create_unique_short_code()
            
            # Create the URL mapping
            url_mapping = URLShortenResponse(
                original_url=url_request.url,
                short_code=short_code,
                short_url=f"{os.environ.get('BACKEND_URL', 'http://localhost:8001')}/api/r/{short_code}",
                custom=False
            )
            
            # Save to database
            await db.url_mappings.insert_one(url_mapping.dict())
            results.append(url_mapping)
            
        except Exception as e:
            errors.append(f"URL {idx + 1} ({url}): {str(e)}")
    
    return BulkURLShortenResponse(
        results=results,
        total_processed=len(results),
        errors=errors
    )

@api_router.get("/urls", response_model=List[URLShortenResponse])
async def get_urls(limit: int = 50):
    """Get list of shortened URLs"""
    try:
        url_mappings = await db.url_mappings.find().sort("created_at", -1).limit(limit).to_list(limit)
        return [URLShortenResponse(**mapping) for mapping in url_mappings]
    except Exception as e:
        logging.error(f"Error fetching URLs: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Redirect route under /api prefix to work with Kubernetes ingress
@api_router.get("/r/{short_code}")
async def redirect_to_url(short_code: str):
    """Redirect short code to original URL"""
    try:
        # Find the URL mapping
        url_mapping = await db.url_mappings.find_one({"short_code": short_code})
        
        if not url_mapping:
            raise HTTPException(status_code=404, detail="Short URL not found")
        
        # Increment click count
        await db.url_mappings.update_one(
            {"short_code": short_code},
            {"$inc": {"click_count": 1}}
        )
        
        # Redirect to original URL
        return RedirectResponse(url=url_mapping["original_url"], status_code=302)
        
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error redirecting URL: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Health check
@api_router.get("/health")
async def health_check():
    return {"status": "healthy", "service": "URL Shortener"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
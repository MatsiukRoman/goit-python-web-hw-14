"""
Main entry point for the FastAPI application.

This module sets up the FastAPI app instance, configures middleware such as CORS and rate limiting,
registers API routers, and defines global exception handlers and utility endpoints.
"""

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from jose import jwt
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from src.services.auth import auth_service
from src.database.db import get_db
from src.routes import users, contacts, auth
from src.services.rate_limit import limiter

app = FastAPI(
    title="REST API",
    version="0.0.1",
    description="REST API for user, contact, and authentication management"
)

# Register routers
app.include_router(users.router)
app.include_router(contacts.router)
app.include_router(auth.router)

# Configure CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
    "https://frontend-domain.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate Limiting
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def add_user_email_to_request(request: Request, call_next):
    """
    Middleware to extract user email from JWT token if present.

    Adds `user_email` to `request.state` based on the decoded JWT token subject (sub claim).
    Falls back to client IP address if no valid token is found.
    """
    request.state.user_email = get_remote_address(request)
    try:
        token = await auth_service.oauth2_scheme(request)
        payload = jwt.decode(
            token,
            auth_service.SECRET_KEY,
            algorithms=[auth_service.ALGORITHM]
        )
        request.state.user_email = payload.get("sub")
    except:
        pass  # Unauthenticated or invalid token

    response = await call_next(request)
    return response


@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """
    Exception handler for rate limiting errors.

    Returns a 429 Too Many Requests response when the user exceeds the rate limit.
    """
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": "Too many requests. Please slow down."}
    )


@app.get("/api/healthchecker")
def healthchecker(db: Session = Depends(get_db)):
    """
    Health check endpoint.

    Returns a welcome message if the database connection is successful.
    Raises 500 if database is not responding or misconfigured.
    """
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        if result is None:
            raise HTTPException(
                status_code=500, detail="Database is not configured correctly"
            )
        return {"message": "Welcome to FastAPI!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")


@app.get("/")
def main_root():
    """
    Root endpoint.

    Returns a simple welcome message indicating application version.
    """
    return {"message": "Application Ver 0.0.1"}

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routers import requests, resources, allocations, rules, options
from logging_config import api_logger

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Turkcell Business Logic Service",
    description="Requests, Resources, Allocations, and Rules Management",
    version="2.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(requests.router)
app.include_router(resources.router)
app.include_router(allocations.router)
app.include_router(rules.router)
app.include_router(options.router)


@app.get("/")
def read_root():
    return {
        "service": "Business Logic Service",
        "version": "2.0.0",
        "endpoints": ["/requests", "/resources", "/allocations", "/rules"],
    }


@app.on_event("startup")
async def startup_event():
    api_logger.info("🚀 Business Logic Service starting...")
    api_logger.info(f"✅ Service ready on port 8001")

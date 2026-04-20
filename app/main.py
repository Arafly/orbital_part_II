from __future__ import annotations

from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, HTTPException, Depends

from app.clients import OrbitalClient, UpsteamServerError
from app.schemas import UsageResponse
from app.service import UsageService

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with httpx.AsyncClient(timeout=10.0) as http_client:
        app.state.http_client = http_client
        yield

app = FastAPI(title="Orbital Usage API", lifespan=lifespan)

def get_http_client() -> httpx.AsyncClient:
    return app.state.http_client

def get_service(http_client: httpx.AsyncClient = Depends(get_http_client)) -> UsageService:
    client = OrbitalClient(http_client)
    return UsageService(client)

@app.get("/health")
async def health() -> dict:
    return {"status": "ok"}

@app.get("/usage", response_model=UsageResponse, response_model_exclude_none=True)
async def usage(service: UsageService = Depends(get_service)) -> UsageResponse:
    try:
        return await service.build_usage()
    except UpsteamServerError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

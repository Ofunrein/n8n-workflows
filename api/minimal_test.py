#!/usr/bin/env python3
"""
Minimal test to debug Vercel Python runtime.
"""

from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/test")
async def test():
    return {"message": "Test endpoint working"}

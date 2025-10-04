from fastapi import FastAPI

app = FastAPI(title="WhatTo")

@app.get("/")
def root():
    return {"ok": True, "service": "WhatTo-backend"}
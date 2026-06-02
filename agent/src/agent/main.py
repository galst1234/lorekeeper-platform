from fastapi import FastAPI

app = FastAPI(title="Lorekeeper Agent (stub)")


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}

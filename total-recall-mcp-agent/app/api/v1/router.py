from fastapi import FastAPI

from app.mcp_server import mcp

app = FastAPI()

app.mount("/mcp", mcp.streamable_http_app())


@app.get("/health")
async def health():
    return {"status": "ok"}

"""PyScopeLive web and API server.

Start: python -m pyscopelive.server
Then open http://127.0.0.1:8000 in a browser and start the desktop client.
"""
from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, WebSocket
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field, ConfigDict
import uvicorn

from .service import ScopeService


class Controls(BaseModel):
    model_config = ConfigDict(extra="forbid")
    waveform: str | None = None
    frequency_hz: float | None = Field(default=None, ge=0.5, le=100.0, allow_inf_nan=False)
    amplitude_v: float | None = Field(default=None, ge=0.1, le=10.0, allow_inf_nan=False)
    paused: bool | None = None


def create_app(service: ScopeService | None = None) -> FastAPI:
    scope = service or ScopeService()

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        async def sampling_loop():
            while True:
                scope.tick()
                await asyncio.sleep(0.02)
        task = asyncio.create_task(sampling_loop())
        try:
            yield
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

    app = FastAPI(title="PyScopeLive", lifespan=lifespan)

    @app.get("/", response_class=HTMLResponse)
    async def home():
        html_path = Path(__file__).parent / "web" / "index.html"
        return html_path.read_text(encoding="utf-8")

    @app.get("/api/state")
    async def get_state():
        return scope.state()

    @app.get("/api/snapshot")
    async def snapshot(window_s: float = 0.4, max_points: int = 1200):
        try:
            return scope.snapshot(window_s=window_s, max_points=max_points)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.post("/api/control")
    async def configure(body: Controls):
        try:
            return scope.configure(**body.model_dump(exclude_none=True))
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

    @app.websocket("/ws")
    async def ws_stream(ws: WebSocket, window_s: float = 0.4):
        await ws.accept()
        if not 0.05 <= window_s <= 2.0:
            await ws.close(code=1008)
            return
        try:
            while True:
                await ws.send_json(scope.snapshot(window_s=window_s, max_points=1200))
                await asyncio.sleep(0.1)
        except Exception as exc:
            # Browser disconnects are expected; don't terminate acquisition.
            from starlette.websockets import WebSocketDisconnect
            if isinstance(exc, WebSocketDisconnect):
                return
            if isinstance(exc, (ConnectionResetError, RuntimeError)):
                return
            raise

    return app


app = create_app()


def main():
    # One process / one event loop / one acquisition stream.
    uvicorn.run(app, host="127.0.0.1", port=8000, workers=1)


if __name__ == "__main__":
    main()

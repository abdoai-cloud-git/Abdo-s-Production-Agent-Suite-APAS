"""FastAPI application entry point."""

from __future__ import annotations

from fastapi import FastAPI

from .api import router


def create_app() -> FastAPI:
    app = FastAPI(
        title="Abdo's Production Agent Suite API",
        version="0.1.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )
    app.include_router(router)
    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("server.main:app", host="0.0.0.0", port=8000, reload=False)

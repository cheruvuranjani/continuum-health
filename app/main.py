from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from app.routers import search, route, pharmacy, metrics
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title="Continuum",
    version ="1.0",
    description="Agentic patient access routing — MTTR as the north star metric.",
    docs_url="/docs",           # keeps Swagger at /docs
    redoc_url= None      # adds ReDoc at /redoc
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["Content-Type"]
)

app.include_router(search.router, prefix="/api/v1")
app.include_router(route.router, prefix="/api/v1")
app.include_router(pharmacy.router, prefix="/api/v1")
app.include_router(metrics.router, prefix="/api/v1")


@app.get("/health", tags=["health"])
def health() -> dict:
    """Service health check — confirms API is live."""
    return {
        "status": "ok",
        "service": "continuum",
        "environment": settings.environment
    }

@app.get("/redoc", include_in_schema=False)
def redoc() -> HTMLResponse:
    return HTMLResponse("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Continuum</title>
            <meta charset="utf-8"/>
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <link href="https://fonts.googleapis.com/css?family=Montserrat:300,400,700|Roboto:300,400,700" rel="stylesheet">
            <style>
                body { margin: 0; padding: 0; }
                .api-info-header h1 span { display: none; }
            </style>
        </head>
        <body>
            <redoc spec-url='/openapi.json'></redoc>
            <script src="https://cdn.jsdelivr.net/npm/redoc/bundles/redoc.standalone.js"></script>
        </body>
        </html>
    """)
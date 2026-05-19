from fastapi import APIRouter
from app.services.metrics_service import metrics_service

router = APIRouter(tags=["metrics"])

@router.get("/metrics")
def get_metrics() -> dict:
    """
    MTTR dashboard endpoint — north star metrics from the article.
    MTTR, leakage rate, agentic deflection rate, pharmacy coverage.
    """
    return metrics_service.summary()


@router.get("/metrics/recent")
def get_recent(limit: int = 10) -> list:
    """Returns most recent routing records."""
    return metrics_service.recent(limit)


@router.delete("/metrics/reset")
def reset_metrics() -> dict:
    """Resets all metrics — useful for demo resets."""
    metrics_service.reset()
    return {"message": "Metrics reset successfully."}
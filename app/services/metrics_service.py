from datetime import datetime
from app.models.provider import RouteResponse


class MetricsService:
    """
    Tracks routing outcomes and MTTR in memory.
    Surfaces the north star metrics from the Continuum article:
    MTTR, leakage rate, agentic deflection rate.
    """

    def __init__(self):
        self._records: list[dict] = []

    def record(self, response: RouteResponse) -> None:
        """Public — records a routing outcome after each request."""
        self._records.append({
            "timestamp":      datetime.utcnow().isoformat(),
            "resolved":       response.resolved,
            "mttr_seconds":   response.mttr_seconds,
            "routed_to":      "primary" if response.primary_care else "urgent",
            "pharmacy_found": response.pharmacy is not None
        })

    def summary(self) -> dict:
        """Public — returns aggregated metrics or empty state."""
        if not self._records:
            return {
                "total_requests": 0,
                "message": "No routing requests recorded yet."
            }
        return self._calculate_summary()

    def _calculate_summary(self) -> dict:
        """
        Protected — calculates MTTR metrics from resolved records.
        """
        resolved   = [r for r in self._records if r["resolved"]]
        deflected  = [r for r in resolved if r["routed_to"] == "urgent"]
        mttr       = sorted(r["mttr_seconds"] for r in resolved)
        pharmacy   = sum(1 for r in resolved if r["pharmacy_found"])
        n          = len(self._records)
        n_resolved = len(resolved)

        avg_mttr    = round(sum(mttr) / len(mttr), 2)       if mttr     else 0
        p95_mttr    = round(mttr[int(len(mttr) * 0.95)], 2) if mttr     else 0
        deflect_rate = round(len(deflected) / n_resolved, 3) if resolved else 0
        pharma_rate  = round(pharmacy / n_resolved, 3)        if resolved else 0

        return {
            "total_requests":          n,
            "resolved_count":          n_resolved,
            "leakage_rate":            round(1 - n_resolved / n, 3),
            "avg_mttr_seconds":        avg_mttr,
            "p95_mttr_seconds":        p95_mttr,
            "agentic_deflection_rate": deflect_rate,
            "pharmacy_coverage_rate":  pharma_rate,
            "last_updated":            datetime.utcnow().isoformat()
        }

    def recent(self, limit: int = 10) -> list:
        """Public — returns most recent routing records."""
        return self._records[-limit:]

    def reset(self) -> None:
        """Public — clears all records."""
        self._records.clear()

# singleton instance — shared across all routers
metrics_service = MetricsService()
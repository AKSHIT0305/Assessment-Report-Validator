class ReportService:
    """Builds the API/dashboard-friendly validation result."""

    @staticmethod
    def summarize(results):
        total = len(results)
        correct = sum(r.get("status") == "PASS" for r in results)
        return {
            "total": total,
            "correct": correct,
            "incorrect": total - correct,
        }

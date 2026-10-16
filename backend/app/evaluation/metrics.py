from collections import Counter
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.settings import Settings
from app.database.models import Case, Evaluation, Feedback
from app.modules.registry import MODULES


def metric(key, label, value, unit, kind, description):
    return {"key": key, "label": label, "value": round(value, 2), "unit": unit, "kind": kind, "description": description}


def impact_report(db: Session, settings: Settings):
    cases = list(db.scalars(select(Case)))
    evaluations = list(db.scalars(select(Evaluation)))
    total = len(cases)
    resolved = sum(case.status == "resolved" for case in cases)
    review = sum(case.status == "in_review" for case in cases)
    escalated = sum(evaluation.escalated for evaluation in evaluations)
    with_sources = sum(evaluation.source_count > 0 for evaluation in evaluations)
    average_ms = sum(row.processing_ms for row in evaluations) / max(1, len(evaluations))
    ratings = list(db.scalars(select(Feedback.rating)))
    context = "Observed inside this prototype using fictional demo cases." if settings.demo_mode else "Observed inside this prototype; not a validated council outcome."
    metrics = [
        metric("enquiries_processed", "Enquiries processed", total, "cases", "observed", context),
        metric("resolved", "Reviewed resolutions", resolved, "cases", "observed", "Cases marked resolved with a human review note. " + context),
        metric("resolution_rate", "Reviewed resolution rate", 100 * resolved / max(1, total), "%", "observed", "Resolved cases divided by all recorded cases; this is not a service outcome study."),
        metric("escalation_rate", "Human escalation rate", 100 * escalated / max(1, len(evaluations)), "%", "observed", "Requests that triggered a configured or consequential human-review safeguard."),
        metric("source_coverage", "Source-backed discovery", 100 * with_sources / max(1, len(evaluations)), "%", "observed", "Requests with at least one retrieved source. This does not measure retrieval accuracy."),
        metric("processing_time", "Average processing time", average_ms, "ms", "observed", "Measured orchestration latency; excludes queue, network transport and human review."),
        metric("estimated_staff_time", "Illustrative staff time saved", with_sources * 4, "minutes", "estimated", "Assumes four minutes saved per source-backed request. This operational assumption is unvalidated and excludes human review effort."),
    ]
    for module in MODULES.values():
        metrics.extend(item.model_dump() for item in module.impact_metrics(cases, evaluations))
    if ratings:
        metrics.append(metric("satisfaction", "Recorded prototype ratings", sum(ratings) / len(ratings), "/ 5", "observed", f"Average of {len(ratings)} recorded ratings. Fictional seed ratings are included in demo mode; not a resident satisfaction study."))
    else:
        metrics.append(metric("feedback_count", "Feedback received", 0, "ratings", "observed", "No ratings recorded; no satisfaction result is claimed."))
    today = datetime.now(timezone.utc).date()
    trend = []
    for offset in range(6, -1, -1):
        date = today - timedelta(days=offset)
        on_day = [case for case in cases if case.created_at.date() == date]
        trend.append({"label": date.strftime("%a"), "enquiries": len(on_day), "resolved": sum(case.status == "resolved" for case in on_day)})
    providers = Counter(row.provider for row in evaluations)
    provider = providers.most_common(1)[0][0] if providers else ("deterministic-demo" if settings.demo_mode else "deterministic-grounded")
    return {"metrics": metrics, "trend": trend, "categories": [{"label": label, "count": count} for label, count in sorted(Counter(case.category for case in cases).items())],
            "total_cases": total, "review_count": review, "resolved_count": resolved, "provider": provider, "demo_mode": settings.demo_mode}


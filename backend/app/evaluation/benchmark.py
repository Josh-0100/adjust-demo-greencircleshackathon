"""Repeatable labelled synthetic fixtures, independent of claimed council outcomes.

Run: python -m app.evaluation.benchmark
The CLI uses an isolated temporary migrated database and writes its measured
fixture results to stdout. It never overwrites live demonstration cases.
"""
from dataclasses import dataclass
import json
from pathlib import Path
import tempfile

from app.ai.orchestrator import analyse
from app.core.settings import PROJECT_ROOT, Settings
from app.database.bootstrap import bootstrap
from app.database.session import session_factory
from app.modules.registry import get_module
from app.services.config import read_config


@dataclass(frozen=True)
class Fixture:
    module_id: str
    message: str
    category: str
    expected_title: str | None


FIXTURES = [
    Fixture("service-navigator", "My home is cold and has damp. Where can I find housing support?", "Housing and wellbeing", "Fictional housing support navigator"),
    Fixture("service-navigator", "My recycling bin collection was missed. How do I report waste?", "Waste and recycling", "Fictional waste enquiry guide"),
    Fixture("employment", "I have customer service and email experience and want office work using spreadsheets.", "Employment and skills", "Fictional office support trainee opportunity"),
    Fixture("employment", "I have practical skills and construction experience and want a green retrofit job.", "Employment and skills", "Fictional green construction pathway"),
    Fixture("community", "I enjoy gardening and would like to volunteer in a community garden.", "Volunteering", "Fictional community garden volunteering"),
    Fixture("community", "I need food support and a pantry referral.", "Community support", "Fictional community food support resource"),
    Fixture("triage", "A pothole on the road could injure cyclists. Please route the road report.", "Roads and public space", "Fictional highways triage checklist"),
    Fixture("triage", "My recycling bin collection was missed and I need to report rubbish.", "Waste and recycling", "Fictional neighbourhood service triage"),
    Fixture("learning", "I want to learn digital skills and spreadsheets for office work.", "Learning and retraining", "Fictional digital office skills course"),
    Fixture("learning", "I want green construction training in practical skills and health and safety.", "Learning and retraining", "Fictional green construction skills course"),
    Fixture("custom", "My flat has damp and is cold. I need a warm home plan with a human adviser.", "Warm homes assessment", "Fictional warm home advice plan"),
    Fixture("service-navigator", "I need instructions for quantum zeppelin navigation.", "General support", None),
]


def run_benchmark(db, settings):
    rows = []
    config = read_config(settings.challenge_config_path)
    for fixture in FIXTURES:
        analysis, classification, priority = analyse(fixture.message, config.challenge.borough, get_module(fixture.module_id), settings, config, db)
        sources = [source.title for source in analysis.sources]
        rows.append({"module_id": fixture.module_id, "category_correct": classification.category == fixture.category,
                     "expected_source_present": fixture.expected_title in sources if fixture.expected_title else not sources,
                     "recommendations_grounded": all(item.title in sources for item in analysis.recommendations),
                     "expected_title": fixture.expected_title, "actual_titles": sources})
    n = len(rows)
    return {"dataset": "12 labelled fictional prototype fixtures; not representative of live residents", "fixture_count": n,
            "category_accuracy": sum(row["category_correct"] for row in rows) / n,
            "expected_source_recall": sum(row["expected_source_present"] for row in rows) / n,
            "grounded_recommendation_rate": sum(row["recommendations_grounded"] for row in rows) / n,
            "results": rows}


def main():
    with tempfile.TemporaryDirectory(prefix="civicforge-evaluation-") as folder:
        settings = Settings(database_url=f"sqlite:///{folder}/evaluation.db", demo_mode=True, llm_provider="deterministic",
                            challenge_config_path=PROJECT_ROOT / "config" / "challenge_config.yaml")
        engine = bootstrap(settings)
        with session_factory(engine)() as db:
            report = run_benchmark(db, settings)
        engine.dispose()
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()

from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.settings import get_settings
from app.database.session import make_engine, session_factory

BACKEND_ROOT = Path(__file__).resolve().parents[2]


def migrate(engine):
    config = Config(str(BACKEND_ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND_ROOT / "alembic"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")


def bootstrap(settings=None):
    from app.services.seed import seed_demo
    settings = settings or get_settings()
    engine = make_engine(settings.database_url)
    migrate(engine)
    if settings.demo_mode:
        with session_factory(engine)() as db:
            seed_demo(db, settings)
    return engine


if __name__ == "__main__":
    engine = bootstrap()
    from sqlalchemy import func, select
    from app.database.models import Case, Resource
    with session_factory(engine)() as db:
        print(f"Migration complete. Resources: {db.scalar(select(func.count(Resource.id)))}; cases: {db.scalar(select(func.count(Case.id)))}.")
    engine.dispose()


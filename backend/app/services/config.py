from pathlib import Path
import os
import tempfile

import yaml
from fastapi import HTTPException
from pydantic import ValidationError

from app.schemas.api import ChallengeConfig


def read_config(path: Path) -> ChallengeConfig:
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        return ChallengeConfig.model_validate(raw)
    except (OSError, yaml.YAMLError, ValidationError, TypeError) as error:
        # Do not return filesystem paths or document contents to residents.
        raise HTTPException(status_code=503, detail="Challenge configuration is unavailable or invalid. An administrator should validate the YAML file.") from error


def write_config(path: Path, config: ChallengeConfig):
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".challenge-", suffix=".yaml", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            yaml.safe_dump(config.model_dump(mode="json"), stream, sort_keys=False, allow_unicode=True)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


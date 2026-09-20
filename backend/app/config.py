from pathlib import Path

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BACKEND_DIR.parent

# litellm reads provider keys (OPENROUTER_API_KEY, OPENAI_API_KEY, ...) from os.environ
load_dotenv(REPO_ROOT / ".env")

DEFAULT_MODEL = "openrouter/google/gemini-3.7-flash"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=REPO_ROOT / ".env", extra="ignore")

    db_path: Path = REPO_ROOT / "data" / "scify.db"
    analysis_model: str = DEFAULT_MODEL
    sidekick_model: str = DEFAULT_MODEL
    # Reasoning models spend most of a request thinking; a low effort answers sooner.
    # Leave empty for a model that does not accept the setting.
    sidekick_reasoning_effort: str = "low"


settings = Settings()

import os
from functools import lru_cache

from dotenv import load_dotenv
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict

env_path = os.getenv("ENV_PATH")
load_dotenv(dotenv_path=env_path)


class AgentModels(BaseModel):
    root: str = "gemini-2.0-flash-exp"


class Settings(BaseSettings):
    debug: bool = False
    app_name: str = "PersonalAgent"

    agent_models: AgentModels = AgentModels()

    model_config = SettingsConfigDict(
        case_sensitive=False, env_nested_delimiter="_", env_nested_max_split=1
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

__all__ = ["settings"]

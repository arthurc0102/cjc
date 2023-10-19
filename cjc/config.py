import functools

import pydantic_settings


class Settings(pydantic_settings.BaseSettings):
    BASE_URL: str = "https://www.codejudger.com"

    model_config = pydantic_settings.SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_prefix="CJC_",
    )


@functools.lru_cache
def get_settings():
    return Settings()

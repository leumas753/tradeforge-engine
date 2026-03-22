from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Default to empty string so the app starts cleanly even without env vars.
    # /health will always return 200. /run-bots will fail at the DB call if unset.
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    # Optional — if set, /run-bots requires Authorization: Bearer <secret>
    cron_secret: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()

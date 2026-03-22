from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_service_role_key: str
    # Optional — if set, /run-bots requires Authorization: Bearer <secret>
    cron_secret: str | None = None

    class Config:
        env_file = ".env"


settings = Settings()

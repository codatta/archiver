from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Shared Supabase (same instance as developer-portal)
    supabase_url: str = "https://uxafdddzhgdhsabkwmgw.supabase.co"
    supabase_publishable_key: str = ""
    supabase_secret_key: str = ""

    # Vision Engine (external GPU server, consumed via ML Backend adapter)
    vision_engine_url: str = "http://47.84.74.124:8001"

    # Storage
    storage_bucket: str = "contribution-uploads"

    # URLs
    webapp_url: str = "http://localhost:3000"

    # Feature flags
    campaign_source: str = "mock"  # mock | supabase
    attempt_index_backend: str = "postgres"  # postgres | elasticsearch
    lineage_backend: str = "staging"  # staging | onchain

    model_config = {"env_file": "../../.env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

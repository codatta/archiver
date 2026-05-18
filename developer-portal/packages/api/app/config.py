from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    supabase_url: str
    supabase_publishable_key: str = ""
    supabase_secret_key: str = ""

    stripe_secret_key: str = ""
    stripe_publishable_key: str = ""
    stripe_webhook_secret: str = ""

    resend_api_key: str = ""
    supabase_auth_hook_secret: str = ""

    # Supply-side data: Supabase Postgres direct connection (asyncpg)
    supabase_db_url: str = ""

    # Legacy AliCloud RDS MySQL (kept for migration ETL script only)
    mysql_host: str = ""
    mysql_port: int = 3306
    mysql_user: str = ""
    mysql_password: str = ""
    mysql_database: str = "cfp_metacore"

    webapp_url: str = "http://localhost:3000"

    # HuggingFace OAuth (custom OIDC provider)
    hf_client_id: str = ""
    hf_client_secret: str = ""
    hf_redirect_uri: str = ""
    hf_oauth_state_secret: str = ""

    @property
    def stripe_environment(self) -> str:
        """Derive billing environment from Stripe key prefix."""
        if self.stripe_secret_key.startswith("sk_live_"):
            return "live"
        return "test"

    model_config = {"env_file": "../../.env", "env_file_encoding": "utf-8", "extra": "ignore"}


settings = Settings()

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    log_level: str = "INFO"
    default_http_timeout: int = 15
    default_retry_count: int = 2
    cache_dir: str = ".cache"
    enable_mootdx: bool = False
    iwencai_api_key: str = ""
    iwencai_base_url: str = "https://openapi.iwencai.com"

    model_config = {"env_prefix": "", "case_sensitive": False}


settings = Settings()

import os
from typing import List, Optional, Any
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, PostgresDsn, field_validator, ValidationInfo
import yaml

class Settings(BaseSettings):
    PROJECT_NAME: str = "AIToday Backend"
    API_V1_STR: str = "/api/v1"
    
    # Database
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "password")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "aitoday")
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @field_validator("SQLALCHEMY_DATABASE_URI", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info: ValidationInfo) -> Any:
        if isinstance(v, str):
            return v
            
        # Try to load from sources.yaml first
        # Use os.getenv directly to avoid validation order issues
        config_path = os.getenv("SOURCES_CONFIG_PATH", "sources.yaml")
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f) or {}
                    db_config = config.get("database", {})
                    if db_config.get("host"):
                        print(f"Loading DB config from {config_path}: {db_config.get('host')}")
                        return PostgresDsn.build(
                            scheme="postgresql",
                            username=db_config.get("user", "postgres"),
                            password=db_config.get("password", ""),
                            host=db_config.get("host"),
                            port=db_config.get("port", 5432),
                            path=db_config.get('dbname', 'postgres')
                        )
            except Exception as e:
                print(f"Error loading DB config from yaml: {e}")
                pass

        print("Falling back to env vars for DB config")
        # Fallback to env vars
        db_name = os.getenv("POSTGRES_DB", "aitoday")
        return PostgresDsn.build(
            scheme="postgresql",
            username=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "password"),
            host=os.getenv("POSTGRES_SERVER", "localhost"),
            path=db_name,
        )

    # OpenAI
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
    
    # YouTube
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")

    # Twitter
    TWITTER_BEARER_TOKEN: str = os.getenv("TWITTER_BEARER_TOKEN", "")

    # Reddit
    REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT", "AIToday/0.1.0")

    # Sources Config Path
    SOURCES_CONFIG_PATH: str = os.getenv("SOURCES_CONFIG_PATH", "sources.yaml")

    class Config:
        case_sensitive = True

    @field_validator("OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL", "YOUTUBE_API_KEY", "TWITTER_BEARER_TOKEN", "REDDIT_CLIENT_ID", "REDDIT_CLIENT_SECRET", "REDDIT_USER_AGENT", mode="before")
    @classmethod
    def load_from_yaml(cls, v, info: ValidationInfo) -> Any:
        # Logic to load from yaml
        # Note: In Pydantic v2, info.data might not contain all fields if they haven't been validated yet.
        # However, SOURCES_CONFIG_PATH is defined at the end, so it might not be in info.data yet if we validate these fields first.
        # But SOURCES_CONFIG_PATH has a default value.
        # A safer way is to just check the default path if missing.
        
        config_path = "sources.yaml" # Default
        if info.data and "SOURCES_CONFIG_PATH" in info.data:
             config_path = info.data["SOURCES_CONFIG_PATH"]
        
        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f) or {}
                    api_keys = config.get("api_keys", {})
                    ai_config = config.get("ai", {})
                    
                    field_name = info.field_name
                    
                    if field_name == "OPENAI_API_KEY":
                        return ai_config.get("api_key") or api_keys.get("openai", "") or v
                    if field_name == "OPENAI_BASE_URL":
                        return ai_config.get("base_url") or v
                    if field_name == "OPENAI_MODEL":
                        return ai_config.get("model") or v
                        
                    if field_name == "YOUTUBE_API_KEY":
                        return api_keys.get("youtube", "") or v
                    if field_name == "TWITTER_BEARER_TOKEN":
                        return api_keys.get("twitter_bearer_token", "") or v
                    if field_name == "REDDIT_CLIENT_ID":
                        return api_keys.get("reddit_client_id", "") or v
                    if field_name == "REDDIT_CLIENT_SECRET":
                        return api_keys.get("reddit_client_secret", "") or v
                    if field_name == "REDDIT_USER_AGENT":
                        return api_keys.get("reddit_user_agent", "") or v
            except Exception:
                pass
        return v

    @field_validator("SOURCES_CONFIG_PATH", mode="after")
    @classmethod
    def apply_proxy(cls, v, info: ValidationInfo):
        # We use SOURCES_CONFIG_PATH as a trigger to load system config
        if os.path.exists(v):
            try:
                with open(v, "r") as f:
                    config = yaml.safe_load(f) or {}
                    system_config = config.get("system", {})
                    proxy = system_config.get("proxy")
                    if proxy:
                        os.environ["http_proxy"] = proxy
                        os.environ["https_proxy"] = proxy
                        os.environ["HTTP_PROXY"] = proxy
                        os.environ["HTTPS_PROXY"] = proxy
                        print(f"Applied proxy settings: {proxy}")
            except Exception:
                pass
        return v

settings = Settings()

def load_sources_config():
    if os.path.exists(settings.SOURCES_CONFIG_PATH):
        with open(settings.SOURCES_CONFIG_PATH, "r") as f:
            return yaml.safe_load(f)
    return {}

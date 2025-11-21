import os
from typing import List, Optional, Any
from pydantic_settings import BaseSettings
from pydantic import AnyHttpUrl, PostgresDsn, field_validator, ValidationInfo
import yaml

class Settings(BaseSettings):
    PROJECT_NAME: str = "AIToday Backend"
    API_V1_STR: str = "/api/v1"
    
    # CORS Configuration
    BACKEND_CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # 数据库配置
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
            
        # If running in Docker (POSTGRES_SERVER=postgres), prioritize env vars
        if os.getenv("POSTGRES_SERVER") == "postgres":
            print("Running in Docker, using env vars for DB config")
            config_path = "non_existent_file"
        else:
            # 首先尝试从 sources.yaml 加载
            # 直接使用 os.getenv 以避免验证顺序问题
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
        # 回退到环境变量进行数据库配置
        db_name = os.getenv("POSTGRES_DB", "aitoday")
        return PostgresDsn.build(
            scheme="postgresql",
            username=os.getenv("POSTGRES_USER", "postgres"),
            password=os.getenv("POSTGRES_PASSWORD", "password"),
            host=os.getenv("POSTGRES_SERVER", "localhost"),
            path=db_name,
        )

    # OpenAI 配置
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_BASE_URL: str = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")

    # Vector Model 配置
    VECTOR_API_KEY: str = os.getenv("VECTOR_API_KEY", "")
    VECTOR_BASE_URL: str = os.getenv("VECTOR_BASE_URL", "https://api.openai.com/v1")
    VECTOR_MODEL: str = os.getenv("VECTOR_MODEL", "text-embedding-3-small")
    
    # YouTube 配置
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")

    # Twitter 配置
    TWITTER_BEARER_TOKEN: str = os.getenv("TWITTER_BEARER_TOKEN", "")

    # Reddit 配置
    REDDIT_CLIENT_ID: str = os.getenv("REDDIT_CLIENT_ID", "")
    REDDIT_CLIENT_SECRET: str = os.getenv("REDDIT_CLIENT_SECRET", "")
    REDDIT_USER_AGENT: str = os.getenv("REDDIT_USER_AGENT", "AIToday/0.1.0")
    REDDIT_USERNAME: str = os.getenv("REDDIT_USERNAME", "")
    REDDIT_PASSWORD: str = os.getenv("REDDIT_PASSWORD", "")

    # 源配置文件路径
    SOURCES_CONFIG_PATH: str = os.getenv("SOURCES_CONFIG_PATH", "sources.yaml")

    # 新闻分类
    NEWS_CATEGORIES: List[str] = [
        "AI工具",
        "学术论文",
        "行业新闻",
        "教程指南",
        "其他"
    ]

    # 调度与时区
    TIMEZONE: str = os.getenv("TIMEZONE", "Asia/Shanghai")

    class Config:
        case_sensitive = True

    @field_validator(
        "OPENAI_API_KEY",
        "OPENAI_BASE_URL",
        "OPENAI_MODEL",
        "VECTOR_API_KEY",
        "VECTOR_BASE_URL",
        "VECTOR_MODEL",
        "YOUTUBE_API_KEY",
        "TWITTER_BEARER_TOKEN",
        "REDDIT_CLIENT_ID",
        "REDDIT_CLIENT_SECRET",
        "REDDIT_USER_AGENT",
        "REDDIT_USERNAME",
        "REDDIT_PASSWORD",
        mode="before",
    )
    @classmethod
    def load_from_yaml(cls, v, info: ValidationInfo) -> Any:
        # 从 yaml 加载的逻辑
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

                    if field_name == "VECTOR_API_KEY":
                        return ai_config.get("vector_api_key") or api_keys.get("vector", "") or v
                    if field_name == "VECTOR_BASE_URL":
                        return ai_config.get("vector_base_url") or v
                    if field_name == "VECTOR_MODEL":
                        return ai_config.get("vector_model") or v
                        
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
                    if field_name == "REDDIT_USERNAME":
                        return api_keys.get("reddit_username", "") or v
                    if field_name == "REDDIT_PASSWORD":
                        return api_keys.get("reddit_password", "") or v
            except Exception:
                pass
        return v

    @field_validator("TIMEZONE", mode="before")
    @classmethod
    def load_timezone(cls, v, info: ValidationInfo):
        config_path = "sources.yaml"
        if info.data:
            config_path = info.data.get("SOURCES_CONFIG_PATH", config_path)
        config_path = os.getenv("SOURCES_CONFIG_PATH", config_path)

        if os.path.exists(config_path):
            try:
                with open(config_path, "r") as f:
                    config = yaml.safe_load(f) or {}
                    timezone = config.get("system", {}).get("timezone")
                    if timezone:
                        return timezone
            except Exception:
                pass
        return v

    @field_validator("SOURCES_CONFIG_PATH", mode="after")
    @classmethod
    def apply_proxy(cls, v, info: ValidationInfo):
        # 我们使用 SOURCES_CONFIG_PATH 作为触发器来加载系统配置
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

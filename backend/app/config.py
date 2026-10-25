from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # --- LLM: "openai_compat" (Gemini free tier, Groq, OpenRouter, Ollama...) or "anthropic"
    llm_provider: str = "openai_compat"
    llm_api_key: str = ""
    llm_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    llm_model: str = "gemini-flash-latest"
    anthropic_api_key: str = ""  # only used when llm_provider=anthropic

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "nexusgraph"

    rss_feeds: str = "https://news.google.com/rss/search?q=semiconductor+supply+chain"
    min_confidence: float = 0.6
    max_chars: int = 6000

    @property
    def feeds(self) -> list[str]:
        return [f.strip() for f in self.rss_feeds.split(",") if f.strip()]


settings = Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    llm_provider: str = "openai_compat"
    llm_api_key: str = ""
    llm_base_url: str = "https://generativelanguage.googleapis.com/v1beta/openai/"
    llm_model: str = "gemini-flash-latest"
    llm_fallback_model: str = ""
    anthropic_api_key: str = "" 

    neo4j_uri: str = "bolt://localhost:7687"
    neo4j_user: str = "neo4j"
    neo4j_password: str = "nexusgraph"

    rss_feeds: str = (
        "https://feeds.bbci.co.uk/news/business/rss.xml,"
        "https://feeds.bbci.co.uk/news/technology/rss.xml"
    )
    keywords: str = "chip,semiconductor,supply chain,supplier,factory,shortage,export,tariff,sanction,port,strike,shipping,rare earth,foundry,neon,wafer,lithography"
    min_confidence: float = 0.6
    max_chars: int = 6000

    @property
    def feeds(self) -> list[str]:
        return [f.strip() for f in self.rss_feeds.split(",") if f.strip()]

    @property
    def keyword_list(self) -> list[str]:
        return [k.strip().lower() for k in self.keywords.split(",") if k.strip()]


settings = Settings()
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Anthropic
    anthropic_api_key: str = ""
    llm_provider: str = "anthropic"
    llm_model: str = "claude-sonnet-4-6"
    llm_max_tokens: int = 2048
    llm_temperature: float = 0.8

    # ElevenLabs
    elevenlabs_api_key: str = ""
    tts_provider: str = "elevenlabs"
    elevenlabs_tts_model: str = "eleven_v3"
    # Optional: set these to override auto-selected voices (get IDs from elevenlabs.io → Voices)
    elevenlabs_voice_id: str = ""
    elevenlabs_voice_id_male: str = ""

    # Audio
    audio_output_dir: str = "tmp/audio"
    ambience_volume_db: float = -18.0
    voice_volume_db: float = 0.0

    # Speech recognition
    whisper_model: str = "base"
    whisper_device: str = "cpu"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:3000"

    # Database
    database_url: str = "sqlite:///./voice_emotion.db"

    # Obsidian
    obsidian_vault_path: str = "/Users/samy/Library/Mobile Documents/iCloud~md~obsidian/EchoVault"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Early Disease Screening Research Prototype"
    database_url: str = "sqlite:///./screening.db"
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"
    max_upload_bytes: int = 12 * 1024 * 1024
    max_image_pixels: int = 20_000_000
    min_image_side: int = 128
    retain_images: bool = False
    tb_checkpoint: str = ""
    dr_checkpoint: str = ""
    model_device: str = "cpu"
    model_threshold: float = 0.5
    uncertainty_margin: float = 0.08
    auth_required: bool = False
    access_username: str = ""
    access_password: str = ""
    supabase_url: str = ""
    supabase_publishable_key: str = ""
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

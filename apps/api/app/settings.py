from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file="../../.env", extra="ignore")

    google_cloud_project: str = ""
    google_cloud_region: str = "asia-northeast1"
    vertex_location: str = "global"
    gemini_model_pro: str = "gemini-1.5-pro-002"
    gemini_model_flash: str = "gemini-1.5-flash-002"
    agent_runtime: str = "cloudrun"
    coding_engine: str = "adk_gemini"
    firestore_database: str = "(default)"
    gcs_upload_bucket: str = ""
    github_org: str = "poc-recycle"
    github_app_id: int = 0
    github_app_installation_id: int = 0
    github_app_private_key: str = ""
    charter_score_threshold: int = 80
    max_pr_diff_lines: int = 400
    preview_ttl_hours: int = 48
    preview_max_concurrent: int = 2

def get_settings() -> Settings:
    return Settings()

from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    app_name: str = "Heroic AI"
    environment: str = "development"
    version: str = "0.1.0"


settings = Settings()

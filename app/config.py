from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List
import os


class Settings(BaseSettings):

    # ── App ───────────────────────────────────────────────────
    APP_NAME: str = "ESG Sustainability Analytics Platform"
    APP_VERSION: str = "1.0.0"
    APP_DESCRIPTION: str = (
        "AI-powered ESG analytics platform for tracking, scoring, "
        "and reporting environmental, social, and governance performance."
    )
    DEBUG: bool = False

    # ── API ───────────────────────────────────────────────────
    API_V1_PREFIX: str = "/api/v1"

    # ── Database ──────────────────────────────────────────────
    DATABASE_URL: str = "postgresql://postgres:aabb@localhost:5432/esg_db"

    # ── CORS ──────────────────────────────────────────────────
    # Streamlit dashboard origin; extend in production
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ]

    # ── File uploads ──────────────────────────────────────────
    UPLOAD_DIR: str = "data/uploads"
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = [".csv", ".xlsx", ".xls"]

    # ── ESG scoring weights (must sum to exactly 1.0) ─────────
    ENVIRONMENTAL_WEIGHT: float = 0.40
    SOCIAL_WEIGHT: float = 0.30
    GOVERNANCE_WEIGHT: float = 0.30

    # ── ESG score rating thresholds (0–100 scale) ─────────────
    SCORE_EXCELLENT_THRESHOLD: float = 80.0   # A — leader
    SCORE_GOOD_THRESHOLD: float = 60.0        # B — above average
    SCORE_AVERAGE_THRESHOLD: float = 40.0     # C — average
    # below 40 → D — needs improvement

    # ── KPI limits ────────────────────────────────────────────
    # Environmental
    CO2_EMISSIONS_UNIT: str = "tCO2e"         # tonnes CO2 equivalent
    ENERGY_UNIT: str = "MWh"
    WATER_UNIT: str = "m³"

    # Social
    MIN_DIVERSITY_RATIO: float = 0.30          # 30 % minimum gender diversity target
    TARGET_RETENTION_RATE: float = 0.90        # 90 % employee retention target
    TARGET_ENGAGEMENT_SCORE: float = 70.0      # out of 100

    # Governance
    TARGET_COMPLIANCE_SCORE: float = 90.0      # out of 100
    MAX_RISK_INDEX: float = 30.0               # acceptable risk ceiling

    @field_validator("ENVIRONMENTAL_WEIGHT", "SOCIAL_WEIGHT", "GOVERNANCE_WEIGHT")
    @classmethod
    def weights_must_be_positive(cls, v: float) -> float:
        if not 0.0 < v < 1.0:
            raise ValueError("Each ESG weight must be between 0 and 1 (exclusive).")
        return v

    def esg_weights_sum_to_one(self) -> bool:
        total = round(
            self.ENVIRONMENTAL_WEIGHT + self.SOCIAL_WEIGHT + self.GOVERNANCE_WEIGHT, 10
        )
        return total == 1.0

    def get_score_label(self, score: float) -> str:
        """Return a human-readable rating label for any ESG score."""
        if score >= self.SCORE_EXCELLENT_THRESHOLD:
            return "A — Excellent"
        if score >= self.SCORE_GOOD_THRESHOLD:
            return "B — Good"
        if score >= self.SCORE_AVERAGE_THRESHOLD:
            return "C — Average"
        return "D — Needs improvement"

    def ensure_upload_dir(self) -> None:
        """Create the upload directory on startup if it does not exist."""
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
    }


# Single shared instance — import this everywhere
settings = Settings()
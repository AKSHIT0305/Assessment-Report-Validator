import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR.parent / "data"
INCOMING_DIR = DATA_DIR / "incoming"
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = DATA_DIR / "reports"
LOGS_DIR = DATA_DIR / "logs"

# ==================================================
# Laya AI Classification Configuration
# ==================================================

# Enable/disable Laya AI classification for REVIEW items
LAYA_ENABLED = os.getenv("LAYA_ENABLED", "false").lower() == "true"

# Model configuration
# Supports: claude-haiku-4-5, claude-3-5-haiku, gpt-4o-mini, gemini-1.5-flash, etc.
# Or local models via LiteLLM: ollama/model-name, openai/model-name (for LMStudio)
LAYA_MODEL = os.getenv("LAYA_MODEL", "claude-haiku-4-5")

# Optional: API key for cloud providers (Anthropic, OpenAI, Gemini)
# If not provided for local providers, LiteLLM will use a placeholder
LAYA_API_KEY = os.getenv("LAYA_API_KEY")

# Optional: Custom API base for local providers (e.g., LMStudio, Ollama)
# Example: http://localhost:1234/v1 for LMStudio
LAYA_API_BASE = os.getenv("LAYA_API_BASE")

# Timeout for LLM calls (seconds)
LAYA_TIMEOUT_SECONDS = int(os.getenv("LAYA_TIMEOUT_SECONDS", "30"))

# Maximum tokens for LLM response
LAYA_MAX_TOKENS = int(os.getenv("LAYA_MAX_TOKENS", "512"))

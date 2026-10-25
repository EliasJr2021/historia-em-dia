"""Configuração central. Valores vêm de variáveis de ambiente (Actions secrets/variables)."""
import os


def _get(name: str, default: str = "") -> str:
    v = os.getenv(name)
    return v if v not in (None, "") else default


REPO = _get("GITHUB_REPOSITORY", "EliasJr2021/historia-em-dia")
OWNER, REPO_NAME = REPO.split("/", 1)

SITE_BASE = _get("SITE_BASE", "https://historiaemdia.com.br").rstrip("/")
SITE_HOST = SITE_BASE.replace("https://", "").replace("http://", "")
IG_HANDLE = "@historia.em.diaa"

APPROVAL_MODE = _get("APPROVAL_MODE", "manual").lower()  # manual | auto
CLAUDE_MODEL = _get("CLAUDE_MODEL", "claude-sonnet-5-5")
MAX_SLIDES = max(4, min(10, int(_get("MAX_SLIDES", "10"))))
ORDER = _get("ORDER", "chronological")  # chronological | page
AI_IMAGE_NOTICE = _get("AI_IMAGE_NOTICE", "false").lower() == "true"

IG_API_VERSION = _get("IG_API_VERSION", "v24.0")
IG_USER_ID = _get("IG_USER_ID", "me")

# Onde os JPEGs ficam públicos para a Meta baixar (branch `media` + GitHub Pages).
# Alternativa sem Pages: https://raw.githubusercontent.com/<owner>/<repo>/media
MEDIA_BASE_URL = _get("MEDIA_BASE_URL", f"https://{OWNER.lower()}.github.io/{REPO_NAME}").rstrip("/")

GITHUB_TOKEN = _get("GITHUB_TOKEN")
USER_AGENT = "HistoriaEmDiaBot/1.0 (+https://historiaemdia.com.br)"
STATE_PATH = "state/state.json"

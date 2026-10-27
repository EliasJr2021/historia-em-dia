"""Legenda do Instagram (limite de 2.200 caracteres)."""
import re
from urllib.parse import urlencode, urlparse, urlunparse

from . import config
from .models import Carousel
from .plan import Plan

DEFAULT_TAGS = ["história", "históriadomundo", "curiosidadeshistóricas"]


def utm_link(link: str) -> str:
    p = urlparse(link)
    q = urlencode({"utm_source": "instagram", "utm_medium": "carrossel", "utm_campaign": "diario"})
    return urlunparse(p._replace(query=(p.query + "&" if p.query else "") + q))


def clean_tags(tags: list[str]) -> list[str]:
    out = []
    for t in tags + DEFAULT_TAGS:
        t = re.sub(r"[^\w]", "", t.lstrip("#").lower())
        if "hoje" in t:   # regra do perfil: nunca usar "hoje" (a data é sempre histórica)
            continue
        if t and t not in out:
            out.append(t)
    return ["#" + t for t in out[:8]]


def build_caption(c: Carousel, plan: Plan, link: str) -> str:
    lines = [f"📅 {c.date_label} na História", f"{c.hook.rstrip()} Deslize ➡️", ""]
    for e in plan.main:
        lines.append(f"{e.year} • {e.title}")
    hidden = len(plan.others) + plan.extra
    if hidden:
        lines.append(f"+ {hidden} fatos no carrossel e no site")
    lines += ["", "📖 Texto completo no site (link na bio):", utm_link(link), ""]
    if config.AI_IMAGE_NOTICE:
        lines += ["Imagem ilustrativa gerada por IA.", ""]
    lines.append("Conteúdo informativo, com finalidade histórica e educativa.")
    lines.append("")
    lines.append(" ".join(clean_tags(c.hashtags)))
    text = "\n".join(lines)
    return text[:2200]

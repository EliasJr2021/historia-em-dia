"""Descoberta e leitura das páginas do site (WordPress)."""
import html
import re
import unicodedata
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from . import config

MESES = "janeiro|fevereiro|marco|março|abril|maio|junho|julho|agosto|setembro|outubro|novembro|dezembro"
DATE_RE = re.compile(rf"(\d{{1,2}})\s*(?:º|°|o)?[\s-]+de[\s-]+({MESES})", re.I)


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": config.USER_AGENT, "Accept-Language": "pt-BR,pt;q=0.9"})
    return s


def _strip_accents(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


def is_date_page(title: str, slug: str) -> bool:
    text = _strip_accents(f"{title} {slug.replace('-', ' ')}").lower()
    return bool(DATE_RE.search(_strip_accents(text).replace(" de ", " de ")))


def list_posts_rest(s: requests.Session) -> list[dict]:
    posts, page = [], 1
    while True:
        r = s.get(
            f"{config.SITE_BASE}/wp-json/wp/v2/posts",
            params={"per_page": 100, "page": page, "orderby": "date", "order": "asc",
                    "_fields": "id,date_gmt,slug,link,title"},
            timeout=30,
        )
        if r.status_code == 400:  # página além do total
            break
        r.raise_for_status()
        for p in r.json():
            posts.append({
                "id": p["id"], "date": p["date_gmt"], "slug": p["slug"], "link": p["link"],
                "title": html.unescape(p["title"]["rendered"]),
            })
        total_pages = int(r.headers.get("X-WP-TotalPages", page))
        if page >= total_pages:
            break
        page += 1
    return posts


def list_posts_sitemap(s: requests.Session) -> list[dict]:
    """Reserva: wp-sitemap.xml (ordem por lastmod)."""
    idx = s.get(f"{config.SITE_BASE}/wp-sitemap.xml", timeout=30)
    idx.raise_for_status()
    ns = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    maps = [e.text for e in ET.fromstring(idx.content).findall(".//sm:loc", ns) if "posts-post" in (e.text or "")]
    posts = []
    for m in maps:
        r = s.get(m, timeout=30)
        r.raise_for_status()
        for u in ET.fromstring(r.content).findall("sm:url", ns):
            loc = u.findtext("sm:loc", namespaces=ns)
            last = u.findtext("sm:lastmod", namespaces=ns) or ""
            slug = urlparse(loc).path.strip("/").split("/")[-1]
            posts.append({"id": 0, "date": last, "slug": slug, "link": loc, "title": slug})
    posts.sort(key=lambda p: p["date"])
    return posts


def list_posts() -> list[dict]:
    s = _session()
    try:
        posts = list_posts_rest(s)
        if posts:
            return posts
    except Exception as e:  # noqa: BLE001
        print(f"[discover] API REST indisponível ({e}); tentando sitemap.")
    return list_posts_sitemap(s)


def next_post(done_slugs: set[str]) -> dict | None:
    for p in list_posts():
        if p["slug"] in done_slugs:
            continue
        if not is_date_page(p["title"], p["slug"]):
            continue
        return p
    return None


def _clean_text(soup: BeautifulSoup) -> str:
    root = (soup.select_one('[data-elementor-type="wp-post"]') or soup.select_one("article")
            or soup.select_one("main") or soup.body)
    for t in root.find_all(["script", "style", "nav", "header", "footer", "aside", "form", "noscript"]):
        t.decompose()
    lines, seen = [], set()
    for el in root.find_all(["h1", "h2", "h3", "h4", "p", "li", "tr"]):
        if el.name == "tr":
            txt = " | ".join(c.get_text(" ", strip=True) for c in el.find_all(["th", "td"]))
        else:
            txt = el.get_text(" ", strip=True)
        if not txt or txt in seen:
            continue
        seen.add(txt)
        if el.name in ("h1", "h2", "h3", "h4"):
            lines.append(f"\n## {txt}")
        elif el.name == "li":
            lines.append(f"- {txt}")
        else:
            lines.append(txt)
    return "\n".join(lines)[:40000]


def fetch_page(link: str) -> dict:
    s = _session()
    r = s.get(link, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    og = soup.find("meta", property="og:image")
    title = soup.find("meta", property="og:title")
    return {
        "link": link,
        "title": (title["content"] if title and title.get("content") else (soup.title.string if soup.title else "")),
        "cover_url": og["content"] if og and og.get("content") else None,
        "text": _clean_text(soup),
    }


def download_image(url: str) -> bytes | None:
    try:
        r = _session().get(url, timeout=45)
        r.raise_for_status()
        if "image" not in r.headers.get("Content-Type", ""):
            return None
        return r.content
    except Exception as e:  # noqa: BLE001
        print(f"[discover] não foi possível baixar a imagem de capa: {e}")
        return None

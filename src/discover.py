"""Descoberta e leitura das páginas do site (WordPress)."""
import html
import re
import unicodedata
import xml.etree.ElementTree as ET
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from . import config

MESES_NOMES = ["janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto",
               "setembro", "outubro", "novembro", "dezembro"]
MESES = "|".join(MESES_NOMES + ["março"])
DATE_RE = re.compile(rf"(?<!\d)(\d{{1,2}})\s*(?:º|°|o)?[\s-]+de[\s-]+({MESES})(?![a-z])", re.I)
NUM_RE = re.compile(r"(?<!\d)(\d{1,2})[-/_.](\d{1,2})(?!\d)")


def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": config.USER_AGENT, "Accept-Language": "pt-BR,pt;q=0.9"})
    return s


def _strip_accents(t: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", t) if unicodedata.category(c) != "Mn")


def parse_date(title: str, slug: str) -> tuple[int, int] | None:
    """Devolve (dia, mês) se título ou slug indicam uma data; senão None."""
    slug_n = slug.replace("_", "-")
    for text in (_strip_accents(title).lower(), _strip_accents(slug_n.replace("-", " ")).lower()):
        m = DATE_RE.search(text)
        if m:
            mes = _strip_accents(m.group(2).lower())
            idx = MESES_NOMES.index(mes) + 1
            if 1 <= int(m.group(1)) <= 31:
                return int(m.group(1)), idx
    # dd-mm no slug ou no título (ex.: fatos-historicos-incriveis-em-14-12, 14/12)
    for text in (slug_n, title):
        m = NUM_RE.search(text)
        if m and 1 <= int(m.group(1)) <= 31 and 1 <= int(m.group(2)) <= 12:
            return int(m.group(1)), int(m.group(2))
    return None


def is_date_page(title: str, slug: str) -> bool:
    return parse_date(title, slug) is not None


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


def _blocks_to_text(root) -> str:
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


def html_to_text(html_str: str) -> str:
    return _blocks_to_text(BeautifulSoup(html_str, "html.parser"))


def _clean_text(soup: BeautifulSoup) -> str:
    """Reserva: raspagem do HTML. Testa vários contêineres e fica com o de mais texto."""
    best = ""
    for sel in ('[data-elementor-type="wp-post"]', ".entry-content", "article", "main", "body"):
        root = soup.select_one(sel)
        if root is None:
            continue
        txt = _blocks_to_text(BeautifulSoup(str(root), "html.parser"))
        if len(txt) > len(best):
            best = txt
    return best


def fetch_content_rest(post_id: int) -> str:
    """Corpo do post pela API REST (content.rendered): independente do tema/Elementor."""
    if not post_id:
        return ""
    try:
        r = _session().get(f"{config.SITE_BASE}/wp-json/wp/v2/posts/{post_id}",
                           params={"_fields": "id,content"}, timeout=30)
        r.raise_for_status()
        return html_to_text(r.json()["content"]["rendered"])
    except Exception as e:  # noqa: BLE001
        print(f"[discover] conteúdo via REST indisponível ({e}); usando HTML.")
        return ""


def fetch_page(link: str, post_id: int = 0) -> dict:
    s = _session()
    r = s.get(link, timeout=30)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    og = soup.find("meta", property="og:image")
    title = soup.find("meta", property="og:title")
    text, source = fetch_content_rest(post_id), "rest"
    html_text = _clean_text(soup)
    if len(html_text) > len(text):
        text, source = html_text, "html"
    return {
        "link": link,
        "title": (title["content"] if title and title.get("content") else (soup.title.string if soup.title else "")),
        "cover_url": og["content"] if og and og.get("content") else None,
        "text": text[:40000],
        "text_source": source,
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

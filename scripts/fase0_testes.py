"""Fase 0 — testes de viabilidade. Execute localmente e também pelo workflow `Fase 0`.

Uso:
  python -m scripts.fase0_testes            # site (API REST, feed, sitemap, imagens de capa)
  python -m scripts.fase0_testes --media    # também testa a hospedagem (branch media + Pages)
  python -m scripts.fase0_testes --instagram# também valida token e cota do Instagram
"""
import argparse
import io
import sys

import requests
from PIL import Image

from src import config, discover
from src.instagram import Instagram
from src.media import push_media, wait_for_urls
from src.token import get_token
from src import state as st

OK, FAIL = "✅", "❌"


def check_site() -> list[dict]:
    s = discover._session()
    posts = []
    try:
        posts = discover.list_posts_rest(s)
        print(f"{OK} API REST: {len(posts)} posts")
    except Exception as e:  # noqa: BLE001
        print(f"{FAIL} API REST indisponível: {e}")
        try:
            posts = discover.list_posts_sitemap(s)
            print(f"{OK} Sitemap (reserva): {len(posts)} posts")
        except Exception as e2:  # noqa: BLE001
            print(f"{FAIL} Sitemap também falhou: {e2}")
    pages = [p for p in posts if discover.is_date_page(p["title"], p["slug"])]
    print(f"   Páginas de data reconhecidas: {len(pages)} de {len(posts)}")
    ignored = [p for p in posts if not discover.is_date_page(p["title"], p["slug"])]
    if ignored:
        print(f"   NÃO reconhecidas como data ({len(ignored)}) — confira se alguma é página de data:")
        for p in ignored[:70]:
            print(f"     - {p['slug']}  |  {p['title'][:70]}")
    dates = {}
    for p in pages:
        dates.setdefault(discover.parse_date(p["title"], p["slug"]), []).append(p["slug"])
    dups = {k: v for k, v in dates.items() if len(v) > 1}
    print(f"   Datas distintas: {len(dates)}; datas com mais de uma página: {len(dups)}")
    for k, v in list(dups.items())[:10]:
        print(f"     dia/mês {k}: {v}")
    for p in pages[:3]:
        print(f"   mais antigas: {p['date'][:10]}  {p['slug']}")
    for p in pages[-3:]:
        print(f"   mais recentes: {p['date'][:10]}  {p['slug']}")
    return pages


def check_covers(pages: list[dict], n: int = 10):
    sample = pages[:: max(1, len(pages) // n)][:n] if pages else []
    good = 0
    for p in sample:
        try:
            page = discover.fetch_page(p["link"], p["id"])
            img = discover.download_image(page["cover_url"]) if page["cover_url"] else None
            n = len(page["text"])
            if img:
                w, h = Image.open(io.BytesIO(img)).size
                flag = OK if n >= 1500 else FAIL + " TEXTO CURTO"
                print(f"{flag} {p['slug']}: capa {w}x{h}; texto {n} car. (fonte: {page['text_source']}; rest={page['rest_len']}, html={page['html_len']})")
                good += 1
            else:
                print(f"{FAIL} sem imagem de capa utilizável: {p['slug']}")
        except Exception as e:  # noqa: BLE001
            print(f"{FAIL} {p['slug']}: {e}")
    print(f"   Capas utilizáveis: {good}/{len(sample)}")
    if sample:
        first = discover.fetch_page(sample[0]["link"], sample[0]["id"])
        print("   --- prévia do texto extraído (primeiros 500 caracteres) ---")
        print("   " + first["text"][:500].replace("\n", "\n   "))


def check_media():
    im = Image.new("RGB", (1080, 1350), (13, 22, 38))
    from pathlib import Path
    out = Path("out/_teste"); out.mkdir(parents=True, exist_ok=True)
    f = out / "teste.jpg"; im.save(f, "JPEG", quality=90)
    urls = push_media("_teste", [f])
    print("   enviado para a branch media:", urls[0])
    try:
        wait_for_urls(urls, timeout=420)
        print(f"{OK} URL pública acessível como image/jpeg")
    except Exception as e:  # noqa: BLE001
        print(f"{FAIL} {e}")


def check_instagram():
    ig = Instagram(get_token(st.load()))
    print(f"{OK} conta:", ig.whoami())
    print(f"{OK} cota de publicação:", ig.quota())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--media", action="store_true")
    ap.add_argument("--instagram", action="store_true")
    a = ap.parse_args()
    pages = check_site()
    check_covers(pages)
    if a.media:
        check_media()
    if a.instagram:
        check_instagram()

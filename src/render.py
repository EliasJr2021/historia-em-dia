"""Renderização dos slides (Pillow, 1080x1350, JPEG sRGB)."""
import io
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

from . import config
from .models import Carousel
from .plan import Plan

W, H, M = 1080, 1350, 84
FONTS = Path(__file__).resolve().parent.parent / "assets" / "fonts"

BG = (13, 22, 38)
PANEL = (22, 35, 58)
INK = (244, 239, 230)
MUTED = (160, 174, 196)
GOLD = (217, 164, 65)
ERA = {
    "antiguidade": ((201, 139, 60), "ANTIGUIDADE"),
    "medieval": ((138, 111, 181), "IDADE MÉDIA"),
    "moderna": ((62, 156, 143), "IDADE MODERNA"),
    "contemporanea": ((217, 96, 76), "ÉPOCA CONTEMPORÂNEA"),
}


def font(name: str, size: int) -> ImageFont.FreeTypeFont:
    path = FONTS / name
    try:
        return ImageFont.truetype(str(path), size)
    except OSError:
        return ImageFont.load_default(size)


def anton(s): return font("Anton-Regular.ttf", s)
def lato(s): return font("Lato-Regular.ttf", s)
def lato_b(s): return font("Lato-Bold.ttf", s)
def lato_k(s): return font("Lato-Black.ttf", s)


def wrap(draw: ImageDraw.ImageDraw, text: str, f, max_w: int) -> list[str]:
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if draw.textlength(trial, font=f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit(draw, text, make_font, max_w, max_h, start, minimum, spacing=1.28, max_lines=None):
    """Maior fonte (start..minimum) em que o texto cabe em max_w x max_h."""
    size = start
    while True:
        f = make_font(size)
        lines = wrap(draw, text, f, max_w)
        lh = int(size * spacing)
        ok = len(lines) * lh <= max_h and (max_lines is None or len(lines) <= max_lines)
        if ok or size <= minimum:
            return f, lines, lh
        size -= 2


def draw_lines(draw, x, y, lines, f, lh, fill):
    for ln in lines:
        draw.text((x, y), ln, font=f, fill=fill, anchor="la")
        y += lh
    return y


def base() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, W, 10], fill=GOLD)
    return im, d


def footer(d, idx: int, total: int):
    d.text((M, H - 80), config.IG_HANDLE, font=lato_b(30), fill=MUTED, anchor="la")
    d.text((W - M, H - 80), f"{idx}/{total}", font=lato_b(30), fill=MUTED, anchor="ra")


def rounded(img: Image.Image, radius: int) -> Image.Image:
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, img.size[0], img.size[1]], radius=radius, fill=255)
    out = img.convert("RGB")
    out.putalpha(mask)
    return out


def arrow(d, x, y, color=GOLD):
    d.line([(x, y), (x + 70, y)], fill=color, width=6)
    d.polygon([(x + 84, y), (x + 62, y - 16), (x + 62, y + 16)], fill=color)


# ───────────────────────── slides ─────────────────────────

def slide_cover(c: Carousel, plan: Plan, cover: Image.Image | None) -> Image.Image:
    im, d = base()
    date = c.date_label.upper()
    if cover is not None:
        bg = ImageOps.fit(cover.convert("RGB"), (W, H), Image.LANCZOS).filter(ImageFilter.GaussianBlur(30))
        im = Image.blend(bg, Image.new("RGB", (W, H), (5, 10, 20)), 0.62)
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, W, 10], fill=GOLD)
    f, lines, lh = fit(d, date, anton, W - 2 * M, 260, 170, 90, spacing=1.15, max_lines=2)
    y = draw_lines(d, M, 96, lines, f, lh, INK)
    d.text((M, y + 16), "NA HISTÓRIA", font=lato_k(44), fill=GOLD, anchor="la")
    y += 90

    if cover is not None:
        py = max(y + 40, 400)
        max_w = W - 2 * M
        max_h = max(380, min(640, H - 190 - 190 - 44 - py))   # reserva espaço para o gancho e o rodapé
        cw_, ch_ = cover.size
        scale = min(max_w / cw_, max_h / ch_)
        iw, ih = int(cw_ * scale), int(ch_ * scale)           # sem recorte: 1:1, 3:2 ou 16:9
        photo = rounded(cover.convert("RGB").resize((iw, ih), Image.LANCZOS), 28)
        px = (W - iw) // 2
        im.paste(photo, (px, py), photo)
        d = ImageDraw.Draw(im)
        d.rounded_rectangle([px, py, px + iw, py + ih], radius=28, outline=GOLD, width=3)
        y = py + ih + 44
    else:
        y += 40
        for e in plan.main[:6]:
            d.text((M, y), e.year, font=anton(60), fill=GOLD, anchor="la")
            f2, l2, lh2 = fit(d, e.title, lato_b, W - 2 * M - 230, 110, 38, 28, max_lines=2)
            draw_lines(d, M + 230, y + 4, l2, f2, lh2, INK)
            y += max(80, len(l2) * lh2 + 24)
        y += 30

    f3, l3, lh3 = fit(d, c.hook, lato_b, W - 2 * M, max(H - 190 - y, 80), 42, 30, max_lines=4)
    draw_lines(d, M, y, l3, f3, lh3, INK)

    d.text((M, H - 80), "DESLIZE", font=lato_k(34), fill=GOLD, anchor="la")
    arrow(d, M + 150, H - 62)
    d.text((W - M, H - 80), f"{plan.total_facts} fatos", font=lato_b(30), fill=MUTED, anchor="ra")
    return im


def slide_event(e, idx: int, total: int) -> Image.Image:
    color, label = ERA[e.era]
    im, d = base()
    d.rectangle([0, 0, 16, H], fill=color)
    y = M
    cf = lato_b(28)
    cw = int(d.textlength(label, font=cf)) + 44
    d.rounded_rectangle([M, y, M + cw, y + 52], radius=26, fill=color)
    d.text((M + 22, y + 26), label, font=cf, fill=(13, 22, 38), anchor="lm")
    y += 52 + 36

    yf, yl, ylh = fit(d, e.year, anton, W - 2 * M, 400, 300, 120, spacing=1.0, max_lines=1)
    bbox = d.textbbox((M, y), e.year, font=yf, anchor="la")
    d.text((M, y), e.year, font=yf, fill=color, anchor="la")
    y = bbox[3] + 44

    tf, tl, tlh = fit(d, e.title, lato_k, W - 2 * M, 250, 66, 44, spacing=1.2, max_lines=3)
    y = draw_lines(d, M, y, tl, tf, tlh, INK) + 20
    d.rectangle([M, y, M + 120, y + 6], fill=color)
    y += 6 + 36

    avail = (H - 140) - y
    sf, sl, slh = fit(d, e.summary, lato, W - 2 * M, avail, 46, 32, spacing=1.38)
    draw_lines(d, M, y, sl, sf, slh, (222, 226, 234))
    footer(d, idx, total)
    return im


def slide_others(plan: Plan, idx: int, total: int) -> Image.Image:
    im, d = base()
    d.rectangle([0, 0, 16, H], fill=GOLD)
    tf, tl, tlh = fit(d, "TAMBÉM ACONTECEU NESTE DIA", anton, W - 2 * M, 300, 96, 64, spacing=1.15, max_lines=2)
    y = draw_lines(d, M, M + 10, tl, tf, tlh, INK) + 30
    d.rectangle([M, y, M + 120, y + 6], fill=GOLD)
    y += 6 + 44
    bottom = H - (210 if plan.extra else 150)
    col = 230
    size = 40
    while True:
        rows, total_h = [], 0
        for year, line in plan.others:
            f = lato(size)
            ls = wrap(d, line, f, W - 2 * M - col)
            h = max(int(size * 1.35) * len(ls), 64) + 30
            rows.append((year, ls, h))
            total_h += h
        if total_h <= bottom - y or size <= 26:
            break
        size -= 2
    for year, ls, h in rows:
        d.text((M, y), year, font=anton(54), fill=GOLD, anchor="la")
        draw_lines(d, M + col, y + 4, ls, lato(size), int(size * 1.35), INK)
        y += h
        d.line([(M, y - 14), (W - M, y - 14)], fill=(40, 56, 84), width=2)
    if plan.extra:
        d.text((M, H - 170), f"e mais {plan.extra} fatos no site", font=lato_b(36), fill=MUTED, anchor="la")
    footer(d, idx, total)
    return im


def slide_closing(c: Carousel, idx: int, total: int) -> Image.Image:
    im, d = base()
    d.rectangle([0, 0, 16, H], fill=GOLD)
    y = 170
    d.text((M, y), "QUER SABER MAIS?", font=anton(120), fill=INK, anchor="la")
    y += 190
    d.rectangle([M, y, M + 120, y + 6], fill=GOLD)
    y += 56
    d.text((M, y), "Leia o texto completo desta data no site:", font=lato(42), fill=(222, 226, 234), anchor="la")
    y += 96
    box_h = 120
    d.rounded_rectangle([M, y, W - M, y + box_h], radius=24, fill=GOLD)
    uf, _, _ = fit(d, config.SITE_HOST, lato_k, W - 2 * M - 60, box_h, 56, 34, max_lines=1)
    d.text((W // 2, y + box_h // 2), config.SITE_HOST, font=uf, fill=(13, 22, 38), anchor="mm")
    y += box_h + 70
    f, lines, lh = fit(d, f"Siga {config.IG_HANDLE} e acompanhe um dia da história todos os dias.",
                       lato_b, W - 2 * M, 200, 44, 32)
    y = draw_lines(d, M, y, lines, f, lh, INK) + 40
    notes = ["Fonte: " + config.SITE_HOST, "Conteúdo informativo, com finalidade histórica e educativa."]
    if config.AI_IMAGE_NOTICE:
        notes.append("Imagem ilustrativa gerada por IA.")
    for n in notes:
        d.text((M, y), n, font=lato(30), fill=MUTED, anchor="la")
        y += 46
    footer(d, idx, total)
    return im


def build_slides(c: Carousel, plan: Plan, cover_bytes: bytes | None) -> list[Image.Image]:
    cover = None
    if cover_bytes:
        try:
            cover = Image.open(io.BytesIO(cover_bytes))
            cover.load()
        except Exception as e:  # noqa: BLE001
            print(f"[render] capa ilegível, usando capa tipográfica: {e}")
    slides = [slide_cover(c, plan, cover)]
    n = plan.total_slides
    for i, e in enumerate(plan.main, start=2):
        slides.append(slide_event(e, i, n))
    if plan.others:
        slides.append(slide_others(plan, len(slides) + 1, n))
    slides.append(slide_closing(c, len(slides) + 1, n))
    return slides


def save_jpegs(slides: list[Image.Image], out_dir: Path) -> list[Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i, im in enumerate(slides, start=1):
        p = out_dir / f"slide_{i:02d}.jpg"
        im.convert("RGB").save(p, "JPEG", quality=90, optimize=True)
        if p.stat().st_size > 8 * 1024 * 1024:
            im.convert("RGB").save(p, "JPEG", quality=75, optimize=True)
        paths.append(p)
    return paths

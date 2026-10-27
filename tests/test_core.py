import io
import json
from pathlib import Path

import pytest
import yaml
from PIL import Image

from src import caption, github_api, plan as plan_mod, render
from src.discover import is_date_page
from src.models import Carousel
from tests.fixtures import SAMPLE, sample

ROOT = Path(__file__).resolve().parent.parent


def test_year_key():
    assert plan_mod.year_key("44 a.C.") == -44
    assert plan_mod.year_key("1912") == 1912
    assert plan_mod.year_key("sem ano") == 0


def test_date_page_filter():
    assert is_date_page("Fatos em 14 de abril", "x")
    assert is_date_page("x", "fatos-historicos-17-de-abril")
    assert is_date_page("1º de janeiro", "1o-de-janeiro-na-historia")
    assert not is_date_page("Sobre nós", "sobre")
    # formatos reais vistos no site
    assert is_date_page("x", "fatos-historicos-incriveis-em-14-12")
    assert is_date_page("x", "fatos_historicos_incriveis_em_22_03")
    assert is_date_page("x", "fatos-hitoricos-incriveis-em-09-01")
    assert is_date_page("x", "3-de-abril-na-historia")
    assert is_date_page("Fatos de 28/12", "x")
    assert not is_date_page("Política de privacidade", "politica-de-privacidade")
    assert not is_date_page("Top 10 de 2026", "top-10-de-2026")
    from src.discover import parse_date
    assert parse_date("x", "fatos-historicos-incriveis-em-14-12") == (14, 12)
    assert parse_date("x", "10-de-marco-historia") == (10, 3)


def test_plan_limits_and_order():
    c = sample()
    p = plan_mod.make_plan(c, max_slides=10, order="chronological")
    assert p.total_slides <= 10
    years = [plan_mod.year_key(e.year) for e in p.main]
    assert years == sorted(years)


def test_plan_demotes_when_too_many():
    data = json.loads(json.dumps(SAMPLE))
    extra = [dict(data["events"][0], year=str(1700 + i), title=f"Fato {i}", importance=1) for i in range(8)]
    data["events"] += extra
    c = Carousel.model_validate(data)
    p = plan_mod.make_plan(c, max_slides=10)
    assert len(p.main) == 7
    assert p.total_slides == 10
    assert len(p.others) <= plan_mod.OTHERS_LINES_MAX


def test_caption_limits_and_link():
    c = sample()
    p = plan_mod.make_plan(c)
    cap = caption.build_caption(c, p, "https://historiaemdia.com.br/14-de-abril-na-historia/")
    assert len(cap) <= 2200
    assert "utm_source=instagram" in cap
    assert "hoje" not in cap.lower().split("\n")[0]
    assert cap.count("#") <= 8


def test_render_outputs(tmp_path):
    c = sample()
    p = plan_mod.make_plan(c)
    buf = io.BytesIO()
    Image.new("RGB", (1376, 768), (50, 70, 100)).save(buf, "JPEG")
    slides = render.build_slides(c, p, buf.getvalue())
    assert len(slides) == p.total_slides
    paths = render.save_jpegs(slides, tmp_path)
    for f in paths:
        im = Image.open(f)
        assert im.size == (1080, 1350) and im.format == "JPEG"
        assert f.stat().st_size < 8 * 1024 * 1024


def test_render_without_cover(tmp_path):
    c = sample()
    p = plan_mod.make_plan(c)
    slides = render.build_slides(c, p, None)
    assert len(slides) == p.total_slides


def test_caption_roundtrip_from_issue_body():
    pending = {"date_label": "14 de abril", "link": "https://x", "slides": ["https://a/1.jpg"], "caption": "Linha 1\nLinha 2 #tag"}
    body = github_api.issue_body(pending, "ok")
    assert github_api.parse_caption(body) == "Linha 1\nLinha 2 #tag"
    edited = body.replace("Linha 2", "Linha editada")
    assert "Linha editada" in github_api.parse_caption(edited)


def test_workflows_are_valid_yaml_and_owner_guard():
    for f in (ROOT / ".github" / "workflows").glob("*.yml"):
        data = yaml.safe_load(f.read_text())
        assert "jobs" in data
    publish = (ROOT / ".github" / "workflows" / "publish.yml").read_text()
    assert "author_association == 'OWNER'" in publish
    assert "pull_request_target" not in publish


def test_validation_rejects_long_title():
    data = json.loads(json.dumps(SAMPLE))
    data["events"][0]["title"] = "x" * 90
    with pytest.raises(Exception):
        Carousel.model_validate(data)


@pytest.mark.parametrize("size", [(1024, 1024), (1536, 1024), (1344, 768), (1376, 768)])
def test_cover_any_aspect_ratio(size, tmp_path):
    c = sample()
    p = plan_mod.make_plan(c)
    buf = io.BytesIO()
    Image.new("RGB", size, (50, 70, 100)).save(buf, "JPEG")
    slides = render.build_slides(c, p, buf.getvalue())
    assert slides[0].size == (1080, 1350)
    slides[0].convert("RGB").save(tmp_path / f"cover_{size[0]}x{size[1]}.jpg")


def test_text_source_prefers_rest():
    from src.discover import choose_text
    art = "artigo " * 800
    chrome = "menu popular posts " * 2000
    assert choose_text(art, art + chrome) == (art, "rest")
    assert choose_text("curto", chrome)[1] == "html"


def test_html_fallback_drops_chrome_and_starts_at_h1():
    from bs4 import BeautifulSoup
    from src.discover import _clean_text
    html = ("<body><div class='x-popup'><h2>Quer fazer uma parceria conosco?</h2></div>"
            "<main><p>Popular menu</p><h1>14 de abril na História</h1><p>Texto do artigo.</p></main></body>")
    out = _clean_text(BeautifulSoup(html, "html.parser"))
    assert "parceria" not in out and out.startswith("## 14 de abril") and "Texto do artigo" in out

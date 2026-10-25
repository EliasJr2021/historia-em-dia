"""Seleção de fatos e ordem dos slides (máximo de 10 itens no carrossel)."""
import re
from dataclasses import dataclass

from . import config
from .models import Carousel, Event

OTHERS_LINES_MAX = 6


def year_key(year: str) -> int:
    m = re.search(r"\d+", year)
    if not m:
        return 0
    n = int(m.group())
    return -n if re.search(r"a\.?\s?C", year, re.I) else n


@dataclass
class Plan:
    main: list[Event]
    others: list[tuple[str, str]]   # (ano, linha)
    extra: int                      # fatos que não couberam
    total_slides: int
    total_facts: int


def make_plan(c: Carousel, max_slides: int | None = None, order: str | None = None) -> Plan:
    max_slides = max_slides or config.MAX_SLIDES
    order = order or config.ORDER
    events = list(c.events)
    other_items = [(o.year, o.line) for o in c.others]

    # capa + encerramento = 2; slide "outros" = +1 quando necessário
    if len(events) <= max_slides - 2 and not other_items:
        main, demoted = events, []
    else:
        cap = max_slides - 3
        ranked = sorted(range(len(events)), key=lambda i: (-events[i].importance, i))
        keep = set(ranked[:cap])
        main = [e for i, e in enumerate(events) if i in keep]
        demoted = [e for i, e in enumerate(events) if i not in keep]

    if order == "chronological":
        main.sort(key=lambda e: year_key(e.year))
        demoted.sort(key=lambda e: year_key(e.year))

    others_all = [(e.year, e.title) for e in demoted] + other_items
    shown = others_all[:OTHERS_LINES_MAX]
    extra = len(others_all) - len(shown)
    total = 1 + len(main) + (1 if shown else 0) + 1
    return Plan(main=main, others=shown, extra=extra, total_slides=total, total_facts=len(events) + len(other_items))

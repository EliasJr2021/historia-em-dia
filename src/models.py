"""Modelos e esquemas (JSON Schema escrito à mão para as ferramentas do Claude)."""
from typing import Literal, Optional
from pydantic import BaseModel, Field, ValidationError  # noqa: F401

ERAS = ["antiguidade", "medieval", "moderna", "contemporanea"]


class Event(BaseModel):
    year: str = Field(max_length=12)
    title: str = Field(max_length=70)
    summary: str = Field(max_length=300)
    importance: int = Field(ge=1, le=5)
    sensitivity: Literal["baixa", "media", "alta"]
    era: Literal["antiguidade", "medieval", "moderna", "contemporanea"]


class Other(BaseModel):
    year: str = Field(max_length=12)
    line: str = Field(max_length=110)


class Risk(BaseModel):
    level: Literal["baixo", "medio", "alto"]
    reasons: list[str] = []


class Carousel(BaseModel):
    date_label: str = Field(max_length=30)
    hook: str = Field(max_length=150)
    events: list[Event] = Field(min_length=1, max_length=14)
    others: list[Other] = Field(default=[], max_length=14)
    hashtags: list[str] = Field(default=[], max_length=10)
    risk: Risk


class Review(BaseModel):
    verdict: Literal["ok", "ajustar", "reter"]
    reasons: list[str] = []
    fixes: list[str] = []
    image_ok: bool = True
    image_flags: list[str] = []


CAROUSEL_SCHEMA = {
    "type": "object",
    "properties": {
        "date_label": {"type": "string", "description": "Data histórica, ex.: '17 de abril'."},
        "hook": {"type": "string", "description": "Gancho de uma linha (até 150 caracteres) citando 2 ou 3 fatos."},
        "events": {
            "type": "array",
            "description": "Fatos principais da página, um por item (divida blocos que agrupam vários fatos).",
            "items": {
                "type": "object",
                "properties": {
                    "year": {"type": "string", "description": "Ex.: '1912' ou '44 a.C.'"},
                    "title": {"type": "string", "description": "Até 60 caracteres."},
                    "summary": {"type": "string", "description": "Até 260 caracteres, 2 a 3 frases curtas."},
                    "importance": {"type": "integer", "minimum": 1, "maximum": 5},
                    "sensitivity": {"type": "string", "enum": ["baixa", "media", "alta"]},
                    "era": {"type": "string", "enum": ERAS},
                },
                "required": ["year", "title", "summary", "importance", "sensitivity", "era"],
            },
        },
        "others": {
            "type": "array",
            "description": "Fatos secundários ('Outros eventos'), uma linha cada (até 90 caracteres).",
            "items": {
                "type": "object",
                "properties": {"year": {"type": "string"}, "line": {"type": "string"}},
                "required": ["year", "line"],
            },
        },
        "hashtags": {"type": "array", "items": {"type": "string"}, "description": "5 a 8 hashtags em português."},
        "risk": {
            "type": "object",
            "properties": {
                "level": {"type": "string", "enum": ["baixo", "medio", "alto"]},
                "reasons": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["level", "reasons"],
        },
    },
    "required": ["date_label", "hook", "events", "others", "hashtags", "risk"],
}

REVIEW_SCHEMA = {
    "type": "object",
    "properties": {
        "verdict": {"type": "string", "enum": ["ok", "ajustar", "reter"]},
        "reasons": {"type": "array", "items": {"type": "string"}},
        "fixes": {"type": "array", "items": {"type": "string"},
                  "description": "Correções objetivas e específicas, quando verdict = ajustar."},
        "image_ok": {"type": "boolean"},
        "image_flags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["verdict", "reasons", "fixes", "image_ok", "image_flags"],
}

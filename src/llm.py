"""Chamadas ao Claude com saída estruturada via ferramenta forçada."""
import anthropic

from . import config

_client = None


def client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic()  # usa ANTHROPIC_API_KEY
    return _client


def call_tool(system: str, content, tool_name: str, description: str, schema: dict, max_tokens: int = 4096) -> dict:
    resp = client().messages.create(
        model=config.CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system,
        tools=[{"name": tool_name, "description": description, "input_schema": schema}],
        tool_choice={"type": "tool", "name": tool_name},
        messages=[{"role": "user", "content": content}],
    )
    for block in resp.content:
        if block.type == "tool_use" and block.name == tool_name:
            return block.input
    raise RuntimeError("O modelo não devolveu a ferramenta esperada.")

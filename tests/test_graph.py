from __future__ import annotations

from pathlib import Path

import pytest
from langchain_core.messages import AIMessage, HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver

from ia_entrega_5.graph import build_graph


class ScriptedModel:
    """Doble del LLM que fuerza una vuelta modelo → herramienta → modelo."""

    def __init__(self) -> None:
        self.calls = 0

    async def ainvoke(self, _messages: object) -> AIMessage:
        self.calls += 1
        if self.calls == 1:
            return AIMessage(
                content="",
                tool_calls=[{"name": "consultar_inventario", "args": {"activo": "srv-fin-01"}, "id": "call-1"}],
            )
        return AIMessage(content="El activo ficticio fue encontrado.")


@pytest.mark.asyncio
async def test_react_cycle_and_sqlite_checkpoint(tmp_path: Path) -> None:
    database = tmp_path / "memory.sqlite"
    async with AsyncSqliteSaver.from_conn_string(str(database)) as saver:
        graph = build_graph(saver, ScriptedModel())
        config = {"configurable": {"thread_id": "same-session"}, "recursion_limit": 10}
        result = await graph.ainvoke({"messages": [HumanMessage(content="Busca srv-fin-01")]}, config)

    assert result["messages"][-1].content == "El activo ficticio fue encontrado."
    assert database.exists()

"""Grafo ReAct y persistencia asíncrona del agente."""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_groq import ChatGroq
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from .tools import TOOLS

SYSTEM_PROMPT = """Eres un asistente de inventario y vulnerabilidades ficticias.
Decide autónomamente si necesitas herramientas; no inventes datos de activos.
Si una herramienta devuelve ok=false, corrige y reintenta si existen alternativas.
Si devuelve complete=false, reintenta con los datos solicitados completos. Si falta un
dato que el usuario no proporcionó ni está en la respuesta de la herramienta, pide una
aclaración breve. Aclara que los resultados son ficticios. Responde en español."""


def build_model() -> Any:
    """Crea el modelo Groq con las herramientas disponibles para decisiones autónomas."""
    model_name = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    return ChatGroq(model=model_name, temperature=0).bind_tools(TOOLS)


def build_graph(checkpointer: AsyncSqliteSaver, model: Any | None = None) -> Any:
    """Compila el StateGraph MessagesState con ciclo modelo → herramientas → modelo."""
    chat_model = model or build_model()

    async def call_model(state: MessagesState) -> dict[str, list[BaseMessage]]:
        messages: list[BaseMessage] = [SystemMessage(content=SYSTEM_PROMPT), *state["messages"]]
        response: AIMessage = await chat_model.ainvoke(messages)
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", ToolNode(TOOLS))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    return graph.compile(checkpointer=checkpointer)


@asynccontextmanager
async def open_graph(sqlite_path: str | Path, model: Any | None = None) -> AsyncIterator[Any]:
    """Abre un checkpointer SQLite asíncrono durante el ciclo de vida del grafo."""
    path = Path(sqlite_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    async with AsyncSqliteSaver.from_conn_string(str(path)) as checkpointer:
        yield build_graph(checkpointer, model)

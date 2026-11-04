"""Punto de entrada de consola con memoria por thread_id."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncIterator

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from .graph import open_graph


@asynccontextmanager
async def agent_session(sqlite_path: str | Path) -> AsyncIterator[Any]:
    """Expone el grafo sin filtrar detalles de ciclo de vida del checkpointer."""
    async with open_graph(sqlite_path) as graph:
        yield graph


def message_to_json(message: Any) -> dict[str, Any]:
    """Serializa una parte legible de un mensaje para una traza de demostración."""
    return {
        "type": message.__class__.__name__,
        "content": message.content,
        "tool_calls": getattr(message, "tool_calls", []),
        "tool_call_id": getattr(message, "tool_call_id", None),
    }


async def run(prompt: str, thread_id: str, sqlite_path: str, trace: bool) -> None:
    """Ejecuta una vuelta, preservando el historial asociado al thread_id."""
    config = {"configurable": {"thread_id": thread_id}, "recursion_limit": 10}
    async with agent_session(sqlite_path) as graph:
        if trace:
            events: list[dict[str, Any]] = []
            async for event in graph.astream({"messages": [HumanMessage(content=prompt)]}, config):
                for node_name, update in event.items():
                    events.append({
                        "node": node_name,
                        "messages": [message_to_json(m) for m in update.get("messages", [])],
                    })
            print(json.dumps({"trace_type": "REAL", "thread_id": thread_id, "events": events}, ensure_ascii=False, indent=2))
            return
        result = await graph.ainvoke({"messages": [HumanMessage(content=prompt)]}, config)
        print(result["messages"][-1].content)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Agente ReAct persistente (datos ficticios).")
    parser.add_argument("prompt", help="Consulta en español para el agente.")
    parser.add_argument("--thread-id", default="demo-001", help="Identificador de sesión persistente.")
    parser.add_argument("--trace", action="store_true", help="Imprime una traza JSON real en lugar de la respuesta final.")
    parser.add_argument("--db", default=os.getenv("SQLITE_PATH", "data/agent_memory.sqlite"), help="Ruta de la base SQLite.")
    return parser.parse_args()


def main() -> None:
    load_dotenv()
    if not os.getenv("GROQ_API_KEY"):
        raise SystemExit("Falta GROQ_API_KEY: copia .env.example a .env y configura tu clave.")
    args = parse_args()
    asyncio.run(run(args.prompt, args.thread_id, args.db, args.trace))


if __name__ == "__main__":
    main()

"""Herramientas completamente ficticias para la demostración académica."""

from __future__ import annotations

from typing import Any

from langchain_core.tools import tool

_INVENTORY: dict[str, dict[str, Any]] = {
    "srv-fin-01": {
        "asset_id": "srv-fin-01",
        "name": "servidor-finanzas",
        "owner": "Finanzas",
        "environment": "produccion",
        "os": "Ubuntu 22.04",
    },
    "ws-dev-03": {
        "asset_id": "ws-dev-03",
        "name": "estacion-desarrollo-03",
        "owner": "Ingenieria",
        "environment": "desarrollo",
        "os": "Windows 11",
    },
}

_VULNERABILITIES: dict[str, list[dict[str, str]]] = {
    "srv-fin-01": [
        {
            "id": "DEMO-CVE-2026-0001",
            "severity": "alta",
            "status": "pendiente",
            "summary": "Paquete de demostracion desactualizado; no es una CVE real.",
        }
    ],
    "ws-dev-03": [],
}


def _find_asset(identifier: str) -> dict[str, Any] | None:
    normalized = identifier.strip().lower()
    return next(
        (
            asset
            for asset in _INVENTORY.values()
            if normalized in {asset["asset_id"].lower(), asset["name"].lower()}
        ),
        None,
    )


@tool
def consultar_inventario(activo: str) -> dict[str, Any]:
    """Consulta el inventario simulado de activos de una empresa ficticia.

    Úsala cuando necesites confirmar el ID, nombre, propietario, entorno o sistema
    operativo de un activo antes de responder sobre él. Acepta un ID (por ejemplo,
    ``srv-fin-01``) o nombre (``servidor-finanzas``). Si no existe, devuelve un
    error recuperable con los activos disponibles para que intentes de nuevo con un
    identificador válido. Todos los datos son ficticios y seguros para demostración.
    """
    asset = _find_asset(activo)
    if asset is None:
        return {
            "ok": False,
            "kind": "not_found",
            "retryable": True,
            "message": "Activo no encontrado. Solicita un ID o usa uno de los activos disponibles.",
            "available_assets": list(_INVENTORY),
        }
    return {"ok": True, "complete": True, "asset": asset}


@tool
def consultar_vulnerabilidades(activo: str, incluir_detalle: bool = True) -> dict[str, Any]:
    """Devuelve vulnerabilidades ficticias para un activo de demostración.

    Úsala después de identificar el activo, para revisar sus hallazgos simulados.
    Acepta ID o nombre. Si no encuentra el activo, devuelve un error recuperable y
    una lista de IDs válidos, por lo que debes corregir el identificador y reintentar.
    Cuando ``incluir_detalle`` es falso, el resultado se marca incompleto: vuelve a
    invocarla con ``incluir_detalle=True`` si el usuario pidió severidad, estado o
    descripción. No realiza escaneos reales ni contiene inteligencia de seguridad real.
    """
    asset = _find_asset(activo)
    if asset is None:
        return {
            "ok": False,
            "kind": "not_found",
            "retryable": True,
            "message": "No puedo relacionar ese activo con el inventario ficticio.",
            "available_assets": list(_INVENTORY),
        }
    findings = _VULNERABILITIES[asset["asset_id"]]
    if not incluir_detalle:
        return {
            "ok": True,
            "complete": False,
            "message": "Resultado parcial: faltan detalles. Reintenta con incluir_detalle=True.",
            "count": len(findings),
        }
    return {
        "ok": True,
        "complete": True,
        "asset_id": asset["asset_id"],
        "findings": findings,
        "count": len(findings),
        "disclaimer": "Hallazgos enteramente ficticios para fines académicos.",
    }


TOOLS = [consultar_inventario, consultar_vulnerabilidades]

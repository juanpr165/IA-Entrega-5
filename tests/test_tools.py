from ia_entrega_5.tools import consultar_inventario, consultar_vulnerabilidades


def test_inventory_returns_a_fictitious_asset() -> None:
    result = consultar_inventario.invoke({"activo": "servidor-finanzas"})
    assert result["ok"] is True
    assert result["asset"]["asset_id"] == "srv-fin-01"


def test_unknown_asset_is_recoverable() -> None:
    result = consultar_vulnerabilidades.invoke({"activo": "no-existe"})
    assert result["ok"] is False
    assert result["retryable"] is True
    assert "srv-fin-01" in result["available_assets"]


def test_partial_vulnerability_result_instructs_a_retry() -> None:
    result = consultar_vulnerabilidades.invoke({"activo": "srv-fin-01", "incluir_detalle": False})
    assert result["ok"] is True
    assert result["complete"] is False
    assert "Reintenta" in result["message"]

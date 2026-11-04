# IA-Entrega 5 — Agente cíclico persistente

Entrega académica en Python 3.12: un agente ReAct que decide autónomamente cuándo usar herramientas, conserva contexto mediante SQLite y puede volver a intentar ante datos inválidos o incompletos.

> Los activos y vulnerabilidades de este proyecto son **completamente ficticios**. No realiza escaneos, conexiones a infraestructura ni consultas de seguridad reales.

## Qué demuestra

- `StateGraph(MessagesState)` de LangGraph con el ciclo `agent → tools → agent`.
- Selección autónoma de `@tool` mediante `ChatGroq.bind_tools(TOOLS)`: no hay rutas manuales `if/else` para elegir herramientas.
- `tools_condition` dirige la salida del modelo al nodo de herramientas o finaliza el flujo.
- Las herramientas tienen docstrings descriptivos e informan `ok`, `retryable` y `complete`. El prompt de sistema indica al modelo reintentar para errores recuperables o respuestas incompletas, y pedir una aclaración si no hay datos para continuar.
- Persistencia por `thread_id` usando `AsyncSqliteSaver`, compatible con `asyncio`.
- Techo de seguridad `recursion_limit=10` en cada invocación.
- Pruebas automatizadas sin API key y una traza JSON de ejemplo etiquetada como ficticia.

## Requisitos

- Python 3.12
- Una API key propia de Groq, solo para ejecutar el agente real

## Instalación en Visual Studio Code

1. Abre esta carpeta con **File → Open Folder** en VS Code.
2. Crea y activa el entorno virtual:

   ```powershell
   py -3.12 -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

3. Instala las dependencias y el paquete:

   ```powershell
   python -m pip install --upgrade pip
   pip install -r requirements.txt
   pip install -e .
   ```

4. Copia `.env.example` a `.env` y escribe tu `GROQ_API_KEY`. El archivo `.env` está ignorado por Git y nunca se incluye una clave en este repositorio.

La carpeta `.vscode/` deja configurados el intérprete, Pytest y un perfil de depuración para el módulo.

## Ejecución

Consulta normal (crea o reutiliza `data/agent_memory.sqlite`):

```powershell
python -m ia_entrega_5.main "¿Qué vulnerabilidades tiene servidor-finanzas?" --thread-id clase-01
```

Para continuar la misma conversación persistente, usa exactamente el mismo `thread_id`:

```powershell
python -m ia_entrega_5.main "¿Quién es el dueño de ese activo?" --thread-id clase-01
```

Para generar una traza **real** de esa ejecución como JSON:

```powershell
python -m ia_entrega_5.main "Revisa srv-fin-01" --thread-id clase-02 --trace
```

La traza de muestra, que no requiere red ni API key, está en [`examples/traza_ejemplo.json`](examples/traza_ejemplo.json). Su campo `trace_type` dice `EJEMPLO_FICTICIO` para diferenciarla inequívocamente de `REAL`, que es lo que emite `--trace`.

## Pruebas

```powershell
pytest -q
```

Las pruebas verifican los contratos de resultados recuperables/incompletos y una vuelta completa `modelo → herramienta → modelo` guardada en SQLite con un modelo simulado.

## Estructura

```text
src/ia_entrega_5/
  tools.py       Herramientas @tool y datos ficticios
  graph.py       StateGraph, tools_condition y AsyncSqliteSaver
  main.py        CLI, thread_id y salida de trazas JSON
tests/           Pruebas sin credenciales
examples/        Traza JSON ficticia etiquetada
.vscode/         Configuración para abrir directamente en VS Code
```
## Nota sobre el segundo intento

La recuperación la guía el contrato de cada herramienta y el prompt del sistema, que es el patrón ReAct solicitado. Por ejemplo, una consulta de vulnerabilidades sin detalle devuelve `complete: false` y ordena reintentar con `incluir_detalle: true`; un activo desconocido devuelve `retryable: true` y los IDs disponibles. El LLM decide la siguiente llamada al observar esa respuesta, sin reglas de ruteo manuales.

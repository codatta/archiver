import json
import os
from pathlib import Path

import httpx
import typer

app = typer.Typer(name="attempt-index", help="AttemptIndex service CLI")

_DEFAULT_URL = "http://localhost:8000"


def _base_url() -> str:
    return os.environ.get("ATTEMPT_INDEX_URL", _DEFAULT_URL)


@app.command()
def serve(
    host: str = "0.0.0.0",
    port: int = typer.Option(8000, envvar="PORT"),
    reload: bool = False,
):
    """Start the AttemptIndex FastAPI server."""
    import uvicorn

    uvicorn.run("app.main:app", host=host, port=port, reload=reload)


@app.command()
def health(url: str = typer.Option("", help="Base URL override (default: ATTEMPT_INDEX_URL env)")):
    """Check service health."""
    base = url or _base_url()
    try:
        r = httpx.get(f"{base}/health", timeout=5)
        typer.echo(json.dumps(r.json(), indent=2))
        raise typer.Exit(0 if r.json().get("status") == "ok" else 1)
    except httpx.ConnectError:
        typer.echo(f"Error: could not connect to {base}", err=True)
        raise typer.Exit(1)


@app.command()
def evaluate(
    payload_json: str = typer.Option(..., "--json", help="JSON string of the evaluate request"),
    url: str = typer.Option("", help="Base URL"),
):
    """Call POST /v1/evaluate and print the result."""
    base = url or _base_url()
    try:
        data = json.loads(payload_json)
    except json.JSONDecodeError as e:
        typer.echo(f"Invalid JSON: {e}", err=True)
        raise typer.Exit(1)

    r = httpx.post(f"{base}/v1/evaluate", json=data, timeout=30)
    typer.echo(json.dumps(r.json(), indent=2))
    raise typer.Exit(0 if r.is_success else 1)


@app.command()
def bootstrap_cmd(
    file: Path = typer.Argument(..., help="JSON file with {records: [...]} or array of records"),
    url: str = typer.Option("", help="Base URL"),
):
    """Bulk-bootstrap known records from a JSON file."""
    base = url or _base_url()
    raw = json.loads(file.read_text())
    records = raw if isinstance(raw, list) else raw.get("records", raw)

    r = httpx.post(f"{base}/v1/bootstrap", json={"records": records}, timeout=60)
    typer.echo(json.dumps(r.json(), indent=2))
    raise typer.Exit(0 if r.is_success else 1)


# Rename to avoid clash with built-in
app.command(name="bootstrap")(bootstrap_cmd)

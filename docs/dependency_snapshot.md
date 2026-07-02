# Dependency Snapshot

Snapshot purpose: record the Phase 3.3 environment used to freeze the API contract.

## Commands Used

```powershell
python --version
python -m pip freeze
python -c "import importlib.metadata as m; ..."
python -c "from fastapi.testclient import TestClient; import starlette.testclient as tc; ..."
```

## Python

```text
Python 3.12.13
```

## Relevant Installed Packages

```text
anyio==4.14.1
fastapi==0.138.1
h11==0.16.0
httpcore2==2.5.0
httpx2==2.5.0
pydantic==2.13.4
pytest==9.1.1
PyYAML==6.0.3
starlette==1.3.1
truststore==0.10.4
uvicorn==0.49.0
```

Not installed in this environment:

```text
httpx==NOT_INSTALLED
httpcore==NOT_INSTALLED
```

## TestClient Dependency Check

`fastapi.testclient.TestClient` imports from `starlette.testclient`.

Current `starlette.testclient` behavior:

```text
try:
    import httpx2 as httpx
except ModuleNotFoundError:
    try:
        import httpx
    except ModuleNotFoundError:
        raise RuntimeError("The starlette.testclient module requires the httpx2 package to be installed.")
    else:
        warn("Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.")
```

The local environment successfully imports `TestClient` only after `httpx2` is installed. `httpx` is not installed. Therefore, `requirements.txt` correctly includes `httpx2` for the current FastAPI/Starlette testing environment.

## Dependency Boundary

No new runtime product dependency was added for Phase 3.3. The recorded `httpx2` dependency exists to support real FastAPI `TestClient` HTTP tests introduced in Phase 3.2.

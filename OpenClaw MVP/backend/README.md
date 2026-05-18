# OpenClaw MVP Backend

FastAPI prototype for validating the OpenClaw runtime boundary.

Run locally:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

The current `OpenClawClient` is a mock adapter. It preserves the intended
backend boundary so the real OpenClaw API can replace it without changing the
frontend contract.

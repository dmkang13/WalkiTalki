# OpenClaw MVP Backend

FastAPI prototype for validating the real OpenClaw runtime boundary.

Prerequisite:

- Install the `openclaw` CLI and ensure it is on `PATH`.

Run locally:

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8001
```

The backend will:

- Start/check `openclaw gateway` on `OPENCLAW_GATEWAY_URL`, default
  `http://127.0.0.1:18789`.
- Trigger `openclaw models auth login --provider openai-codex`.
- Call the gateway's OpenAI-compatible `/v1/responses` endpoint.

Useful environment variables:

- `OPENCLAW_CLI`: CLI executable name, default `openclaw`
- `OPENCLAW_GATEWAY_URL`: default `http://127.0.0.1:18789`
- `OPENCLAW_MODEL`: default `openai-codex/gpt-5.4`
- `OPENCLAW_PROVIDER`: default `openai-codex`
- `OPENCLAW_GATEWAY_TOKEN`: optional bearer token for the gateway
- `OPENCLAW_WORKSPACE`: default `./openclaw_workspace`

import { readFileSync } from "node:fs";
import readline from "node:readline";
import { homedir } from "node:os";
import { join } from "node:path";
import { pathToFileURL } from "node:url";

function emit(event) {
  process.stdout.write(`${JSON.stringify(event)}\n`);
}

function moduleUrl(path) {
  return pathToFileURL(path).href;
}

function resolveAuthProfileId(config) {
  const requested = process.env.OPENCLAW_AUTH_PROFILE_ID?.trim();
  if (requested) return requested;

  const profiles = config?.auth?.profiles ?? {};
  for (const [profileId, profile] of Object.entries(profiles)) {
    if (profile?.provider === "openai-codex") return profileId;
  }

  return undefined;
}

function normalizeModelId(model) {
  const raw = model || process.env.OPENCLAW_MODEL || "openai-codex/gpt-5.4";
  return raw.replace(/^openai-codex\//, "");
}

function tokenExpiresAt(accessToken) {
  try {
    const [, payload] = accessToken.split(".");
    const decoded = JSON.parse(Buffer.from(payload, "base64url").toString("utf8"));
    return typeof decoded.exp === "number" ? decoded.exp * 1000 : 0;
  } catch {
    return 0;
  }
}

const home = homedir();
const piAiPath =
  process.env.OPENCLAW_PI_AI_MODULE ||
  join(home, ".openclaw/npm/node_modules/@earendil-works/pi-ai/dist/index.js");
const codexPath =
  process.env.OPENCLAW_CODEX_SHARED_CLIENT_MODULE ||
  join(home, ".openclaw/npm/node_modules/@openclaw/codex/dist/shared-client-Cr6W-a2G.js");
const [{ getModel, streamSimple }, { o: refreshCodexAppServerAuthTokens }] = await Promise.all([
  import(moduleUrl(piAiPath)),
  import(moduleUrl(codexPath)),
]);
const configPath = process.env.OPENCLAW_CONFIG_PATH || join(home, ".openclaw/openclaw.json");
const config = JSON.parse(readFileSync(configPath, "utf8"));
const agentDir = process.env.OPENCLAW_AGENT_DIR || join(home, ".openclaw/agents/main/agent");
const authProfileId = resolveAuthProfileId(config);
let cachedTokenInfo = null;
let cachedTokenExpiresAt = 0;

async function getAccessToken() {
  if (cachedTokenInfo?.accessToken && cachedTokenExpiresAt - Date.now() > 60_000) {
    return cachedTokenInfo.accessToken;
  }
  cachedTokenInfo = await refreshCodexAppServerAuthTokens({ agentDir, authProfileId, config });
  cachedTokenExpiresAt = tokenExpiresAt(cachedTokenInfo.accessToken);
  return cachedTokenInfo.accessToken;
}

async function handleRequest(input) {
  const requestId = input.requestId;
  if (input.type === "warm") {
    await getAccessToken();
    emit({ requestId, type: "warm_done" });
    return;
  }

  const apiKey = await getAccessToken();
  const model = getModel("openai-codex", normalizeModelId(input.model));
  if (!model) {
    throw new Error(`Unknown OpenAI Codex model: ${input.model}`);
  }

  const stream = streamSimple(
    model,
    {
      messages: [{ role: "user", content: input.prompt }],
    },
    {
      apiKey,
      reasoning: input.reasoning || "minimal",
      transport: input.transport || "sse",
      sessionId: input.sessionId,
    },
  );

  for await (const event of stream) {
    if (event?.type === "text_delta" && event.delta) {
      emit({ requestId, type: "delta", text: event.delta });
    } else if (event?.type === "error") {
      emit({
        requestId,
        type: "error",
        code: "codex_direct_stream_failed",
        message: event.error?.errorMessage || event.reason || "Codex direct stream failed.",
      });
    } else if (event?.type === "done") {
      const usage = event.message?.usage ?? {};
      emit({
        requestId,
        type: "done",
        usage: {
          input_tokens: usage.input ?? 0,
          output_tokens: usage.output ?? 0,
        },
      });
    }
  }
}

const input = readline.createInterface({
  input: process.stdin,
  crlfDelay: Infinity,
});

emit({ type: "ready" });

for await (const line of input) {
  if (!line.trim()) continue;
  let request = null;
  try {
    request = JSON.parse(line);
    await handleRequest(request);
  } catch (error) {
    emit({
      requestId: request?.requestId,
      type: "error",
      code: "codex_direct_stream_failed",
      message: error instanceof Error ? error.message : String(error),
    });
  }
}

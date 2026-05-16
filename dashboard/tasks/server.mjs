import { createServer } from "node:http";
import { readFile, stat } from "node:fs/promises";
import { extname, join, normalize, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(fileURLToPath(new URL(".", import.meta.url)));
const projectRoot = resolve(root, "..", "..");
const port = Number(process.env.PORT || 4173);
const host = process.env.HOST || "127.0.0.1";

const contentTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".jsonl": "application/x-ndjson; charset=utf-8",
};

const server = createServer(async (request, response) => {
  const url = new URL(request.url || "/", `http://${host}:${port}`);
  if (url.pathname === "/api/bot-status") {
    const status = await botStatus();
    response.writeHead(200, {
      "Cache-Control": "no-store",
      "Content-Type": "application/json; charset=utf-8",
    });
    response.end(JSON.stringify(status, null, 2));
    return;
  }

  const apiPath = apiFile(url.pathname);
  if (apiPath) {
    try {
      const file = await readFile(apiPath);
      response.writeHead(200, {
        "Cache-Control": "no-store",
        "Content-Type": contentTypes[extname(apiPath)] || "text/plain; charset=utf-8",
      });
      response.end(file);
    } catch {
      response.writeHead(404, { "Content-Type": "application/json; charset=utf-8" });
      response.end(JSON.stringify({ error: "not found" }));
    }
    return;
  }

  const pathname = url.pathname === "/" ? "/index.html" : url.pathname;
  const filePath = resolve(normalize(join(root, pathname)));

  if (!filePath.startsWith(root)) {
    response.writeHead(403);
    response.end("Forbidden");
    return;
  }

  try {
    const file = await readFile(filePath);
    response.writeHead(200, {
      "Cache-Control": "no-store",
      "Content-Type": contentTypes[extname(filePath)] || "application/octet-stream",
    });
    response.end(file);
  } catch {
    response.writeHead(404, { "Content-Type": "text/plain; charset=utf-8" });
    response.end("Not found");
  }
});

function apiFile(pathname) {
  const routes = {
    "/api/agent-status": ["data", "derived", "agent_status.json"],
    "/api/agent-events": ["data", "derived", "agent_events.jsonl"],
    "/api/project-status": ["data", "derived", "project_status.json"],
    "/api/training-feedback": ["data", "feedback", "training_feedback.jsonl"],
  };
  const parts = routes[pathname];
  if (!parts) {
    return null;
  }
  return resolve(projectRoot, ...parts);
}

async function botStatus() {
  const pidPath = resolve(projectRoot, "logs", "bot.pid");
  const logPath = resolve(projectRoot, "logs", "running_bot.log");
  const pid = await readPid(pidPath);
  const processAlive = pid !== null && isProcessAlive(pid);
  const logUpdatedAt = await fileUpdatedAt(logPath);
  const status = processAlive ? "running" : pid !== null ? "stale_pid" : "down";

  return {
    status,
    pid,
    pid_file: "logs/bot.pid",
    pid_file_exists: pid !== null,
    process_alive: processAlive,
    log_file: "logs/running_bot.log",
    log_file_exists: logUpdatedAt !== null,
    log_updated_at: logUpdatedAt,
    checked_at: new Date().toISOString(),
    message:
      status === "running"
        ? `Bot is running. PID=${pid}`
        : status === "stale_pid"
          ? `PID file exists but process is not alive. PID=${pid}`
          : "Bot is not running.",
  };
}

async function readPid(path) {
  try {
    const raw = (await readFile(path, "utf8")).trim();
    return /^\d+$/.test(raw) ? Number(raw) : null;
  } catch {
    return null;
  }
}

function isProcessAlive(pid) {
  try {
    process.kill(pid, 0);
    return true;
  } catch {
    return false;
  }
}

async function fileUpdatedAt(path) {
  try {
    return (await stat(path)).mtime.toISOString();
  } catch {
    return null;
  }
}

server.listen(port, host, () => {
  console.log(`Roadmap page: http://${host}:${port}/`);
});

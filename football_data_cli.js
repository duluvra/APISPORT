#!/usr/bin/env node
/**
 * Football-Data.org CLI (Node 18+)
 * --------------------------------
 * PASTE YOUR API KEY HERE:
 */
const API_KEY = "077ce3f148ea4b05a9dca097ff96948f";

const BASE = "https://api.football-data.org/v4";
import fs from "node:fs";
import path from "node:path";

if (!API_KEY || API_KEY.includes("PASTE_")) {
  console.error("❌ Set API_KEY at the top of the file.");
  process.exit(1);
}

// ---- tiny argv parser ----
function parseArgs(argv) {
  const args = {};
  let key = null;
  for (const token of argv.slice(2)) {
    if (token.startsWith("--")) {
      key = token.slice(2);
      args[key] = true;
    } else if (key) {
      args[key] = token;
      key = null;
    } else if (!args._) {
      args._ = [token];
    } else {
      args._.push(token);
    }
  }
  args._ ||= [];
  return args;
}

const args = parseArgs(process.argv);
const cmd = args._[0] || "help";

// ---- fetch helper with basic 429 handling ----
async function getJSON(url) {
  let attempt = 0;
  while (attempt < 3) {
    const res = await fetch(url, { headers: { "X-Auth-Token": API_KEY } });
    if (res.status === 429) {
      const wait = 1500 * (attempt + 1);
      console.warn(`⚠️  429 rate-limit. Backing off ${wait}ms…`);
      await new Promise(r => setTimeout(r, wait));
      attempt++;
      continue;
    }
    if (!res.ok) {
      const text = await res.text();
      throw new Error(`HTTP ${res.status} — ${text}`);
    }
    return res.json();
  }
  throw new Error("Too many 429s — try again later.");
}

function withQuery(url, params = {}) {
  const q = Object.entries(params)
    .filter(([,v]) => v !== undefined && v !== null && v !== true && v !== "")
    .map(([k,v]) => `${encodeURIComponent(k)}=${encodeURIComponent(v)}`)
    .join("&");
  return q ? `${url}?${q}` : url;
}

function saveIfRequested(data, out) {
  if (!out) return;
  const fp = path.resolve(process.cwd(), out);
  fs.writeFileSync(fp, JSON.stringify(data, null, 2), "utf8");
  console.log(`💾 Saved -> ${fp}`);
}

// ---- commands ----
async function cmdCompetitions() {
  const url = `${BASE}/competitions`;
  const data = await getJSON(url);
  console.log(JSON.stringify(data, null, 2));
  saveIfRequested(data, args.out);
}

async function cmdMatches() {
  const params = {
    dateFrom: args.dateFrom, // YYYY-MM-DD
    dateTo: args.dateTo,     // YYYY-MM-DD
    status: args.status,     // SCHEDULED|LIVE|FINISHED|TIMED|IN_PLAY|PAUSED|POSTPONED|SUSPENDED|CANCELED
    competitions: args.competition, // e.g. PL, BL1, PD, SA, FL1, CL, EL, etc. (comma for many)
  };
  const url = withQuery(`${BASE}/matches`, params);
  const data = await getJSON(url);
  console.log(JSON.stringify(data, null, 2));
  saveIfRequested(data, args.out);
}

async function cmdStandings() {
  const comp = args.competition || "PL";
  const season = args.season; // e.g. 2024
  const url = withQuery(`${BASE}/competitions/${comp}/standings`, { season });
  const data = await getJSON(url);
  console.log(JSON.stringify(data, null, 2));
  saveIfRequested(data, args.out);
}

async function cmdScorers() {
  const comp = args.competition || "PL";
  const limit = args.limit || 10;
  const season = args.season; // optional
  const url = withQuery(`${BASE}/competitions/${comp}/scorers`, { limit, season });
  const data = await getJSON(url);
  console.log(JSON.stringify(data, null, 2));
  saveIfRequested(data, args.out);
}

function printHelp() {
  console.log(`
Football-Data.org CLI (Node)

Usage:
  node football_data_cli.js competitions [--out data/competitions.json]
  node football_data_cli.js matches [--dateFrom YYYY-MM-DD] [--dateTo YYYY-MM-DD] [--status FINISHED] [--competition PL] [--out today.json]
  node football_data_cli.js standings --competition PL [--season 2024] [--out pl_standings.json]
  node football_data_cli.js scorers --competition PL [--limit 10] [--season 2024] [--out pl_scorers.json]

Notes:
- Free plan limit: ~10 requests/minute. Ako dobiješ 429, skripta će kratko sačekati i pokušati ponovo.
- Datumi su u ISO formatu (UTC).
`);
}

(async () => {
  try {
    if (cmd === "competitions") await cmdCompetitions();
    else if (cmd === "matches") await cmdMatches();
    else if (cmd === "standings") await cmdStandings();
    else if (cmd === "scorers") await cmdScorers();
    else printHelp();
  } catch (err) {
    console.error("❌ Error:", err.message);
    process.exit(1);
  }
})();
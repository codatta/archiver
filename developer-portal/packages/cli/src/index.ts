#!/usr/bin/env bun
/**
 * hb — Humanbased CLI
 *
 * Usage:
 *   hb auth set-key <key>       Store API key
 *   hb auth whoami              Verify key, show org
 *   hb verticals list           List available verticals
 *   hb verticals topics <slug>  Topics in a vertical
 *   hb frontiers list           List live data sources
 *   hb frontiers tasks <id>     List tasks in a frontier
 *   hb live pull <sub-id>       Pull live data (cursor-based)
 *   hb live adopt <sub-id> <id> Adopt a submission
 *   hb live dispute <sub-id> <id> Dispute a submission
 *   hb data pull <sub-id>       Pull pending items (simulated)
 *   hb data adopt <item-id>     Adopt a data item
 *   hb data dispute <item-id>   Dispute a data item
 *   hb billing balance          Check balance
 */

import {
  authSetKey, authWhoami,
  verticalsList, verticalTopics,
  frontiersList, frontierTasks,
  livePull, liveAdopt, liveDispute,
  dataPull, dataAdopt, dataDispute,
  billingBalance, subscriptionsList,
} from "./commands";

const args = process.argv.slice(2);
const cmd = args[0];
const sub = args[1];
const arg1 = args[2];
const arg2 = args[3];

function usage() {
  console.log(`
  hb — Humanbased CLI

  Auth:
    hb auth set-key <key>        Save your API key
    hb auth whoami               Verify key and show org info

  Frontiers (live production data):
    hb frontiers list [--all]           List live data sources (default: online only)
    hb frontiers tasks <frontier-id>    List tasks in a frontier

  Live Data (production — frontier subscriptions):
    hb live pull <sub-id> [--limit N] [--cursor C]   Pull submissions (cursor-based)
    hb live adopt <sub-id> <submission-id>            Adopt a submission
    hb live dispute <sub-id> <submission-id>          Dispute a submission

  Verticals (simulated data):
    hb verticals list            List available data verticals
    hb verticals topics <slug>   List topics in a vertical

  Subscriptions:
    hb subscriptions list        List deliveries

  Data (simulated — vertical subscriptions):
    hb data pull <sub-id> [--limit N]   Pull pending items (default: 50)
    hb data adopt <item-id>             Adopt a data item
    hb data dispute <item-id>           Dispute a data item

  Billing:
    hb billing balance           Check account balance

  Config:
    Key stored in ~/.humanbased/config.json
    Default API: https://api.humanbased.ai
`);
}

async function main() {
  if (!cmd || cmd === "help" || cmd === "--help" || cmd === "-h") {
    usage();
    return;
  }

  switch (cmd) {
    case "auth":
      if (sub === "set-key" && arg1) return authSetKey(arg1);
      if (sub === "whoami") return authWhoami();
      break;
    case "frontiers":
      if (sub === "list") return frontiersList(arg1 === "--all" ? "all" : "online");
      if (sub === "tasks" && arg1) return frontierTasks(arg1);
      break;
    case "live":
      if (sub === "pull" && arg1) {
        let limit = 50;
        let cursor: string | undefined;
        for (let i = 3; i < args.length; i += 2) {
          if (args[i] === "--limit") limit = parseInt(args[i + 1] ?? "50", 10);
          if (args[i] === "--cursor") cursor = args[i + 1];
        }
        return livePull(arg1, limit, cursor);
      }
      if (sub === "adopt" && arg1 && arg2) return liveAdopt(arg2, arg1);
      if (sub === "dispute" && arg1 && arg2) return liveDispute(arg2, arg1);
      break;
    case "verticals":
      if (sub === "list") return verticalsList();
      if (sub === "topics" && arg1) return verticalTopics(arg1);
      break;
    case "subscriptions":
      if (sub === "list") return subscriptionsList();
      break;
    case "data":
      if (sub === "pull" && arg1) {
        const limit = arg2 === "--limit" ? parseInt(args[4] ?? "50", 10) : 50;
        return dataPull(arg1, limit);
      }
      if (sub === "adopt" && arg1) return dataAdopt(arg1);
      if (sub === "dispute" && arg1) return dataDispute(arg1);
      break;
    case "billing":
      if (sub === "balance") return billingBalance();
      break;
  }

  console.error(`Unknown command: ${args.join(" ")}`);
  usage();
  process.exit(1);
}

main();

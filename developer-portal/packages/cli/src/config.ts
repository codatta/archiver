import { join } from "path";
import { homedir } from "os";

const CONFIG_DIR = join(homedir(), ".humanbased");
const CONFIG_FILE = join(CONFIG_DIR, "config.json");

type Config = {
  api_key?: string;
  api_url?: string;
};

export async function readConfig(): Promise<Config> {
  try {
    const file = Bun.file(CONFIG_FILE);
    if (await file.exists()) {
      return await file.json();
    }
  } catch {}
  return {};
}

export async function writeConfig(config: Config): Promise<void> {
  await Bun.$`mkdir -p ${CONFIG_DIR}`;
  await Bun.write(CONFIG_FILE, JSON.stringify(config, null, 2) + "\n");
}

export function getApiUrl(config: Config): string {
  return process.env.HB_API_URL ?? config.api_url ?? "https://api.humanbased.ai";
}

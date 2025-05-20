import fs from 'fs';
import path from 'path';
import readline from 'readline';

const SETTINGS_PATH = process.env.SETTINGS_PATH || path.join(
  'C:/Users/crypt/AppData/Roaming/Code/User/globalStorage/blackboxapp.blackboxagent/settings/blackbox_mcp_settings.json'
);
const BACKUP_DIR = process.env.BACKUP_DIR || path.dirname(SETTINGS_PATH);
const TIMESTAMP = new Date().toISOString().replace(/[:.]/g, '-');
const BACKUP_PATH = path.join(BACKUP_DIR, `blackbox_mcp_settings_${TIMESTAMP}.backup`);

const SERVER_CONFIGS = [
  {
    name: "codebase-memory-server",
    config: {
      command: "node",
      args: [
        "C:/Users/crypt/OneDrive/Documents/.blackbox/MCP/codebase-memory-server/build/index.js"
      ],
      env: {}
    }
  },
  {
    name: "smart-contract-helper",
    config: {
      command: "node",
      args: [
        "C:/Users/crypt/CascadeProjects/bumbot/smart_contract_helper.js"
      ],
      env: {}
    }
  },
  {
    name: "crypto-trading-helper",
    config: {
      command: "node",
      args: [
        "C:/Users/crypt/CascadeProjects/bumbot/crypto_trading_helper.js"
      ],
      env: {
        API_KEY: "your_api_key_here",
        API_SECRET: "your_api_secret_here"
      }
    }
  }
];

async function backupSettings() {
  if (!fs.existsSync(SETTINGS_PATH)) return;
  await fs.promises.copyFile(SETTINGS_PATH, BACKUP_PATH);
  console.log('Backup created at:', BACKUP_PATH);
}

async function rollbackSettings() {
  if (!fs.existsSync(BACKUP_PATH)) {
    console.error('No backup found to rollback.');
    return;
  }
  await fs.promises.copyFile(BACKUP_PATH, SETTINGS_PATH);
  console.log('Settings rolled back from backup.');
}

async function updateMcpSettings(options: { dryRun?: boolean; interactive?: boolean; verbose?: boolean }) {
  const { dryRun, interactive, verbose } = options;
  if (verbose) console.log('Starting MCP settings update...');

  try {
    if (!fs.existsSync(SETTINGS_PATH)) {
      console.error(`Settings file not found at: ${SETTINGS_PATH}`);
      return;
    }

    const settingsContent = await fs.promises.readFile(SETTINGS_PATH, 'utf-8');
    const settings = JSON.parse(settingsContent);

    if (!settings.mcpServers) {
      settings.mcpServers = {};
    }

    for (const { name, config } of SERVER_CONFIGS) {
      if (settings.mcpServers[name]) {
        if (verbose) console.log(`Server "${name}" already exists. Skipping.`);
        continue;
      }

      if (interactive) {
        const rl = readline.createInterface({
          input: process.stdin,
          output: process.stdout,
        });
        const answer = await new Promise<string>((resolve) =>
          rl.question(`Add "${name}" configuration? (y/n): `, resolve)
        );
        rl.close();
        if (typeof answer !== 'string' || answer.toLowerCase() !== 'y') {
          console.log(`Skipping "${name}" as per user input.`);
          continue;
        }
      }

      settings.mcpServers[name] = config;
      if (verbose) console.log(`Added configuration for "${name}".`);
    }

    if (dryRun) {
      console.log('Dry run mode enabled. No changes will be saved.');
      console.log('Updated settings preview:', JSON.stringify(settings, null, 2));
      return;
    }

    await backupSettings();
    await fs.promises.writeFile(
      SETTINGS_PATH,
      JSON.stringify(settings, null, 2),
      'utf-8'
    );

    console.log('MCP settings updated successfully!');
  } catch (error) {
    if (error && typeof error === 'object' && 'message' in error && typeof (error as any).message === 'string') {
      console.error('An error occurred while updating MCP settings:', (error as any).message);
    } else {
      console.error('An error occurred while updating MCP settings:', error);
    }
    await rollbackSettings();
  }
}

// Command-line arguments handling
const args = process.argv.slice(2);
const dryRun = args.includes('--dry-run');
const restore = args.includes('--restore');
const interactive = args.includes('--interactive');
const verbose = args.includes('--verbose');

console.log("Running MCP Settings Updater...");

if (args.includes('--help')) {
  console.log(`
Usage: node update_mcp_settings.ts [options]

Options:
  --dry-run       Simulate changes without modifying the file.
  --interactive   Confirm changes interactively before applying them.
  --restore       Restore the settings file from the last backup.
  --verbose       Log detailed information about each step.
  --help          Display this help message.
`);
} else if (restore) {
  rollbackSettings();
} else {
  updateMcpSettings({ dryRun, interactive, verbose });
}

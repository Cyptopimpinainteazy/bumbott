import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import readline from 'readline';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const TEMPLATES_DIR = path.join(__dirname, 'smart_contract_templates');

console.log("Running Smart Contract Helper...");

function generateContractTemplate(name) {
  const templatePath = path.join(TEMPLATES_DIR, 'basic_contract.sol');
  const outputPath = path.join(process.cwd(), `${name}.sol`);

  if (!fs.existsSync(templatePath)) {
    console.error('Template file not found:', templatePath);
    return;
  }

  const template = fs.readFileSync(templatePath, 'utf-8');
  const contract = template.replace(/{{ContractName}}/g, name);

  fs.writeFileSync(outputPath, contract);
  console.log('Smart contract generated at:', outputPath);
}

function runTests() {
  exec('npx hardhat test', (error, stdout, stderr) => {
    if (error) {
      console.error('Error running tests:', error.message);
      return;
    }
    console.log('Test Results:\n', stdout);
    if (stderr) console.error('Test Errors:\n', stderr);
  });
}

function deployContract(network) {
  exec(`npx hardhat run scripts/deploy.js --network ${network}`, (error, stdout, stderr) => {
    if (error) {
      console.error('Error deploying contract:', error.message);
      return;
    }
    console.log('Deployment Output:\n', stdout);
    if (stderr) console.error('Deployment Errors:\n', stderr);
  });
}

function confirmAndExecute(action, description, autoConfirm = false) {
  if (autoConfirm) {
    action();
    return;
  }
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });

  rl.question(`Are you sure you want to ${description}? (y/n): `, (answer) => {
    if (answer.toLowerCase() === 'y') {
      action();
    } else {
      console.log('Operation canceled.');
    }
    rl.close();
  });
}

// Command-line interface
const args = process.argv.slice(2);
const command = args[0];
const param = args[1];

switch (command) {
  case 'generate':
    confirmAndExecute(() => generateContractTemplate(param), `generate a smart contract named "${param}"`, process.argv.includes('--yes'));
    break;
  case 'test':
    confirmAndExecute(runTests, 'run smart contract tests', process.argv.includes('--yes'));
    break;
  case 'deploy':
    confirmAndExecute(() => deployContract(param), `deploy the contract to the "${param}" network`, process.argv.includes('--yes'));
    break;
  default:
    console.log(`
Usage:
  node smart_contract_helper.js generate <ContractName>  - Generate a new smart contract template
  node smart_contract_helper.js test                     - Run smart contract tests
  node smart_contract_helper.js deploy <network>         - Deploy contract to a specified network
  --yes                                                  - Auto-confirm prompts
`);
}

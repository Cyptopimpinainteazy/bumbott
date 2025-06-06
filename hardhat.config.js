require("@nomicfoundation/hardhat-toolbox");

/**
 * @type import('hardhat/config').HardhatUserConfig
 */
module.exports = {
  solidity: "0.8.18",
  paths: {
    sources: "./smart_contract_templates",
    tests: "./test",
    cache: "./cache",
    artifacts: "./artifacts"
  },
  networks: {
    hardhat: {
        chainId: 1337,
      },
      localhost: {
        url: "http://127.0.0.1:8545"
}
    }
  }
};

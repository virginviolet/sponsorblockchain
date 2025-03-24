# region Imports
# Standard Library
from pathlib import Path
import json

# Local
if __package__ is None or __package__ == "":
    from sponsorblockchain_type_aliases import BlockchainConfig
else:
    from sponsorblockchain.sponsorblockchain_type_aliases import (
        BlockchainConfig)
# endregion

# region Blockchain config


class BlockchainConfiguration:
    # IMPROVE Make all paths start with the package name (I have to move files on my server first)
    # The path has to be relative to the package if the blockchain is running
    # as a package in a separate thread
    def __init__(self,
                 blockchain_config_path: str = (
                     f"data/blockchain_configuration.json"),
                 blockchain_path: str | None = None,
                 transactions_path: str | None = None) -> None:
        if __package__ is not None and __package__ != "":
            blockchain_config_path = f"{__package__}/{blockchain_config_path}"
        self.blockchain_config_path: Path = Path(blockchain_config_path)
        
        # Set default configuration
        if blockchain_path is None or transactions_path is None:
            if blockchain_path is None:
                blockchain_path = "data/blockchain.json"
            if transactions_path is None:
                transactions_path = "data/transactions.txt"
            if __package__ is not None and __package__ != "":
                # When the blockchain is running as a package in a
                # separate thread, the blockchain and transactions will be
                # in a subdirectory of the main project directory.
                # Therefore, we need to go up a directory to access the
                # blockchain and transactions.
                package_depth: int = __package__.count(".") + 1
                blockchain_path = f"{'../' * package_depth}{blockchain_path}"
                transactions_path = f"{'../' * package_depth}{transactions_path}"
            self.default_configuration: BlockchainConfig = {
                "blockchain_path": blockchain_path,
                "transactions_path": transactions_path
        }
        self.configuration: BlockchainConfig = self.read()
        attributes_set = False
        while not attributes_set:
            try:
                blockchain_path_raw: str = (
                    self.configuration["blockchain_path"])
                self.blockchain_path: Path = Path(blockchain_path_raw)
                transactions_path_raw: str = (
                    self.configuration["transactions_path"])
                self.transactions_path: Path = Path(transactions_path_raw)
                attributes_set = True
            except KeyError:
                self.configuration = self.default_configuration
                self.create()

    def read(self) -> BlockchainConfig:
        file_exists: bool = self.blockchain_config_path.exists()
        file_empty: bool = (
            file_exists and self.blockchain_config_path.stat().st_size == 0)
        print(f"File exists: {file_exists}")
        print(f"File empty: {file_empty}")
        if file_empty or not file_exists:
            print("Blockchain configuration not found.")
            self.create()
            return self.default_configuration
        with open(self.blockchain_config_path, "r") as file:
            return json.load(file)
        return self.default_configuration

    def create(self) -> None:
        print("Creating blockchain configuration")
        directories: Path = self.blockchain_config_path.parent
        directories.mkdir(parents=True, exist_ok=True)
        with open(self.blockchain_config_path, "w") as file:
            json.dump(self.default_configuration, file, indent=4)
# endregion

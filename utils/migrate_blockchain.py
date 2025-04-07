# This script cannot be run directly with the current structure, because it
# depends on 'block', and 'block' needs to import type aliases from
# a parent directory

# region Imports
# Standard library
import os
import json
from pathlib import Path
from typing import TypedDict, Dict, List

# Third party
import lazyimports

# Local
try:
    # For some reason, this doesn't work when blockchain.py is imported like
    # modules/blockchain.py <- modules/__init__.py <- sponsorblockchain_main.py
    with lazyimports.lazy_imports(
            "..sponsorblockchain_type_aliases:BlockData",
            "..sponsorblockchain_type_aliases:BlockModel"):
        from ..sponsorblockchain_type_aliases import (BlockData, BlockModel)
    with lazyimports.lazy_imports(
            "..models.block:Block"):
        from ..models.block import Block
    with lazyimports.lazy_imports(
            "..models.blockchain:Blockchain"):
        from ..models.blockchain import Blockchain
except ImportError:
    try:
        # Running the blockchain directly from a script
        # in the blockchain root directory
        with lazyimports.lazy_imports(
                "sponsorblockchain_type_aliases:BlockData",
                "sponsorblockchain_type_aliases:BlockModel"):
            from sponsorblockchain_type_aliases import BlockData, BlockModel
        with lazyimports.lazy_imports("models.block:Block"):
            from models.block import Block
        with lazyimports.lazy_imports("models.blockchain:Blockchain"):
            from models.blockchain import Blockchain
    except ImportError:
        # Running the blockchain as a package
        with lazyimports.lazy_imports(
                "sponsorblockchain.sponsorblockchain_type_aliases:BlockData",
                "sponsorblockchain.sponsorblockchain_type_aliases:BlockModel"):
            from sponsorblockchain.sponsorblockchain_type_aliases import (
                BlockData, BlockModel)
        with lazyimports.lazy_imports(
                "sponsorblockchain.models.block:Block"):
            from sponsorblockchain.models.block import Block
        with lazyimports.lazy_imports(
                "sponsorblockchain.models.blockchain:Blockchain"):
            from sponsorblockchain.models.blockchain import Blockchain
# endregion

# region Type aliases


class TransactionLegacy(TypedDict):
    """
    Deprecated and replaced by Transaction.
    Used in BlockDataLegacy.
    """
    sender: str
    receiver: str
    amount: int
    method: str

BlockDataLegacy = List[str | Dict[str, TransactionLegacy]]

class BlockDict(TypedDict):
    """
    Deprecated and replaced by BlockModel. Formerly used for
    deserializing blocks from json. It would then be converted to a Block.
    """
    index: int
    timestamp: float
    data: BlockData | BlockDataLegacy
    previous_block_hash: str
    nonce: int
    block_hash: str
# endregion

# region Legacy load block


def dict_to_block(block_dict: BlockDict) -> Block:
    block_data: BlockData | BlockDataLegacy = block_dict["data"]
    block = Block(
        index=block_dict["index"],
        timestamp=block_dict["timestamp"],
        data=block_data,
        previous_block_hash=block_dict["previous_block_hash"],
        nonce=block_dict["nonce"],
        block_hash=block_dict["block_hash"]
    )
    print(f"Created block: {block}")
    return block


def legacy_load_block(json_block: str) -> Block:
    # Deserialize JSON data to a dictionary
    # Create a new block object from the dictionary
    block_dict: BlockDict = json.loads(json_block)
    block: Block = dict_to_block(block_dict=block_dict)
    return block
# endregion

# region Migrate chain


def migrate_blockchain(blockchain: Blockchain) -> Blockchain:
    """
    Migrates the blockchain. All the hashes changed when Pydantic models were
    added. This function recreates the blockchain from the old file and
    re-calculates the hashes.
    The old blockchain file is renamed to _blockchain_old.json and a new
    blockchain file is created.
    """
    print("Migrating blockchain...")
    # Check if the blockchain file exists
    if not os.path.exists(blockchain.blockchain_path):
        raise FileNotFoundError(
            f"Blockchain file {blockchain.blockchain_path} does not exist.")
    # Check if the blockchain file is empty
    if os.stat(blockchain.blockchain_path).st_size == 0:
        raise ValueError(
            "Old blockchain file is empty. Cannot migrate.")

    # copy the old blockchain file to _blockchain_old.json
    old_blockchain_path: Path = blockchain.blockchain_path
    old_blockchain_backup_path: Path = old_blockchain_path.with_name(
        old_blockchain_path.stem + "_old" + old_blockchain_path.suffix)
    print(f"Backing up old blockchain file to "
          f"'{old_blockchain_backup_path}'")
    os.rename(blockchain.blockchain_path, old_blockchain_backup_path)
    blockchain.blockchain_path = old_blockchain_backup_path
    new_blockchain = Blockchain(
        blockchain_path=str(old_blockchain_path),
        transactions_path=str(blockchain.transactions_path)
    )
    # Create a new blockchain file
    print("A new blockchain file will be created at "
          f"'{new_blockchain.blockchain_path}'.")
    with open(new_blockchain.blockchain_path, "w") as new_file:
        # Open the old blockchain file
        current_block: None | Block = None
        previous_block: None | Block = None
        with open(old_blockchain_backup_path, "r") as old_file:
            for line in old_file:
                # Load the line as a block
                try:
                    current_block = legacy_load_block(json_block=line)
                except json.JSONDecodeError:
                    print("Invalid JSON in the blockchain file.")
                    continue
                current_block_data: BlockData | BlockDataLegacy = (
                    current_block.data)
                # Write the block to the new file
                loaded_block_model = BlockModel(
                    index=current_block.index,
                    timestamp=current_block.timestamp,
                    data=current_block_data,
                    previous_block_hash=current_block.previous_block_hash,
                    nonce=current_block.nonce,
                    block_hash=current_block.block_hash
                )
                block_data_parsed: BlockData = blockchain.parse_block_data(
                    loaded_block_model.data)
                previous_block_hash: str
                if not previous_block:
                    previous_block_hash = loaded_block_model.block_hash
                else:
                    previous_block_hash = previous_block.block_hash
                new_block = Block(
                    index=loaded_block_model.index,
                    timestamp=loaded_block_model.timestamp,
                    data=block_data_parsed,
                    previous_block_hash=previous_block_hash
                )
                new_block_data: BlockData | BlockDataLegacy = new_block.data
                new_block_model_instance = BlockModel(
                    index=new_block.index,
                    timestamp=new_block.timestamp,
                    data=new_block_data,
                    previous_block_hash=new_block.previous_block_hash,
                    nonce=new_block.nonce,
                    block_hash=new_block.block_hash
                )
                block_json: str = new_block_model_instance.model_dump_json()
                print(f"New block data:        {new_block.data}")
                print(f"New block data (json): {block_json}")
                new_file.write(block_json + "\n")
                previous_block = new_block
    print("Blockchain migrated.")
    return new_blockchain
# endregion

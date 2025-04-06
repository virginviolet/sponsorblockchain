# region Imports
# Standard library
import hashlib
import time

# Third party
import lazyimports

# Local
try:
    # For some reason, this doesn't work when block.py is imported like
    # modules/block.py <- modules/__init__.py <- modules/blockchain.py <- sponsorblockchain_main.py
    with lazyimports.lazy_imports(
            "..sponsorblockchain_type_aliases:BlockData"):
        from ..sponsorblockchain_type_aliases import BlockData
except ImportError:
    try:
        # Running the blockchain directly from a script
        # in the blockchain root directory
        with lazyimports.lazy_imports(
                "sponsorblockchain_type_aliases:BlockData"):
            from sponsorblockchain_type_aliases import BlockData
    except ImportError:
        # Running the blockchain as a package
        with lazyimports.lazy_imports(
                "sponsorblockchain.sponsorblockchain_type_aliases:BlockData"):
            from sponsorblockchain.sponsorblockchain_type_aliases import (
                BlockData)
# endregion

# region Block class


class Block:
    def __init__(self,
                 index: int,
                 data: BlockData,
                 previous_block_hash: str,
                 timestamp: float = 0.0,
                 nonce: int = 0,
                 block_hash: str | None = None) -> None:
        self.index: int = index
        self.timestamp: float = timestamp if timestamp else time.time()
        self.data: BlockData = data
        self.previous_block_hash: str = previous_block_hash
        self.nonce: int = nonce
        self.block_hash: str = (
            block_hash if block_hash else self.calculate_hash())

    def calculate_hash(self) -> str:
        block_contents: str = f"{self.index}{self.timestamp}{
            self.data}{self.previous_block_hash}{self.nonce}"
        hash_string: str = hashlib.sha256(block_contents.encode()).hexdigest()
        # print(f"block_hash: {hash_string}")
        return hash_string

    def mine_block(self, difficulty: int) -> None:
        target: str = "0" * difficulty  # Create a string of zeros
        while not self.block_hash.startswith(target):
            self.nonce += 1
            self.block_hash = self.calculate_hash()
# endregion

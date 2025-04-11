# region Imports
# Standard Library
from typing import List, Dict

# Third party
from pydantic import BaseModel
# endregion


# region Types

class Transaction(BaseModel):
    """
    Pydantic model for a transaction in the blockchain, used for deserializing
    transactions in block data.
    """
    sender: str
    receiver: str
    amount: int
    method: str

    class Config:
        extra: str = "forbid"


BlockData = List[str | Dict[str, Transaction]]


class BlockModel(BaseModel):
    """
    Pydantic model for a block in the blockchain, used for serializing and
    deserializing blocks.
    """
    index: int
    timestamp: float
    data: BlockData
    previous_block_hash: str
    nonce: int
    block_hash: str

    class Config:
        extra: str = "forbid"
# endregion

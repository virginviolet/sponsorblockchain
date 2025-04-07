# region Imports
# Standard Library
from typing import List, Dict, TypedDict

# Third party
from pydantic import BaseModel
# endregion


# region Data classes

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


class TransactionLegacy(TypedDict):
    """
    Deprecated and replaced by Transaction.
    Used in BlockDataLegacy.
    """
    sender: str
    receiver: str
    amount: int
    method: str


BlockData = List[str | Dict[str, Transaction]]
BlockDataLegacy = List[str | Dict[str, TransactionLegacy]]


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

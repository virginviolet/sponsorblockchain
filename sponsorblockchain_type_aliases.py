# region Imports
# Standard Library
from typing import List, Dict, TypedDict

# Third party
from pydantic import BaseModel
# endregion


# region Data classes

class Transaction(BaseModel):
    sender: str
    receiver: str
    amount: int
    method: str

    class Config:
        extra: str = "forbid"

class TransactionOld(TypedDict):
    sender: str
    receiver: str
    amount: int
    method: str

BlockData = List[str | Dict[str, Transaction]]
BlockDataWithSerializedTransactions = List[str | Dict[str, str]]
BlockDataOld = List[str | Dict[str, TransactionOld]]


class BlockModel(BaseModel):
    index: int
    timestamp: float
    data: BlockData | BlockDataOld
    previous_block_hash: str
    nonce: int
    block_hash: str

    class Config:
        extra: str = "forbid"

class BlockDict(TypedDict):
    index: int
    timestamp: float
    data: BlockData | BlockDataWithSerializedTransactions | BlockDataOld
    previous_block_hash: str
    nonce: int
    block_hash: str
# endregion

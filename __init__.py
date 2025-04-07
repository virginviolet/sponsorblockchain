# Standard Library

# Third party
import lazyimports

# Local
with lazyimports.lazy_imports(
        ".sponsorblockchain_type_aliases:Transaction",
        ".sponsorblockchain_type_aliases:TransactionLegacy",
        ".sponsorblockchain_type_aliases:BlockData",
        ".sponsorblockchain_type_aliases:BlockDataLegacy",
        ".sponsorblockchain_type_aliases:BlockModel",
        ".sponsorblockchain_type_aliases:BlockDict"):
    from .sponsorblockchain_type_aliases import (
        Transaction, TransactionLegacy, BlockData, BlockModel, BlockDataLegacy,
        BlockDict)
with lazyimports.lazy_imports(
        ".sponsorblockchain_main:app",
        ".sponsorblockchain_main:blockchain",
        ".sponsorblockchain_main:SERVER_TOKEN"):
    from .sponsorblockchain_main import app, blockchain, SERVER_TOKEN

with lazyimports.lazy_imports(
        ".start_sponsorblockchain:start_flask_app_waitress",
        ".start_sponsorblockchain:start_flask_app"):
    from .start_sponsorblockchain import (start_flask_app_waitress,
                                          start_flask_app)

__all__: list[str] = [
    "app",
    "blockchain",
    "SERVER_TOKEN",
    "start_flask_app_waitress",
    "start_flask_app",
    "Transaction",
    "TransactionLegacy",
    "BlockDict",
    "BlockData",
    "BlockModel",
    "BlockDataLegacy"
]

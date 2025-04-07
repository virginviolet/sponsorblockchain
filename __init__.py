# Standard Library

# Third party
import lazyimports

# Local
with lazyimports.lazy_imports(
        ".sponsorblockchain_type_aliases:Transaction",
        ".sponsorblockchain_type_aliases:BlockData",
        ".sponsorblockchain_type_aliases:BlockModel"):
    from .sponsorblockchain_type_aliases import (
        Transaction, BlockData, BlockModel)
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
with lazyimports.lazy_imports(
        ".utils.migrate_blockchain:TransactionLegacy",
        ".utils.migrate_blockchain:BlockDict",
        ".utils.migrate_blockchain:BlockDataLegacy"
        ".utils.migrate_blockchain:migrate_blockchain"):
    from .utils.migrate_blockchain import (TransactionLegacy, BlockDict,
                                           BlockDataLegacy, migrate_blockchain)

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
    "BlockDataLegacy",
    "migrate_blockchain"
]

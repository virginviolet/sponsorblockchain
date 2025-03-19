# Standard Library
from typing import TYPE_CHECKING

# Third party
import lazyimports
if TYPE_CHECKING:
    from .sponsorblockchain_type_aliases import TransactionDict, BlockDict

# Local
with lazyimports.lazy_imports(
        ".sponsorblockchain_main:app",
        ".sponsorblockchain_main:blockchain",
        ".sponsorblockchain_main:SERVER_TOKEN",
        ".start_sponsorblockchain:start_flask_app_waitress",
        ".start_sponsorblockchain:start_flask_app"):
    from .sponsorblockchain_main import app, blockchain, SERVER_TOKEN
    from .start_sponsorblockchain import (start_flask_app_waitress,
                                          start_flask_app)

__all__: list[str] = [
    "app",
    "blockchain",
    "SERVER_TOKEN",
    "start_flask_app_waitress",
    "start_flask_app",
    "TransactionDict",
    "BlockDict",
]

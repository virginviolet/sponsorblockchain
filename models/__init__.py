# Import
# Standard library
from typing import List

# Third party
import lazyimports

# Local
with lazyimports.lazy_imports(".block:Block",
                              ".blockchain:Blockchain"):
    from .block import Block
    from .blockchain import Blockchain

# Export classes
__all__: List[str] = ["Block", "Blockchain"]

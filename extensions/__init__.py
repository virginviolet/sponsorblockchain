# Imports
# Third party
import lazyimports

# Local
with lazyimports.lazy_imports(
        "discord_coin_bot_extension:register_routes"):
    from .discord_coin_bot_extension import register_routes

__all__: list[str] = ["register_routes"]

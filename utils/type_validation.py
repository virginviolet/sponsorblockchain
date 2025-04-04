# region Imports
# Standard library
from typing import Any, Tuple, Dict, List, cast, TYPE_CHECKING

# Local
if TYPE_CHECKING:
    # For type checking only
    from sponsorblockchain_type_aliases import TransactionDict
# endregion

# region Validate tx dict


def validate_transaction_dict(
        transaction: Any) -> Tuple[bool, str]:
    """
    Validates the structure of a transaction dictionary.

    Args:
        transaction: The transaction dictionary to validate.

    Returns:
        bool: True if the transaction dictionary is valid, False otherwise.
    """
    if not isinstance(transaction, dict):
        message = "Transaction must be a dictionary."
        return False, message
    else:
        transaction = cast(dict[Any, Any], transaction)
    required_fields: list[str | tuple[str, str]] = [
        ("sender", "sender_unhashed"),
        ("receiver", "receiver_unhashed"),
        "amount",
        "method"
    ]
    message: str
    for field in required_fields:
        if isinstance(field, tuple):
            if all(transaction.get(f, "") == "" for f in field):
                message = f"{' or '.join(field)} is required."
                return False, message
        else:
            if transaction.get(field, "") == "":
                message = f"{field} is required."
                return False, message
    if not isinstance(transaction.get("amount"), int):
        try:
            transaction["amount"] = int(transaction["amount"])
        except ValueError:
            message = "Amount must be an integer."
            return False, message
    # Ensure no extra fields are present
    allowed_fields: set[str] = {
        "sender", "sender_unhashed", "receiver", "receiver_unhashed",
        "amount", "method"}
    extra_fields: set[Any] = set(transaction.keys()) - allowed_fields
    if extra_fields:
        message = (f"Extra fields are not allowed: "
                   f"{', '.join(extra_fields)}")
        return False, message
    message = "TransactionDict is valid."
    cast(TransactionDict, transaction)
    print(message)
    return True, message
# endregion

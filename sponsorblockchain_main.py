# region Imports
# Standard Library
import os
import json
from sys import exit as sys_exit
from typing import Tuple, Dict, List, Any, Callable, cast, TYPE_CHECKING

# Third party
import lazyimports
from flask import Flask, request, jsonify, Response, send_file
from dotenv import load_dotenv

# Local
register_routes: Callable[[Flask], None] | None = None
if __name__ == "__main__" or __package__ == "":
    # Running as a script or from the parent directory
    if TYPE_CHECKING:
        from models.block import Block
    with lazyimports.lazy_imports(
            "models.blockchain:Blockchain"):
        from models.blockchain import Blockchain
else:
    # Running as a package
    if TYPE_CHECKING:
        from sponsorblockchain.models.block import Block
    sponsorblockcasino_extension_register_routes_import: str = (
        "sponsorblockchain.extensions.sponsorblockcasino_extension:")
    with lazyimports.lazy_imports(
            "sponsorblockchain.models.blockchain:Blockchain",
            sponsorblockcasino_extension_register_routes_import):
        from sponsorblockchain.models.blockchain import Blockchain
        from sponsorblockchain.extensions.sponsorblockcasino_extension import (
            register_routes)
# endregion

# region Init
app = Flask(__name__)
# Load .env file for the server token
load_dotenv()
SERVER_TOKEN: str | None = os.getenv('SERVER_TOKEN')
# Register the API routes from extension
if __package__ == "sponsorblockchain" and register_routes:
    register_routes(app)
else:
    print("Will not register extension routes because "
          "the blockchain is not running as a package.")

blockchain: Blockchain = Blockchain()
# The send_file method does not work for me
# without resolving the paths (Flask bug?)
blockchain_path_resolved: str = str(blockchain.blockchain_path.resolve())
transactions_path_resolved: str = str(blockchain.transactions_path.resolve())
# endregion

# region API Routes


@app.route("/add_block", methods=["POST"])
# API Route: Add a new block to the blockchain
def add_block() -> Tuple[Response, int]:
    print("Received request to add a block.")
    message: str | None = None
    token: str | None = request.headers.get("token")
    if not token:
        message = "Token is required."
        print(message)
        return jsonify({"message": message}), 400
    if token != SERVER_TOKEN:
        message = "Invalid token."
        print(message)
        return jsonify({"message": message}), 400

    try:
        request_data: Any = request.get_json()
    except Exception as e:
        message = f"Request data could not be retrieved: {e}"
        print(message)
        return jsonify({"message": message}), 400
    if "data" not in request_data:
        message = "'data' key not found in request."
        print(message)
        return jsonify({"message": message}), 400
    data: Any = request.get_json().get("data")
    if not data:
        message = "The 'data' key is empty."
        print(message)
        return jsonify({"message": message}), 400
    # IMPROVE Make data a named tuple?
    if not isinstance(data, list) and (
            all(isinstance(item, (str, dict)) for item in data)):
        message = "Data must be a list of strings or dictionaries."
        print(message)
        return jsonify({"message": message}), 400
    # Ensure that no fields are missing in transactions
    should_send_400: bool = False
    if not isinstance(data, list):
        message = "Data must be a list."
        should_send_400 = True
    data = cast(List[Any], data)
    if len(data) == 0:
        message = "Data is empty."
        should_send_400 = True
    for data_unit in data:
        data_unit: Any
        if not isinstance(data_unit, dict):
            continue
        data_unit = cast(dict[Any, Any], data_unit)
        if data_unit.get("transaction", "") == "":
            continue
        data_unit = cast(dict[str, Any], data_unit)
        transaction: Any = data_unit.get("transaction")
        if not isinstance(transaction, dict):
            message = "Transaction must be a dictionary."
            should_send_400 = True
            break
        data = cast(dict[str, Dict[Any, Any]], data_unit)
        transaction = cast(dict[Any, Any], transaction)
        required_fields: list[str | tuple[str, str]] = [
            ("sender", "sender_unhashed"),
            ("receiver", "receiver_unhashed"),
            "amount",
            "method"
        ]
        for field in required_fields:
            if isinstance(field, tuple):
                if all(transaction.get(f, "") == "" for f in field):
                    message = f"{' or '.join(field)} is required."
                    should_send_400 = True
                    break
            else:
                if transaction.get(field, "") == "":
                    message = f"{field} is required."
                    should_send_400 = True
                    break
        if should_send_400:
            break
        if not isinstance(transaction.get("amount"), int):
            try:
                transaction["amount"] = int(transaction["amount"])
            except ValueError:
                message = "amount must be an integer."
                should_send_400 = True
                break
        # Ensure no extra fields are present
        allowed_fields: set[str] = {
            "sender", "sender_unhashed", "receiver", "receiver_unhashed", "amount", "method"}
        extra_fields: set[Any] = set(transaction.keys()) - allowed_fields
        if extra_fields:
            message = (f"Extra fields are not allowed: "
                       f"{', '.join(extra_fields)}")
            should_send_400 = True
            break
    if should_send_400:
        if message is None:
            raise ValueError("message is None.")
        print(message)
        return jsonify({"message": message}), 400
    try:
        blockchain.add_block(data)
        last_block: None | Block = blockchain.get_last_block()
        if last_block and last_block.data != data:
            message = "Block could not be added."
            print(message)
            return jsonify({"message": message}), 500
        else:
            message = "Block added successfully."
            print(message)
            return jsonify({"message": message,
                            "block": last_block.__dict__}), 200
    except Exception as e:
        message = f"An error occurred: {e}"
        print(message)
        return jsonify({"message": message}), 500


@app.route("/get_chain", methods=["GET"])
# API Route: Get the blockchain
def get_chain() -> Tuple[Response, int]:
    print("Received request to get the blockchain.")
    print("Retrieving blockchain...")
    with open(blockchain_path_resolved, "r") as file:
        chain_data: list[dict[str, Any]] = [
            json.loads(line) for line in file.readlines()]
        print("Blockchain retrieved.")
        print("Blockchain will be returned.")
        return jsonify({"length": len(chain_data), "chain": chain_data}), 200


@app.route("/download_chain", methods=["GET"])
# API Route: Download the blockchain
def download_chain() -> Tuple[Response | Any, int]:
    print("Received request to download the blockchain.")
    file_exists: bool = os.path.exists(blockchain_path_resolved)
    if not file_exists:
        message = "No blockchain found."
        print(message)
        return jsonify({"message": message}), 404
    else:
        print("Blockchain will be sent as a file.")
        return send_file(
            blockchain_path_resolved,
            as_attachment=True), 200


@app.route("/get_last_block", methods=["GET"])
# API Route: Get the last block of the blockchain
def get_last_block() -> Tuple[Response, int]:
    print("Received request to get the last block.")
    last_block: None | Block = blockchain.get_last_block()
    if last_block:
        print("Last block found.")
        print("Last block will be returned.")
        return jsonify({"block": last_block.__dict__}), 200
    else:
        message = "No blocks found."
        print(message)
        return jsonify({"message": message}), 404


@app.route("/validate_chain", methods=["GET"])
# API Route: Validate the blockchain
def validate_chain() -> Tuple[Response | Dict[str, str], int]:
    print("Received request to validate the blockchain.")
    is_valid: bool = blockchain.is_chain_valid()
    message: str = "The blockchain is valid." if is_valid else (
        "The blockchain is not valid.")
    print(message)
    return jsonify({"message": message}), 200


@app.route("/validate_transactions", methods=["GET"])
# API Route: Validate the blockchain
def validate_transactions() -> Tuple[Response | Dict[str, str], int]:
    token: str | None = request.headers.get("token")
    repair: bool = request.args.get("repair", "false").lower() == "true"
    force: bool = request.args.get("force", "false").lower() == "true"
    message: str
    is_valid: bool
    if token:
        message, is_valid = blockchain.is_transactions_file_valid(
            repair, force)
    else:
        message, is_valid = blockchain.is_transactions_file_valid(force)

    return jsonify({"message": message}), 200 if is_valid else 400


@app.route("/shutdown", methods=["POST"])
# API Route: Shutdown the Flask app
def shutdown() -> Tuple[Response, int]:
    print("Received request to shutdown the blockchain app.")
    try:
        message: str
        token: str | None = request.headers.get("token")
        if not token:
            message = "Token is required."
            print(message)
            return jsonify({"message": message}), 400
        if token != SERVER_TOKEN:
            message = "Invalid token."
            print(message)
            return jsonify({"message": message}), 400
    except Exception as e:
        message = f"An error occurred: {e}"
        print(message)
        return jsonify({"message": message}), 500

    print("The blockchain app will now exit.")
    sys_exit(0)


@app.route("/download_transactions", methods=["GET"])
# API Route: Download the transactions file
def download_transactions() -> Tuple[Response | Any, int]:
    print("Received request to download the transactions file.")
    file_exists: bool = os.path.exists(transactions_path_resolved)
    if not file_exists:
        message = "No transactions found."
        print(message)
        return jsonify({"message": message}), 404
    else:
        print("Transactions file will be sent as a file.")
        return send_file(
            transactions_path_resolved,
            as_attachment=True), 200


@app.route("/get_balance", methods=["GET"])
# API Route: Get the balance of a user
def get_balance() -> Tuple[Response, int]:
    print("Received request to get balance for a user.")
    user: str | None = request.args.get(str("user"))
    user_unhashed: str | None = request.args.get("user_unhashed")
    message: str

    # Debugging: Print the received query parameters
    print(f"Received user: {user}")
    print(f"Received user_unhashed: {user_unhashed}")

    if not user and not user_unhashed:
        message = "User or user_unhashed is required."
        print(message)
        return jsonify({"message": message}), 400
    elif user and user_unhashed:
        message = "Only one of user or user_unhashed is allowed."
        print(message)
        return jsonify({"message": message}), 400

    # Validate the transactions file
    blockchain.is_transactions_file_valid()

    # Retrieve the balance
    if user:
        balance: int | None = blockchain.get_balance(user=user)
    else:
        balance: int | None = blockchain.get_balance(
            user_unhashed=user_unhashed)

    # Debugging: Print the retrieved balance
    print(f"Retrieved balance: {balance}")

    # Return the balance or an error message
    if balance is not None:
        # Convert to int64 to int for JSON serialization
        balance = int(balance)
        print("Balance will be returned.")
        return jsonify({"balance": balance}), 200
    else:
        message = "No transactions found for user."
        print(message)
        return jsonify({"message": message}), 404
# endregion


# region Run Flask app
if __name__ == "__main__":
    load_dotenv()
    app.run(port=8080, debug=True)
# endregion

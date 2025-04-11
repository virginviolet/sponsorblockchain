# region Imports
# Standard Library
import os
import json
from sys import exit as sys_exit
from typing import Tuple, Dict, Any, Callable, TYPE_CHECKING

# Third party
import lazyimports
from flask import Flask, request, jsonify, Response, send_file
from dotenv import load_dotenv
from pydantic import ValidationError

# Local
register_routes: Callable[[Flask], None] | None = None
if __name__ == "__main__" or __package__ == "":
    # Running as a script or from the parent directory
    if TYPE_CHECKING:
        from models.block import Block
    with lazyimports.lazy_imports(
            "sponsorblockchain_type_aliases:BlockData",
            "sponsorblockchain_type_aliases:BlockModel",):
        from sponsorblockchain.sponsorblockchain_types import (BlockData, BlockModel)
    with lazyimports.lazy_imports(
            "models.blockchain:Blockchain"):
        from models.blockchain import Blockchain
else:
    # Running as a package
    if TYPE_CHECKING:
        from sponsorblockchain.models.block import Block
    with lazyimports.lazy_imports(
            "sponsorblockchain.sponsorblockchain_type_aliases:BlockData",
            "sponsorblockchain.sponsorblockchain_type_aliases:BlockDataLegacy",
            "sponsorblockchain.sponsorblockchain_type_aliases:BlockModel"):
        from sponsorblockchain.sponsorblockchain_types import (
            BlockData, BlockModel)
    with lazyimports.lazy_imports(
            "sponsorblockchain.models.blockchain:Blockchain"):
        from sponsorblockchain.models.blockchain import Blockchain
    sponsorblockcasino_extension_register_routes_import: str = (
        "sponsorblockchain.extensions.sponsorblockcasino_extension:"
        "register_routes")
    with lazyimports.lazy_imports(
            sponsorblockcasino_extension_register_routes_import):
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
# blockchain = migrate_blockchain(blockchain)
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
    # Validate the data
    try:
        data_parsed: BlockData = (
            blockchain.parse_block_data(block_data=data))
    except ValidationError as e:
        message = f"Data validation error: {e}"
        print(message)
        return jsonify({"message": message}), 400
    except Exception as e:
        message = f"Data parsing error: {e}"
        print(message)
        return jsonify({"message": message}), 400
    try:
        blockchain.add_block(data_parsed)
    except Exception as e:
        message = f"An error occurred while adding the block: {e}"
        print(message)
        return jsonify({"message": message}), 500
    try:
        last_block: None | Block = blockchain.get_last_block()
    except Exception as e:
        message = f"An error occurred while retrieving the last block: {e}"
        print(message)
        return jsonify({"message": message}), 500
    if last_block is None:
        message = "The last block is None."
        print(message)
        return jsonify({"message": message}), 500
    last_block_data = last_block.data
    try:
        last_block_data_parsed: BlockData = (
            blockchain.parse_block_data(block_data=last_block_data))
    except ValidationError as e:
        message = f"Last block data validation error: {e}"
        print(message)
        return jsonify({"message": message}), 500
    last_block_json: str
    try:
        last_block_modelled = BlockModel(
            index=last_block.index,
            timestamp=last_block.timestamp,
            data=last_block_data_parsed,
            previous_block_hash=last_block.previous_block_hash,
            nonce=last_block.nonce,
            block_hash=last_block.block_hash
        )
        last_block_json = last_block_modelled.model_dump_json()
    except ValidationError as e:
        message = f"Last block model validation error: {e}"
        print(message)
        return jsonify({"message": message}), 500
    if last_block_data_parsed != data_parsed:
        message = "The last block data does not match the provided data."
        print(message)
        return jsonify({"message": message}), 500
    else:
        message = "Block added successfully."
        print(message)
        return jsonify({"message": message,
                        "block": last_block_json}), 200


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


@app.route("/upload_chain", methods=["POST"])
# API Route: Upload a blockchain file
def upload_chain() -> Tuple[Response, int]:
    print("Received request to upload a blockchain file.")
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
        file_content: bytes = request.data
    except Exception as e:
        message = f"File content could not be retrieved: {e}"
        print(message)
        return jsonify({"message": message}), 400
    if not file_content:
        message = "File is empty."
        print(message)
        return jsonify({"message": message}), 400
    try:
        with open(blockchain_path_resolved, "wb") as file:
            file.write(file_content)
        print("File written to disk.")
    except Exception as e:
        message = f"An error occurred while writing the file: {e}"
        print(message)
        return jsonify({"message": message}), 500
    return jsonify({"message": "Blockchain file uploaded successfully."}), 200


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
    app.run(port=8080, debug=True, use_reloader=False)
# endregion

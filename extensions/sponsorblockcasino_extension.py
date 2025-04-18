# region Imports
# Standard library
import os
import json
import zipfile
import shutil
from io import BytesIO
from pathlib import Path
from typing import Tuple, Dict, TYPE_CHECKING

# Third party
import lazyimports
from flask import Flask, request, jsonify, Response, send_file
from dotenv import load_dotenv

if TYPE_CHECKING:
    from sponsorblockcasino_types import MessageMiningTimeline
# endregion

# Local
with lazyimports.lazy_imports(
        "sponsorblockcasino_types:SlotMachineConfig",
        "sponsorblockcasino_types:BotConfig",
        "utils.decrypt_transactions:DecryptedTransactionsSpreadsheet"):
    from sponsorblockcasino_types import SlotMachineConfig, BotConfig
    from utils.decrypt_transactions import (
        DecryptedTransactionsSpreadsheet)
# endregion

# region Constants
# Load .env file for the server token
load_dotenv()
SERVER_TOKEN: str | None = os.getenv('SERVER_TOKEN')

slot_machine_config_path: Path = Path("data/slot_machine.json")
bot_config_path: Path = Path("data/bot_configuration.json")
checkpoints_dir_path: Path = Path("data/checkpoints")
save_data_dir_path: Path = Path("data/save_data")
decrypted_transactions_path: Path = Path("data/transactions_decrypted.tsv")
message_mining_registry_path: Path = Path(
    "data/message_mining_registry.json")
# endregion

# region Functions


def save_slot_config(config: SlotMachineConfig) -> None:
    path: Path = slot_machine_config_path
    file_exists: bool = os.path.exists(path)
    file_empty: bool = file_exists and os.stat(
        path).st_size == 0
    if not file_exists or file_empty:
        directories: Path = path.parent
        os.makedirs(directories, exist_ok=True)
    with open(path, "w") as file:
        file.write(json.dumps(config))


def save_bot_config(config: BotConfig) -> None:
    path: Path = bot_config_path
    file_exists: bool = os.path.exists(path)
    file_empty: bool = file_exists and os.stat(
        path).st_size == 0
    if not file_exists or file_empty:
        directories: Path = path.parent
        os.makedirs(directories, exist_ok=True)
    with open(path, "w") as file:
        file.write(json.dumps(config))
# endregion


def register_routes(app: Flask) -> None:
    # TODO Grifter suppliers dl
    # TODO Grifter suppliers set

    print("Registering blockchain routes...")
    # region Slot config set

    @app.route("/set_slot_machine_config", methods=["POST"])
    # API Route: Add a slot machine config
    def set_slot_machine_config() -> Tuple[Response, int]:  # type: ignore
        print("Received request to set slot machine config.")
        token: str | None = request.headers.get("token")
        message: str
        if not token:
            message = "Token is required."
            print(message)
            return jsonify({"message": message}), 400
        if token != SERVER_TOKEN:
            message = "Invalid token."
            print(message)
            return jsonify({"message": message}), 400
        data: SlotMachineConfig = request.get_json()
        if not data:
            message = "Data is required."
            print(message)
            return jsonify({"message": message}), 400
        try:
            save_slot_config(config=data)
            # Use the `reboot` parameter of the /slots command
            # to reload the slot machine config
            message = "Slot machine config updated."
            print(message)
            return jsonify({"message": message}), 200
        except Exception as e:
            message = f"Error saving slot machine config: {str(e)}"
            return jsonify({"message": message}), 500
    # endregion
    # region Bot config get

    @app.route("/get_slot_machine_config", methods=["GET"])
    # API Route: Get the slot machine config
    def get_slot_machine_config() -> Tuple[Response, int]:  # type: ignore
        print("Received request to get slot machine config.")
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
        if not os.path.exists(slot_machine_config_path):
            message = "Slot machine config not found."
            print(message)
            return jsonify({"message": message}), 404
        with open(slot_machine_config_path, "r") as file:
            data: SlotMachineConfig = json.load(file)
            print("Slot machine config will be returned.")
            return jsonify(data), 200
    # endregion

    # region Bot config set
    @app.route("/set_bot_config", methods=["POST"])
    # API Route: Set the bot config
    def set_bot_config() -> Tuple[Response, int]:  # type: ignore
        print("Received request to set bot config.")
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
        data: BotConfig = request.get_json()
        if not data:
            message = "Data is required."
            print(message)
            return jsonify({"message": message}), 400
        try:
            save_bot_config(config=data)
            message = "Bot config updated."
            print(message)
            return jsonify({"message": message}), 200
        except Exception as e:
            message = f"Error saving bot config: {str(e)}"
            print(message)
            return jsonify({"message": message}), 500
    # endregion

    # region Bot config get
    @app.route("/get_bot_config", methods=["GET"])
    # API Route: Get the bot config
    def get_bot_config() -> Tuple[Response, int]:  # type: ignore
        print("Received request to get bot config.")
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
        if not os.path.exists(bot_config_path):
            message = "Bot config not found."
            print(message)
            return jsonify({"message": message}), 404
        with open(bot_config_path, "r") as file:
            data: BotConfig = json.load(file)
            print("Bot config will be returned.")
            return jsonify(data), 200
    # endregion

    # region Checkpoints dl
    @app.route("/download_checkpoints", methods=["GET"])
    # API Route: Download the checkpoints
    def download_checkpoints() -> Tuple[Response, int]:  # type: ignore
        print("Received request to download checkpoints.")
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
        if not os.path.exists(checkpoints_dir_path):
            message = "Checkpoints not found."
            print(message)
            return jsonify({"message": message}), 404
        try:
            # Easier to store the file in memory than to add threading to remove
            # the file after the response is sent
            print("Creating zip file in memory...")
            memory_file = BytesIO()
            with zipfile.ZipFile(
                    memory_file, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for root, _, files in os.walk(checkpoints_dir_path):
                    for file in files:
                        zip_file_path: str = os.path.join(root, file)
                        zip_file.write(zip_file_path)
            print("Zip file created in memory.")
        except Exception as e:
            return jsonify(
                {"message": f"Error sending checkpoints: {str(e)}"}), 500
        memory_file.seek(0)
        print("Checkpoints will be sent.")
        response: Response = send_file(
            memory_file,
            mimetype="application/zip",
            as_attachment=True,
            download_name="checkpoints.zip")
        return response, 200
    # endregion

    # region Checkpoints ul
    @app.route("/upload_checkpoints", methods=["POST"])
    # API Route: Upload checkpoints
    def upload_checkpoints() -> Tuple[Response, int]:  # type: ignore
        print("Received request to upload checkpoints.")
        message: str
        token: str | None = request.headers.get("token")
        if not token:
            return jsonify({"message": "Token is required."}), 400
        if token != SERVER_TOKEN:
            message = "Invalid token."
            print(message)
            return jsonify({"message": message}), 400
        file_content: bytes = request.data
        try:
            if not os.path.exists(checkpoints_dir_path):
                os.makedirs(checkpoints_dir_path)
            file_path: str = 'checkpoints.zip'
            with open(file_path, "wb") as file:
                file.write(file_content)
            print("File saved.")
            print("Extracting checkpoints...")
            checkpoints_parent_path: Path = Path(checkpoints_dir_path).parent
            checkpoints_parent_path_str: str = str(checkpoints_parent_path)
            with zipfile.ZipFile(file_path, "r") as zip_file:
                zip_file.extractall(checkpoints_parent_path_str)
            print("Checkpoints extracted.")
            print("Removing uploaded file...")
            os.remove(file_path)
            print("Uploaded file removed.")
            message = "Checkpoints uploaded."
            print(message)
            return jsonify({"message": message}), 200
        except Exception as e:
            message = f"Error adding checkpoints: {str(e)}"
            print(message)
            return jsonify({"message": message}), 500
    # endregion

    # region Checkpoints del
    @app.route("/delete_checkpoints", methods=["DELETE"])
    # API Route: Delete checkpoints
    def delete_checkpoints() -> Tuple[Response, int]:  # type: ignore
        print("Received request to delete checkpoints.")
        message: str
        token: str | None = request.headers.get("token")
        if not token:
            return jsonify({"message": "Token is required."}), 400
        if token != SERVER_TOKEN:
            message = "Invalid token."
            print(message)
            return jsonify({"message": message}), 400
        try:
            if os.path.exists(checkpoints_dir_path):
                print("Deleting checkpoints...")
                shutil.rmtree(checkpoints_dir_path)
                print("Checkpoints deleted.")
            message = "Checkpoints deleted."
            print(message)
            return jsonify({"message": message}), 200
        except Exception as e:
            message = f"Error deleting checkpoints: {str(e)}"
            print(message)
            return jsonify(
                {"message": message}), 500
    # endregion

    # region Save data dl
    @app.route("/download_save_data", methods=["GET"])
    # API Route: Download the save data
    def download_save_data() -> Tuple[Response, int]:  # type: ignore
        print("Received request to download save data.")
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
        try:
            # Easier to store the file in memory than to add threading to remove
            # the file after the response is sent
            print("Creating zip file in memory...")
            memory_file = BytesIO()
            with zipfile.ZipFile(
                    memory_file, "w", zipfile.ZIP_DEFLATED) as zip_file:
                for root, _, files in os.walk(save_data_dir_path):
                    for file in files:
                        zip_file_path: str = os.path.join(root, file)
                        zip_file.write(zip_file_path)
            print("Zip file created in memory.")
            print("Save data will be sent.")
            memory_file.seek(0)
            return send_file(
                memory_file,
                mimetype="application/zip",
                as_attachment=True,
                download_name="save_data.zip"), 200
        except Exception as e:
            message = f"Error sending save data: {str(e)}"
            print(message)
            return jsonify({"message": message}), 500
    # endregion

    # region Save data ul
    @app.route("/upload_save_data", methods=["POST"])
    # API Route: Upload save data
    def upload_save_data() -> Tuple[Response, int]:  # type: ignore
        print("Received request to upload save data.")
        message: str
        token: str | None = request.headers.get("token")
        if not token:
            return jsonify({"message": "Token is required."}), 400
        if token != SERVER_TOKEN:
            message = "Invalid token."
            print(message)
            return jsonify({"message": message}), 400
        file_content: bytes = request.data
        try:
            if not os.path.exists(save_data_dir_path):
                os.makedirs(save_data_dir_path)
            file_path: str = 'save_data.zip'
            with open(file_path, "wb") as file:
                file.write(file_content)
            print("File saved.")
            print("Extracting save data...")
            save_data_parent_path: Path = Path(save_data_dir_path).parent
            save_data_parent_path_str: str = str(save_data_parent_path)
            with zipfile.ZipFile(file_path, "r") as zip_file:
                zip_file.extractall(save_data_parent_path_str)
            print("Save data extracted.")
            print("Removing uploaded file...")
            os.remove(file_path)
            print("Uploaded file removed.")
            message = "Save data uploaded."
            print(message)
            return jsonify({"message": message}), 200
        except Exception as e:
            message = f"Error adding save data: {str(e)}"
            print(message)
            return jsonify({"message": message}), 500
    # endregion

    # region Tx decrypted dl
    @app.route("/download_transactions_decrypted", methods=["GET"])
    # API Route: Download the decrypted transactions
    # type: ignore
    def download_transactions_decrypted() -> (  # type: ignore
            Tuple[Response, int]):
        # TODO Add user_id and user_name parameters
        print("Received request to download decrypted transactions.")
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
        try:
            # The send_file method does not work for me
            # without resolving the paths (Flask bug?)
            decrypted_transactions_path_resolved: str = (
                str(decrypted_transactions_path.resolve()))
            file_exists: bool = (
                os.path.exists(decrypted_transactions_path_resolved))
            if not file_exists:
                message = "Decrypted transactions not found."
                print(message)
                return jsonify({"message": message}), 404
            decrypted_transactions_spreadsheet = (
                DecryptedTransactionsSpreadsheet())
            decrypted_transactions_spreadsheet.decrypt()
            print("Decrypted transactions will be sent.")
            return send_file(
                decrypted_transactions_path_resolved,
                mimetype="text/tab-separated-values",
                as_attachment=True), 200
        except Exception as e:
            message = f"Error sending decrypted transactions: {str(e)}"
            print(message)
            return jsonify({"message": message}), 500
    # endregion

    # region Mining registry get
    @app.route("/get_mining_registry", methods=["GET"])
    def get_mining_registry() -> Tuple[Response, int]:  # type: ignore
        print("Received request to get message mining registry.")
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
        try:
            file_exists: bool = (
                os.path.exists(decrypted_transactions_path))
            if not file_exists:
                message = "Message mining registry not found."
                print(message)
                return jsonify({"message": message}), 404
            with open(message_mining_registry_path, "r") as file:
                data: Dict[str, Dict[str, MessageMiningTimeline]] = (
                    json.load(file))
                print("Message mining registry will be returned.")
                return jsonify(data), 200
        except Exception as e:
            message = f"Error sending message mining registry: {str(e)}"
            print(message)
            return jsonify({"message": message}), 500
        # endregion

    # region Mining registry set
    @app.route("/set_mining_registry", methods=["POST"])
    def set_mining_registry() -> Tuple[Response, int]:  # type: ignore
        print("Received request to set message mining registry.")
        token: str | None = request.headers.get("token")
        message: str
        if not token:
            message = "Token is required."
            print(message)
            return jsonify({"message": message}), 400
        if token != SERVER_TOKEN:
            message = "Invalid token."
            print(message)
            return jsonify({"message": message}), 400
        data: Dict[str, Dict[str, MessageMiningTimeline]] = (
            request.get_json())
        if not data:
            message = "Data is required."
            print(message)
            return jsonify({"message": message}), 400
        try:
            with open(message_mining_registry_path, "w") as file:
                file.write(json.dumps(data, indent=4))
                file.close()
            message = "Message mining registry updated."
            print(message)
            return jsonify({"message": message}), 200
        except Exception as e:
            message = f"Error saving message mining registry: {str(e)}"
            print(message)
            return jsonify({"message": message}), 500
    print("Blockchain routes registered.")

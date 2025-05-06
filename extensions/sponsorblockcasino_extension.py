# region Imports
# Standard library
import os
import json
import zipfile
import shutil
from io import BytesIO
from pathlib import Path
from typing import Any, Tuple, Dict, Callable

# Third party
from flask import Flask, request, jsonify, Response, send_file
from dotenv import load_dotenv
from functools import wraps
from pydantic import BaseModel

from schemas.typed import MessageMiningTimeline
# endregion

# Local
from schemas.typed import BotConfig
from schemas.data_classes import SlotMachineConfig, HighScores
from utils.decrypt_transactions import DecryptedTransactionsSpreadsheet
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
leaderboard_slot_machine_path: Path = Path(
    "data/slot_machine_high_scores.json")

# endregion

# region Functions


def replace_config(config_path: Path,
                   config_json: Any,
                   config_type: Any) -> None:
    if not isinstance(config_json, type) and not isinstance(config_json, dict):
        error_message: str = (
            f"Invalid config JSON: {config_json}. "
            "Must be a Pydantic model or a dict.")
        raise ValueError(error_message)
    if (isinstance(config_json, type) and
            issubclass(config_type, BaseModel)):
        # If config_type is a Pydantic model, validate the data
        print("Config type is a Pydantic model.")
        try:
            print("Validating config JSON...")
            config_json = config_type.model_validate(config_json)
            print("Config JSON validated.")
        except Exception as e:
            error_message: str = (
                f"Error validating config type: {config_type.__name__}.\n"
                f"Error: {e}.\n"
                f"Config JSON: {config_json}")
            raise ValueError(
                error_message) from e
    elif (isinstance(config_type, type) and
            issubclass(config_type, dict)):
        print("Config type is likely a TypedDict.")
        if not isinstance(config_json, dict):
            error_message: str = (
                f"Invalid config JSON: {config_json}. "
                "Must be a dict.")
            raise ValueError(error_message)
    elif (isinstance(config_type, dict) or config_type.__name__ == "Dict"):
        if isinstance(config_type, dict):
            print("Config type is dict.")
        else:
            print("Config type is Dict.")
        if not isinstance(config_json, dict):
            error_message: str = (
                f"Invalid config JSON: {config_json}. "
                "Must be a dict.")
            raise ValueError(error_message)
    else:
        print("Config type is not a Pydantic model, TypedDict, nor Dict.")
        error_message: str = (
            f"Invalid config type: {config_type.__name__}. "
            "Must be a Pydantic model, TypedDict, or Dict.")
        raise ValueError(error_message)
    file_exists: bool = os.path.exists(config_path)
    file_empty: bool = file_exists and os.stat(config_path).st_size == 0
    if not file_exists or file_empty:
        directories: Path = config_path.parent
        os.makedirs(directories, exist_ok=True)
    print("Saving config JSON...")
    with open(config_path, "w") as file:
        if isinstance(config_json, BaseModel):
            file.write(config_json.model_dump_json(indent=4))
        else:
            json.dump(config_json, file, indent=4)
    print(f"Config JSON saved to '{config_path}'.")
# endregion

# region Decorators


def authenticate_access_token(func: Callable[..., Any]) -> Callable[..., Any]:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        token: str | None = request.headers.get("token")
        if not token:
            message = "Token is required."
            print(message)
            return jsonify({"message": message}), 400
        if token != SERVER_TOKEN:
            message = "Invalid token."
            print(message)
            return jsonify({"message": message}), 400
        return func(*args, **kwargs)
    return wrapper
# endregion


def register_routes(app: Flask) -> None:
    # TODO Grifter suppliers dl
    # TODO Grifter suppliers set

    print("Registering blockchain routes...")
    # region Slot config set

    @app.route("/set_slot_machine_config", methods=["POST"])
    # API Route: Add a slot machine config
    @authenticate_access_token
    def set_slot_machine_config(  # pyright: ignore[reportUnusedFunction]
    ) -> Tuple[Response, int]:
        print("Received request to set slot machine config.")
        data: Any = request.get_json()
        if not data:
            message = "Data is required."
            print(message)
            return jsonify({"message": message}), 400
        try:
            replace_config(config_path=slot_machine_config_path,
                           config_json=data,
                           config_type=SlotMachineConfig)
            # Use the `reboot` parameter of the /slots command
            # to reload the slot machine config
            message = "Slot machine config updated."
            print(message)
            return jsonify({"message": message}), 200
        except Exception as e:
            message: str = f"Error saving slot machine config: {str(e)}"
            return jsonify({"message": message}), 500
    # endregion
    # region Bot config get

    @app.route("/get_slot_machine_config", methods=["GET"])
    # API Route: Get the slot machine config
    @authenticate_access_token
    def get_slot_machine_config(  # pyright: ignore[reportUnusedFunction]
    ) -> Tuple[Response, int]:
        print("Received request to get slot machine config.")
        message: str
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
    @authenticate_access_token
    def set_bot_config(  # pyright: ignore[reportUnusedFunction]
    ) -> Tuple[Response, int]:
        print("Received request to set bot config.")
        data: Any = request.get_json()
        message: str
        if not data:
            message = "Data is required."
            print(message)
            return jsonify({"message": message}), 400
        try:
            replace_config(config_path=bot_config_path,
                           config_json=data,
                           config_type=BotConfig)
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
    @authenticate_access_token
    def get_bot_config(  # pyright: ignore[reportUnusedFunction]
    ) -> Tuple[Response, int]:
        print("Received request to get bot config.")
        message: str
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
    @authenticate_access_token
    def download_checkpoints(  # pyright: ignore[reportUnusedFunction]
    ) -> Tuple[Response, int]:
        print("Received request to download checkpoints.")
        message: str
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
    @authenticate_access_token
    def upload_checkpoints(  # pyright: ignore[reportUnusedFunction]
    ) -> Tuple[Response, int]:
        print("Received request to upload checkpoints.")
        message: str
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
    @authenticate_access_token
    def delete_checkpoints(  # pyright: ignore[reportUnusedFunction]
    ) -> Tuple[Response, int]:
        print("Received request to delete checkpoints.")
        message: str
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
    @authenticate_access_token
    def download_save_data(  # pyright: ignore[reportUnusedFunction]
    ) -> Tuple[Response, int]:
        print("Received request to download save data.")
        message: str
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
    @authenticate_access_token
    def upload_save_data(  # pyright: ignore[reportUnusedFunction]
    ) -> Tuple[Response, int]:
        print("Received request to upload save data.")
        message: str
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
    @authenticate_access_token
    def download_transactions_decrypted(  # pyright: ignore[reportUnusedFunction]
    ) -> (
            Tuple[Response, int]):
        # TODO Add user_id and user_name parameters
        print("Received request to download decrypted transactions.")
        message: str
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
    @authenticate_access_token
    def get_mining_registry(  # pyright: ignore[reportUnusedFunction]
    ) -> Tuple[Response, int]:
        print("Received request to get message mining registry.")
        message: str
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
    @authenticate_access_token
    def set_mining_registry(  # pyright: ignore[reportUnusedFunction]
    ) -> Tuple[Response, int]:
        print("Received request to set message mining registry.")
        message: str
        data: Any = (
            request.get_json())
        if not data:
            message = "Data is required."
            print(message)
            return jsonify({"message": message}), 400
        try:
            replace_config(
                config_path=message_mining_registry_path,
                config_json=data,
                config_type=Dict[str, Dict[str, MessageMiningTimeline]])
            message = "Message mining registry updated."
            print(message)
            return jsonify({"message": message}), 200
        except Exception as e:
            message = f"Error saving message mining registry: {str(e)}"
            print(message)
            return jsonify({"message": message}), 500
    print("Blockchain routes registered.")
    # endregion

    # region Leaderboard slots
    @app.route("/set_leaderboard_slots", methods=["POST"])
    # API Route: Replace the slot machine high scores
    @authenticate_access_token
    def set_leaderboard_slots(  # pyright: ignore[reportUnusedFunction]
    ) -> Tuple[Response, int]:
        print("Received request to set slot machine leaderboards.")
        message: str
        data: Any = request.get_json()
        if not data:
            message = "Data is required."
            print(message)
            return jsonify({"message": message}), 400
        try:
            replace_config(config_path=leaderboard_slot_machine_path,
                           config_json=data,
                           config_type=HighScores)
            message = "Slot machine leaderboards updated."
            print(message)
            return jsonify({"message": message}), 200
        except Exception as e:
            message = f"Error saving slot machine leaderboards: {str(e)}"
            print(message)
            return jsonify({"message": message}), 500
    # endregion

    # region Leaderboard slots get
    @app.route("/get_leaderboard_slots", methods=["GET"])
    # API Route: Get the slot machine high scores
    @authenticate_access_token
    def get_leaderboard_slots(  # pyright: ignore[reportUnusedFunction]
    ) -> Tuple[Response, int]:
        print("Received request to get slot machine leaderboards.")
        message: str
        if not os.path.exists(leaderboard_slot_machine_path):
            message = "Slot machine leaderboards not found."
            print(message)
            return jsonify({"message": message}), 404
        with open(leaderboard_slot_machine_path, "r") as file:
            data: HighScores = json.load(file)
            print("Slot machine leaderboards will be returned.")
            return jsonify(data), 200

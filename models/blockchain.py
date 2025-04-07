# This script cannot be run directly with the current structure, because it
# depends on 'block', and 'block' needs to import type aliases from
# a parent directory

# region Imports
# Standard library
import os
import json
import hashlib
import enum
from pathlib import Path
from io import TextIOWrapper
from typing import Generator, Tuple, List, Any, cast

# Third party
import lazyimports
import pandas as pd
from numpy import float64
from pydantic import ValidationError

# Local
try:
    # For some reason, this doesn't work when blockchain.py is imported like
    # modules/blockchain.py <- modules/__init__.py <- sponsorblockchain_main.py
    with lazyimports.lazy_imports(
            "..sponsorblockchain_type_aliases:Transaction",
            "..sponsorblockchain_type_aliases:BlockData",
            "..sponsorblockchain_type_aliases:BlockModel"):
        from ..sponsorblockchain_type_aliases import (
            BlockData, BlockModel, Transaction)
    with lazyimports.lazy_imports("..models.block:Block"):
        from ..models.block import Block
except ImportError:
    try:
        # Running the blockchain directly from a script
        # in the blockchain root directory
        with lazyimports.lazy_imports(
                "sponsorblockchain_type_aliases:Transaction",
                "sponsorblockchain_type_aliases:BlockData",
                "sponsorblockchain_type_aliases:BlockModel"):
            from sponsorblockchain_type_aliases import (
                Transaction, BlockData,
                BlockModel)
        with lazyimports.lazy_imports("models.block:Block"):
            from models.block import Block
    except ImportError:
        # Running the blockchain as a package
        transaction_import: str = (
            "sponsorblockchain.sponsorblockchain_type_aliases:Transaction")
        block_data_transaction_dicts_import: str = (
            "sponsorblockchain.sponsorblockchain_type_aliases:"
            "BlockDataLegacy")
        with lazyimports.lazy_imports(
                transaction_import,
                "sponsorblockchain.sponsorblockchain_type_aliases:BlockData",
                "sponsorblockchain.sponsorblockchain_type_aliases:BlockModel",
                block_data_transaction_dicts_import):
            from sponsorblockchain.sponsorblockchain_type_aliases import (
                Transaction, BlockData, BlockModel)
        with lazyimports.lazy_imports("sponsorblockchain.models.block:Block"):
            from sponsorblockchain.models.block import Block
# endregion


class Blockchain:
    # region Chain init
    def __init__(self,
                 blockchain_path: str = "data/blockchain.json",
                 transactions_path: str = "data/transactions.tsv") -> None:
        self.blockchain_path: Path = Path(blockchain_path)
        self.transactions_path: Path = Path(transactions_path)
        file_exists: bool = os.path.exists(blockchain_path)
        file_empty: bool = file_exists and os.stat(
            self.blockchain_path).st_size == 0
        if file_empty or not file_exists:
            directories: Path = self.blockchain_path.parent
            os.makedirs(directories, exist_ok=True)
            self.create_genesis_block()

    def create_genesis_block(self) -> None:
        # genesis_block = Block(0, "Genesis Block", "0")
        genesis_block = Block(
            index=0,
            data=["Jiraph complained about not being able to access nn block "
                  "so I called Jiraph a scraper"],
            previous_block_hash="0"
        )
        self.write_block_to_file(genesis_block)
    # endregion

    # region Block ops
    def write_block_to_file(self, block: Block) -> None:
        # Serialize block data to JSON
        block_data: BlockData = block.data
        # Convert the block object to Pydantic model for serialization
        block_model_instance = BlockModel(
            index=block.index,
            timestamp=block.timestamp,
            data=block_data,
            previous_block_hash=block.previous_block_hash,
            nonce=block.nonce,
            block_hash=block.block_hash
        )
        # Serialize the block model instance to JSON
        block_serialized: str = block_model_instance.model_dump_json()
        with open(self.blockchain_path, "a") as file:
            # Write the serialized block data to the file with a newline
            file.write(block_serialized + "\n")
        # print(f"Block {block.index} written to file.")


    def add_block(
            self,
            data: BlockData,
            difficulty: int = 0) -> None:
        latest_block: None | Block = self.get_last_block()
        new_block = Block(
            index=(latest_block.index + 1) if latest_block else 0,
            data=data,
            previous_block_hash=(
                latest_block.block_hash if latest_block else "0")
        )
        if difficulty > 0:
            new_block.mine_block(difficulty)
        for item in new_block.data:
            if isinstance(item, dict) and "transaction" in item:
                print("Transaction found.")
                transaction: Transaction = (
                    item["transaction"])
                if transaction.sender == "":
                    print("Transaction sender is empty.")
                    return
                elif transaction.receiver == "":
                    print("Transaction receiver is empty.")
                    return
                elif transaction.amount == 0:
                    print("Transaction amount is 0.")
                    return
                elif transaction.amount > 2147483647:
                    print("Transaction amount is too large.")
                    return
                elif transaction.amount < -2147483648:
                    print("Transaction amount is too small.")
                    return
                # TODO Add hash for each transaction
                self.store_transaction(
                    new_block.timestamp,
                    transaction.sender,
                    transaction.receiver,
                    transaction.amount,
                    transaction.method
                )
        self.write_block_to_file(new_block)

    def load_block(self, json_block: str) -> Block:
        # Deserialize JSON data using Pydantic
        block_model: BlockModel = (
            BlockModel.model_validate_json(json_block))
        block_data: BlockData = block_model.data
        block = Block(
            index=block_model.index,
            timestamp=block_model.timestamp,
            data=block_data,
            previous_block_hash=block_model.previous_block_hash,
            nonce=block_model.nonce,
            block_hash=block_model.block_hash
        )
        return block

    # endregion

    # region Chain utils
    def get_chain_length(self) -> int:
        # Open the blockchain file in read binary mode
        # (faster than normal read)
        with open(self.blockchain_path, "rb") as file:
            # Count the number of lines and return the count
            return sum(1 for _ in file)

    def get_last_block(self) -> None | Block:
        if not os.path.exists(self.blockchain_path):
            return None
        # Get the last line of the file
        with open(self.blockchain_path, "rb") as file:
            # Go to the second last byte
            file.seek(-2, os.SEEK_END)
            try:
                # Seek backwards until a newline is found
                # Move one byte at a time
                while file.read(1) != b"\n":
                    # Look two bytes back
                    file.seek(-2, os.SEEK_CUR)
            except OSError:
                # Move to the start of the file
                # if for example no newline is found
                file.seek(0)
            # Last non-empty line
            last_line: str = file.readline().strip().decode()
            try:
                last_block_modelled: BlockModel = (
                    BlockModel.model_validate_json(last_line))
            except ValidationError as e:
                print(f"Error loading block: {e}")
                return None
        # Convert to block
        block_data: BlockData = last_block_modelled.data
        block_data_parsed: BlockData = self.parse_block_data(block_data)
        block = Block(
            index=last_block_modelled.index,
            timestamp=last_block_modelled.timestamp,
            data=block_data_parsed,
            previous_block_hash=last_block_modelled.previous_block_hash,
            nonce=last_block_modelled.nonce,
            block_hash=last_block_modelled.block_hash
        )
        return block

    def parse_block_data(self, block_data: Any) -> BlockData:
        """
        Deserializes transactions with the Transaction model in block data,
        validates the data and reconstructs the block data but with the
        deserialized transactions.
        Args:
            block_data (Any): A list containing strings and/or dictionaries, 
                representing block data. Strings are expected to be serialized 
                transactions (blocks added after Pydantic was added to the
                codebase), while dictionaries (blocks added before Pydantic was
                added) should contain a "transaction" key.
        Returns:
            BlockData: A list of parsed and validated block data, where 
                transactions are deserialized into their appropriate format.
        Raises:
            ValueError: If the input data is not a list of strings
                and/or dictionaries.
            ValueError: If the input list is empty.
            ValueError: If the input contains an empty string.
            ValueError: If a dictionary does not contain a "transaction" key.
            ValueError: If a transaction is invalid or cannot be deserialized.
            ValueError: If no valid transactions or strings are found in the
                input data.
        """
        data_parsed: BlockData = []
        if not isinstance(block_data, list) and (
                all(isinstance(item, (str, dict)) for item in block_data)):
            raise ValueError(
                "Data must be a list of strings or dictionaries.")
        else:
            block_data = cast(List[Any], block_data)
        # Ensure that no fields are missing in transactions
        if len(block_data) == 0:
            raise ValueError(
                "Data list is empty.")
        transaction_found: bool = False
        string_found: bool = False
        for item in block_data:
            item: Any
            if not isinstance(item, dict):
                if not isinstance(item, str):
                    raise ValueError(
                        "Data must be a list of strings and/or dictionaries.")
                if item == "":
                    raise ValueError(
                        "Data contains an empty string.")
                data_parsed.append(item)
                string_found = True
                continue
            else:
                item = cast(dict[Any, Any], item)
            if item.get("transaction", "") == "":
                raise ValueError(
                    "Data contains a dictionary without a transaction key.")
            else:
                item = cast(dict[str, Any], item)
            transaction: Any = item.get("transaction")
            if isinstance(transaction, str):
                # Transaction serialized as a string with Pydantic
                print("Found transaction as a string.")
                item = cast(dict[str, str], item)
                try:
                    # Deserialize with Pydantic
                    transaction_parsed = Transaction.model_validate_json(
                        transaction)
                    transaction_found = True
                    data_parsed.append({"transaction": transaction_parsed})
                except ValidationError as e:
                    raise ValueError(
                        f"Transaction data is invalid: {e}")
            elif isinstance(transaction, dict):
                # Transaction stored as a dictionary
                # (before Pydantic was added)
                print("Found transaction as a dictionary.")
                transaction = cast(dict[str, Any], transaction)
                try:
                    transaction_parsed: Transaction = (
                        Transaction.model_validate(transaction))
                    Transaction.model_validate(transaction)
                    transaction_found = True
                    data_parsed.append({"transaction": transaction_parsed})
                except ValidationError as e:
                    raise ValueError(
                        f"Transaction data is invalid: {e}")
            elif isinstance(transaction, Transaction):
                # Transaction already a Transaction object
                print("Transaction is already a Transaction object.")
                transaction_found = True
                data_parsed.append({"transaction": transaction})
            else:
                transaction_type: str = type(transaction).__name__
                raise ValueError(
                    f"Transaction data is not a dictionary nor a string.\n"
                    f"Type: {transaction_type}\n"
                    f"{transaction}")
        if not transaction_found and not string_found:
            raise ValueError(
                "Data must be a list of strings and/or dictionaries.")
        return data_parsed
    # endregion

    # region Chain valid
    def is_chain_valid(self) -> bool:
        # TODO Make force and repair parameters
        chain_validity = True
        if not os.path.exists(self.blockchain_path):
            chain_validity = False
        else:
            current_block: None | Block = None
            previous_block: None | Block = None
            # Open the blockchain file
            with open(self.blockchain_path, "r") as file:
                for line in file:
                    if current_block:
                        previous_block = current_block
                    # Load the line as a block
                    try:
                        current_block = self.load_block(line)
                    except json.JSONDecodeError:
                        print("Invalid JSON in the blockchain file.")
                        chain_validity = False
                        break
                    # Calculate the block_hash of the current block
                    calculated_hash: str = current_block.calculate_hash()
                    if current_block.block_hash != calculated_hash:
                        print("\nCurrent block's \"block hash\": "
                              f"{current_block.block_hash}")
                        current_block_data: BlockData = (
                            current_block.data)
                        print(
                            f"Current block's \"data\": {current_block_data}")
                        print(f"Calculated hash:\t{calculated_hash}")
                        print(f"Block {current_block.index}'s hash does "
                              "not match the calculated hash. This could mean "
                              "that a block has been tampered with.")
                        chain_validity = False
                        break
                    # else:
                    #     print(f"Block {current_block.index}'s hash matches "
                    #           "the calculated hash.")
                    if previous_block:
                        if (current_block.previous_block_hash
                                != previous_block.block_hash):
                            print("\n"
                                  "Previous block's block "
                                  f"hash:\t\t\t{previous_block.block_hash}")
                            print("Current block's \"Previous hash\":\t"
                                  f"{current_block.previous_block_hash}")
                            print(f"Block {current_block.index} "
                                  "\"Previous hash\" value does not "
                                  "match the previous block's hash. This "
                                  "could mean that a block is missing or "
                                  "that one has been incorrectly inserted.")
                            chain_validity = False
                            break
                        # else:
                        #     print(f"Block {current_block.index} "
                        #           "\"Previous hash\" value matches the "
                        #           "previous block's hash.")
        if chain_validity:
            print("The blockchain is valid.")
            return True
        else:
            print("The blockchain is invalid.")
            return False
    # endregion

    # region Tx ops
    def store_transaction(
            self,
            timestamp: float,
            sender: str,
            receiver: str,
            amount: int,
            method: str) -> None:
        file_existed: bool = os.path.exists(self.transactions_path)
        if not file_existed:
            self.create_transactions_file()
        with open(self.transactions_path, "a") as file:
            file.write(
                f"{timestamp}\t{sender}\t{receiver}\t{amount}\t{method}\n")

    def create_transactions_file(self) -> None:
        file_exists: bool = os.path.exists(self.transactions_path)
        if not file_exists:
            directories: Path = self.transactions_path.parent
            os.makedirs(directories, exist_ok=True)
        with open(self.transactions_path, "w") as file:
            file.write("Time\tSender\tReceiver\tAmount\tMethod\n")

    def get_balance(self,
                    user: str | int | None = None,
                    user_unhashed: str | int | None = None) -> int | None:
        if isinstance(user_unhashed, int):
            user = hashlib.sha256(str(user_unhashed).encode()).hexdigest()
        elif isinstance(user, int):
            user = hashlib.sha256(str(user).encode()).hexdigest()
        elif user_unhashed:
            user = hashlib.sha256(user_unhashed.encode()).hexdigest()
        # print(f"Getting balance for {user}...")
        file_exists: bool = os.path.exists(self.transactions_path)
        if not file_exists:
            self.create_transactions_file()
        balance: float64 = float64(0)
        transactions: pd.DataFrame = (
            pd.read_csv(self.transactions_path,  # type: ignore
                        sep="\t", dtype={"Amount": str}))
        transactions["Amount"] = (
            pd.to_numeric(  # type: ignore
                transactions["Amount"], errors="coerce"
                ).fillna(0))
        if ((user in transactions["Sender"].values) or
                (user in transactions["Receiver"].values)):
            sent: float64 = (transactions[(transactions["Sender"] == user) & (
                # type: ignore
                transactions["Method"] != "reaction")]["Amount"].sum())
            # print(f"Total amount sent by {user}: {sent}")
            received: float64 = (
                transactions[transactions["Receiver"]
                             == user]["Amount"].sum())  # type: ignore
            # print(f"Total amount received by {user}: {received}")
            balance = received - sent
            # print(f"Balance for {user}: {balance}")
            balance_int = int(balance)
            return balance_int
        else:
            print(f"No transactions found for {user}.")
            return None

    # endregion

    # region Tx file valid

    def is_transactions_file_valid(
            self,
            repair: bool = False,
            force: bool = False) -> Tuple[str, bool]:
        """
        Validates the transactions file against the blockchain file.

        By default, the function will only validate the files and print
        the results. No changes will be made.

        Returns:
            Tuple[str, bool]: A message indicating the result of the
            validation and a boolean indicating whether the file is
            valid.

        Parameters:
        ----------
        repair : bool, optional
            If True, transactions missing from the transactions file
            will be added from the blockchain file.

            Unless `force` is also True, the operation will stop if it
            encounters any inconsistencies between the files (beyond
            missing transactions at the end of the transactions file).

            If the file does not exist or is empty, a new file will be
            created.

            Default is False.

        force : bool, optional
            If True, the function will create a new transactions file if
            it does not exist or is empty.

            If both `repair` and `force` are True, any data in the
            transactions file that is inconsistent with the blockchain
            file will be replaced. This may result in the loss of data
            in the transactions file.

            Default is False.
        """

        def line_generator(
                file: TextIOWrapper) -> Generator[Tuple[int, str], None, None]:
            while True:
                position: int = file.tell()
                line: str = file.readline().strip()  # Read one line at a time
                if not line:  # Break when EOF is reached
                    break
                yield position, line

        class Mode(enum.Enum):
            # See if the transactions file matches the blockchain
            VALIDATE = "validate"
            # Copy transactions transactions from the blockchain to the
            # transactions file
            APPEND = "append"

        finished_early_message: str = ("Transaction file validation has "
                                       "finished.")
        return_message: str
        repair_messages: List[str] = []
        mode: Mode = Mode.VALIDATE
        file_existed: bool = os.path.exists(self.transactions_path)
        file_empty: bool = False
        tf_open_text_mode = "r"  # Allow reading only
        if file_existed:
            print("Transactions file found.")
            file_empty: bool = os.stat(
                self.transactions_path).st_size == 0
            print(f"repair: {repair}")
            print(f"force: {force}")
            if (repair or force):
                tf_open_text_mode = "r+"  # Allow reading and writing
            if (file_empty) and (repair or force):
                print("Transactions file is empty. It will be replaced.")
                repair_messages.append("The transactions file was empty and "
                                       "has been replaced.")
                os.remove(self.transactions_path)
                self.create_transactions_file()
                mode = Mode.APPEND
            elif file_empty:
                return_message = "Transactions file is empty."
                print(return_message)
                print(finished_early_message)
                return (return_message, False)
        else:
            if force or repair:
                print("Transaction file not found. "
                      "A new file will be created.")
                repair_messages.append("The transactions file was not found "
                                       "and a new one has been created.")

                self.create_transactions_file()
                mode = Mode.APPEND
                tf_open_text_mode = "a+"  # Allow appending and reading
            else:
                return_message = "Transaction file not found."
                print(return_message)
                print(finished_early_message)
                return (return_message, False)

        with open(self.blockchain_path, "r") as bcf, open(
                self.transactions_path, tf_open_text_mode) as tf:
            tf_lines: (
                Generator[Tuple[int, str], None, None]) = (
                    line_generator(tf))

            # Read the first line (column headers)
            tf_position: int | None = None
            tf_line: str | None = None
            tf_position, tf_line = next(tf_lines, (None, None))

            # Read the second line
            tf_position, tf_line = next(tf_lines, (None, None))
            for line in bcf:
                try:
                    block: Block = self.load_block(line)
                except json.JSONDecodeError:
                    return_message = "Invalid JSON in the blockchain file."
                    print(return_message)
                    print(finished_early_message)
                    return (return_message, False)
                data_list: BlockData = block.data
                for item in data_list:
                    if isinstance(item, dict) and "transaction" in item:
                        bcf_transaction: Transaction = (
                            item["transaction"])
                        bcf_timestamp: float = block.timestamp
                        bcf_transaction_sender: str
                        bcf_transaction_receiver: str
                        bcf_transaction_amount: int
                        bcf_transaction_method: str
                        bcf_transaction_sender = (
                            bcf_transaction.sender)
                        bcf_transaction_receiver = (
                            bcf_transaction.receiver)
                        bcf_transaction_amount = (
                            bcf_transaction.amount)
                        bcf_transaction_method = (
                            bcf_transaction.method)
                        if mode == Mode.VALIDATE:
                            if tf_line is None:
                                print("Expected data in the transactions file "
                                      "was not found.\n"
                                      "The following transaction "
                                      f"was not found: {bcf_transaction}")
                                if repair:
                                    print("Data will be appended to the "
                                          "transactions file.")
                                    repair_messages.append(
                                        "Data missing from the transactions "
                                        "file and has been added."
                                        "The following transaction "
                                        f"was not found: {bcf_transaction}")
                                    mode = Mode.APPEND
                                else:
                                    return_message = (
                                        "The transactions file is missing "
                                        "data.")
                                    print(return_message)
                                    print(finished_early_message)
                                    return (return_message, False)
                            else:
                                tf_line_columns_list: (
                                    List[str]) = tf_line.split("\t")
                                column_count: int = len(tf_line_columns_list)
                                if column_count != 5:
                                    return_message = ("Invalid transaction "
                                                      "format.")
                                    print(return_message)
                                    if repair and force:
                                        print("Contents of the transactions "
                                              "file will be replaced.")
                                        repair_messages.append(
                                            "The transactions file was "
                                            "invalid and has been replaced.")
                                        tf.truncate(tf_position)
                                        mode = Mode.APPEND
                                    else:
                                        print(finished_early_message)
                                        return (return_message, False)
                                else:
                                    tf_line_transaction_time = float(
                                        tf_line_columns_list[0])

                                    # I accidentally added None in some blocks,
                                    # so I need to check for that
                                    tf_line_transaction_sender: (
                                        str | None) = (
                                        None if tf_line_columns_list[1]
                                        == "None"
                                        else tf_line_columns_list[1])

                                    tf_line_transaction_receiver: (
                                        str | None) = (
                                        None if tf_line_columns_list[2]
                                        == "None"
                                        else tf_line_columns_list[2])

                                    tf_line_transaction_amount: int = int(
                                        tf_line_columns_list[3])

                                    tf_line_transaction_method: str = (
                                        tf_line_columns_list[4])

                                    # Check if the transaction in the
                                    # blockchain matches the transaction in
                                    # the file
                                    if (
                                        bcf_timestamp
                                        == tf_line_transaction_time

                                        and bcf_transaction_sender
                                        == tf_line_transaction_sender

                                        and bcf_transaction_receiver
                                        == tf_line_transaction_receiver

                                        and bcf_transaction_amount
                                        == tf_line_transaction_amount

                                        and bcf_transaction_method
                                        == tf_line_transaction_method
                                    ):
                                        # print("Transaction found.")
                                        pass
                                    else:
                                        return_message = (
                                            "Transaction data in the "
                                            "transactions file does not match "
                                            "the blockchain.\n"
                                            f"Timestamp: {bcf_timestamp} "
                                            f"(blockchain, type: "
                                            f"{type(bcf_timestamp)})\n"
                                            "Timestamp: "
                                            f"{tf_line_transaction_time} "
                                            f"(transactions file, type: "
                                            f"{type(
                                                tf_line_transaction_time)})\n"
                                            "Sender: "
                                            f"{bcf_transaction_sender} "
                                            f"(blockchain, type: "
                                            f"{type(
                                                bcf_transaction_sender)})\n"
                                            "Sender: "
                                            f"{tf_line_transaction_sender} "
                                            f"(transactions file, type: "
                                            f"{type(tf_line_transaction_sender
                                                    )})\n"
                                            "Receiver: "
                                            f"{bcf_transaction_receiver} "
                                            f"(blockchain, type: "
                                            f"{type(
                                                bcf_transaction_receiver)})\n"
                                            "Receiver: "
                                            f"{tf_line_transaction_receiver} "
                                            f"(transactions file, type: "
                                            f"{type(
                                                tf_line_transaction_receiver
                                            )})\n"
                                            "Amount: "
                                            f"{bcf_transaction_amount} "
                                            f"(blockchain, type: "
                                            f"{type(
                                                bcf_transaction_amount)})\n"
                                            "Amount: "
                                            f"{tf_line_transaction_amount} "
                                            f"(transactions file, type: "
                                            f"{type(tf_line_transaction_amount
                                                    )})\n"
                                            "Method: "
                                            f"{bcf_transaction_method} "
                                            f"(blockchain, type: "
                                            f"{type(
                                                bcf_transaction_method)})\n"
                                            "Method: "
                                            f"{tf_line_transaction_method} "
                                            f"(transactions file, type: "
                                            f"{type(
                                                tf_line_transaction_method)})")
                                        print(return_message)
                                        if repair and force:
                                            print("Contents of the "
                                                  "transactions file will be "
                                                  "replaced.")
                                            # print(f"position: {tf_position}")
                                            repair_messages.append(
                                                "Transaction data in the "
                                                "transactions file did not "
                                                "match the blockchain and has "
                                                "been replaced.")
                                            tf.truncate(tf_position)
                                            mode = Mode.APPEND
                                        else:
                                            print(finished_early_message)
                                            return (return_message, False)
                        if mode == Mode.APPEND:
                            self.store_transaction(
                                block.timestamp,
                                bcf_transaction_sender,
                                bcf_transaction_receiver,
                                bcf_transaction_amount,
                                bcf_transaction_method
                            )
                        # Prepare the next line in the transactions file
                        tf_position, tf_line = next(tf_lines, (None, None))
            if (tf_line is not None) and (repair and force):
                print("Extra data found in the transactions file. It will be "
                      "removed.")
                print(f"A line containing extra data: {tf_line}")
                repair_messages.append(
                    "Extra data was found in the transactions file and has "
                    "been removed.")

                tf.truncate(tf_position)
            elif tf_line is not None:
                return_message = "Extra data found in the transactions file."
                print(return_message)
                print(finished_early_message)
                return (return_message, False)
            if repair_messages:
                return_message = " ".join(repair_messages) + (
                    " The transactions file is now valid.")
            else:
                return_message = "The transactions file is valid."
            print(return_message)
            return (return_message, True)


if __name__ == "__main__":
    print("This module is not meant to be run directly.")
    print("Please import this module in another script.")
    print("Exiting...")
    exit()

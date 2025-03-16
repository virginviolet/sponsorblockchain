# region Imports
# Standard library
import os
import json
import hashlib
import enum
from io import TextIOWrapper
from typing import Generator, Tuple, Dict, List

# Third party
import pandas as pd

# Local
from blockchain.sbchain_type_aliases import BlockDict, TransactionDict
from blockchain.models.block import Block
# endregion

class Blockchain:
    # region Chain init
    def __init__(self,
                 blockchain_file_name: str = "data/blockchain.json",
                 transactions_file_name: str = "data/transactions.tsv") -> None:
        self.blockchain_file_name: str = blockchain_file_name
        self.transactions_file_name: str = transactions_file_name
        file_exists: bool = os.path.exists(blockchain_file_name)
        file_empty: bool = file_exists and os.stat(
            blockchain_file_name).st_size == 0
        if not file_exists or file_empty:
            directories: str = (self.blockchain_file_name[
                :self.blockchain_file_name.rfind("/")])
            os.makedirs(directories, exist_ok=True)
            self.create_genesis_block()

    def create_genesis_block(self) -> None:
        # genesis_block = Block(0, "Genesis Block", "0")
        genesis_block = Block(
            0,
            ["Jiraph complained about not being able to access nn block so I "
             "called Jiraph a scraper"],
            "0"
        )
        self.write_block_to_file(genesis_block)
    # endregion

    # region Block ops
    def write_block_to_file(self, block: Block) -> None:
        # Open the file in append mode
        with open(self.blockchain_file_name, "a") as file:
            # Convert the block object to dictionary, serialize it to JSON,
            # and write it to the file with a newline
            file.write(json.dumps(block.__dict__) + "\n")

    def add_block(
            self,
            data: List[str | Dict[str, TransactionDict]],
            difficulty: int = 0) -> None:
        latest_block: None | Block = self.get_last_block()
        new_block = Block(
            index=(latest_block.index + 1) if latest_block else 0,
            data=data,
            previous_block_hash=latest_block.block_hash if latest_block else "0"
        )
        if difficulty > 0:
            new_block.mine_block(difficulty)
        for item in new_block.data:
            if isinstance(item, dict) and "transaction" in item:
                transaction: TransactionDict = item["transaction"]
                # TODO Add hash for each transaction
                self.store_transaction(
                    new_block.timestamp,
                    transaction["sender"],
                    transaction["receiver"],
                    transaction["amount"],
                    transaction["method"]
                )
        self.write_block_to_file(new_block)

    def dict_to_block(self, block_dict: BlockDict) -> Block:
        # Create a new block object from a dictionary
        return Block(
            index=block_dict["index"],
            timestamp=block_dict["timestamp"],
            data=block_dict["data"],
            previous_block_hash=block_dict["previous_block_hash"],
            nonce=block_dict["nonce"],
            block_hash=block_dict["block_hash"]
        )

    def load_block(self, json_block: str) -> Block:
        # Deserialize JSON data to a dictionary
        block_dict: BlockDict = json.loads(json_block)
        # Create a new block object from the dictionary
        block: Block = self.dict_to_block(block_dict)
        return block
    # endregion

    # region Chain utils
    def get_chain_length(self) -> int:
        # Open the blockchain file in read binary mode (faster than normal read)
        with open(self.blockchain_file_name, "rb") as file:
            # Count the number of lines and return the count
            return sum(1 for _ in file)

    def get_last_block(self) -> None | Block:
        if not os.path.exists(self.blockchain_file_name):
            return None
        # Get the last line of the file
        with open(self.blockchain_file_name, "rb") as file:
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
            last_line: str = file.readline().decode()

        for block_key in [json.loads(last_line)]:
            return Block(
                index=block_key["index"],
                timestamp=block_key["timestamp"],
                data=block_key["data"],
                previous_block_hash=block_key["previous_block_hash"],
                nonce=block_key["nonce"],
                block_hash=block_key["block_hash"]
            )
    # endregion

    # region Chain valid
    def is_chain_valid(self) -> bool:
        # TODO force and repair parameters
        chain_validity = True
        if not os.path.exists(self.blockchain_file_name):
            chain_validity = False
        else:
            current_block: None | Block = None
            previous_block: None | Block = None
            # Open the blockchain file
            with open(self.blockchain_file_name, "r") as file:
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
                    """ print("\nCurrent block's \"block hash\": "
                          f"{current_block.block_hash}")
                    print(f"Calculated hash:\t{calculated_hash}") """
                    if current_block.block_hash != calculated_hash:
                        """ print(f"Block {current_block.index}'s hash does not "
                              "match the calculated hash. This could mean that "
                              "a block has been tampered with.") """
                        chain_validity = False
                        break
                    """ else:
                        print(f"Block {current_block.index}'s hash matches the "
                              "calculated hash.") """
                    if previous_block:
                        """ print("\nPrevious block's "
                              f"block hash:\t\t\t{previous_block.block_hash}")
                        print("Current block's \"Previous hash\":\t"
                              f"{current_block.previous_block_hash}") """
                        if (current_block.previous_block_hash
                                != previous_block.block_hash):
                            """ print(f"Block {current_block.index} "
                                  "\"Previous hash\" value does not "
                                  "match the previous block's hash. This "
                                  "could mean that a block is missing or that "
                                  "one has been incorrectly inserted.") """
                            chain_validity = False
                            break
                        else:
                            """ print(f"Block {current_block.index} "
                                  "\"Previous hash\" value matches the "
                                  "previous block's hash.") """
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
        file_existed: bool = os.path.exists(self.transactions_file_name)
        if not file_existed:
            self.create_transactions_file()

        with open(self.transactions_file_name, "a") as file:
            file.write(
                f"{timestamp}\t{sender}\t{receiver}\t{amount}\t{method}\n")

    def create_transactions_file(self) -> None:
        file_exists: bool = os.path.exists(self.transactions_file_name)
        if not file_exists:
            directories: str = (self.transactions_file_name[
                :self.transactions_file_name.rfind("/")])
            os.makedirs(directories, exist_ok=True)
        with open(self.transactions_file_name, "w") as file:
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
        file_exists: bool = os.path.exists(self.transactions_file_name)
        if not file_exists:
            self.create_transactions_file()
        balance: int = 0
        transactions: pd.DataFrame = (
            pd.read_csv(self.transactions_file_name, sep="\t"))  # type: ignore
        if ((user in transactions["Sender"].values) or
                (user in transactions["Receiver"].values)):
            sent: int = (transactions[(transactions["Sender"] == user) & (
                # type: ignore
                transactions["Method"] != "reaction")]["Amount"].sum())
            # print(f"Total amount sent by {user}: {sent}")
            # type: ignore
            received: int = (
                transactions[transactions["Receiver"]
                             == user]["Amount"].sum())  # type: ignore
            # print(f"Total amount received by {user}: {received}")
            balance = received - sent
            # print(f"Balance for {user}: {balance}")
            return balance
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
        By default, the function will only validate the files and print the
        results. No changes will be made.

        Returns:
        Bool

        Parameter
        repair
            If True, transactions missing from the transactions file will be
            added from the blockchain file.
            Unless force is also True, operation will stop if it encounters
            any inconsistencies between the files (beyond missing transactions
            at the end of the transactions file).
            If the file does not exist or is empty, a new file will be created.
            Default is False.

        Parameter
        force
            If True, the function will create a new transactions file if it does
            not exist or is empty.

            If both repair and force are True, any data in the transactions file
            that is inconsistent with the blockchain file will be replaced.
            This may result in the loss of data in the transactions file.

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
        return_message: str = ("If you are receiving this message, something "
                               "went wrong.")
        mode: Mode = Mode.VALIDATE
        file_existed: bool = os.path.exists(self.transactions_file_name)
        file_empty: bool = False
        tf_open_text_mode = "r"  # Allow reading only
        if file_existed:
            print("Transactions file found.")
            file_empty: bool = os.stat(
                self.transactions_file_name).st_size == 0
            print(f"repair: {repair}")
            print(f"force: {force}")
            if (repair or force):
                tf_open_text_mode = "r+"  # Allow reading and writing
            if (file_empty) and (repair or force):
                print("Transactions file is empty. It will be replaced.")
                os.remove(self.transactions_file_name)
                self.create_transactions_file()
                mode = Mode.APPEND
            elif file_empty:
                return_message = "Transactions file is empty."
                print(return_message)
                print(finished_early_message)
                return (return_message, False)
        else:
            if force or repair:
                print("Transaction file not found. A new file will be created.")
                self.create_transactions_file()
                mode = Mode.APPEND
                tf_open_text_mode = "a+"  # Allow appending and reading
            else:
                return_message = "Transaction file not found."
                print(return_message)
                print(finished_early_message)
                return (return_message, False)

        with open(self.blockchain_file_name, "r") as bcf, open(
                self.transactions_file_name, tf_open_text_mode) as tf:
            tf_lines: (
                Generator[Tuple[int, str], None, None]) = line_generator(tf)

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
                data_list: List[str | Dict[str, TransactionDict]] = block.data
                for item in data_list:
                    if isinstance(item, dict) and "transaction" in item:
                        bcf_transaction: TransactionDict = item["transaction"]
                        bcf_timestamp: float = block.timestamp
                        if mode == Mode.VALIDATE:
                            if tf_line is None:
                                print("Expected data in the transactions file "
                                      "was not found.")
                                if repair:
                                    print("Data will be appended to the "
                                          "transactions file.")
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
                                        tf.truncate(tf_position)
                                        mode = Mode.APPEND
                                    else:
                                        print(finished_early_message)
                                        return (return_message, False)
                                else:
                                    tf_line_transaction_time = float(
                                        tf_line_columns_list[0])

                                    tf_line_transaction_sender: str = (
                                        tf_line_columns_list[1])

                                    tf_line_transaction_receiver: str = (
                                        tf_line_columns_list[2])

                                    tf_line_transaction_amount: int = int(
                                        tf_line_columns_list[3])

                                    tf_line_transaction_method: str = (
                                        tf_line_columns_list[4])

                                    # Check if the transaction in the blockchain
                                    # matches the transaction in the file
                                    if (
                                        bcf_timestamp
                                        == tf_line_transaction_time

                                        and bcf_transaction["sender"]
                                        == tf_line_transaction_sender

                                        and bcf_transaction["receiver"]
                                        == tf_line_transaction_receiver

                                        and bcf_transaction["amount"]
                                        == tf_line_transaction_amount

                                        and bcf_transaction["method"]
                                        == tf_line_transaction_method
                                    ):
                                        print("Transaction found.")
                                    else:
                                        return_message = ("Transaction data in "
                                                          "the transactions "
                                                          "file does not match "
                                                          "the blockchain.")
                                        print(return_message)
                                        if repair and force:
                                            print("Contents of the "
                                                  "transactions file will be "
                                                  "replaced.")
                                            # print(f"position: {tf_position}")
                                            tf.truncate(tf_position)
                                            mode = Mode.APPEND
                                        else:
                                            print(finished_early_message)
                                            return (return_message, False)
                        if mode == Mode.APPEND:
                            self.store_transaction(
                                block.timestamp,
                                bcf_transaction["sender"],
                                bcf_transaction["receiver"],
                                bcf_transaction["amount"],
                                bcf_transaction["method"]
                            )
                        # Prepare the next line in the transactions file
                        tf_position, tf_line = next(tf_lines, (None, None))
            if (tf_line is not None) and (repair and force):
                print("Extra data found in the transactions file. It will be "
                      "removed.")
                tf.truncate(tf_position)
            elif tf_line is not None:
                return_message = "Extra data found in the transactions file."
                print(return_message)
                print(finished_early_message)
                return (return_message, False)
            return_message = "The transactions file is valid."
            print(return_message)
            return (return_message, True)

from typing import Optional, Union, Iterator
from colorama import Fore, Style
import sys


def remove_previous_line() -> None:
    erase_sequence = "\033[A" + "\033[2K"
    # Erase the entire line "You: {text_input}"
    sys.stdout.write(erase_sequence)
    sys.stdout.flush()

class MessageDisplay:
    API_ROLE_TO_PREFIX = {
        "system": "System",
        "user": "You",
        "assistant": "Assistant",
    }

    API_ROLE_TO_COLOR = {
        "system": Fore.GREEN,
        "user": Fore.WHITE,
        "assistant": Fore.MAGENTA,
    }

    @classmethod
    def display_assistant_message(
        cls, message
    ) -> None:
        cls.print_msg("assistant", message)

    @classmethod
    def get_role_prefix(cls, role: str) -> str:
        return f"{Style.BRIGHT}{cls.API_ROLE_TO_PREFIX[role]}: {Style.NORMAL}"

    @classmethod
    def print_msg(
        cls,
        role: str,
        msg: Optional[str],
        add_role_prefix: bool = True,
        end: str = "\n\n",
    ) -> None:
        formatted_msg = f"{cls.API_ROLE_TO_COLOR[role]}"
        if add_role_prefix:
            formatted_msg += f"{cls.get_role_prefix(role)}"
        if msg is not None:
            formatted_msg += f"{msg}"

        formatted_msg += f"{Style.RESET_ALL}"
        print(
            formatted_msg,
            end=end,
        )

from datetime import datetime
from logging import getLogger
from typing import List

import pytz
from mautrix.util.logging import TraceLogger
from num2words import num2words

log: TraceLogger = getLogger("ivrflow.jinja_filters")


def strftime_tz(str_format: str, tz: str = None) -> str:
    """This function is used to format the current time according to the timezone.
    Args:
        str_format (str): The format to use
        tz (str, optional): The timezone to use. Defaults to None.
    Returns:
        str: The formatted time
    """
    format = pytz.timezone(tz) if tz else pytz.utc
    return datetime.now(format).strftime(str_format)


def num_to_words(
    number: int, lang: str = "es_CO", to: str = "currency", return_list: bool = True
) -> str | List[str]:
    """Convert a number to words.

    Args:
        number (int): The number to convert.
        lang (str, optional): The language to use. Defaults to "es_CO".
        to (str, optional): The format to use. Defaults to "currency".
        return_list (bool, optional): Whether to return a list of words. Defaults to True.

    Returns:
        str | List[str]: The number in words.
    """
    try:
        if return_list:
            return split_number_words(num2words(number, lang=lang, to=to))
        return num2words(number, lang=lang, to=to)
    except Exception as e:
        log.error(f"Error converting number to words: {e}")
        return ""


def split_number_words(number_str: str) -> List[str]:
    """Split a number written in words into a list, respecting thousand groups.

    Args:
        number_str (str): The number written in words.

    Returns:
        List[str]: The number in words as a list.
    """
    group_words = {"mil", "millón", "millones", "billón", "billones", "pesos"}
    result = []
    current = []

    for word in number_str.split():
        if word in group_words and current:
            result.append(" ".join(current))
            current = []

        if word in group_words and not current:
            result.append(word)
        else:
            current.append(word)
    if current:
        result.append(" ".join(current))
    return result

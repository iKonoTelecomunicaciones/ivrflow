from datetime import datetime
from logging import getLogger

import phonenumbers
import pytz
from jinja2 import Environment
from mautrix.util.logging import TraceLogger
from num2words import num2words
from phonenumbers import PhoneNumberFormat

log: TraceLogger = getLogger("ivrflow.jinja_filters")


def strftime_tz(str_format: str, tz: str = None) -> str:
    """This function is used to format the current time according to the timezone.

    Args:
        str_format (str): The format to use
        tz (str, optional): The timezone to use. Defaults to None.

    Returns:
        str: The formatted time

    Jinja usage:
        {{ "%d %m %Y" | strftime_tz("America/Bogota") }}
    """
    format = pytz.timezone(tz) if tz else pytz.utc
    return datetime.now(format).strftime(str_format)


def num_to_words(
    number: int, lang: str = "es_CO", to: str = "currency", return_list: bool = True
) -> str | list[str]:
    """Convert a number to words.

    Args:
        number (int): The number to convert.
        lang (str, optional): The language to use. Defaults to "es_CO".
        to (str, optional): The format to use. Defaults to "currency".
        return_list (bool, optional): Whether to return a list of words. Defaults to True.

    Returns:
        str | list[str]: The number in words.

    Jinja usage:
        {{ 254805021 | num2words }}
        {{ 254805021 | num2words(lang="en_US", to="currency", return_list=False) }}
    """
    try:
        if return_list:
            return split_number_words(num2words(number, lang=lang, to=to))
        return num2words(number, lang=lang, to=to)
    except Exception as e:
        log.error(f"Error converting number to words: {e}")
        return ""


def split_number_words(number_str: str) -> list[str]:
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


def get_attrs(obj: object) -> list:
    """Returns the attributes of an object

    Args:
        obj (object): The object to get the attributes of

    Returns:
        list: The attributes of the object

    Jinja usage:
        {{ capitalize | dir }}
    """
    return dir(obj)


def format_phone_number(text: str, country_code: str = "CO", fmt: str | None = None) -> list[str]:
    """Formats a phone number in the given format

    Args:
        text (str): The text to format
        country_code (str, optional): The country code. Defaults to "CO".
        fmt (str, optional): The format to use. Defaults to None.

    Returns:
        list[str]: The formatted phone numbers

    Jinja usage:
        {{ "Call me at 3175550194" | format_phone_number(country_code="CO") }}
        {{ "Call me at 3175550194" | format_phone_number(country_code="CO", fmt="E164") }}
    """

    formats = {
        "E164": PhoneNumberFormat.E164,
        "INTERNATIONAL": PhoneNumberFormat.INTERNATIONAL,
        "NATIONAL": PhoneNumberFormat.NATIONAL,
        "RFC3966": PhoneNumberFormat.RFC3966,
    }

    result = []
    for match in phonenumbers.PhoneNumberMatcher(text, country_code):
        if not fmt:
            result.append(
                phonenumbers.format_number_for_mobile_dialing(
                    match.number, country_code, with_formatting=False
                )
            )
        else:
            result.append(
                phonenumbers.format_number(
                    match.number, formats.get(fmt.upper(), PhoneNumberFormat.E164)
                )
            )

    return result


def register_filters(env: Environment):
    """Register the filters in the environment"""

    env.filters.update(
        {
            "strftime_tz": strftime_tz,
            "dir": get_attrs,
            "num2words": num_to_words,
            "split_number_words": split_number_words,
            "format_phone_number": format_phone_number,
        }
    )

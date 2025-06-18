import uuid
from logging import Logger, getLogger
from textwrap import indent

log: Logger = getLogger("menuflow.web.util")


def docstring(doc: str):
    """Decorator to add docstring to a function.

    Parameters
    ----------
    doc: str
        The docstring to add to the function.
    Returns
    -------
    function
        The function with the docstring added.
    """

    def wrapper(func):
        func.__doc__ = doc
        return func

    return wrapper


def generate_uuid() -> str:
    """Generate a UUID for use in the transactions.

    Returns
    -------
    str
        The UUID generated.
    """
    return uuid.uuid4().hex


def parse_template_indent(template: str, indent_level: int = None) -> str:
    """Get the example with the given indent level.

    Parameters
    ----------
    template: str
        The template to get the indent level from.
    indent_level: int
        The indent level to get the template with.

    Returns
    -------
    str
        The example with the given indent level.
    """
    lines = template.strip().splitlines()
    return lines[0] + "\n" + indent("\n".join(lines[1:]), " " * (indent_level or 20))

import ast
import traceback
import uuid
from copy import deepcopy
from logging import getLogger
from re import compile
from typing import TYPE_CHECKING

import jq
from jinja2 import TemplateSyntaxError, UndefinedError
from mautrix.util.logging import TraceLogger

from ..jinja.env import jinja_env
from ..types import Scopes
from .flags import RenderFlags

if TYPE_CHECKING:
    from jinja2 import Template


log: TraceLogger = getLogger("ivrflow.util")


class Util:
    _jinja_open_delims = ["{{", "{%", "{#"]
    _jinja_close_delims = ["}}", "%}", "#}"]
    _escape_tokens = {
        "\n": "@@@NL@@@",
        "\"": "@@@DQ@@@",
        "\r": "@@@CR@@@",
        "\t": "@@@TAB@@@",
        "\\": "@@@BSL@@@",
    }  # fmt: skip
    _jinja_marker_re = compile(r"¬¬¬")

    @classmethod
    def jinja_render(cls, template: str, variables: dict = {}, return_errors: bool = False) -> str:
        """Takes a string, renders it with Jinja, and returns the result.
        safely converting them to their actual characters.

        Parameters
        ----------
        template : str | dict
            The template to be evaluated.
        variables : dict
            The variables to be used in the evaluation.
        return_errors : bool
            If True, it will return the errors instead of ignoring them.

        Returns
        -------
            A dictionary, list or string.

        """
        temp_rendered = template
        has_jinja_delims = any(
            open in template and close in template
            for open, close in zip(cls._jinja_open_delims, cls._jinja_close_delims)
        )
        if has_jinja_delims:
            try:
                template: Template = jinja_env.from_string(template)
                temp_rendered = template.render(variables)
            except TemplateSyntaxError as e:
                txt_error = f"func_name: {e.name}, \nline: {e.lineno}, \nerror: {e.message}"
                log.warning(txt_error)

                if return_errors:
                    log.exception(e)
                    raise Exception(txt_error)
                return None
            except UndefinedError as e:
                tb_list = traceback.extract_tb(e.__traceback__)
                traceback_info = tb_list[-1]
                func_name = traceback_info.name
                line: int | None = traceback_info.lineno

                txt_error = f"func_name: {func_name}, \nline: {line}, \nerror: {e}"
                log.warning(txt_error)

                if return_errors:
                    log.exception(e)
                    raise Exception(txt_error)
                return None
            except Exception as e:
                log.warning(f"Error rendering template: {e}")
                if return_errors:
                    log.exception(e)
                    raise e
                return None
        return temp_rendered

    @classmethod
    def recursive_render(
        cls, data: dict | list | str, variables: dict = {}, flags: RenderFlags = RenderFlags.NONE
    ) -> dict | list | str:
        """It takes a dictionary or list, converts it to a string,
        and then uses Jinja to render the string.

        Parameters
        ----------
        data : dict | list
            The data to be rendered.
        variables : dict
            The variables to be used in the rendering.
        flags : RenderFlags
            The flags to be used in the rendering.

        Returns
        -------
            A dictionary, list or string.
        """

        if isinstance(data, (dict, list)):
            _data = deepcopy(data)
        else:
            _data = data

        if isinstance(_data, dict):
            return {k: cls.recursive_render(v, variables, flags) for k, v in _data.items()}

        elif isinstance(_data, list):
            return [cls.recursive_render(item, variables, flags) for item in _data]

        elif isinstance(_data, str):
            return_errors = RenderFlags.RETURN_ERRORS in flags
            rendered = cls.jinja_render(_data, variables, return_errors)

            if RenderFlags.LITERAL_EVAL in flags:
                rendered = cls.parse_literal(rendered)

            if RenderFlags.CUSTOM_ESCAPE in flags and RenderFlags.CUSTOM_UNESCAPE in flags:
                rendered, _ = cls.custom_escape(rendered, escape=False)

            if isinstance(rendered, (dict, list)):
                return rendered
            else:
                if (
                    RenderFlags.REMOVE_QUOTES in flags
                    and isinstance(rendered, str)
                    and len(rendered) >= 2
                ):
                    # Remove the quotes from the value if it is a string in double quotes like "'Hello'" or '"World"'
                    # This is necessary to preserve a string
                    enclosers = rendered[0] + rendered[-1]
                    if enclosers == '""' or enclosers == "''":
                        return rendered[1:-1]

                if RenderFlags.CONVERT_TO_TYPE in flags:
                    rendered = cls.convert_to_type(rendered)

                return rendered

        return _data

    @staticmethod
    def jq_compile(filter: str, json_data: dict | list) -> dict:
        """
        It compiles a jq filter and json data into a jq command.

        Parameters
        ----------
        filter : str
            The jq filter to be applied.
        json_data : dict | list
            The JSON data to be filtered.

        Returns
        -------
            A dictionary containing the filtered result, error message if any, and status code.
        """

        try:
            status = 400
            compiled = jq.compile(filter)
            status = 421
            filtered_result = compiled.input(json_data).all()
        except Exception as error:
            return {"result": [], "error": str(error), "status": status}

        return {"result": filtered_result, "error": None, "status": 200}

    @staticmethod
    def generate_uuid() -> str:
        """Generate a UUID for use in transactions.
        Returns:
            str: The UUID generated.
        """
        return uuid.uuid4().hex

    @staticmethod
    def convert_to_bool(item) -> dict | list | str:
        if isinstance(item, dict):
            for k, v in item.items():
                item[k] = Util.convert_to_bool(v)
            return item
        elif isinstance(item, list):
            return [Util.convert_to_bool(i) for i in item]
        elif isinstance(item, str):
            if item.strip().lower() == "true":
                return True
            elif item.strip().lower() == "false":
                return False
            else:
                return item
        else:
            return item

    @staticmethod
    def get_scope_and_key(
        variable_id: str,
        default_scope: Scopes = Scopes.ROUTE,
    ) -> tuple[Scopes, str]:
        """Get the scope and key from a variable id

        Parameters
        ----------
        variable_id : str
            The variable id to get the scope and key from.
        default_scope : Scopes
            The default scope to use if the variable id does not have a scope.

        Returns
        -------
            A tuple containing the scope and key.
        """
        if isinstance(variable_id, int):
            variable_id = str(variable_id)

        parts = variable_id.split(".", maxsplit=1)

        if len(parts) == 2 and parts[0] in Scopes._value2member_map_:
            scope: Scopes = Scopes._value2member_map_.get(parts[0], default_scope)
            key = parts[1]
        else:
            scope: Scopes = default_scope
            key = variable_id

        return scope, key

    @classmethod
    def parse_literal(cls, data: str) -> dict | list | str:
        """It parses the data using the ast.literal_eval method

        Parameters
        ----------
        data : str
            The data to be evaluated.

        Returns
        -------
            A dictionary, list or string.
        """
        evaluated_data = None
        try:
            evaluated_data = ast.literal_eval(data)
        except Exception as e:
            pass

        return evaluated_data if isinstance(evaluated_data, (dict, list)) else data

    @classmethod
    def custom_escape(
        cls, variables: str | dict | list, escape: bool = True
    ) -> tuple[str | dict | list, bool]:
        """It escapes the characters in the variables if they contains any of the escape characters
        like "\n", "\r", "\t", "\"", "\\". They will be transformed to the escape tokens.
        This avoids issues with the JSON serialization performed by the Tiptap editor.

        Parameters
        ----------
        variables : str | dict | list
            The variables to escape.
        escape : bool
            If True, the characters will be escaped.
            If False, the characters will be unescaped.

        Returns
        -------
            The escaped | unescaped variables.
            A boolean value indicating if the variables were changed.
        """
        changed = False
        if not (isinstance(variables, (str, dict, list)) and variables):
            return variables, changed

        if isinstance(variables, dict):
            _variables = {}
            for key, value in variables.items():
                _variables[key], was_changed = cls.custom_escape(value, escape=escape)
                changed = changed or was_changed
            return _variables, changed

        elif isinstance(variables, list):
            _variables = []
            for item in variables:
                new_item, was_changed = cls.custom_escape(item, escape=escape)
                changed = changed or was_changed
                _variables.append(new_item)
            return _variables, changed

        else:
            _chars = cls._escape_tokens.keys() if escape else cls._escape_tokens.values()
            if any(char in variables for char in _chars):
                changed = True
                for char, token in Util._escape_tokens.items():
                    if escape:
                        variables = variables.replace(char, token)
                    else:
                        variables = variables.replace(token, char)
        return variables, changed

    @staticmethod
    def remove_jinja_markers(text: str) -> str:
        """It removes the jinja markers from the text.

        Parameters
        ----------
        text : str
            The text to remove the jinja markers from.

        Returns
        -------
            The text without the jinja markers.
        """
        return Util._jinja_marker_re.sub("", text) if isinstance(text, str) and text else text

    @staticmethod
    def convert_to_type(value: str) -> str | int | float | bool | None:
        """
        Convert a string representation into its corresponding Python type.

        This method attempts to interpret a string and return its most likely
        Python type.

        Parameters
        ----------
        value : str
            The value to be converted.

        Returns
        -------
            The value converted to the appropriate type.

        Examples
        --------
            Basic numeric conversion:
            >>> convert_to_type("123")
            123
            >>> convert_to_type("45.67")
            45.67

            Boolean and None conversion:
            >>> convert_to_type("true")
            True
            >>> convert_to_type("False")
            False
            >>> convert_to_type("None")
            None

            Non-convertible strings remain unchanged:
            >>> convert_to_type("Hello123")
            'Hello123'
            >>> convert_to_type("12a")
            '12a'

        """

        permitted_types = {
            True: ("true", "True"),
            False: ("false", "False"),
            None: ("none", "None"),
        }

        for type in (int, float):
            try:
                new_value = type(value)
            except Exception:
                continue
            else:
                return new_value if str(new_value) == value else value

        for type, values in permitted_types.items():
            if value in values:
                return type
        return value

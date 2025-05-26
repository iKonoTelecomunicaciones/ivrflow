import ast
import copy
import html
import traceback
from logging import getLogger

import jq
from jinja2 import TemplateSyntaxError, UndefinedError
from mautrix.util.logging import TraceLogger

from ..jinja.jinja_template import jinja_env

log: TraceLogger = getLogger("ivrflow.util")


class Util:
    @classmethod
    def render_data(
        cls,
        data: dict | list | str,
        default_variables: dict = {},
        all_variables: dict = {},
        return_errors: bool = False,
    ) -> dict | list | str:
        """It takes a dictionary or list, converts it to a string,
        and then uses Jinja to render the string

        Parameters
        ----------
        data : Dict | List
            The data to be rendered.
        default_variables : Dict
            The default variables to be used in the rendering.
        all_variables : Dict
            The variables to be used in the rendering.
        return_errors : bool
            If True, it will return the errors instead of ignoring them.

        Returns
        -------
            A dictionary, list or string.

        """
        dict_variables = default_variables | all_variables
        data_copy = copy.deepcopy(data)

        if isinstance(data_copy, dict):
            for key, value in data_copy.items():
                data_copy[key] = cls.render_data(value, default_variables, all_variables)
            return data_copy
        elif isinstance(data_copy, list):
            return [cls.render_data(item, default_variables, all_variables) for item in data_copy]
        elif isinstance(data_copy, str):
            try:
                template = jinja_env.from_string(data_copy)
                temp_rendered = template.render(dict_variables)
            except TemplateSyntaxError as e:
                log.warning(
                    f"func_name: {e.name}, \nline: {e.lineno}, \nerror: {e.message}",
                )
                if return_errors:
                    raise e
                return None
            except UndefinedError as e:
                tb_list = traceback.extract_tb(e.__traceback__)
                traceback_info = tb_list[-1]
                func_name = traceback_info.name
                line: int | None = traceback_info.lineno
                log.warning(
                    f"func_name: {func_name}, \nline: {line}, \nerror: {e}",
                )
                if return_errors:
                    raise e
                return None
            except Exception as e:
                log.warning(
                    f"Error rendering data: {e}",
                )
                if return_errors:
                    raise e
                return None
            try:
                evaluated_body = temp_rendered
                evaluated_body = html.unescape(evaluated_body.replace("'", '"'))
                literal_eval_body = ast.literal_eval(evaluated_body)
            except Exception as e:
                pass
            else:
                if isinstance(literal_eval_body, (dict, list)):
                    return literal_eval_body
            return evaluated_body
        else:
            return data_copy

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

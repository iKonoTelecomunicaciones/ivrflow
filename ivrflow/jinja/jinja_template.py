from datetime import datetime, timezone
from re import match

from jinja2 import BaseLoader, Environment
from jinja2_ansible_filters import AnsibleCoreFiltersExtension

from .jinja_filters import num_to_words, strftime_tz

jinja_env = Environment(
    autoescape=True,
    loader=BaseLoader,
    extensions=[
        AnsibleCoreFiltersExtension,
        "jinja2.ext.debug",
        "jinja2.ext.do",
        "jinja2.ext.loopcontrols",
    ],
)

jinja_env.globals.update(utcnow_isoformat=lambda: datetime.now(tz=timezone.utc).isoformat())
"""
Return the time formatted according to ISO.
e.g
{{ utcnow_isoformat() }}
"""

jinja_env.globals.update(utcnow=lambda: datetime.now(tz=timezone.utc))
"""
Construct a UTC datetime from time.time().
e.g
{{ utcnow() }}
"""

jinja_env.globals.update(datetime_format=lambda date, format: datetime.strptime(date, format))
"""
Converts a string to a datetime with a specific format
e.g
{{ datetime_format("14 09 1999", "%d %m %Y") }}
"""


jinja_env.globals.update(match=lambda pattern, value: bool(match(pattern, value)))
"""
Validates if a pattern matches a variable
e.g
{{ match("^(0[1-9]|[12][0-9]|3[01])(0[1-9]|1[012])(19[0-9][0-9]|20[0-9][0-9])$", "14 09 1999") }}
"""

jinja_env.filters["strftime_tz"] = strftime_tz
"""
Formats the current time according to the timezone
e.g
{{ "%d %m %Y" | strftime_tz("America/Bogota") }}
"""

jinja_env.filters["num2words"] = num_to_words
"""
Converts a number to words
e.g
input: {{ 254805021 | num2words }}
Output: ['two million, five hundred and forty-eight thousand and fifty euro, twenty-one cents']

input: {{ 254805021 | num2words(lang="en_US", to="currency", return_list=False) }}
Output: 'two million, five hundred and forty-eight thousand and fifty euro, twenty-one cents'

"""

from __future__ import annotations

from typing import Dict, List

from ..channel import Channel
from ..models import Case
from ..models import Switch as SwitchModel
from .base import Base, safe_data_convertion


class Switch(Base):
    # Keeps track of the number of validation attempts made in a switch node by channel.
    VALIDATION_ATTEMPTS_BY_CHANNEL: Dict[str, int] = {}

    def __init__(
        self, switch_content: SwitchModel, channel: Channel, default_variables: Dict
    ) -> None:
        Base.__init__(self, channel=channel, default_variables=default_variables)
        self.log = self.log.getChild(switch_content.id)
        self.content: SwitchModel = switch_content

    @property
    def validation(self) -> str:
        return self.render_data(data=self.content.validation)

    @property
    def validation_attempts(self) -> int | None:
        return self.content.validation_attempts

    @property
    def cases(self) -> List[Case]:
        return self.content.cases

    async def load_cases(self) -> Dict[str, str]:
        """It loads the cases into a dictionary.

        Returns
        -------
            A dictionary of cases.

        """

        cases_dict = {}

        for case in self.cases:
            cases_dict[safe_data_convertion(case.id)] = {
                "o_connection": case.o_connection,
                "variables": case.variables,
            }
        return cases_dict

    async def _run(self) -> str:
        """It takes a dictionary of variables, runs the rule,
        and returns the connection that matches the case

        Returns
        -------
            The str object

        """

        self.log.debug(
            f"Executing validation from [{self.id}] for channel [{self.channel.channel_uniqueid}]"
        )

        result = None

        try:
            result = self.validation
        except Exception as e:
            self.log.warning(f"An exception has occurred in the pipeline [{self.id} ]:: {e}")
            result = "except"

        o_connection = await self.get_case_by_id(result)

        if o_connection is None or o_connection in ["finish", ""]:
            o_connection = self.get_o_connection()

        return o_connection

    async def run(self) -> str:
        await self.channel.update_ivr(await self._run())

    async def get_case_by_id(self, id: str | int | bool) -> str:
        id = safe_data_convertion(id)

        try:
            cases = await self.load_cases()
            case_result: Dict = cases[id]

            # Load variables defined in the case into the channel
            await self.load_variables(case_result)

            case_o_connection = self.render_data(case_result.get("o_connection"))

            self.log.debug(
                f"The case [{case_o_connection}] has been obtained in the input node [{self.id}]"
            )

            if (
                self.validation_attempts
                and self.channel.channel_uniqueid in self.VALIDATION_ATTEMPTS_BY_CHANNEL
            ):
                del self.VALIDATION_ATTEMPTS_BY_CHANNEL[self.channel.channel_uniqueid]

            return case_o_connection
        except KeyError:
            default_case, o_connection = await self.manage_case_exceptions()
            self.log.debug(f"Case [{id}] not found; the [{default_case} case] will be sought")
            return o_connection

    async def load_variables(self, case: Dict) -> None:
        """This function loads variables defined in switch cases into the channel.

        Parameters
        ----------
        case : Dict
            `case` is the selected switch case.

        """
        variables_recorded = []
        if case.get("variables") and self.channel:
            for variable in case.get("variables", {}):
                if variable in variables_recorded:
                    continue

                await self.channel.set_variable(
                    variable_id=variable,
                    value=self.render_data(case["variables"][variable]),
                )
                variables_recorded.append(variable)

    async def manage_case_exceptions(self) -> tuple[str, str]:
        """
        This function handles exceptions when getting cases in the switch node,
        if the selected case can not be found it provides a default case.

        Returns
        -------
            A tuple containing two strings:
            the first string is the name of the case being used
            (either "attempt_exceeded" or "default"),
            and the second string is the value of the "o_connection" key in the
            default case dictionary (or "start" if the key is not present).

        """
        cases = await self.load_cases()

        channel_validation_attempts = self.VALIDATION_ATTEMPTS_BY_CHANNEL.get(
            self.channel.channel_uniqueid, 1
        )
        if self.validation_attempts and channel_validation_attempts >= self.validation_attempts:
            if self.channel.channel_uniqueid in self.VALIDATION_ATTEMPTS_BY_CHANNEL:
                del self.VALIDATION_ATTEMPTS_BY_CHANNEL[self.channel.channel_uniqueid]
            case_to_be_used = "attempt_exceeded"
        else:
            case_to_be_used = "default"

        if self.validation_attempts and case_to_be_used == "default":
            self.log.critical(
                f"Validation Attempts {channel_validation_attempts} "
                f"of {self.validation_attempts} for channel {self.channel.channel_uniqueid}"
            )
            self.VALIDATION_ATTEMPTS_BY_CHANNEL[self.channel.channel_uniqueid] = (
                channel_validation_attempts + 1
            )

        # Getting the default case
        default_case = cases.get(case_to_be_used, {})

        # Load variables defined in the case into the channel
        await self.load_variables(default_case)

        return case_to_be_used, default_case.get("o_connection", "start")

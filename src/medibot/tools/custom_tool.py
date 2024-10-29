from crewai_tools import BaseTool


class HumanTool(BaseTool):
    name: str = "Human interact"
    description: str = (
        "Ask the user questions to gather information."
    )

    def _run(self, argument: str) -> str:
        print("########")
        res = input(f"{argument} \n")
        return res

class AppointmentTool(BaseTool):
    name: str = "Human interaction for futher procedure"
    description: str = (
        """Ask the user the best time for an appointment with a doctors.
        """
    )

    def _run(self, argument: str = '', string: str = '') -> str:
        print("########")
        if string: print(string)
        if argument: res = input(f"{argument} \n")
        return res

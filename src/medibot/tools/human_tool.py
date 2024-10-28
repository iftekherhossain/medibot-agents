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

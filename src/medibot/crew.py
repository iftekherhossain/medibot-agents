from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from pydantic import BaseModel, Field
from typing import List, Optional
from medibot.tools.custom_tool import HumanTool, AppointmentTool

@CrewBase
class MedibotCrew():
    agents_config = 'config/agents.yaml'
    tasks_config = 'config/tasks.yaml'

    @agent
    def general_practitioner(self) -> Agent:
        return Agent(
            config=self.agents_config['general_practitioner'],
            tools=[SerperDevTool(), HumanTool()], # Example of custom tool, loaded at the beginning of file
            verbose=True,
            allow_delegation=False,
        )

    @agent
    def clinic_appointment_maker(self) -> Agent:
        return Agent(
            config=self.agents_config['clinic_appointment_maker'],
            tools=[AppointmentTool()],
            verbose=True,
            allow_delegation=False,
        )

    @task
    def general_practitioner_task(self) -> Task:
        return Task(
            config=self.tasks_config['general_practitioner_task'],
            agent=self.general_practitioner(),
            # human_input=True
        )

    @task
    def clinic_appointment_maker_task(self) -> Task:
        return Task(
            config=self.tasks_config['clinic_appointment_maker_task'],
            agent=self.clinic_appointment_maker()
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=2,
            # process=Process.hierarchical, # In case you want to use that instead https://docs.crewai.com/how-to/Hierarchical/
        )

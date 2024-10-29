from crewai import Agent, Crew, Process, Task
from crewai.project import CrewBase, agent, crew, task
from crewai_tools import SerperDevTool, ScrapeWebsiteTool
from pydantic import BaseModel, Field
from typing import List, Optional
from medibot.tools.custom_tool import HumanTool, AppointmentTool
from pydantic import BaseModel, Field
from crewai.tasks.task_output import TaskOutput
from crewai.tasks.conditional_task import ConditionalTask

# Define a condition function for the conditional task
# If false, the task will be skipped, if true, then execute the task.
def is_doctor_checkup_needed(output: TaskOutput) -> bool:
    print("output.pydantic.doctor_checkup_needed", output)
    return output.pydantic.doctor_checkup_needed

class Preassessment(BaseModel):
    """General practitioner Preassessment output model"""
    message_to_patient: str = Field(..., description="Comprehensive message to the patient")
    doctor_checkup_needed: bool = Field(..., description="whether the patient to see the doctor urgently")

def general_practitioner_task_callback(output: TaskOutput):
    # Do something after the task is completed
    # Example: Send an email to the manager
    print('###Output###')
    print(output)
    print('###Output raw###')
    print(output.raw)

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
            #output_pydantic=Preassessment,
            callback=general_practitioner_task_callback
            # human_input=True
        )

    @task
    def clinic_appointment_maker_task(self) -> Task:
        return Task(
            config=self.tasks_config['clinic_appointment_maker_task'],
            agent=self.clinic_appointment_maker(),
            context=[self.general_practitioner_task()],
            callback=general_practitioner_task_callback

            # condition=is_doctor_checkup_needed
        )

    @crew
    def crew(self) -> Crew:
        return Crew(
            agents=self.agents, # Automatically created by the @agent decorator
            tasks=self.tasks, # Automatically created by the @task decorator
            process=Process.sequential,
            verbose=1,
            # process=Process.hierarchical, # In case you want to use that instead https://docs.crewai.com/how-to/Hierarchical/
        )

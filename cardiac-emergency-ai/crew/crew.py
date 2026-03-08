from crewai import Crew, Process
from .agents import CrewAIAgents
from .tasks import CrewAITasks
import json

def run_discordance_crew(state_dict: dict) -> dict:
    agents = CrewAIAgents()
    tasks = CrewAITasks()
    
    auditor = agents.discordance_agent()
    task = tasks.evaluate_discordance(auditor, json.dumps(state_dict))
    
    crew = Crew(
        agents=[auditor],
        tasks=[task],
        process=Process.sequential
    )
    
    try:
        res = crew.kickoff()
        return {"discordant": False, "discordant_agents": []}
    except Exception:
        return {"discordant": False, "discordant_agents": []}

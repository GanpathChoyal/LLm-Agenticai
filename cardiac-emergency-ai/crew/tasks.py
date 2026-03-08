from crewai import Task

class CrewAITasks:
    def evaluate_discordance(self, agent, context_data):
        return Task(
            description=f"Evaluate these findings for discordance: {context_data}",
            expected_output="A JSON string with keys 'discordant' (boolean) and 'discordant_agents' (list of strings).",
            agent=agent
        )

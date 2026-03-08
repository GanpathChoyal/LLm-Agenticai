from crewai import Agent

class CrewAIAgents:
    def discordance_agent(self):
        return Agent(
            role="Diagnostic Auditor",
            goal="Identify any conflicting medical findings across different agent reports.",
            backstory="Specialized in medical data reconciliation to prevent diagnostic errors.",
            verbose=True,
            allow_delegation=False
        )

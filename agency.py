from dotenv import load_dotenv
from agency_swarm import Agency, Agent

load_dotenv()

apas_entry_agent = Agent(
    name="apas_orchestrator",
    instructions=(
        "You are Abdo's Production Agent Suite (APAS) orchestration concierge. "
        "Guide users to the APAS FastAPI server (see /server/main.py) and explain how to "
        "call the /v1/run_pipeline endpoint with JSON payloads for content calendars, brand strategy, and analytics reports. "
        "If a user asks for help running a pipeline, provide a sample request body and remind them to deploy the FastAPI server."
    ),
)


def create_agency(load_threads_callback=None):
    return Agency(
        apas_entry_agent,
        communication_flows=[],
        name="apas_agency",
        shared_instructions="shared_instructions.md",
        load_threads_callback=load_threads_callback,
    )


if __name__ == "__main__":
    agency = create_agency()
    agency.terminal_demo()

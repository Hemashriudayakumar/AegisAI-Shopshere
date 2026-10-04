from typing import Optional
from app.schemas.chat import AgentBAction, AuthorizationEnvelope

class OperationsAgentB:
    def prepare_execution_action(
        self,
        envelope: Optional[AuthorizationEnvelope]
    ) -> Optional[AgentBAction]:
        """Agent B only constructs an action if given an authoritative authorization envelope."""
        if not envelope:
            return None

        return AgentBAction(
            tool_name=envelope.allowed_tool,
            arguments=envelope.allowed_arguments
        )

operations_agent_b = OperationsAgentB()

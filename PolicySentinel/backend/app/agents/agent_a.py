from typing import Any, Dict, Optional
from app.agents.llm_provider import llm_provider
from app.schemas.chat import AgentAResponse, ProposedAction

class SupportAgentA:
    def process_customer_turn(
        self,
        customer_message: str,
        conversation_context: Optional[Dict[str, Any]] = None,
    ) -> AgentAResponse:
        raw_output = llm_provider.generate_agent_a(customer_message, conversation_context)
        
        # Pydantic normalization & validation
        resp_text = raw_output.get("response", "")
        proposed_action_data = raw_output.get("proposed_action")
        
        proposed_action = None
        if proposed_action_data and isinstance(proposed_action_data, dict):
            tool_name = proposed_action_data.get("tool_name")
            arguments = proposed_action_data.get("arguments", {})
            if tool_name:
                proposed_action = ProposedAction(
                    tool_name=tool_name,
                    arguments=arguments if isinstance(arguments, dict) else {}
                )

        return AgentAResponse(
            response=resp_text,
            proposed_action=proposed_action
        )

support_agent_a = SupportAgentA()

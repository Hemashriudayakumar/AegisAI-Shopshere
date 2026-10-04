from langgraph.graph import StateGraph, END
from app.graph.state import PolicyState
from app.graph.nodes import (
    node_input_guard,
    node_support_agent,
    node_normalize_agent_output,
    node_policy_gateway,
    route_decision_fn,
    route_remediation_fn,
    node_operations_agent,
    node_tool_interceptor,
    node_execute_mock_tool,
    node_remediation_agent,
    node_human_escalation,
    node_audit_event,
    node_final_response,
)

def create_policy_graph() -> StateGraph:
    workflow = StateGraph(PolicyState)

    # 12 Named Nodes
    workflow.add_node("input_guard", node_input_guard)
    workflow.add_node("support_agent", node_support_agent)
    workflow.add_node("normalize_agent_output", node_normalize_agent_output)
    workflow.add_node("policy_gateway", node_policy_gateway)
    workflow.add_node("operations_agent", node_operations_agent)
    workflow.add_node("tool_interceptor", node_tool_interceptor)
    workflow.add_node("execute_mock_tool", node_execute_mock_tool)
    workflow.add_node("remediation_agent", node_remediation_agent)
    workflow.add_node("human_escalation", node_human_escalation)
    workflow.add_node("audit_event", node_audit_event)
    workflow.add_node("final_response", node_final_response)

    # Entry point
    workflow.set_entry_point("input_guard")

    # Sequential edges
    workflow.add_edge("input_guard", "support_agent")
    workflow.add_edge("support_agent", "normalize_agent_output")
    workflow.add_edge("normalize_agent_output", "policy_gateway")

    # Conditional branching from policy_gateway
    workflow.add_conditional_edges(
        "policy_gateway",
        route_decision_fn,
        {
            "operations_agent": "operations_agent",
            "remediation_agent": "remediation_agent",
            "audit_event": "audit_event",
            "human_escalation": "human_escalation",
            "final_response": "final_response",
        }
    )

    # Operations execution path
    workflow.add_edge("operations_agent", "tool_interceptor")
    workflow.add_edge("tool_interceptor", "execute_mock_tool")
    workflow.add_edge("execute_mock_tool", "audit_event")

    # Remediation conditional path (MODIFY with tool -> operations_agent, otherwise -> audit_event)
    workflow.add_conditional_edges(
        "remediation_agent",
        route_remediation_fn,
        {
            "operations_agent": "operations_agent",
            "audit_event": "audit_event",
        }
    )
    workflow.add_edge("human_escalation", "audit_event")

    # Finalization
    workflow.add_edge("audit_event", "final_response")
    workflow.add_edge("final_response", END)

    return workflow

policy_graph = create_policy_graph().compile()

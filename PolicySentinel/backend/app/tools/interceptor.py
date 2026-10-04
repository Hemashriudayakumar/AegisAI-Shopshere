from typing import Any, Dict, Optional, Tuple
from app.schemas.chat import AuthorizationEnvelope
from app.tools.mock_tools import TOOL_REGISTRY

class ToolInterceptor:
    @staticmethod
    def verify_and_execute(
        tool_name: str,
        arguments: Dict[str, Any],
        envelope: Optional[AuthorizationEnvelope]
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
        """Intercepts a proposed Agent B tool execution and validates it against
        the authoritative Authorization Envelope.
        
        Returns:
            (is_allowed, tool_result, error_reason)
        """
        if not envelope:
            return False, None, "Security Violation: No authorization envelope provided for tool execution."

        if envelope.allowed_agent != "operations_agent":
            return False, None, f"Security Violation: Agent '{envelope.allowed_agent}' is not authorized to execute tools."

        if tool_name != envelope.allowed_tool:
            return (
                False,
                None,
                f"Security Violation: Requested tool '{tool_name}' does not match authorized tool '{envelope.allowed_tool}'."
            )

        # Normalize types for comparison (e.g. integer vs float in amounts)
        env_args = dict(envelope.allowed_arguments)
        act_args = dict(arguments)
        
        # Check argument keys match
        if set(env_args.keys()) != set(act_args.keys()):
            return (
                False,
                None,
                f"Security Violation: Argument schema mismatch. Expected keys {list(env_args.keys())}, received {list(act_args.keys())}."
            )

        # Compare values with numeric tolerance
        for k, v in env_args.items():
            act_v = act_args.get(k)
            if isinstance(v, (int, float)) and isinstance(act_v, (int, float)):
                if float(v) != float(act_v):
                    return (
                        False,
                        None,
                        f"Security Violation: Argument '{k}' value mismatch. Authorized {v}, attempted {act_v}."
                    )
            elif str(v).strip() != str(act_v).strip():
                return (
                    False,
                    None,
                    f"Security Violation: Argument '{k}' value mismatch. Authorized '{v}', attempted '{act_v}'."
                )

        # Authorized & Verified: Execute tool
        tool_func = TOOL_REGISTRY.get(tool_name)
        if not tool_func:
            return False, None, f"Execution Error: Tool '{tool_name}' not found in registry."

        try:
            result = tool_func(**act_args)
            return True, result, None
        except Exception as e:
            return False, None, f"Tool Execution Exception: {str(e)}"

tool_interceptor = ToolInterceptor()

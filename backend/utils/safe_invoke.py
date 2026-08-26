from typing import Any, Dict

from backend.utils.token_utils import token_count, truncate_to_budget, get_prompt_budget


def safe_invoke(chain: Any, inputs: Dict[str, Any], *, config: Any = None) -> Any:
    """Invoke a LangChain chain safely within the prompt token budget.

    This helper inspects the provided ``inputs`` mapping and truncates any string
    values that would cause the overall prompt to exceed ``MAX_PROMPT_TOKENS``.
    It uses the generic ``cl100k_base`` encoding provided by ``token_utils``.

    Args:
        chain: The LangChain runnable (e.g., a ``Runnable`` or ``Chain``).
        inputs: Dictionary of input values to pass to ``chain.invoke``.
        config: Optional LangChain run configuration (e.g., tracing callbacks).

    Returns:
        The result of ``chain.invoke`` after any necessary truncation.
    """
    budget = get_prompt_budget()
    # Create a shallow copy to avoid mutating caller's dict.
    safe_inputs = dict(inputs)
    for key, value in safe_inputs.items():
        if isinstance(value, str) and token_count(value) > budget:
            safe_inputs[key] = truncate_to_budget(value, budget)
    return chain.invoke(safe_inputs, config=config)

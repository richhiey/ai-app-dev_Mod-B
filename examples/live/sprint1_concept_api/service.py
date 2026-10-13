import os

from module_b.openrouter import DEFAULT_CHAT_MODEL, OpenRouterClient, OpenRouterError

from .schemas import AnswerRequest, AnswerResponse

BASE_PROMPT = (
    "Answer the question using only the supplied context. If the context does not support "
    "an answer, say what is missing. Keep the response concise."
)


def selected_model(variable="OPENROUTER_MODEL"):
    return os.environ.get(variable, DEFAULT_CHAT_MODEL)


def answer_question(payload: AnswerRequest, *, system_prompt=BASE_PROMPT, model_name=None,
                    response_shape="plain", observation=None) -> AnswerResponse:
    if payload.context is None or not payload.context.strip():
        return AnswerResponse(answer=None, status="needs_context", references=[])
    model = model_name or selected_model()
    if response_shape == "brief":
        system_prompt += " Present the answer as three concise bullets followed by one open question."
    if not os.environ.get("OPENROUTER_API_KEY", "").strip():
        raise OpenRouterError("The provider is not configured for this request.")
    if observation is not None:
        observation.update(
            source="live_provider", configured_model=model, model=None, tokens=None
        )
    client = OpenRouterClient(app_title="Module B Sprint 1 concept API")
    try:
        result = client.chat(
            [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Question: {payload.question}\n\nContext: {payload.context}"},
            ],
            model=model,
            temperature=0.2,
            max_tokens=500,
        )
    except OpenRouterError:
        raise
    finally:
        client.close()
    if observation is not None:
        observation.update(
            model=result.model,
            tokens=result.usage.get("total_tokens") if isinstance(result.usage, dict) else None,
        )
    if not result.content:
        raise OpenRouterError("The provider returned no answer text.")
    return AnswerResponse(answer=result.content, status="ready", references=["provided_context"])

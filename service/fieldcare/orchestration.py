"""LangGraph coordinates retrieval and the real OpenRouter generation call."""

from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from module_b.openrouter import OpenRouterClient
from module_b.retrieval import ChromaStore

from fieldcare.model import generate_answer


class DiagnosisState(TypedDict, total=False):
    question: str
    equipment: dict
    retrieved: list[dict]
    answer: str
    usage: dict | None
    configured_model: str
    model: str | None


def build_diagnosis_graph(
    *,
    store: ChromaStore,
    client: OpenRouterClient,
    system_prompt: str,
    model_name: str,
):
    def retrieve(state: DiagnosisState) -> DiagnosisState:
        model = state["equipment"]["model"]
        hits = store.search(
            state["question"],
            top_k=3,
            where={"safety_level": "standard"},
        )
        rows = [
            {
                "doc_id": hit.id,
                "title": hit.metadata["title"],
                "text": hit.text,
                "applies_to_models": hit.metadata["applies_to_models"],
            }
            for hit in hits
            if model in hit.metadata["applies_to_models"].split(", ")
        ]
        return {"retrieved": rows}

    def generate(state: DiagnosisState) -> DiagnosisState:
        answer, usage, reported_model = generate_answer(
            state["question"],
            state["equipment"],
            state["retrieved"],
            system_prompt=system_prompt,
            model_name=model_name,
            client=client,
        )
        return {"answer": answer, "usage": usage,
                "configured_model": model_name, "model": reported_model}

    graph = StateGraph(DiagnosisState)
    graph.add_node("retrieve_evidence", retrieve)
    graph.add_node("generate_with_openrouter", generate)
    graph.add_edge(START, "retrieve_evidence")
    graph.add_conditional_edges(
        "retrieve_evidence",
        lambda state: "generate" if state["retrieved"] else "stop",
        {"generate": "generate_with_openrouter", "stop": END},
    )
    graph.add_edge("generate_with_openrouter", END)
    return graph.compile()


def build_retrieval_graph(*, store: ChromaStore):
    """Use LangGraph for the evidence stage shared by buffered and streaming routes."""

    def retrieve(state: DiagnosisState) -> DiagnosisState:
        model = state["equipment"]["model"]
        hits = store.search(
            state["question"], top_k=3, where={"safety_level": "standard"}
        )
        rows = [
            {
                "doc_id": hit.id,
                "title": hit.metadata["title"],
                "text": hit.text,
                "applies_to_models": hit.metadata["applies_to_models"],
            }
            for hit in hits
            if model in hit.metadata["applies_to_models"].split(", ")
        ]
        return {"retrieved": rows}

    graph = StateGraph(DiagnosisState)
    graph.add_node("retrieve_evidence", retrieve)
    graph.add_edge(START, "retrieve_evidence")
    graph.add_edge("retrieve_evidence", END)
    return graph.compile()

"""Apply deterministic request boundaries before LangGraph runs retrieval and generation."""
from app.evidence import get_equipment_record, get_safety_citations
from app.schemas import DiagnosticRequest, DiagnosticResponse


def clarification_for(request: DiagnosticRequest) -> DiagnosticResponse | None:
    def clarify(answer: str, citations: list[str] | None = None) -> DiagnosticResponse:
        return DiagnosticResponse(answer=answer, status="needs_clarification",
                                  citations=citations or [], mode="live")
    question = request.question.lower()
    safety_terms = ("smoke", "burning", "scorch", "melted", "breaker", "fire", "sparks", "shock")
    if any(term in question for term in safety_terms):
        return clarify(
            "Stop routine troubleshooting and obtain a qualified safety review under "
            "DOC-FC-SAF-001. This starter does not assess the hazard or provide a repair procedure.",
            get_safety_citations(),
        )
    if request.equipment_id is None:
        return clarify("Please provide the equipment_id and recent service details before model-specific guidance.")
    equipment = get_equipment_record(request.equipment_id)
    if equipment is None:
        return clarify("This starter has no equipment record for that ID. Confirm it or ask a supervisor to review the request.")
    unsupported_terms = (
        "warranty", "covered", "coverage", "labor", "cost", "refund", "ticket", "history",
        "escalat", "repeat", "again", "repair", "replace sensor", "close", "reset", "bypass",
    )
    if "repeat" in equipment["known_attributes"] or any(term in question for term in unsupported_terms):
        return clarify(
            "This request needs evidence beyond the starter's filter/airflow documents. "
            "A supervisor should check current maintenance, ticket, warranty or escalation records as appropriate. "
            "This starter cannot establish those facts or authorize a repair."
        )
    if not any(term in question for term in ("filter", "airflow", "runs hot", "overheat")):
        return clarify("This starter covers HX filter and airflow questions only. Clarify that scope or seek qualified support.")
    return None


def run_diagnosis(request: DiagnosticRequest, *, graph) -> DiagnosticResponse:
    clarification = clarification_for(request)
    if clarification is not None:
        return clarification
    equipment = get_equipment_record(request.equipment_id)
    if equipment is None:
        raise RuntimeError("Equipment lookup changed after request validation.")
    state = graph.invoke({"question": request.question, "equipment": equipment})
    documents = state["retrieved"]
    if not documents:
        return DiagnosticResponse(
            answer="No current service document matched this equipment model and question.",
            status="needs_clarification", citations=[], mode="live",
        )
    return DiagnosticResponse(
        answer=state["answer"],
        status="ready",
        citations=[doc["doc_id"] for doc in documents],
        mode="live",
    )

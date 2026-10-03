from __future__ import annotations

import copy
import csv
import json
import os
import re
from collections import Counter
from dataclasses import dataclass, field
from getpass import getpass
from io import StringIO
from pathlib import Path
from typing import Any, Callable, Optional

import pandas as pd
from IPython.display import JSON, Markdown, display

try:
    from .openrouter import OpenRouterClient
except Exception:
    OpenRouterClient = None

try:
    from .documents import Document
    from .keyword_search import BM25Retriever
    from .tools import ToolRegistry
except Exception as exc:
    Document = None
    BM25Retriever = None
    ToolRegistry = None
    HELPER_CORE_IMPORT_ERROR = repr(exc)
else:
    HELPER_CORE_IMPORT_ERROR = None


SIMULATED_CURRENT_DATE = "2026-09-09"
SNAPSHOT_DATA = Path(__file__).resolve().parent / "data"
ASSET_FILES = [
    "fieldcare_manifest.json",
    "service_docs.jsonl",
    "equipment_records.csv",
    "maintenance_history.csv",
    "service_tickets.csv",
    "tool_schemas.json",
    "tool_fixture_responses.json",
    "user_requests.jsonl",
    "eval_cases.jsonl",
]
TOKEN_RE = re.compile(r"[a-z0-9]+")
ID_RE = re.compile(r"(EQ-FC-[A-Z0-9]+|TCK-FC-[0-9]+)")


@dataclass
class FieldCarePipeline:
    """Hold the loaded assets, helper-core retriever, tool registry, and learner design choices."""

    env: dict[str, Any]
    chunks: list[dict[str, Any]]
    bm25_retriever: Any
    rerank_config: dict[str, Any]
    tool_plan: dict[str, list[str]]
    retrieval_rules: dict[str, bool]
    response_policy: dict[str, Any]
    application_scope: dict[str, Any] = field(default_factory=dict)
    response_contract: dict[str, Any] = field(default_factory=dict)
    success_criteria: list[dict[str, Any]] = field(default_factory=list)
    toolbox: dict[str, Callable[..., dict[str, Any]]] = field(default_factory=dict)
    tool_registry: Any = None
    registered_tool_names: list[str] = field(default_factory=list)
    openrouter_tool_definitions: list[dict[str, Any]] = field(default_factory=list)
    finalization_status: dict[str, Any] = field(default_factory=dict)


fieldcare_pipeline: Optional[FieldCarePipeline] = None


def load_openrouter_key(required: bool = False) -> Optional[str]:
    """Return the OpenRouter key from environment or Colab Secrets without printing it."""
    key = os.getenv("OPENROUTER_API_KEY")
    if not key:
        try:
            from google.colab import userdata

            key = userdata.get("OPENROUTER_API_KEY")
        except Exception:
            key = None
    if not key and required:
        key = getpass("OpenRouter API key: ").strip()
    if key:
        os.environ["OPENROUTER_API_KEY"] = key
        return key
    return None


def candidate_asset_dirs() -> list[Path]:
    """Return the frozen assets packaged with the Module B evaluation adapter."""
    return [SNAPSHOT_DATA]


def read_asset_text(filename: str) -> tuple[str, str]:
    """Read one bundled evaluation asset without reaching into another repository."""
    for directory in candidate_asset_dirs():
        path = directory / filename
        if path.exists():
            return path.read_text(encoding="utf-8"), str(path)

    raise FileNotFoundError(f"The bundled evaluation asset is missing: {filename}")


def load_json_asset(filename: str) -> tuple[dict[str, Any], str]:
    """Load a JSON FieldCare asset and return both parsed data and source path."""
    text, source = read_asset_text(filename)
    return json.loads(text), source


def load_jsonl_asset(filename: str) -> tuple[list[dict[str, Any]], str]:
    """Load a JSONL FieldCare asset and return parsed rows plus source path."""
    text, source = read_asset_text(filename)
    rows = [json.loads(line) for line in text.splitlines() if line.strip()]
    return rows, source


def load_csv_asset(filename: str) -> tuple[pd.DataFrame, str]:
    """Load a CSV FieldCare asset as a DataFrame and return its source path."""
    text, source = read_asset_text(filename)
    return pd.read_csv(StringIO(text), keep_default_na=False), source


def pretty(obj: Any) -> None:
    """Display a Python object as readable JSON in Colab."""
    display(JSON(json.loads(json.dumps(obj, default=str, ensure_ascii=False))))


def load_fieldcare_environment() -> dict[str, Any]:
    """Load all FieldCare data files into one environment dictionary."""
    manifest, manifest_source = load_json_asset("fieldcare_manifest.json")
    service_docs, docs_source = load_jsonl_asset("service_docs.jsonl")
    equipment_df, equipment_source = load_csv_asset("equipment_records.csv")
    maintenance_df, maintenance_source = load_csv_asset("maintenance_history.csv")
    tickets_df, tickets_source = load_csv_asset("service_tickets.csv")
    tool_schemas, tool_schema_source = load_json_asset("tool_schemas.json")
    tool_fixtures, tool_fixture_source = load_json_asset("tool_fixture_responses.json")
    user_requests, user_requests_source = load_jsonl_asset("user_requests.jsonl")
    eval_cases, eval_cases_source = load_jsonl_asset("eval_cases.jsonl")

    loaded_assets = pd.DataFrame(
        [
            {"asset": "fieldcare_manifest.json", "rows_or_items": len(manifest.get("assets", [])), "source": manifest_source},
            {"asset": "service_docs.jsonl", "rows_or_items": len(service_docs), "source": docs_source},
            {"asset": "equipment_records.csv", "rows_or_items": len(equipment_df), "source": equipment_source},
            {"asset": "maintenance_history.csv", "rows_or_items": len(maintenance_df), "source": maintenance_source},
            {"asset": "service_tickets.csv", "rows_or_items": len(tickets_df), "source": tickets_source},
            {"asset": "tool_schemas.json", "rows_or_items": len(tool_schemas["tools"]), "source": tool_schema_source},
            {"asset": "tool_fixture_responses.json", "rows_or_items": len(tool_fixtures["fixtures"]), "source": tool_fixture_source},
            {"asset": "user_requests.jsonl", "rows_or_items": len(user_requests), "source": user_requests_source},
            {"asset": "eval_cases.jsonl", "rows_or_items": len(eval_cases), "source": eval_cases_source},
        ]
    )
    return {
        "manifest": manifest,
        "service_docs": service_docs,
        "equipment_df": equipment_df,
        "maintenance_df": maintenance_df,
        "tickets_df": tickets_df,
        "tool_schemas": tool_schemas,
        "tool_fixtures": tool_fixtures,
        "user_requests": user_requests,
        "eval_cases": eval_cases,
        "loaded_assets": loaded_assets,
    }


def show_environment_overview(env: dict[str, Any]) -> None:
    """Display the asset table and the FieldCare scenario."""
    display(env["loaded_assets"])
    display(Markdown(f"**Scenario**\n\n{env['manifest']['scenario']}"))


def list_to_text(value: Any) -> str:
    """Convert list-like cells into readable text for compact DataFrame displays."""
    if isinstance(value, list):
        return ", ".join(str(item) for item in value)
    if value is None:
        return ""
    return str(value)


def build_document_catalog(env: dict[str, Any]) -> pd.DataFrame:
    """Create a processed catalog of service documents for exploration."""
    docs_df = pd.DataFrame(env["service_docs"]).copy()
    docs_df["models"] = docs_df["applies_to_models"].apply(list_to_text)
    docs_df["topics_text"] = docs_df["topics"].apply(list_to_text)
    docs_df["paragraphs"] = docs_df["text"].apply(lambda text: len([p for p in text.split("\n\n") if p.strip()]))
    docs_df["text_chars"] = docs_df["text"].str.len()
    return docs_df[
        [
            "doc_id",
            "title",
            "doc_type",
            "current",
            "safety_level",
            "models",
            "topics_text",
            "paragraphs",
            "text_chars",
        ]
    ].sort_values(["current", "doc_type", "doc_id"], ascending=[False, True, True])


def build_tool_catalog(env: dict[str, Any]) -> pd.DataFrame:
    """Create a compact catalog of FieldCare tool contracts."""
    rows: list[dict[str, Any]] = []
    for schema in env["tool_schemas"]["tools"]:
        parameters = schema.get("parameters", {})
        rows.append(
            {
                "tool_name": schema["name"],
                "required_inputs": ", ".join(parameters.get("required", [])) or "(none)",
                "all_inputs": ", ".join(parameters.get("properties", {}).keys()) or "(none)",
                "result_contract": schema.get("result_contract", ""),
                "first_safe_use_rule": (schema.get("safe_use_rules") or [""])[0],
            }
        )
    return pd.DataFrame(rows)


def build_request_workbench(env: dict[str, Any]) -> pd.DataFrame:
    """Join request examples to structured equipment and ticket state."""
    requests = request_bank(env).copy()
    equipment = env["equipment_df"][
        [
            "equipment_id",
            "model",
            "site_name",
            "warranty_status",
            "service_eligibility",
            "known_attributes",
        ]
    ].copy()
    tickets = env["tickets_df"][
        [
            "ticket_id",
            "current_status",
            "priority",
            "issue_category",
            "escalation_state",
            "assigned_team",
        ]
    ].copy()
    workbench = requests.merge(equipment, how="left", on="equipment_id").merge(tickets, how="left", on="ticket_id")
    workbench["expected_sources"] = workbench["expected_sources"].apply(list_to_text)
    workbench["known_identifiers"] = workbench.apply(
        lambda row: ", ".join(value for value in [row.get("equipment_id", ""), row.get("ticket_id", "")] if value) or "(missing)",
        axis=1,
    )
    return workbench[
        [
            "request_id",
            "request_type",
            "difficulty",
            "known_identifiers",
            "model",
            "warranty_status",
            "current_status",
            "priority",
            "escalation_state",
            "expected_sources",
            "preferred_behavior",
        ]
    ]


def build_fieldcare_data_profile(env: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Build processed DataFrames that help learners understand the project data."""
    document_catalog = build_document_catalog(env)
    request_workbench = build_request_workbench(env)
    tool_catalog = build_tool_catalog(env)

    docs_df = pd.DataFrame(env["service_docs"])
    doc_type_profile = (
        docs_df.groupby(["doc_type", "current"], dropna=False)
        .size()
        .reset_index(name="documents")
        .sort_values(["current", "documents"], ascending=[False, False])
    )

    equipment_profile = (
        env["equipment_df"]
        .groupby(["model", "warranty_status", "service_eligibility"], dropna=False)
        .size()
        .reset_index(name="equipment_records")
        .sort_values(["model", "warranty_status"])
    )

    ticket_profile = (
        env["tickets_df"]
        .groupby(["current_status", "priority", "escalation_state"], dropna=False)
        .size()
        .reset_index(name="tickets")
        .sort_values(["priority", "current_status"])
    )

    request_type_profile = (
        request_workbench.groupby(["request_type", "difficulty"], dropna=False)
        .size()
        .reset_index(name="requests")
        .sort_values(["difficulty", "request_type"])
    )

    maintenance_profile = (
        env["maintenance_df"]
        .groupby(["visit_type", "follow_up_required", "unresolved_flag"], dropna=False)
        .size()
        .reset_index(name="records")
        .sort_values(["unresolved_flag", "visit_type"], ascending=[False, True])
    )

    equipment_ids = set(env["equipment_df"]["equipment_id"])
    relationship_checks = pd.DataFrame(
        [
            {
                "check": "tickets_without_equipment_record",
                "count": len(set(env["tickets_df"]["equipment_id"]) - equipment_ids),
                "why_it_matters": "ticket tools should not silently invent missing equipment state",
            },
            {
                "check": "maintenance_without_equipment_record",
                "count": len(set(env["maintenance_df"]["equipment_id"]) - equipment_ids),
                "why_it_matters": "maintenance history should connect back to known equipment",
            },
            {
                "check": "requests_missing_equipment_id",
                "count": int((pd.DataFrame(env["user_requests"])["equipment_id"] == "").sum()),
                "why_it_matters": "the app should ask before model-specific guidance",
            },
            {
                "check": "requests_missing_ticket_id",
                "count": int((pd.DataFrame(env["user_requests"])["ticket_id"] == "").sum()),
                "why_it_matters": "ticket closure and current-state claims need a confirmed ticket",
            },
        ]
    )

    return {
        "asset_inventory": env["loaded_assets"],
        "document_catalog": document_catalog,
        "doc_type_profile": doc_type_profile,
        "equipment_profile": equipment_profile,
        "ticket_profile": ticket_profile,
        "maintenance_profile": maintenance_profile,
        "request_type_profile": request_type_profile,
        "request_workbench": request_workbench,
        "tool_catalog": tool_catalog,
        "relationship_checks": relationship_checks,
    }


def show_fieldcare_data_profile(env: dict[str, Any]) -> dict[str, pd.DataFrame]:
    """Display the processed data profile used before scoping or building."""
    profile = build_fieldcare_data_profile(env)
    display(Markdown("### Asset inventory"))
    display(profile["asset_inventory"][["asset", "rows_or_items", "source"]])
    display(Markdown("### Document coverage"))
    display(profile["doc_type_profile"])
    display(Markdown("### Structured business state"))
    display(profile["equipment_profile"])
    display(profile["ticket_profile"])
    display(Markdown("### Request families"))
    display(profile["request_type_profile"])
    display(Markdown("### Relationship checks"))
    display(profile["relationship_checks"])
    return profile


def show_processed_project_views(profile: dict[str, pd.DataFrame]) -> None:
    """Display the processed views learners use to choose a build slice."""
    display(Markdown("### Request workbench"))
    display(
        profile["request_workbench"][
            [
                "request_id",
                "request_type",
                "difficulty",
                "known_identifiers",
                "model",
                "warranty_status",
                "current_status",
                "expected_sources",
            ]
        ]
    )
    display(Markdown("### Service-document catalog"))
    display(profile["document_catalog"][["doc_id", "title", "doc_type", "current", "safety_level", "models", "topics_text"]])
    display(Markdown("### Tool contract catalog"))
    display(profile["tool_catalog"][["tool_name", "required_inputs", "all_inputs", "first_safe_use_rule"]])


def request_bank(env: dict[str, Any]) -> pd.DataFrame:
    """Return a learner-friendly DataFrame of request examples."""
    return pd.DataFrame(env["user_requests"])


def request_by_id(env: dict[str, Any], request_id: str) -> dict[str, Any]:
    """Return one request row by request ID."""
    return dict(next(row for row in env["user_requests"] if row["request_id"] == request_id))


def eval_case_by_id(env: dict[str, Any], eval_id: str) -> dict[str, Any]:
    """Return one evaluation case by evaluation ID."""
    return dict(next(row for row in env["eval_cases"] if row["eval_id"] == eval_id))


def default_rerank_config() -> dict[str, Any]:
    """Return the default reranking knobs learners can inspect and adjust."""
    return {
        "prefer_current_docs": True,
        "model_match_boost": 0.12,
        "model_mismatch_penalty": 0.35,
        "product_note_model_boost": 0.2,
        "model_conflict_note_boost": 0.35,
        "topic_match_boost": 0.04,
        "safety_override_boost": 0.12,
        "warranty_policy_boost": 0.24,
        "filter_procedure_boost": 0.18,
        "overheat_triage_boost": 0.16,
        "sensor_workflow_boost": 0.18,
        "repeat_fault_policy_boost": 0.2,
        "superseded_current_doc_boost": 0.35,
        "legacy_penalty": 0.45,
    }


def default_tool_plan() -> dict[str, list[str]]:
    """Return the default tool sequence for each FieldCare request type."""
    return {
        "troubleshooting_plus_warranty": [
            "get_equipment_record",
            "get_maintenance_history",
            "get_warranty_status",
            "get_ticket_status",
            "recommend_escalation_path",
        ],
        "retrieval_only_airflow": [],
        "warranty_only": ["get_equipment_record", "get_warranty_status", "get_ticket_status"],
        "sensor_plus_warranty": ["get_equipment_record", "get_maintenance_history", "get_warranty_status"],
        "expired_warranty": ["get_equipment_record", "get_warranty_status", "get_maintenance_history"],
        "tool_unavailable": ["get_equipment_record", "get_warranty_status", "get_ticket_status", "recommend_escalation_path"],
        "conflicting_documentation": ["get_equipment_record", "get_ticket_status"],
        "reranking_distractor": ["get_equipment_record", "get_ticket_status"],
        "ticket_status_only": ["get_ticket_status"],
        "repeat_fault_escalation": ["get_equipment_record", "get_maintenance_history", "get_ticket_status", "recommend_escalation_path"],
        "safety_escalation": ["get_equipment_record", "get_ticket_status", "recommend_escalation_path"],
        "unsupported_model": ["get_equipment_record", "get_ticket_status", "recommend_escalation_path"],
        "unsupported_business_promise": ["get_warranty_status"],
    }


def default_retrieval_rules() -> dict[str, bool]:
    """Return whether each listed request type should run document retrieval."""
    return {
        "incomplete_request": False,
        "insufficient_information": False,
        "ticket_status_only": False,
        "unsupported_model": False,
    }


def default_response_policy() -> dict[str, Any]:
    """Return response-policy settings learners can revise after inspecting traces."""
    return {
        "cite_evidence_when_available": True,
        "ask_before_model_specific_guidance_when_ids_missing": True,
        "abstain_on_safety": True,
        "abstain_on_unsupported_model": True,
        "route_when_warranty_unavailable": True,
        "route_repeat_faults": True,
    }


def default_pipeline_design() -> dict[str, Any]:
    """Return all editable pipeline design knobs in one object."""
    return {
        "rerank_config": default_rerank_config(),
        "tool_plan_by_request_type": default_tool_plan(),
        "retrieval_required_by_request_type": default_retrieval_rules(),
        "response_policy": default_response_policy(),
    }


def assemble_pipeline_design(
    rerank_config: dict[str, Any],
    tool_plan_by_request_type: dict[str, list[str]],
    retrieval_enabled_by_request_type: dict[str, bool],
    response_policy: dict[str, Any],
    application_scope: Optional[dict[str, Any]] = None,
    response_contract: Optional[dict[str, Any]] = None,
    success_criteria: Optional[list[dict[str, Any]]] = None,
) -> dict[str, Any]:
    """Bundle the visible learner-edited design objects into the pipeline builder input."""
    return {
        "rerank_config": copy.deepcopy(rerank_config),
        "tool_plan_by_request_type": copy.deepcopy(tool_plan_by_request_type),
        "retrieval_required_by_request_type": copy.deepcopy(retrieval_enabled_by_request_type),
        "response_policy": copy.deepcopy(response_policy),
        "application_scope": copy.deepcopy(application_scope or {}),
        "response_contract": copy.deepcopy(response_contract or {}),
        "success_criteria": copy.deepcopy(success_criteria or []),
    }


def show_rerank_config_guide(rerank_config: dict[str, Any]) -> None:
    """Display learner-facing guidance for the editable reranking knobs."""
    guide = [
        {
            "knob": "prefer_current_docs / legacy_penalty",
            "changes_behavior_when": "old bulletins compete with current guidance",
            "raise_or_enable_when": "legacy content is being accepted as evidence",
            "current_value": f"{rerank_config.get('prefer_current_docs')} / {rerank_config.get('legacy_penalty')}",
        },
        {
            "knob": "model_match_boost / model_mismatch_penalty",
            "changes_behavior_when": "HX, VX, or AX model names are close enough to confuse retrieval",
            "raise_or_enable_when": "accepted docs mention the wrong model family",
            "current_value": f"{rerank_config.get('model_match_boost')} / {rerank_config.get('model_mismatch_penalty')}",
        },
        {
            "knob": "topic_match_boost",
            "changes_behavior_when": "request wording overlaps weakly with the right document topic",
            "raise_or_enable_when": "a relevant topic is present but ranked too low",
            "current_value": rerank_config.get("topic_match_boost"),
        },
        {
            "knob": "safety_override_boost",
            "changes_behavior_when": "burning, smoke, scorched, or breaker language appears",
            "raise_or_enable_when": "safety escalation evidence is missing from accepted docs",
            "current_value": rerank_config.get("safety_override_boost"),
        },
        {
            "knob": "warranty_policy_boost",
            "changes_behavior_when": "coverage or invoice language appears",
            "raise_or_enable_when": "warranty answers lack policy evidence",
            "current_value": rerank_config.get("warranty_policy_boost"),
        },
    ]
    display(pd.DataFrame(guide))


def show_tool_plan(tool_plan_by_request_type: dict[str, list[str]]) -> None:
    """Display the request-type tool plan as a compact table."""
    rows = [
        {
            "request_type": request_type,
            "planned_tools": " -> ".join(tool_names) if tool_names else "(none)",
        }
        for request_type, tool_names in sorted(tool_plan_by_request_type.items())
    ]
    display(pd.DataFrame(rows))


def show_retrieval_rules(retrieval_enabled_by_request_type: dict[str, bool]) -> None:
    """Display request types that override the default retrieval behavior."""
    rows = [
        {
            "request_type": request_type,
            "retrieval_enabled": enabled,
        }
        for request_type, enabled in sorted(retrieval_enabled_by_request_type.items())
    ]
    display(pd.DataFrame(rows))


def make_application_scope(
    supported_request_types: list[str],
    out_of_scope_request_types: list[str],
) -> dict[str, Any]:
    """Build the project scope object from learner choices."""
    return {
        "user": "field-service technician",
        "workflow_moment": "diagnose equipment issue and decide whether to answer, ask, abstain, or escalate",
        "supported_request_types": supported_request_types,
        "out_of_scope_request_types": out_of_scope_request_types,
        "retrieval_sources": ["service_docs.jsonl"],
        "tool_sources": [
            "get_equipment_record",
            "get_warranty_status",
            "get_maintenance_history",
            "get_ticket_status",
            "recommend_escalation_path",
        ],
        "must_ask_for_more_info_when": [
            "equipment_id or model is missing for model-specific repair guidance",
            "ticket closure is requested without a ticket_id",
        ],
        "must_escalate_when": [
            "safety indicators are present",
            "repeat fault threshold is met",
            "warranty data is unavailable for a coverage decision",
        ],
    }


def make_response_contract() -> dict[str, Any]:
    """Return the editable response contract learners can adapt to their scope."""
    return {
        "answer_summary": "short technician-facing answer",
        "next_checks": ["ordered diagnostic checks or empty list"],
        "coverage_statement": "covered | not_covered | conditional | cannot_verify | not_applicable",
        "evidence": [{"doc_id": "DOC-FC-...", "reason": "why this source matters"}],
        "tool_state": [{"tool_name": "get_...", "status": "found | not_found | unavailable | timeout"}],
        "decision_flags": ["cite_evidence", "ask_for_more_information", "abstain", "escalate"],
        "escalation_path": "team or null",
        "limitations": ["what the app cannot verify"],
    }


def make_success_criteria() -> list[dict[str, str]]:
    """Return default success criteria that can be checked from notebook output."""
    return [
        {"criterion": "Required current documents appear in the evidence set", "measure": "all required_doc_ids found unless the case asks for more information"},
        {"criterion": "Warranty answers use the warranty tool", "measure": "coverage questions include get_warranty_status in tool_state"},
        {"criterion": "Unsafe or unsupported requests do not receive routine repair instructions", "measure": "response includes abstain or escalate flag"},
        {"criterion": "Legacy or irrelevant docs do not drive the final answer", "measure": "must_not_use_doc_ids are absent from accepted evidence"},
    ]


def ensure_helper_core() -> None:
    """Raise a clear error when the published helper library is not available."""
    if Document is None or BM25Retriever is None or ToolRegistry is None:
        raise RuntimeError(
            "ms-ai-ml-helper-core is required for this project pipeline. "
            "Run the install cell, then choose Runtime > Restart session and run from the top. "
            f"Import error: {HELPER_CORE_IMPORT_ERROR}"
        )


def tokenize(text: str) -> list[str]:
    """Split text into simple lowercase tokens for lightweight matching rules."""
    return TOKEN_RE.findall(text.lower())


def build_service_doc_chunks(docs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Split service documents into paragraph chunks with document metadata attached."""
    chunks: list[dict[str, Any]] = []
    for doc in docs:
        paragraphs = [p.strip() for p in doc["text"].split("\n\n") if p.strip()]
        for index, paragraph in enumerate(paragraphs, start=1):
            chunks.append(
                {
                    "chunk_id": f"{doc['doc_id']}#C{index:02d}",
                    "doc_id": doc["doc_id"],
                    "title": doc["title"],
                    "doc_type": doc["doc_type"],
                    "version": doc["version"],
                    "effective_date": doc["effective_date"],
                    "text": paragraph,
                    "topics": doc["topics"],
                    "applies_to_models": doc["applies_to_models"],
                    "current": doc["current"],
                    "safety_level": doc["safety_level"],
                    "supersedes": doc.get("supersedes", []),
                }
            )
    return chunks


def chunk_to_helper_document(chunk: dict[str, Any]) -> Any:
    """Convert one FieldCare chunk into a helper-core Document for BM25 retrieval."""
    searchable_text = "\n".join(
        [
            chunk["title"],
            "Topics: " + ", ".join(chunk["topics"]),
            "Models: " + ", ".join(chunk["applies_to_models"]),
            chunk["text"],
        ]
    )
    return Document(id=chunk["chunk_id"], text=searchable_text, metadata=dict(chunk))


def infer_model_from_request(request_text: str, equipment_record: Optional[dict[str, Any]] = None) -> Optional[str]:
    """Infer the equipment model from trusted tool state first, then from request text."""
    if equipment_record:
        return equipment_record.get("model")
    for model in ["HX-200", "HX-220", "VX-500", "AX-90"]:
        if model.lower() in request_text.lower():
            return model
    return None


def build_fieldcare_pipeline(
    env: dict[str, Any],
    pipeline_design: dict[str, Any],
) -> FieldCarePipeline:
    """Create the helper-backed FieldCare pipeline from loaded assets and design settings."""
    global fieldcare_pipeline
    ensure_helper_core()
    chunks = build_service_doc_chunks(env["service_docs"])
    helper_documents = [chunk_to_helper_document(chunk) for chunk in chunks]
    bm25_retriever = BM25Retriever.from_documents(helper_documents)
    pipeline = FieldCarePipeline(
        env=env,
        chunks=chunks,
        bm25_retriever=bm25_retriever,
        rerank_config=copy.deepcopy(pipeline_design["rerank_config"]),
        tool_plan=copy.deepcopy(pipeline_design["tool_plan_by_request_type"]),
        retrieval_rules=copy.deepcopy(pipeline_design["retrieval_required_by_request_type"]),
        response_policy=copy.deepcopy(pipeline_design["response_policy"]),
        application_scope=copy.deepcopy(pipeline_design.get("application_scope", {})),
        response_contract=copy.deepcopy(pipeline_design.get("response_contract", {})),
        success_criteria=copy.deepcopy(pipeline_design.get("success_criteria", [])),
    )
    pipeline.toolbox = make_fieldcare_toolbox(pipeline)
    register_fieldcare_tools(pipeline)
    pipeline.finalization_status = fieldcare_finalization_check(pipeline)
    fieldcare_pipeline = pipeline
    return pipeline


def make_tool_response(status: str, data: Any, message: str, error_type: Optional[str], source_id: str) -> dict[str, Any]:
    """Create the consistent status object returned by every simulated FieldCare tool."""
    return {
        "status": status,
        "data": data,
        "message": message,
        "error_type": error_type,
        "source_id": source_id,
        "retrieved_at": SIMULATED_CURRENT_DATE,
    }


def make_fieldcare_toolbox(pipeline: FieldCarePipeline) -> dict[str, Callable[..., dict[str, Any]]]:
    """Create tool handlers that read from the loaded FieldCare fixture data."""
    equipment_by_id = {row["equipment_id"]: row for row in pipeline.env["equipment_df"].to_dict("records")}
    tickets_by_id = {row["ticket_id"]: row for row in pipeline.env["tickets_df"].to_dict("records")}
    maintenance_records = pipeline.env["maintenance_df"].to_dict("records")

    def get_equipment_record(equipment_id: str) -> dict[str, Any]:
        """Return structured equipment state for one equipment ID."""
        if not equipment_id:
            return make_tool_response("invalid_input", None, "equipment_id is required.", "missing_argument", "equipment_records.csv")
        record = equipment_by_id.get(equipment_id)
        if not record:
            return make_tool_response("not_found", None, f"No equipment record found for {equipment_id}.", "missing_record", "equipment_records.csv")
        return make_tool_response("found", record, f"Equipment record found for {equipment_id}.", None, "equipment_records.csv")

    def get_ticket_status(ticket_id: str) -> dict[str, Any]:
        """Return current ticket state for one ticket ID."""
        if not ticket_id:
            return make_tool_response("invalid_input", None, "ticket_id is required.", "missing_argument", "service_tickets.csv")
        record = tickets_by_id.get(ticket_id)
        if not record:
            return make_tool_response("not_found", None, f"No ticket found for {ticket_id}.", "missing_record", "service_tickets.csv")
        return make_tool_response("found", record, f"Ticket record found for {ticket_id}.", None, "service_tickets.csv")

    def get_maintenance_history(equipment_id: str, limit: int = 5, issue_category: Optional[str] = None) -> dict[str, Any]:
        """Return recent maintenance records for one equipment ID."""
        if not equipment_id:
            return make_tool_response("invalid_input", None, "equipment_id is required.", "missing_argument", "maintenance_history.csv")
        rows = [row for row in maintenance_records if row["equipment_id"] == equipment_id]
        if issue_category:
            issue = issue_category.lower()
            rows = [row for row in rows if issue in row["observed_issue"].lower() or issue in row["visit_type"].lower()]
        rows = sorted(rows, key=lambda row: row["service_date"], reverse=True)[:limit]
        status = "found" if rows else "not_found"
        return make_tool_response(status, rows, f"{len(rows)} maintenance record(s) found.", None if rows else "empty_result", "maintenance_history.csv")

    def get_warranty_status(equipment_id: str, service_date: Optional[str] = None) -> dict[str, Any]:
        """Return fixture warranty status for one equipment ID and service date."""
        if equipment_id == "EQ-FC-TIMEOUT":
            return make_tool_response("timeout", None, "Warranty service did not respond inside the client timeout.", "timeout", "warranty_service_fixture")
        equipment = equipment_by_id.get(equipment_id)
        if not equipment:
            return make_tool_response("not_found", None, f"No equipment record found for {equipment_id}.", "missing_record", "warranty_service_fixture")
        status = equipment["warranty_status"]
        if equipment_id == "EQ-FC-1006":
            return make_tool_response("unavailable", None, "Warranty data is unavailable during asset migration.", "upstream_unavailable", "warranty_service_fixture")
        if status == "active":
            data = {
                "coverage_state": "active",
                "parts_coverage": "active",
                "labor_coverage": "active_when_policy_conditions_match",
                "exclusions": [],
                "confidence": "high",
                "service_date": service_date or SIMULATED_CURRENT_DATE,
            }
        elif status == "active_limited":
            data = {
                "coverage_state": "active_limited",
                "parts_coverage": "active",
                "labor_coverage": "excluded_pending_review",
                "exclusions": ["unapproved_relocation"],
                "confidence": "medium",
                "service_date": service_date or SIMULATED_CURRENT_DATE,
            }
        elif status == "expired":
            data = {
                "coverage_state": "expired",
                "parts_coverage": "expired",
                "labor_coverage": "expired",
                "exclusions": ["warranty_period_ended"],
                "confidence": "high",
                "service_date": service_date or SIMULATED_CURRENT_DATE,
            }
        else:
            data = {
                "coverage_state": status,
                "parts_coverage": "unknown",
                "labor_coverage": "unknown",
                "exclusions": ["unsupported_or_unknown_status"],
                "confidence": "low",
                "service_date": service_date or SIMULATED_CURRENT_DATE,
            }
        return make_tool_response("found", data, f"Warranty state for {equipment_id}: {data['coverage_state']}.", None, "warranty_service_fixture")

    def recommend_escalation_path(equipment_id: str, ticket_id: str, reason_code: str) -> dict[str, Any]:
        """Return the recommended human routing path for a known escalation reason."""
        if not equipment_id or not ticket_id:
            return make_tool_response("invalid_input", None, "equipment_id and ticket_id are required for routing.", "missing_argument", "routing_fixture")
        team_by_reason = {
            "safety_indicator": "Safety Engineering",
            "repeat_fault": "Field Engineering",
            "unsupported_model": "Legacy Service Desk",
            "warranty_unavailable": "Warranty Operations",
            "permission_failure": "Authorized Account Owner",
        }
        team = team_by_reason.get(reason_code)
        if not team:
            return make_tool_response("invalid_input", None, f"Unsupported reason_code: {reason_code}.", "invalid_reason_code", "routing_fixture")
        data = {
            "recommended_team": team,
            "reason_code": reason_code,
            "ticket_id": ticket_id,
            "equipment_id": equipment_id,
            "note": "Recommendation only. No ticket action was performed.",
        }
        return make_tool_response("found", data, f"Route to {team}.", None, "routing_fixture")

    def search_service_docs(query: str, model: Optional[str] = None, topics: Optional[list[str]] = None, top_k: int = 5) -> dict[str, Any]:
        """Run documentation search through the same helper-backed retrieval and reranking path."""
        query_with_topics = " ".join([query, " ".join(topics or [])]).strip()
        candidates = retrieve_service_docs(pipeline, query_with_topics, top_k=min(max(top_k * 2, top_k), 10))
        equipment_record = {"model": model} if model else None
        rows = rerank_service_docs(pipeline, query, candidates, equipment_record=equipment_record)[:top_k]
        data = [
            {
                "doc_id": row["doc_id"],
                "chunk_id": row["chunk_id"],
                "title": row["title"],
                "score": row["rerank_score"],
                "current": row["current"],
                "preview": row["text"][:220] + ("..." if len(row["text"]) > 220 else ""),
            }
            for row in rows
        ]
        status = "found" if data else "not_found"
        return make_tool_response(status, data, f"{len(data)} documentation chunk(s) found.", None if data else "empty_result", "service_docs.jsonl")

    return {
        "get_equipment_record": get_equipment_record,
        "get_warranty_status": get_warranty_status,
        "get_maintenance_history": get_maintenance_history,
        "get_ticket_status": get_ticket_status,
        "search_service_docs": search_service_docs,
        "recommend_escalation_path": recommend_escalation_path,
    }


def register_fieldcare_tools(pipeline: FieldCarePipeline) -> None:
    """Register all FieldCare tool schemas with helper-core ToolRegistry."""
    registry = ToolRegistry()
    registered_names: list[str] = []
    for schema in pipeline.env["tool_schemas"]["tools"]:
        handler = pipeline.toolbox.get(schema["name"])
        if handler is None:
            continue
        registry.register(
            name=schema["name"],
            description=schema["description"],
            parameters=schema["parameters"],
            handler=handler,
        )
        registered_names.append(schema["name"])
    pipeline.tool_registry = registry
    pipeline.registered_tool_names = registered_names
    pipeline.openrouter_tool_definitions = registry.to_openrouter_tools()


def fieldcare_finalization_check(pipeline: FieldCarePipeline) -> dict[str, Any]:
    """Assert that the pipeline uses helper-core retrieval and registered tools."""
    checks = {
        "helper_core_available": Document is not None and BM25Retriever is not None and ToolRegistry is not None,
        "retrieval_backend": "BM25Retriever" if pipeline.bm25_retriever is not None else "missing",
        "indexed_chunks": len(pipeline.chunks),
        "registered_tool_count": len(pipeline.registered_tool_names),
        "registered_tool_names": pipeline.registered_tool_names,
        "service_docs_registered_as_tool": "search_service_docs" in pipeline.registered_tool_names,
        "openrouter_tool_definition_count": len(pipeline.openrouter_tool_definitions),
        "supported_request_type_count": len(pipeline.application_scope.get("supported_request_types", [])),
        "out_of_scope_request_type_count": len(pipeline.application_scope.get("out_of_scope_request_types", [])),
        "response_contract_fields": list(pipeline.response_contract),
        "success_criteria_count": len(pipeline.success_criteria),
    }
    failures: list[str] = []
    if not checks["helper_core_available"]:
        failures.append("ms-ai-ml-helper-core did not import.")
    if checks["retrieval_backend"] != "BM25Retriever":
        failures.append("Retrieval is not using helper-core BM25Retriever.")
    if checks["registered_tool_count"] != len(pipeline.env["tool_schemas"]["tools"]):
        failures.append("Not all FieldCare tools are registered with helper-core ToolRegistry.")
    if not checks["service_docs_registered_as_tool"]:
        failures.append("search_service_docs is not available through ToolRegistry.")
    if failures:
        raise AssertionError("FieldCare helper-core finalization check failed: " + " ".join(failures))
    return checks


def retrieve_service_docs(pipeline: FieldCarePipeline, query: str, top_k: int = 8) -> list[dict[str, Any]]:
    """Return BM25-ranked service-document chunks from helper-core."""
    matches = pipeline.bm25_retriever.search(query, top_k=top_k)
    max_score = max((match.keyword_score for match in matches), default=1.0)
    rows: list[dict[str, Any]] = []
    for match in matches:
        baseline_score = match.keyword_score / max_score if max_score else 0.0
        rows.append(
            {
                **match.document.metadata,
                "baseline_score": round(baseline_score, 4),
                "raw_bm25_score": round(match.keyword_score, 4),
                "retrieval_backend": "BM25Retriever",
            }
        )
    return rows


def rerank_service_docs(
    pipeline: FieldCarePipeline,
    query: str,
    candidates: list[dict[str, Any]],
    equipment_record: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    """Rerank BM25 candidates using current-document, model, safety, and policy signals."""
    config = pipeline.rerank_config
    model = infer_model_from_request(query, equipment_record)
    query_tokens = set(tokenize(query))
    reranked: list[dict[str, Any]] = []
    for row in candidates:
        score = row["baseline_score"]

        if config["prefer_current_docs"] and not row["current"]:
            score -= config["legacy_penalty"]
        if model and model in row["applies_to_models"]:
            score += config["model_match_boost"]
        if model and row["applies_to_models"] and model not in row["applies_to_models"]:
            score -= config["model_mismatch_penalty"]
        if model and row["doc_type"] == "product_note" and model in row["applies_to_models"]:
            score += config["product_note_model_boost"]
        if model and row["doc_type"] == "product_note" and model in row["applies_to_models"] and any(term in query_tokens for term in ["vx", "hx", "model", "guidance", "trust"]):
            score += config["model_conflict_note_boost"]
        if any(topic_token in query_tokens for topic in row["topics"] for topic_token in tokenize(topic)):
            score += config["topic_match_boost"]
        if row["safety_level"] == "critical" and any(term in query_tokens for term in ["burning", "smoke", "scorched", "breaker"]):
            score += config["safety_override_boost"]
        if row["doc_id"] == "DOC-FC-WAR-004" and any(term in query_tokens for term in ["warranty", "covered", "coverage", "invoice", "pay"]):
            score += config["warranty_policy_boost"]
        if row["doc_id"] == "DOC-FC-MP-014" and any(term in query_tokens for term in ["filter", "filters", "replacement", "replace", "airflow", "dusty", "parts"]):
            score += config["filter_procedure_boost"]
        if row["doc_id"] == "DOC-FC-TS-001" and any(term in query_tokens for term in ["overheating", "overheat", "hot", "e", "117"]):
            score += config["overheat_triage_boost"]
        if row["doc_id"] == "DOC-FC-TS-009" and any(term in query_tokens for term in ["sensor", "sensors", "calibration", "drift", "e", "221"]):
            score += config["sensor_workflow_boost"]
        if row["doc_id"] == "DOC-FC-ESC-007" and any(term in query_tokens for term in ["again", "repeat", "recurring", "callback", "third", "escalate"]):
            score += config["repeat_fault_policy_boost"]
        if row["doc_id"] in ["DOC-FC-TS-001", "DOC-FC-MP-014"] and any(term in query_tokens for term in ["2019", "legacy", "bulletin", "reset", "superseded"]):
            score += config["superseded_current_doc_boost"]

        reranked.append({**row, "rerank_score": round(score, 4)})
    return sorted(reranked, key=lambda row: row["rerank_score"], reverse=True)


def show_evidence(rows: list[dict[str, Any]], score_column: str = "rerank_score", columns: Optional[list[str]] = None) -> None:
    """Display document evidence as a compact table."""
    if not rows:
        display(Markdown("_No document evidence selected for this request._"))
        return
    if columns is None:
        columns = ["chunk_id", "doc_id", "title", "current", "safety_level", score_column, "text"]
    display(pd.DataFrame(rows)[columns])


def show_retrieval_comparison(pipeline: FieldCarePipeline, request_id: str, top_k: int = 5) -> None:
    """Display baseline BM25 candidates beside the reranked evidence set."""
    request = request_by_id(pipeline.env, request_id)
    baseline_candidates = retrieve_service_docs(pipeline, request["request_text"], top_k=max(top_k, 8))
    tool_results = execute_planned_tools(pipeline, request)
    accepted = accepted_evidence(pipeline, request, tool_results, top_k=top_k)
    display(Markdown(f"### Retrieval trace for `{request_id}`"))
    display(Markdown(f"> {request['request_text']}"))
    display(Markdown("**Baseline BM25 candidates**"))
    show_evidence(baseline_candidates, "baseline_score", ["chunk_id", "doc_id", "title", "current", "baseline_score"])
    display(Markdown("**Accepted reranked evidence**"))
    show_evidence(accepted, "rerank_score", ["chunk_id", "doc_id", "title", "current", "rerank_score"])


def show_registered_tools(pipeline: FieldCarePipeline) -> None:
    """Display the tool registry status for the FieldCare app."""
    pretty(
        {
            "helper_core_finalization_check": pipeline.finalization_status,
            "available_tools": list(pipeline.toolbox),
            "schema_count": len(pipeline.env["tool_schemas"]["tools"]),
            "openrouter_tool_definition_count": len(pipeline.openrouter_tool_definitions),
        }
    )


def show_documentation_tool_check(pipeline: FieldCarePipeline) -> Any:
    """Execute the documentation-search tool through ToolRegistry and display the result."""
    execution = pipeline.tool_registry.execute_tool_call(
        {
            "id": "fieldcare-tool-check-search-docs",
            "function": {
                "name": "search_service_docs",
                "arguments": json.dumps(
                    {
                        "query": "HX-200 overheating after filter replacement",
                        "model": "HX-200",
                        "topics": ["overheating", "filter replacement"],
                        "top_k": 3,
                    },
                    ensure_ascii=False,
                ),
            },
        }
    )
    pretty(
        {
            "registered_search_service_docs_check": {
                "ok": execution.ok,
                "tool_name": execution.name,
                "tool_call_id": execution.tool_call_id,
                "result": json.loads(execution.content),
            }
        }
    )
    return execution


def extract_known_ids(text: str) -> dict[str, Optional[str]]:
    """Extract FieldCare equipment and ticket IDs from request text."""
    values = ID_RE.findall(text)
    equipment_id = next((value for value in values if value.startswith("EQ-FC-")), None)
    ticket_id = next((value for value in values if value.startswith("TCK-FC-")), None)
    return {"equipment_id": equipment_id, "ticket_id": ticket_id}


def request_ids_for(request: dict[str, Any]) -> dict[str, str]:
    """Resolve equipment and ticket IDs from request text or structured request fields."""
    extracted = extract_known_ids(request["request_text"])
    return {
        "equipment_id": extracted["equipment_id"] or request.get("equipment_id") or "",
        "ticket_id": extracted["ticket_id"] or request.get("ticket_id") or "",
    }


def should_retrieve(pipeline: FieldCarePipeline, request: dict[str, Any]) -> bool:
    """Return whether this request type should run document retrieval."""
    return pipeline.retrieval_rules.get(request["request_type"], True)


def infer_escalation_reason(
    pipeline: FieldCarePipeline,
    request: dict[str, Any],
    tool_results: list[dict[str, Any]],
) -> Optional[str]:
    """Infer the reason code required by the escalation-routing tool."""
    text = request["request_text"].lower()
    request_type = request["request_type"]
    if any(term in text for term in ["burning", "smoke", "scorched", "breaker"]):
        return "safety_indicator"
    if any(term in text for term in ["permission", "cannot access", "not authorized"]):
        return "permission_failure"
    if any(row["tool_name"] == "get_warranty_status" and row["result"]["status"] in ["unavailable", "timeout", "permission_denied"] for row in tool_results):
        return "warranty_unavailable"
    equipment = next((row["result"]["data"] for row in tool_results if row["tool_name"] == "get_equipment_record" and row["result"]["status"] == "found"), None)
    if equipment and equipment.get("warranty_status") == "unsupported_model":
        return "unsupported_model"
    if request_type in ["repeat_fault_escalation", "troubleshooting_plus_warranty"] or any(term in text for term in ["again", "repeat", "recurring", "callback", "third"]):
        return "repeat_fault"
    return None


def build_tool_args(
    pipeline: FieldCarePipeline,
    tool_name: str,
    request: dict[str, Any],
    tool_results: list[dict[str, Any]],
) -> Optional[dict[str, Any]]:
    """Build validated tool arguments from the current request and prior tool results."""
    ids = request_ids_for(request)
    equipment_id = ids["equipment_id"]
    ticket_id = ids["ticket_id"]
    if tool_name == "get_equipment_record":
        return {"equipment_id": equipment_id}
    if tool_name == "get_warranty_status":
        return {"equipment_id": equipment_id, "service_date": SIMULATED_CURRENT_DATE}
    if tool_name == "get_maintenance_history":
        return {"equipment_id": equipment_id, "limit": 5}
    if tool_name == "get_ticket_status":
        return {"ticket_id": ticket_id}
    if tool_name == "recommend_escalation_path":
        reason_code = infer_escalation_reason(pipeline, request, tool_results)
        if reason_code is None:
            return None
        return {"equipment_id": equipment_id, "ticket_id": ticket_id, "reason_code": reason_code}
    return None


def execute_registered_tool(
    pipeline: FieldCarePipeline,
    tool_name: str,
    args: dict[str, Any],
    call_index: int,
) -> dict[str, Any]:
    """Execute one tool call through helper-core ToolRegistry and normalize its result."""
    tool_call = {
        "id": f"fieldcare-tool-call-{call_index:02d}",
        "function": {"name": tool_name, "arguments": json.dumps(args, ensure_ascii=False)},
    }
    execution = pipeline.tool_registry.execute_tool_call(tool_call)
    try:
        payload = json.loads(execution.content)
    except json.JSONDecodeError:
        payload = {"raw_content": execution.content}
    if execution.ok:
        result = payload
    else:
        result = make_tool_response(
            "invalid_input",
            None,
            payload.get("message", "Tool execution failed."),
            payload.get("error_type", execution.error_type),
            "ms-ai-ml-helper-core.ToolRegistry",
        )
    return {
        "tool_name": execution.name or tool_name,
        "args": args,
        "result": result,
        "registry_validated": True,
        "tool_call_id": execution.tool_call_id,
        "retryable": execution.retryable,
    }


def execute_planned_tools(pipeline: FieldCarePipeline, request: dict[str, Any]) -> list[dict[str, Any]]:
    """Run the request-type tool plan in order and return a visible trace."""
    results: list[dict[str, Any]] = []
    for tool_name in pipeline.tool_plan.get(request["request_type"], []):
        args = build_tool_args(pipeline, tool_name, request, results)
        if args is None:
            continue
        results.append(execute_registered_tool(pipeline, tool_name, args, len(results) + 1))
    return results


def accepted_evidence(
    pipeline: FieldCarePipeline,
    request: dict[str, Any],
    tool_results: list[dict[str, Any]],
    top_k: int = 5,
) -> list[dict[str, Any]]:
    """Select the final evidence chunks that should enter the model-ready context."""
    if not should_retrieve(pipeline, request):
        return []
    equipment_result = next((row["result"] for row in tool_results if row["tool_name"] == "get_equipment_record" and row["result"]["status"] == "found"), None)
    equipment_record = equipment_result["data"] if equipment_result else None
    model = infer_model_from_request(request["request_text"], equipment_record)
    search_query = f"{request['request_text']} {model or ''}".strip()
    candidates = retrieve_service_docs(pipeline, search_query, top_k=len(pipeline.chunks))
    ranked = rerank_service_docs(pipeline, request["request_text"], candidates, equipment_record=equipment_record)
    accepted: list[dict[str, Any]] = []
    seen_doc_ids: set[str] = set()
    for row in ranked:
        if not row["current"]:
            continue
        if model and row["applies_to_models"] and model not in row["applies_to_models"]:
            continue
        if row["doc_id"] in seen_doc_ids:
            continue
        accepted.append(row)
        seen_doc_ids.add(row["doc_id"])
        if len(accepted) >= top_k:
            break
    return accepted


def classify_decision_flags(
    pipeline: FieldCarePipeline,
    request: dict[str, Any],
    evidence: list[dict[str, Any]],
    tool_results: list[dict[str, Any]],
) -> list[str]:
    """Create response-control flags from request type, evidence, and tool state."""
    flags: set[str] = set()
    text = request["request_text"].lower()
    request_type = request["request_type"]
    ids = request_ids_for(request)
    policy = pipeline.response_policy
    scope = pipeline.application_scope or {}
    supported_types = set(scope.get("supported_request_types", []))
    out_of_scope_types = set(scope.get("out_of_scope_request_types", []))
    if request_type in out_of_scope_types or (supported_types and request_type not in supported_types):
        flags.update(["scope_boundary", "abstain"])
    if request_type in ["incomplete_request", "insufficient_information"] or (not ids["equipment_id"] and any(term in text for term in ["unit", "close", "covered", "warranty"])):
        if policy["ask_before_model_specific_guidance_when_ids_missing"]:
            flags.update(["ask_for_more_information", "abstain"])
    if request_type == "ticket_status_only":
        flags.add("ticket_state_only")
    if request_type == "unsupported_business_promise" or ("promise" in text and "invoice" in text):
        flags.update(["business_boundary", "mention_coverage_condition", "abstain"])
    if any(term in text for term in ["warranty", "covered", "coverage", "invoice"]):
        flags.add("mention_coverage_condition")
    if any(term in text for term in ["permission", "cannot access", "not authorized"]):
        flags.update(["permission_or_workflow_boundary", "escalate"])
    if any(term in text for term in ["burning", "smoke", "scorched", "breaker"]):
        if policy["abstain_on_safety"]:
            flags.update(["safety_escalation", "abstain", "escalate"])
    if any(row["result"]["status"] in ["unavailable", "timeout", "permission_denied"] for row in tool_results):
        if policy["route_when_warranty_unavailable"]:
            flags.update(["mention_uncertainty", "abstain", "escalate"])
    equipment = next((row["result"]["data"] for row in tool_results if row["tool_name"] == "get_equipment_record" and row["result"]["status"] == "found"), None)
    if equipment and equipment.get("warranty_status") == "unsupported_model":
        if policy["abstain_on_unsupported_model"]:
            flags.update(["unsupported_model", "abstain", "escalate"])
    maintenance = next((row["result"]["data"] for row in tool_results if row["tool_name"] == "get_maintenance_history" and row["result"]["status"] == "found"), [])
    if maintenance and (request_type in ["sensor_plus_warranty", "expired_warranty"] or any(term in text for term in ["again", "third", "callback", "replacement"])):
        flags.add("history_changes_answer")
    if request_type == "reranking_distractor":
        flags.add("reject_irrelevant_evidence")
    if request_type == "conflicting_documentation":
        flags.add("reject_outdated_evidence")
    if any(row["doc_id"] == "DOC-FC-ESC-007" for row in evidence) and request["request_type"] in ["repeat_fault_escalation", "troubleshooting_plus_warranty"]:
        if policy["route_repeat_faults"]:
            flags.add("escalate")
    if any(row["tool_name"] == "recommend_escalation_path" and row["result"]["status"] == "found" for row in tool_results):
        flags.add("escalate")
    if evidence and policy["cite_evidence_when_available"]:
        flags.add("cite_evidence")
    return sorted(flags)


def assemble_fieldcare_context(pipeline: FieldCarePipeline, request: dict[str, Any]) -> dict[str, Any]:
    """Assemble the model-ready context from request, retrieval, tools, and flags."""
    tool_results = execute_planned_tools(pipeline, request)
    evidence = accepted_evidence(pipeline, request, tool_results)
    return assemble_fieldcare_context_from_parts(pipeline, request, tool_results, evidence)


def assemble_fieldcare_context_from_parts(
    pipeline: FieldCarePipeline,
    request: dict[str, Any],
    tool_results: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
) -> dict[str, Any]:
    """Assemble context from already inspected tool results and accepted evidence."""
    flags = classify_decision_flags(pipeline, request, evidence, tool_results)
    return {
        "request": request,
        "retrieved_evidence": [
            {
                "chunk_id": row["chunk_id"],
                "doc_id": row["doc_id"],
                "title": row["title"],
                "current": row["current"],
                "score": row["rerank_score"],
                "preview": row["text"][:260] + ("..." if len(row["text"]) > 260 else ""),
            }
            for row in evidence
        ],
        "tool_results": tool_results,
        "decision_flags": flags,
    }


def draft_fieldcare_response(pipeline: FieldCarePipeline, context: dict[str, Any]) -> dict[str, Any]:
    """Create the deterministic response object that learners can refine or compare to a model draft."""
    request = context["request"]
    flags = context["decision_flags"]
    tool_state = [
        {
            "tool_name": row["tool_name"],
            "status": row["result"]["status"],
            "message": row["result"]["message"],
            "registry_validated": row.get("registry_validated", False),
        }
        for row in context["tool_results"]
    ]
    evidence = [{"doc_id": row["doc_id"], "chunk_id": row["chunk_id"], "title": row["title"]} for row in context["retrieved_evidence"][:4]]
    warranty_result = next((row["result"] for row in context["tool_results"] if row["tool_name"] == "get_warranty_status"), None)
    escalation_result = next((row["result"] for row in context["tool_results"] if row["tool_name"] == "recommend_escalation_path" and row["result"]["status"] == "found"), None)

    if "safety_escalation" in flags:
        summary = "Stop routine troubleshooting and escalate to Safety Engineering before repair guidance."
    elif "unsupported_model" in flags:
        summary = "FieldCare should not guide this repair because the model is outside support scope."
    elif "scope_boundary" in flags:
        summary = "FieldCare should not answer this as a normal supported request because it is outside the current application scope."
    elif "ask_for_more_information" in flags and not evidence:
        summary = "Ask for the equipment ID, ticket ID, model, error codes, and current readings before advising."
    elif "mention_uncertainty" in flags:
        summary = "The application cannot verify one required tool result, so it should route before making a confident claim."
    elif "escalate" in flags:
        summary = "Continue with targeted checks, but escalate because repeat-fault or ticket-state evidence requires review."
    else:
        summary = "Use the retrieved FieldCare evidence and available tool state to answer within scope."

    if warranty_result and warranty_result["status"] in ["unavailable", "timeout", "permission_denied"]:
        coverage_statement = "cannot_verify"
    elif warranty_result and warranty_result["status"] == "found" and warranty_result["data"].get("coverage_state") == "expired":
        coverage_statement = "not_covered"
    elif "mention_coverage_condition" in flags:
        coverage_statement = "conditional"
    else:
        coverage_statement = "not_applicable"

    if escalation_result:
        escalation_path = escalation_result["data"]["recommended_team"]
    elif "permission_or_workflow_boundary" in flags or (warranty_result and warranty_result["status"] in ["unavailable", "timeout", "permission_denied"]):
        escalation_path = "Warranty Operations"
    elif "unsupported_model" in flags:
        escalation_path = "Legacy Service Desk"
    elif "safety_escalation" in flags:
        escalation_path = "Safety Engineering"
    elif "escalate" in flags:
        escalation_path = "Field Engineering or owning operations team"
    else:
        escalation_path = None

    return {
        "request_id": request["request_id"],
        "answer_summary": summary,
        "next_checks": ["Inspect accepted evidence and tool state before writing the final technician response."],
        "coverage_statement": coverage_statement,
        "evidence": evidence,
        "tool_state": tool_state,
        "decision_flags": flags,
        "escalation_path": escalation_path,
        "limitations": ["Deterministic response drafting keeps the evaluation inspectable; learners can refine response rules or compare with the optional model draft."],
    }


def run_fieldcare_pipeline(pipeline: FieldCarePipeline, request_id: str) -> dict[str, Any]:
    """Run the complete FieldCare path for one request ID."""
    request = request_by_id(pipeline.env, request_id)
    context = assemble_fieldcare_context(pipeline, request)
    response = draft_fieldcare_response(pipeline, context)
    return {"context": context, "response": response}


def require_active_pipeline() -> FieldCarePipeline:
    """Return the current pipeline or raise a helpful setup error."""
    if fieldcare_pipeline is None:
        raise RuntimeError("Run section 7 to build `fieldcare_pipeline` before calling this helper.")
    return fieldcare_pipeline


def baseline_retrieve(query: str, top_k: int = 8) -> list[dict[str, Any]]:
    """Learner-facing wrapper for helper-core BM25 retrieval."""
    return retrieve_service_docs(require_active_pipeline(), query, top_k=top_k)


def rerank_candidates(
    query: str,
    candidates: list[dict[str, Any]],
    equipment_record: Optional[dict[str, Any]] = None,
) -> list[dict[str, Any]]:
    """Learner-facing wrapper for the FieldCare reranking rules."""
    return rerank_service_docs(require_active_pipeline(), query, candidates, equipment_record=equipment_record)


def execute_tool_plan(request: dict[str, Any]) -> list[dict[str, Any]]:
    """Learner-facing wrapper for the request-type tool plan."""
    return execute_planned_tools(require_active_pipeline(), request)


def assemble_context(request: dict[str, Any]) -> dict[str, Any]:
    """Learner-facing wrapper for model-ready context assembly."""
    return assemble_fieldcare_context(require_active_pipeline(), request)


def draft_starter_response(context: dict[str, Any]) -> dict[str, Any]:
    """Backward-compatible wrapper for deterministic response drafting."""
    return draft_fieldcare_response(require_active_pipeline(), context)


def draft_application_response(context: dict[str, Any]) -> dict[str, Any]:
    """Learner-facing wrapper for deterministic application response drafting."""
    return draft_fieldcare_response(require_active_pipeline(), context)


def run_fieldcare_app(request_id: str) -> dict[str, Any]:
    """Learner-facing wrapper for the full FieldCare application run."""
    return run_fieldcare_pipeline(require_active_pipeline(), request_id)


def make_custom_request(
    request_text: str,
    request_type: str,
    equipment_id: str = "",
    ticket_id: str = "",
    expected_sources: Optional[list[str]] = None,
    preferred_behavior: str = "Learner task: describe the behavior this custom request should produce.",
) -> dict[str, Any]:
    """Create a custom request row learners can send through the same FieldCare path."""
    return {
        "request_id": "CUSTOM-FC-001",
        "request_text": request_text,
        "equipment_id": equipment_id,
        "ticket_id": ticket_id,
        "request_type": request_type,
        "expected_sources": expected_sources or ["retrieval"],
        "difficulty": "custom",
        "preferred_behavior": preferred_behavior,
    }


def run_fieldcare_request(pipeline: FieldCarePipeline, request: dict[str, Any]) -> dict[str, Any]:
    """Run the complete FieldCare path for a request dictionary, including custom requests."""
    context = assemble_fieldcare_context(pipeline, request)
    response = draft_fieldcare_response(pipeline, context)
    return {"request": request, "context": context, "response": response}


def show_tool_trace(pipeline: FieldCarePipeline, request_id: str) -> None:
    """Display planned tool calls, arguments, statuses, and registry validation."""
    request = request_by_id(pipeline.env, request_id)
    tool_results = execute_planned_tools(pipeline, request)
    rows = [
        {
            "tool_name": row["tool_name"],
            "args": row["args"],
            "status": row["result"]["status"],
            "message": row["result"]["message"],
            "registry_validated": row["registry_validated"],
        }
        for row in tool_results
    ]
    display(pd.DataFrame(rows) if rows else Markdown("_No tools planned for this request type._"))


def show_context_trace(context: dict[str, Any]) -> None:
    """Display the context handoff in three learner-readable parts."""
    display(Markdown("**Retrieved evidence**"))
    show_evidence(context["retrieved_evidence"], "score", ["doc_id", "chunk_id", "title", "current", "score"])
    display(Markdown("**Tool results**"))
    tool_rows = [
        {
            "tool_name": row["tool_name"],
            "status": row["result"]["status"],
            "message": row["result"]["message"],
            "registry_validated": row["registry_validated"],
        }
        for row in context["tool_results"]
    ]
    display(pd.DataFrame(tool_rows) if tool_rows else Markdown("_No tool results for this request._"))
    display(Markdown("**Decision flags**"))
    pretty(context["decision_flags"])


def show_tool_results_table(tool_results: list[dict[str, Any]]) -> None:
    """Display tool execution results without exposing helper internals."""
    rows = [
        {
            "tool_name": row["tool_name"],
            "args": row["args"],
            "status": row["result"]["status"],
            "message": row["result"]["message"],
            "source_id": row["result"]["source_id"],
            "registry_validated": row["registry_validated"],
        }
        for row in tool_results
    ]
    display(pd.DataFrame(rows) if rows else Markdown("_No tools planned for this request type._"))


def show_orchestration_summary(
    request: dict[str, Any],
    baseline_candidates: list[dict[str, Any]],
    tool_results: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    context: dict[str, Any],
    response: dict[str, Any],
) -> None:
    """Display one complete FieldCare orchestration in the order the app runs it."""
    display(Markdown(f"### 1. User request: `{request['request_id']}`"))
    display(Markdown(f"> {request['request_text']}"))
    pretty(
        {
            "request_type": request["request_type"],
            "equipment_id": request.get("equipment_id") or "(missing)",
            "ticket_id": request.get("ticket_id") or "(missing)",
            "expected_sources": request.get("expected_sources", []),
            "preferred_behavior": request.get("preferred_behavior", ""),
        }
    )

    display(Markdown("### 2. Baseline retrieval candidates"))
    show_evidence(baseline_candidates, "baseline_score", ["chunk_id", "doc_id", "title", "current", "baseline_score"])

    display(Markdown("### 3. Registered business tools"))
    show_tool_results_table(tool_results)

    display(Markdown("### 4. Accepted evidence after reranking and filtering"))
    show_evidence(evidence, "rerank_score", ["chunk_id", "doc_id", "title", "current", "rerank_score"])

    display(Markdown("### 5. Model-ready context"))
    show_context_trace(context)

    display(Markdown("### 6. Application response object"))
    pretty(response)

    display(Markdown("### 7. What this trace proves"))
    pretty(
        {
            "docs_used": [row["doc_id"] for row in context["retrieved_evidence"]],
            "tools_used": [row["tool_name"] for row in context["tool_results"]],
            "decision_flags": context["decision_flags"],
            "safe_next_move": response["answer_summary"],
        }
    )


def show_extension_points() -> None:
    """Display the learner-facing surfaces that are intended for project customization."""
    display(
        pd.DataFrame(
            [
                {
                    "surface": "APPLICATION_SCOPE",
                    "use_when": "you want to support a narrower or different request family",
                    "change_example": "move unsupported or unsafe requests out of scope",
                },
                {
                    "surface": "RESPONSE_CONTRACT",
                    "use_when": "your app needs a different structured output shape",
                    "change_example": "add a field for customer-safe summary or technician-only notes",
                },
                {
                    "surface": "RERANK_CONFIG",
                    "use_when": "the right document appears but ranks too low",
                    "change_example": "increase model-match, safety, warranty, or current-document weight",
                },
                {
                    "surface": "TOOL_PLAN_BY_REQUEST_TYPE",
                    "use_when": "the app needs structured state before answering",
                    "change_example": "add `get_ticket_status` for a ticket-state request",
                },
                {
                    "surface": "RETRIEVAL_ENABLED_BY_REQUEST_TYPE",
                    "use_when": "retrieval creates noise for a state-only request",
                    "change_example": "disable retrieval for ticket-status-only questions",
                },
                {
                    "surface": "RESPONSE_POLICY",
                    "use_when": "the evidence is right but the response behavior is unsafe or unclear",
                    "change_example": "route when warranty is unavailable or abstain on safety indicators",
                },
            ]
        )
    )


def show_pipeline_result(pipeline: FieldCarePipeline, request_id: str) -> dict[str, Any]:
    """Run one request and display context plus response evidence."""
    result = run_fieldcare_pipeline(pipeline, request_id)
    display(Markdown(f"### End-to-end run for `{request_id}`"))
    display(Markdown(f"> {result['context']['request']['request_text']}"))
    show_context_trace(result["context"])
    display(Markdown("**Response object**"))
    pretty(result["response"])
    return result


def generate_model_response(
    context: dict[str, Any],
    run_live_model: bool = False,
    model_id: str = "google/gemini-3.1-flash-lite",
) -> str:
    """Generate optional model wording from the assembled context using OpenRouter."""
    if not run_live_model:
        return "Live model call skipped. Set RUN_LIVE_MODEL = True only when instructed and when OPENROUTER_API_KEY is available."
    if OpenRouterClient is None:
        return "OpenRouterClient is unavailable in this runtime."
    if not load_openrouter_key(required=False):
        return "OPENROUTER_API_KEY is not available."

    client = OpenRouterClient(app_title="fieldcare-sprint-4-project")
    messages = [
        {
            "role": "system",
            "content": (
                "You are a HelioDesk FieldCare assistant. Answer only from the supplied context. "
                "Preserve decision_flags. If a flag says ask, abstain, or escalate, do that visibly. "
                "Cite doc_id values and tool statuses."
            ),
        },
        {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
    ]
    response = client.chat(messages, model=model_id, temperature=0, max_tokens=700)
    return response.content or ""


def request_for_eval_case(pipeline: FieldCarePipeline, eval_case: dict[str, Any]) -> dict[str, Any]:
    """Build the request row used for an evaluation case, including fixture-specific text."""
    request = request_by_id(pipeline.env, eval_case["request_id"])
    if eval_case["input"] != request["request_text"]:
        request["request_text"] = eval_case["input"]
        ids = extract_known_ids(eval_case["input"])
        if ids["equipment_id"] is not None:
            request["equipment_id"] = ids["equipment_id"]
        if ids["ticket_id"] is not None:
            request["ticket_id"] = ids["ticket_id"]
    return request


def evaluate_case(pipeline: FieldCarePipeline, eval_case: dict[str, Any]) -> dict[str, Any]:
    """Compare one actual pipeline run against one reusable evaluation case."""
    request = request_for_eval_case(pipeline, eval_case)
    context = assemble_fieldcare_context(pipeline, request)
    response = draft_fieldcare_response(pipeline, context)

    actual_doc_ids = {row["doc_id"] for row in context["retrieved_evidence"]}
    actual_tools = {row["tool_name"] for row in context["tool_results"]}
    actual_flags = set(response["decision_flags"])

    required_docs = set(eval_case["required_doc_ids"])
    required_tools = set(eval_case["required_tool_calls"])
    required_flags = set(eval_case["expected_response_flags"])
    forbidden_docs = set(eval_case["must_not_use_doc_ids"])

    pass_value = not (
        required_docs - actual_doc_ids
        or forbidden_docs & actual_doc_ids
        or required_tools - actual_tools
        or required_flags - actual_flags
    )

    return {
        "eval_id": eval_case["eval_id"],
        "request_id": eval_case["request_id"],
        "missing_required_docs": sorted(required_docs - actual_doc_ids),
        "forbidden_docs_present": sorted(forbidden_docs & actual_doc_ids),
        "missing_required_tools": sorted(required_tools - actual_tools),
        "missing_expected_flags": sorted(required_flags - actual_flags),
        "actual_doc_ids": sorted(actual_doc_ids),
        "actual_tools": sorted(actual_tools),
        "actual_flags": sorted(actual_flags),
        "pipeline_pass": pass_value,
        "starter_pass": pass_value,
    }


def evaluate_fieldcare_pipeline(pipeline: FieldCarePipeline) -> list[dict[str, Any]]:
    """Evaluate the current pipeline across all reusable FieldCare eval cases."""
    return [evaluate_case(pipeline, case) for case in pipeline.env["eval_cases"]]


def show_evaluation_results(evaluation_df: pd.DataFrame) -> None:
    """Display the compact evaluation columns learners should inspect first."""
    display(
        evaluation_df[
            [
                "eval_id",
                "request_id",
                "pipeline_pass",
                "missing_required_docs",
                "forbidden_docs_present",
                "missing_required_tools",
                "missing_expected_flags",
            ]
        ]
    )


def run_eval_case(pipeline: FieldCarePipeline, eval_id: str) -> dict[str, Any]:
    """Run the pipeline with the exact input text from one evaluation case."""
    eval_case = eval_case_by_id(pipeline.env, eval_id)
    request = request_for_eval_case(pipeline, eval_case)
    context = assemble_fieldcare_context(pipeline, request)
    response = draft_fieldcare_response(pipeline, context)
    return {"eval_case": eval_case, "request": request, "context": context, "response": response}


def build_edge_case_log_template(env: dict[str, Any], eval_ids: list[str]) -> pd.DataFrame:
    """Return a starter edge-case log with expected behavior prefilled from eval cases."""
    rows: list[dict[str, str]] = []
    for eval_id in eval_ids:
        case = eval_case_by_id(env, eval_id)
        rows.append(
            {
                "eval_id": eval_id,
                "input": case["input"],
                "expected_behavior": "; ".join(case["expected_response_flags"]) or "Check required docs and tools.",
                "actual_behavior": "Learner task: run the app and summarize.",
                "retrieved_evidence": "Learner task: list accepted doc IDs.",
                "tool_information": "Learner task: list tool statuses.",
                "observed_failure": "Learner task: describe mismatch or write none.",
                "likely_cause": "Learner task: retrieval, tool plan, classification, prompt, or response assembly.",
                "possible_improvement": "Learner task: one targeted change.",
            }
        )
    return pd.DataFrame(rows)

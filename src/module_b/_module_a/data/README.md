# Synthetic evaluation data

These files give the bundled FieldCare evaluator repeatable inputs for inspecting retrieval, tool use, and response behavior. All records are synthetic. They are separate from the working service data in [`service/data/`](../../../../service/data/).

| File | Contents |
|---|---|
| `service_docs.jsonl` | Equipment service and troubleshooting documents |
| `equipment_records.csv` | Equipment, site, and configuration details |
| `maintenance_history.csv` | Synthetic maintenance visits and outcomes |
| `service_tickets.csv` | Synthetic ticket state and next actions |
| `tool_schemas.json` | Input and output shapes for the example tools |
| `tool_fixture_responses.json` | Repeatable tool success and failure responses |
| `user_requests.jsonl` | Sample requests for exploring the evaluator |
| `eval_cases.jsonl` | Cases used by the bundled evaluation functions |

The original records remain unchanged so comparisons are repeatable. For the service you build, use the data and setup described in the repository's [local development guide](../../../../docs/local-development.md).

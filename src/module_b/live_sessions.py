"""Persist formative live-session evidence without awarding completion or grades.

Records belong to the student's service checkpoint. They are synthetic/public
practice observations and short learner explanations, never raw keys or private
assessment payloads. This is not a general secret scanner.
"""
import json
from pathlib import Path
from datetime import datetime, timezone
from .notebook import revision

_RECORD = 'live-session-records.json'


def read_records(project):
    path = Path(project) / 'fixtures' / _RECORD
    if not path.exists():
        return {}
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise ValueError('Live-session evidence must be a JSON object.')
    return value


def save_record(project, session, *, observations, reasoning, origin, observed_project=None):
    """Save one explicitly chosen formative record; retain every other session.

    `project` owns the final checkpoint. `observed_project` identifies the actual
    source used for the observations, including a separate public practice lab.
    An empty explanation stays pending. Callers must supply only safe, reviewed
    observations. A record's freshness is separate from its correctness.
    """
    if type(session) is not int or not 1 <= session <= 16:
        raise ValueError('Session must be an integer from 1 to 16.')
    if origin not in {'learner_service', 'public_practice', 'recorded_replay'}:
        raise ValueError('Declare where the evidence came from.')
    if not isinstance(reasoning, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in reasoning.items()):
        raise ValueError('Reasoning must map field names to text.')
    project = Path(project)
    observed_project = Path(observed_project or project)
    record = {
        'session': session, 'recorded_at': datetime.now(timezone.utc).isoformat(),
        'origin': origin, 'source_revision': revision(observed_project),
        'observations': observations, 'reasoning': reasoning,
        'review_status': 'ready_for_discussion' if observations and reasoning and all(v.strip() for v in reasoning.values()) else 'pending',
        'grade': None,
    }
    # Serialization validates before mutating the saved index.
    record = json.loads(json.dumps(record, allow_nan=False))
    records = read_records(project)
    records[f'LS{session:02d}'] = record
    path = project / 'fixtures' / _RECORD
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(records, indent=2, ensure_ascii=False) + '\n')
    temporary.replace(path)
    return record


def record_is_current(record, observed_project):
    return record.get('source_revision') == revision(observed_project)

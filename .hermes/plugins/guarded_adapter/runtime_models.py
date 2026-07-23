"""runtime_models.py — Python dataclass mappings for the three ADT JSON Schemas.

Reads and validates against (read-only, never copies):
  - schemas/adapter-envelope.schema.json
  - schemas/adapter-output.schema.json
  - schemas/execution-authorization-binding.schema.json

Provides typed dataclasses for use by gate.py and the guarded tools.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parents[4]
_SCHEMAS_DIR = _REPO_ROOT / "schemas"


def _load_schema(filename: str) -> Dict[str, Any]:
    """Load a JSON Schema file from the schemas/ directory (read-only)."""
    schema_path = _SCHEMAS_DIR / filename
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# adapter-envelope.schema.json
# ---------------------------------------------------------------------------

@dataclass
class IndependenceEvidence:
    """Two-phase Checker independence evidence (§7 of ADT_RUNTIME_ADAPTER_CONTRACT.md)."""
    separate_execution_context: bool
    maker_context_inherited: bool       # MUST be false
    participated_in_implementation: bool  # MUST be false
    independent_fact_read: bool          # MUST be true
    independent_conclusion: bool         # MUST be true (not required pre-execution)


@dataclass
class AdapterEnvelope:
    """Layer 2 structured metadata carried alongside the task intake."""
    tool_identity: str
    tool_session_id: str
    tool_capability_tags: List[str]
    session_principal: str
    credential_tags: List[str]
    claimed_actor: Optional[str] = None
    independence_evidence: Optional[IndependenceEvidence] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdapterEnvelope":
        indep = data.get("independence_evidence")
        return cls(
            tool_identity=data["tool_identity"],
            tool_session_id=data["tool_session_id"],
            tool_capability_tags=list(data["tool_capability_tags"]),
            session_principal=data["session_principal"],
            credential_tags=list(data["credential_tags"]),
            claimed_actor=data.get("claimed_actor"),
            independence_evidence=(
                IndependenceEvidence(**indep) if indep else None
            ),
        )

    def validate(self) -> List[str]:
        """Validate required fields per schema. Returns list of errors (empty = valid)."""
        errors: List[str] = []
        valid_tags = {"git", "file_write", "file_read", "browser", "terminal", "github_api", "network"}
        if not self.tool_identity:
            errors.append("tool_identity is required")
        if not self.tool_session_id:
            errors.append("tool_session_id is required")
        if not self.tool_capability_tags or len(self.tool_capability_tags) == 0:
            errors.append("tool_capability_tags must have at least 1 item")
        else:
            for tag in self.tool_capability_tags:
                if tag not in valid_tags:
                    errors.append(f"Invalid tool_capability_tag: {tag}")
        if not self.session_principal:
            errors.append("session_principal is required")
        if self.independence_evidence:
            if self.independence_evidence.maker_context_inherited:
                errors.append("maker_context_inherited must be false")
            if self.independence_evidence.participated_in_implementation:
                errors.append("participated_in_implementation must be false")
            if not self.independence_evidence.independent_fact_read:
                errors.append("independent_fact_read must be true")
        return errors


# ---------------------------------------------------------------------------
# adapter-output.schema.json
# ---------------------------------------------------------------------------

@dataclass
class AdapterOutput:
    """Output contract for the Runtime Adapter.

    Wraps the Governance Plan with adapter-level error state.
    """
    governance_plan: GovernancePlan
    adapter_error: Optional[str]          # enum or null
    route: str                            # mirrors governance_plan.route, not authoritative

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AdapterOutput":
        return cls(
            governance_plan=GovernancePlan.from_dict(data["governance_plan"]),
            adapter_error=data.get("adapter_error"),
            route=data["route"],
        )

    def validate(self) -> List[str]:
        errors: List[str] = []
        valid_errors = {
            None, "SCOPE_VIOLATION", "UNAUTHORIZED_ACTION", "BINDING_MISSING",
            "BINDING_INVALID", "CREDENTIAL_LEAK", "INDEPENDENCE_FAILED",
            "ATTEMPTED_SCOPE_VIOLATION",
        }
        if self.adapter_error not in valid_errors:
            errors.append(f"Invalid adapter_error: {self.adapter_error}")
        valid_routes = {
            "DIRECT_LOCAL_EXECUTION", "FILE_LOCAL_EXECUTION",
            "READ_ONLY_REPOSITORY_ANALYSIS", "CANDIDATE_IMPLEMENTATION",
            "INDEPENDENT_AUDIT", "HUMAN_DECISION_REQUIRED",
            "FACT_SOURCE_REBIND", "HARD_STOP",
        }
        if self.route not in valid_routes:
            errors.append(f"Invalid route: {self.route}")
        errors.extend(self.governance_plan.validate())
        return errors


# ---------------------------------------------------------------------------
# governance-plan.schema.json (used by AdapterOutput)
# ---------------------------------------------------------------------------

@dataclass
class Step:
    """A single execution step in the Governance Plan."""
    step_id: str
    objective: str
    dependencies: List[str]
    required_facts: List[str]
    authorized_write_scope: List[str]
    executor_role: str
    checker_required: bool
    pass_conditions: List[str]
    fail_closed_action: str
    next_gate: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Step":
        return cls(
            step_id=data["step_id"],
            objective=data["objective"],
            dependencies=list(data.get("dependencies", [])),
            required_facts=list(data.get("required_facts", [])),
            authorized_write_scope=list(data.get("authorized_write_scope", [])),
            executor_role=data["executor_role"],
            checker_required=data["checker_required"],
            pass_conditions=list(data.get("pass_conditions", [])),
            fail_closed_action=data["fail_closed_action"],
            next_gate=data["next_gate"],
        )


@dataclass
class GovernancePlan:
    """Output of the Dynamic Governance Router."""
    route: str
    risk: str
    task_type: str
    facts_status: str
    control_packet_status: str
    write_scope: List[str]
    steps: List[Step]
    checker_required: bool
    human_authorization_required: bool
    write_actions_permitted: bool
    limitations: Optional[List[str]] = None
    hard_stop_reason: Optional[str] = None
    authorization_id: Optional[str] = None
    task_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "GovernancePlan":
        return cls(
            route=data["route"],
            risk=data["risk"],
            task_type=data["task_type"],
            facts_status=data["facts_status"],
            control_packet_status=data["control_packet_status"],
            write_scope=list(data.get("write_scope", [])),
            steps=[Step.from_dict(s) for s in data.get("steps", [])],
            checker_required=data["checker_required"],
            human_authorization_required=data["human_authorization_required"],
            write_actions_permitted=data["write_actions_permitted"],
            limitations=list(data.get("limitations", [])) if data.get("limitations") else None,
            hard_stop_reason=data.get("hard_stop_reason"),
            authorization_id=data.get("authorization_id"),
            task_id=data.get("task_id"),
        )

    def validate(self) -> List[str]:
        errors: List[str] = []
        valid_routes = {
            "DIRECT_LOCAL_EXECUTION", "FILE_LOCAL_EXECUTION",
            "READ_ONLY_REPOSITORY_ANALYSIS", "CANDIDATE_IMPLEMENTATION",
            "INDEPENDENT_AUDIT", "HUMAN_DECISION_REQUIRED",
            "FACT_SOURCE_REBIND", "HARD_STOP",
        }
        if self.route not in valid_routes:
            errors.append(f"Invalid route: {self.route}")
        valid_risks = {"LOW", "MODERATE", "HIGH", "CRITICAL"}
        if self.risk not in valid_risks:
            errors.append(f"Invalid risk: {self.risk}")
        if self.control_packet_status not in {"CANDIDATE", "NOT_AUTHORIZED"}:
            errors.append(f"Invalid control_packet_status: {self.control_packet_status}")
        return errors


# ---------------------------------------------------------------------------
# execution-authorization-binding.schema.json
# ---------------------------------------------------------------------------

@dataclass
class ExecutionAuthorizationBinding:
    """External authorization evidence that gates execution after the Governance Router.

    The adapter MUST NOT self-set human_holder_approved: true.
    """
    authorization_id: str
    authority_source: str
    human_role: str
    repository: str
    base_sha: str
    branch: str
    authorized_actions: List[str]
    authorized_write_scope: List[str]
    human_holder_approved: Optional[bool] = None   # MUST be set externally
    risk_boundary: Optional[str] = None
    task_id: Optional[str] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExecutionAuthorizationBinding":
        return cls(
            authorization_id=data["authorization_id"],
            authority_source=data["authority_source"],
            human_role=data["human_role"],
            repository=data["repository"],
            base_sha=data["base_sha"],
            branch=data["branch"],
            authorized_actions=list(data["authorized_actions"]),
            authorized_write_scope=list(data["authorized_write_scope"]),
            human_holder_approved=data.get("human_holder_approved"),
            risk_boundary=data.get("risk_boundary"),
            task_id=data.get("task_id"),
        )

    def validate(self) -> List[str]:
        """Validate fields per schema. Returns list of errors (empty = valid)."""
        errors: List[str] = []
        import re
        if not self.authorization_id:
            errors.append("authorization_id is required")
        if not self.authority_source:
            errors.append("authority_source is required")
        if not self.human_role:
            errors.append("human_role is required")
        if not re.match(r"^[a-zA-Z0-9._-]+/[a-zA-Z0-9._-]+$", self.repository):
            errors.append(f"Invalid repository format: {self.repository}")
        if not re.match(r"^[0-9a-f]{40}$", self.base_sha):
            errors.append(f"Invalid base_sha format (must be 40 hex chars): {self.base_sha}")
        if not self.branch:
            errors.append("branch is required")
        valid_actions = {"read", "write_file", "commit", "push", "create_draft_pr"}
        for action in self.authorized_actions:
            if action not in valid_actions:
                errors.append(f"Invalid authorized_action: {action}")
        if self.risk_boundary and self.risk_boundary not in {"LOW", "MODERATE", "HIGH"}:
            errors.append(f"Invalid risk_boundary: {self.risk_boundary}")
        return errors

    def to_dict(self) -> Dict[str, Any]:
        """Serialize back to a dict matching the JSON schema."""
        result: Dict[str, Any] = {
            "authorization_id": self.authorization_id,
            "authority_source": self.authority_source,
            "human_role": self.human_role,
            "repository": self.repository,
            "base_sha": self.base_sha,
            "branch": self.branch,
            "authorized_actions": list(self.authorized_actions),
            "authorized_write_scope": list(self.authorized_write_scope),
        }
        if self.human_holder_approved is not None:
            result["human_holder_approved"] = self.human_holder_approved
        if self.risk_boundary is not None:
            result["risk_boundary"] = self.risk_boundary
        if self.task_id is not None:
            result["task_id"] = self.task_id
        return result

    @classmethod
    def from_json_file(cls, path: Optional[Path] = None) -> "ExecutionAuthorizationBinding":
        """Load and validate an ExecutionAuthorizationBinding from a JSON file.

        Args:
            path: Path to the JSON file (Path or str).
                  Defaults to REPO_ROOT / ".hermes" / "CANDIDATE_BINDING.json".

        Returns:
            ExecutionAuthorizationBinding instance.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file content is invalid or fails validation.
        """
        if path is None:
            path = _REPO_ROOT / ".hermes" / "CANDIDATE_BINDING.json"
        elif isinstance(path, str):
            path = Path(path)

        if not path.exists():
            raise FileNotFoundError(f"Authorization binding file not found: {path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in binding file {path}: {e}")

        if not isinstance(data, dict):
            raise ValueError(f"Binding file {path} must contain a JSON object, got {type(data).__name__}")

        # Basic required-field check (matches schema required fields)
        required_fields = [
            "authorization_id", "authority_source", "human_role",
            "repository", "base_sha", "branch",
            "authorized_actions", "authorized_write_scope",
        ]
        missing = [k for k in required_fields if k not in data]
        if missing:
            raise ValueError(
                f"Binding file {path} missing required fields: {', '.join(missing)}"
            )

        if not isinstance(data["authorized_actions"], list) or len(data["authorized_actions"]) == 0:
            raise ValueError(
                f"Binding file {path}: authorized_actions must be a non-empty list"
            )

        if not isinstance(data["authorized_write_scope"], list):
            raise ValueError(
                f"Binding file {path}: authorized_write_scope must be a list"
            )

        binding = cls.from_dict(data)
        errors = binding.validate()
        if errors:
            raise ValueError(
                f"Binding file {path} validation failed: {'; '.join(errors)}"
            )

        return binding


def load_binding() -> Optional[ExecutionAuthorizationBinding]:
    """Load the execution authorization binding.

    Tries CANDIDATE_BINDING.json first. Returns None on missing file
    (with a warning) so callers can fall back to PROJECT_STATE.md.

    Returns:
        ExecutionAuthorizationBinding instance or None if the file is missing.
    """
    try:
        return ExecutionAuthorizationBinding.from_json_file()
    except FileNotFoundError:
        logger.warning(
            "CANDIDATE_BINDING.json not found; "
            "no external authorization binding available."
        )
        return None
    except ValueError as e:
        logger.warning("CANDIDATE_BINDING.json is invalid: %s", e)
        return None
    except Exception as e:
        logger.warning(
            "Unexpected error loading CANDIDATE_BINDING.json: %s", e
        )
        return None

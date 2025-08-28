#!/usr/bin/env python3

import json
import uuid
import hashlib
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path
import jsonschema


class ProvLogger:
    def __init__(self, schema_path: Optional[str] = None):
        self.schema_path = schema_path or str(
            Path(__file__).parent.parent.parent / "schema" / "prov_event.schema.json"
        )
        self.context_path = str(
            Path(__file__).parent.parent.parent / "schema" / "prov_context.json"
        )
        self._load_schema()
        self._load_context()

    def _load_schema(self):
        """Load PROV event JSON Schema for validation"""
        try:
            with open(self.schema_path, "r") as f:
                self.schema = json.load(f)
        except FileNotFoundError:
            raise RuntimeError(f"PROV schema not found at {self.schema_path}")

    def _load_context(self):
        """Load PROV JSON-LD context"""
        try:
            with open(self.context_path, "r") as f:
                context_data = json.load(f)
                self.context = context_data["@context"]
        except FileNotFoundError:
            raise RuntimeError(f"PROV context not found at {self.context_path}")

    def _generate_id(self, prefix: str = "prov") -> str:
        """Generate unique identifier for PROV records"""
        return f"{prefix}:{uuid.uuid4()}"

    def _generate_entity_hash(self, content: str) -> str:
        """Generate SHA-256 hash for entity content"""
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def _current_timestamp(self) -> str:
        """Get current timestamp in ISO 8601 format"""
        return datetime.now(timezone.utc).isoformat()

    def log_decision(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate W3C PROV JSON-LD record for a decision event

        Args:
            event: Decision event data containing:
                - decision_id: Unique identifier for the decision
                - inputs: List of input entities (files, configs, etc.)
                - outputs: List of output entities (decisions, policies, etc.)
                - agent_spiffe_id: SPIFFE ID of the deciding agent
                - activity_type: Type of activity (e.g., 'policy_evaluation', 'admission_review')
                - metadata: Additional metadata

        Returns:
            W3C PROV JSON-LD compliant record
        """
        timestamp = self._current_timestamp()
        prov_id = self._generate_id("prov")

        # Create entities for inputs and outputs
        entities = {}
        for idx, input_data in enumerate(event.get("inputs", [])):
            entity_id = f"entity:{uuid.uuid4()}"
            entities[entity_id] = {
                "type": "Entity",
                "label": input_data.get("label", f"Input Entity {idx+1}"),
                "hash": self._generate_entity_hash(
                    json.dumps(input_data.get("content", ""))
                ),
                "algorithm": "sha256",
            }
            if "uri" in input_data:
                entities[entity_id]["uri"] = input_data["uri"]

        for idx, output_data in enumerate(event.get("outputs", [])):
            entity_id = f"entity:{uuid.uuid4()}"
            entities[entity_id] = {
                "type": "Entity",
                "label": output_data.get("label", f"Output Entity {idx+1}"),
                "hash": self._generate_entity_hash(
                    json.dumps(output_data.get("content", ""))
                ),
                "algorithm": "sha256",
            }
            if "uri" in output_data:
                entities[entity_id]["uri"] = output_data["uri"]

        # Create activity
        activity_id = f"activity:{uuid.uuid4()}"
        activities = {
            activity_id: {
                "type": "Activity",
                "label": event.get("activity_type", "Decision Activity"),
                "startedAtTime": timestamp,
                "endedAtTime": timestamp,
            }
        }

        # Create agent
        agent_id = f"agent:spiffe:{event.get('decision_id', uuid.uuid4())}"
        agents = {
            agent_id: {
                "type": "Agent",
                "label": f"Decision Agent {event.get('decision_id', '')}",
                "spiffe_id": event.get(
                    "agent_spiffe_id", "spiffe://vpm-mini.local/default"
                ),
            }
        }

        # Create relationships
        input_entities = [
            k
            for k in entities.keys()
            if any("content" in inp for inp in event.get("inputs", []))
        ]
        output_entities = [
            k
            for k in entities.keys()
            if any("content" in out for out in event.get("outputs", []))
        ]

        # Usage relationships (activity used input entities)
        used_relations = {}
        for entity_id in input_entities:
            rel_id = f"_:{uuid.uuid4()}"
            used_relations[rel_id] = {
                "prov:activity": activity_id,
                "prov:entity": entity_id,
                "prov:time": timestamp,
            }

        # Generation relationships (activity generated output entities)
        generation_relations = {}
        for entity_id in output_entities:
            rel_id = f"_:{uuid.uuid4()}"
            generation_relations[rel_id] = {
                "prov:entity": entity_id,
                "prov:activity": activity_id,
                "prov:time": timestamp,
            }

        # Attribution relationships (entities attributed to agent)
        attribution_relations = {}
        for entity_id in output_entities:
            rel_id = f"_:{uuid.uuid4()}"
            attribution_relations[rel_id] = {
                "prov:entity": entity_id,
                "prov:agent": agent_id,
            }

        # Association relationship (activity associated with agent)
        association_relations = {}
        rel_id = f"_:{uuid.uuid4()}"
        association_relations[rel_id] = {
            "prov:activity": activity_id,
            "prov:agent": agent_id,
        }

        # Construct PROV record
        prov_record = {
            "@context": self.context,
            "@id": prov_id,
            "entity": entities,
            "activity": activities,
            "agent": agents,
            "used": used_relations,
            "wasGeneratedBy": generation_relations,
            "wasAttributedTo": attribution_relations,
            "wasAssociatedWith": association_relations,
        }

        # Validate against schema
        try:
            jsonschema.validate(prov_record, self.schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Generated PROV record failed schema validation: {e}")

        return prov_record

    def log_admission_decision(
        self,
        pod_name: str,
        namespace: str,
        decision: str,
        violated_constraints: list = None,
        spiffe_id: str = None,
    ) -> Dict[str, Any]:
        """
        Convenience method for logging Gatekeeper admission decisions

        Args:
            pod_name: Name of the Pod being evaluated
            namespace: Kubernetes namespace
            decision: 'allow' or 'deny'
            violated_constraints: List of violated constraint names (for deny decisions)
            spiffe_id: SPIFFE ID of the admission controller

        Returns:
            W3C PROV JSON-LD compliant record
        """
        event = {
            "decision_id": f"{namespace}-{pod_name}-{uuid.uuid4().hex[:8]}",
            "inputs": [
                {
                    "label": f"Pod Manifest: {pod_name}",
                    "content": {"name": pod_name, "namespace": namespace},
                    "uri": f"k8s://pods/{namespace}/{pod_name}",
                }
            ],
            "outputs": [
                {
                    "label": f"Admission Decision: {decision}",
                    "content": {
                        "decision": decision,
                        "violated_constraints": violated_constraints or [],
                    },
                }
            ],
            "agent_spiffe_id": spiffe_id or "spiffe://vpm-mini.local/gatekeeper",
            "activity_type": "admission_review",
            "metadata": {
                "pod_name": pod_name,
                "namespace": namespace,
                "decision": decision,
            },
        }

        return self.log_decision(event)


if __name__ == "__main__":
    # Example usage
    logger = ProvLogger()

    # Example admission decision
    prov_record = logger.log_admission_decision(
        pod_name="test-pod",
        namespace="hyper-swarm",
        decision="deny",
        violated_constraints=["require-spire-socket"],
        spiffe_id="spiffe://vpm-mini.local/gatekeeper",
    )

    print(json.dumps(prov_record, indent=2))

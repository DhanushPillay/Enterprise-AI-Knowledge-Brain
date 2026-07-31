"""Graph schema — defines all node and relationship types.

This is the law. Every node and relationship in Neo4j MUST
use a type defined here. No agent is allowed to create ad-hoc types.

The schema is intentionally simple: 6 node types and 7 relationship types.
Enterprise knowledge maps cleanly to these categories.
"""

from enum import Enum


class NodeType(str, Enum):
    """Valid node types in the knowledge graph."""

    PERSON = "Person"
    PROJECT = "Project"
    TECHNOLOGY = "Technology"
    CONCEPT = "Concept"
    ORGANIZATION = "Organization"
    DOCUMENT = "Document"


class RelationType(str, Enum):
    """Valid relationship types in the knowledge graph."""

    WORKS_ON = "WORKS_ON"
    USES = "USES"
    DEPENDS_ON = "DEPENDS_ON"
    AUTHORED = "AUTHORED"
    MANAGES = "MANAGES"
    RELATED_TO = "RELATED_TO"
    PART_OF = "PART_OF"


# Mapping from LLM output strings to our enums.
# The extraction agent may return slightly different casing or names.
NODE_TYPE_MAP: dict[str, NodeType] = {
    "person": NodeType.PERSON,
    "project": NodeType.PROJECT,
    "technology": NodeType.TECHNOLOGY,
    "concept": NodeType.CONCEPT,
    "organization": NodeType.ORGANIZATION,
    "document": NodeType.DOCUMENT,
}

REL_TYPE_MAP: dict[str, RelationType] = {
    "works_on": RelationType.WORKS_ON,
    "uses": RelationType.USES,
    "depends_on": RelationType.DEPENDS_ON,
    "authored": RelationType.AUTHORED,
    "manages": RelationType.MANAGES,
    "related_to": RelationType.RELATED_TO,
    "part_of": RelationType.PART_OF,
}


def resolve_node_type(raw: str) -> NodeType:
    """Map a raw string from the LLM to a valid NodeType.

    Falls back to CONCEPT if the string is not recognized,
    since concepts are the most generic category.
    """
    return NODE_TYPE_MAP.get(raw.lower().strip(), NodeType.CONCEPT)


def resolve_rel_type(raw: str) -> RelationType:
    """Map a raw string from the LLM to a valid RelationType.

    Falls back to RELATED_TO if the string is not recognized.
    """
    return REL_TYPE_MAP.get(raw.lower().strip(), RelationType.RELATED_TO)

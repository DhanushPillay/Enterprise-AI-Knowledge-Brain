"""Cypher query templates for Neo4j operations.

All Cypher queries used by the graph builder and query agents
are defined here. Uses parameterized queries to prevent injection.

Usage:
    from backend.src.graph.queries import MERGE_ENTITY, CREATE_RELATIONSHIP
"""

# ---------------------------------------------------------------------------
# Write Queries (used by graph_builder agent)
# ---------------------------------------------------------------------------

MERGE_ENTITY = """
MERGE (n:{label} {{name: $name}})
ON CREATE SET
    n.description = $description,
    n.created_at = datetime(),
    n.source_chunk = $source_chunk
ON MATCH SET
    n.description = CASE
        WHEN size(n.description) < size($description) THEN $description
        ELSE n.description
    END,
    n.updated_at = datetime()
RETURN n
"""

CREATE_RELATIONSHIP = """
MATCH (a {{name: $source_name}})
MATCH (b {{name: $target_name}})
MERGE (a)-[r:{rel_type}]->(b)
ON CREATE SET
    r.description = $description,
    r.created_at = datetime()
RETURN r
"""


# ---------------------------------------------------------------------------
# Read Queries (used by query and retrieval agents)
# ---------------------------------------------------------------------------

FIND_ENTITY_BY_NAME = """
MATCH (n)
WHERE toLower(n.name) CONTAINS toLower($name)
RETURN n.name AS name, labels(n)[0] AS type, n.description AS description
LIMIT $limit
"""

FIND_NEIGHBORS = """
MATCH (n {{name: $name}})-[r]-(neighbor)
RETURN
    n.name AS source,
    type(r) AS relationship,
    neighbor.name AS target,
    labels(neighbor)[0] AS target_type,
    r.description AS rel_description,
    neighbor.description AS target_description
LIMIT $limit
"""

FIND_PATH_BETWEEN = """
MATCH path = shortestPath(
    (a {{name: $source_name}})-[*..{max_depth}]-(b {{name: $target_name}})
)
RETURN
    [node IN nodes(path) | node.name] AS node_names,
    [rel IN relationships(path) | type(rel)] AS relationship_types,
    length(path) AS path_length
"""

FIND_ENTITIES_BY_TYPE = """
MATCH (n:{label})
RETURN n.name AS name, n.description AS description
ORDER BY n.name
LIMIT $limit
"""

GET_GRAPH_STATS = """
MATCH (n)
WITH labels(n)[0] AS label, count(n) AS count
RETURN label, count
ORDER BY count DESC
"""

GET_RELATIONSHIP_STATS = """
MATCH ()-[r]->()
WITH type(r) AS rel_type, count(r) AS count
RETURN rel_type, count
ORDER BY count DESC
"""

SUBGRAPH_AROUND_ENTITY = """
MATCH (center {{name: $name}})
CALL {{
    WITH center
    MATCH (center)-[r*1..{depth}]-(connected)
    RETURN connected, r
}}
WITH center, collect(DISTINCT connected) AS nodes
RETURN
    center.name AS center,
    [n IN nodes | {{name: n.name, type: labels(n)[0], description: n.description}}] AS connected_nodes
"""

# Knowledge Graph Schema

Everything extracted from documents lives in Neo4j Community 5.x as nodes and relationships.

---

## Node Types

Every node has these base properties:

```cypher
{
    name: String,           // Display name (unique per type)
    type: String,           // Node type (one of the labels below)
    created_at: DateTime,   // When this node was created
    updated_at: DateTime,   // Last time this node was updated
    source_docs: [String],  // Document IDs that mentioned this entity
    confidence: Float       // Average extraction confidence (0-1)
}
```

### Person

```cypher
(:Person {
    name: String,           // "John Smith"
    role: String,           // "Software Engineer" (optional)
    department: String,     // "Engineering" (optional)
    email: String,          // "john@company.com" (optional)
    expertise: [String],    // ["Python", "ML", "NLP"] (optional)
    source_docs: [String],
    confidence: Float
})
```

### Organization

```cypher
(:Organization {
    name: String,           // "Engineering Department"
    type: String,           // "department", "company", "team"
    parent_org: String,     // Parent organization name (optional)
    description: String,    // Brief description (optional)
    source_docs: [String],
    confidence: Float
})
```

### Project

```cypher
(:Project {
    name: String,           // "Project Alpha"
    status: String,         // "active", "completed", "planned" (optional)
    start_date: String,     // "2024-Q1" (optional)
    end_date: String,       // "2024-Q3" (optional)
    description: String,    // Brief description (optional)
    tech_stack: [String],   // ["Python", "Neo4j", "Groq"] (optional)
    source_docs: [String],
    confidence: Float
})
```

### Technology

```cypher
(:Technology {
    name: String,           // "Python", "Neo4j", "LangChain"
    category: String,       // "language", "framework", "database", "tool"
    version: String,        // "3.11" (optional)
    description: String,    // Brief description (optional)
    source_docs: [String],
    confidence: Float
})
```

### Concept

```cypher
(:Concept {
    name: String,           // "Knowledge Graph", "RAG", "Multi-Agent"
    category: String,       // "methodology", "pattern", "architecture"
    description: String,    // Brief description (optional)
    source_docs: [String],
    confidence: Float
})
```

### Document

```cypher
(:Document {
    name: String,           // "architecture-spec.pdf"
    path: String,           // "/data/docs/architecture-spec.pdf"
    type: String,           // "pdf", "txt", "md", "code"
    chunk_count: Integer,   // Number of text chunks
    ingested_at: DateTime,  // When the document was ingested
    summary: String         // LLM-generated summary (optional)
})
```

---

## Relationship Types

Every relationship carries these base properties:

```cypher
{
    source_docs: [String],  // Document(s) that established this relationship
    confidence: Float,      // Extraction confidence (0-1)
    created_at: DateTime    // When this relationship was created
}
```

### WORKS_ON (Person → Project)

```cypher
(:Person)-[:WORKS_ON {
    role: String,           // "lead", "contributor", "reviewer" (optional)
    start_date: String,     // When they started (optional)
    end_date: String,       // When they finished (optional)
}]->(:Project)
```

### WORKS_FOR (Person → Organization)

```cypher
(:Person)-[:WORKS_FOR {
    start_date: String,
    end_date: String,
}]->(:Organization)
```

### USES (Project/Person → Technology)

```cypher
(:Project)-[:USES {
    purpose: String,        // "backend", "frontend", "database" (optional)
}]->(:Technology)

(:Person)-[:USES {
    proficiency: String,    // "expert", "intermediate", "beginner" (optional)
}]->(:Technology)
```

### DEPENDS_ON (Project → Project/Technology)

```cypher
(:Project)-[:DEPENDS_ON {
    type: String,           // "hard", "soft" (optional)
}]->(:Project)

(:Project)-[:DEPENDS_ON {
    type: String,           // "runtime", "build", "test" (optional)
}]->(:Technology)
```

### MENTIONS (Document → Entity)

```cypher
(:Document)-[:MENTIONS {
    count: Integer,
    context: String,        // Brief context (optional)
}]->(:Person|Organization|Project|Technology|Concept)
```

### AUTHORED_BY (Document → Person)

```cypher
(:Document)-[:AUTHORED_BY {
    role: String,           // "author", "editor", "reviewer" (optional)
}]->(:Person)
```

### MANAGES (Person → Person/Project)

```cypher
(:Person)-[:MANAGES {
    scope: String,          // "direct", "indirect" (optional)
}]->(:Person)

(:Person)-[:MANAGES {
    authority: String,      // "technical", "business", "both" (optional)
}]->(:Project)
```

### PART_OF (Organization → Organization)

```cypher
(:Organization)-[:PART_OF {
    type: String,           // "parent", "child", "sibling" (optional)
}]->(:Organization)
```

### RELATED_TO (generic, any entity pair)

```cypher
(:Entity)-[:RELATED_TO {
    type: String,
    strength: Float,        // 0-1
}]->(:Entity)
```

---

## Indexes

These keep queries fast:

```cypher
// Unique constraints (also create indexes)
CREATE CONSTRAINT person_name IF NOT EXISTS
FOR (p:Person) REQUIRE p.name IS UNIQUE;

CREATE CONSTRAINT org_name IF NOT EXISTS
FOR (o:Organization) REQUIRE o.name IS UNIQUE;

CREATE CONSTRAINT project_name IF NOT EXISTS
FOR (p:Project) REQUIRE p.name IS UNIQUE;

CREATE CONSTRAINT tech_name IF NOT EXISTS
FOR (t:Technology) REQUIRE t.name IS UNIQUE;

CREATE CONSTRAINT concept_name IF NOT EXISTS
FOR (c:Concept) REQUIRE c.name IS UNIQUE;

CREATE CONSTRAINT doc_name IF NOT EXISTS
FOR (d:Document) REQUIRE d.name IS UNIQUE;

// Performance indexes
CREATE INDEX person_dept IF NOT EXISTS
FOR (p:Person) ON (p.department);

CREATE INDEX project_status IF NOT EXISTS
FOR (p:Project) ON (p.status);

CREATE INDEX tech_category IF NOT EXISTS
FOR (t:Technology) ON (t.category);
```

---

## Query Patterns

Stuff you'll actually run:

### Who's working on a project?

```cypher
MATCH (p:Person)-[:WORKS_ON]->(proj:Project {name: $project_name})
RETURN p.name, p.role, p.department
ORDER BY p.name;
```

### What tech does a project use?

```cypher
MATCH (proj:Project {name: $project_name})-[:USES]->(t:Technology)
RETURN t.name, t.category
ORDER BY t.name;
```

### Who knows a particular technology?

```cypher
MATCH (p:Person)-[:USES]->(t:Technology {name: $tech_name})
RETURN p.name, p.role, p.department
ORDER BY p.name;
```

### What does a project depend on?

```cypher
MATCH (proj:Project {name: $project_name})-[:DEPENDS_ON]->(dep)
RETURN labels(dep)[0] AS type, dep.name AS name
ORDER BY type, name;
```

### Which documents mention an entity?

```cypher
MATCH (d:Document)-[:MENTIONS]->(e {name: $entity_name})
RETURN d.name, d.type, d.path
ORDER BY d.name;
```

### Full-text search (needs a full-text index)

```cypher
// Create the index first
CREATE FULLTEXT INDEX entity_fulltext IF NOT EXISTS
FOR (e:Person|Organization|Project|Technology|Concept)
ON EACH [e.name, e.description];

// Then search
CALL db.index.fulltext.queryNodes("entity_fulltext", $search_term)
YIELD node, score
RETURN labels(node)[0] AS type, node.name AS name, score
ORDER BY score DESC
LIMIT 10;
```

### Get a subgraph for GNN processing

```cypher
MATCH path = (start {name: $node_name})-[*1..3]-(connected)
RETURN DISTINCT connected
LIMIT 100;
```

---

## Graph Stats

Quick health checks:

```cypher
// How many nodes of each type?
MATCH (n)
RETURN labels(n)[0] AS type, count(n) AS count
ORDER BY count DESC;

// How many relationships of each type?
MATCH ()-[r]->()
RETURN type(r) AS type, count(r) AS count
ORDER BY count DESC;

// Average connections per node
MATCH (n)-[r]-()
RETURN count(DISTINCT n) AS nodes, count(r) AS relationships,
       toFloat(count(r)) / count(DISTINCT n) AS avg_degree;
```

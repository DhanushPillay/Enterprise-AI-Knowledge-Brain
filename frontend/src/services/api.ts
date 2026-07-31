/**
 * API client — all communication with the Python backend goes through here.
 *
 * No component should call fetch() directly. They import from this file.
 * This keeps the API surface centralized and easy to change.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/** Shape of a chat response from the backend */
export interface ChatResponse {
  answer: string;
  reasoning: string[];
  sources: { name: string; snippet: string; type: string; score: number }[];
  is_safe: boolean;
}

/** Shape of an ingestion response from the backend */
export interface IngestResponse {
  filename: string;
  chunks_created: number;
  entities_extracted: number;
  relationships_extracted: number;
  graph_entities_written: number;
  graph_relationships_written: number;
}

/** Shape of graph stats from the backend */
export interface GraphStats {
  nodes: { label: string; count: number }[];
  relationships: { rel_type: string; count: number }[];
  total_chunks: number;
}

/**
 * Send a chat query to the backend.
 * Goes through: Security Agent → Query Agent → LLM Answer.
 */
export async function sendChatMessage(query: string): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query }),
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Chat request failed (${response.status}): ${error}`);
  }

  return response.json();
}

/**
 * Upload a document for ingestion into the knowledge graph.
 * Backend pipeline: Load → Chunk → Extract Entities → Write to Neo4j.
 */
export async function ingestDocument(file: File): Promise<IngestResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`${API_BASE}/ingest`, {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    const error = await response.text();
    throw new Error(`Ingestion failed (${response.status}): ${error}`);
  }

  return response.json();
}

/**
 * Fetch knowledge graph statistics for the admin dashboard.
 */
export async function fetchGraphStats(): Promise<GraphStats> {
  const response = await fetch(`${API_BASE}/graph/stats`);

  if (!response.ok) {
    throw new Error(`Failed to fetch graph stats (${response.status})`);
  }

  return response.json();
}

/**
 * Health check — verify the backend is running.
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

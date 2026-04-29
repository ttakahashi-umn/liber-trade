CREATE TABLE IF NOT EXISTS document_processes (
  process_id TEXT PRIMARY KEY,
  status TEXT NOT NULL,
  normalized_payload_json TEXT NOT NULL,
  consistency_result_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

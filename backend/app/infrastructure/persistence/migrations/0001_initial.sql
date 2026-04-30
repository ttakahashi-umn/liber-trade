PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS document_processes (
  process_id TEXT PRIMARY KEY,
  status TEXT NOT NULL,
  normalized_payload_json TEXT NOT NULL,
  consistency_result_json TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trade_chains (
  chain_id TEXT PRIMARY KEY,
  case_no TEXT NOT NULL UNIQUE,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS trade_documents (
  document_id TEXT PRIMARY KEY,
  chain_id TEXT NOT NULL,
  doc_type TEXT NOT NULL CHECK (doc_type IN ('UNKNOWN', 'QUT', 'EST', 'PO', 'PPL', 'INV')),
  doc_no TEXT,
  issue_date TEXT,
  version_no INTEGER NOT NULL DEFAULT 1,
  source_process_id TEXT,
  normalized_payload_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (chain_id) REFERENCES trade_chains(chain_id) ON DELETE CASCADE,
  FOREIGN KEY (source_process_id) REFERENCES document_processes(process_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS document_links (
  link_id TEXT PRIMARY KEY,
  from_document_id TEXT NOT NULL,
  to_document_id TEXT NOT NULL,
  relation_type TEXT NOT NULL CHECK (relation_type IN ('DERIVED_FROM', 'MATCH_TARGET', 'REVISION_OF')),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (from_document_id) REFERENCES trade_documents(document_id) ON DELETE CASCADE,
  FOREIGN KEY (to_document_id) REFERENCES trade_documents(document_id) ON DELETE CASCADE,
  CHECK (from_document_id != to_document_id)
);

CREATE TABLE IF NOT EXISTS comparison_rule_sets (
  rule_set_id TEXT PRIMARY KEY,
  version TEXT NOT NULL UNIQUE,
  description TEXT,
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_type_rule_sets (
  rule_set_id TEXT PRIMARY KEY,
  version TEXT NOT NULL UNIQUE,
  description TEXT,
  is_active INTEGER NOT NULL DEFAULT 1 CHECK (is_active IN (0, 1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS document_type_rules (
  rule_id TEXT PRIMARY KEY,
  rule_set_id TEXT NOT NULL,
  doc_type TEXT NOT NULL CHECK (doc_type IN ('UNKNOWN', 'QUT', 'EST', 'PO', 'PPL', 'INV')),
  condition_type TEXT NOT NULL CHECK (condition_type IN ('FIELD_EXISTS', 'KEYWORD_CONTAINS')),
  condition_key TEXT NOT NULL,
  condition_value TEXT,
  score REAL NOT NULL DEFAULT 0,
  priority INTEGER NOT NULL DEFAULT 0,
  is_enabled INTEGER NOT NULL DEFAULT 1 CHECK (is_enabled IN (0, 1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (rule_set_id) REFERENCES document_type_rule_sets(rule_set_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS comparison_rules (
  rule_id TEXT PRIMARY KEY,
  rule_set_id TEXT NOT NULL,
  base_doc_type TEXT NOT NULL CHECK (base_doc_type IN ('QUT', 'EST', 'PO', 'PPL', 'INV')),
  target_doc_type TEXT NOT NULL CHECK (target_doc_type IN ('QUT', 'EST', 'PO', 'PPL', 'INV')),
  field_path TEXT NOT NULL,
  comparison_operator TEXT NOT NULL CHECK (comparison_operator IN ('EQUALS', 'NUMERIC_TOLERANCE', 'EXISTS_ON_BOTH')),
  tolerance_type TEXT CHECK (tolerance_type IN ('RATIO', 'ABSOLUTE')),
  tolerance_value REAL,
  severity TEXT NOT NULL CHECK (severity IN ('INFO', 'WARN', 'ERROR')),
  is_enabled INTEGER NOT NULL DEFAULT 1 CHECK (is_enabled IN (0, 1)),
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (rule_set_id) REFERENCES comparison_rule_sets(rule_set_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS document_comparisons (
  comparison_id TEXT PRIMARY KEY,
  chain_id TEXT NOT NULL,
  base_document_id TEXT NOT NULL,
  target_document_id TEXT NOT NULL,
  rule_set_version TEXT,
  result_status TEXT NOT NULL CHECK (result_status IN ('PASS', 'WARN', 'FAIL')),
  summary_json TEXT NOT NULL DEFAULT '{}',
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (chain_id) REFERENCES trade_chains(chain_id) ON DELETE CASCADE,
  FOREIGN KEY (base_document_id) REFERENCES trade_documents(document_id) ON DELETE CASCADE,
  FOREIGN KEY (target_document_id) REFERENCES trade_documents(document_id) ON DELETE CASCADE,
  CHECK (base_document_id != target_document_id)
);

CREATE TABLE IF NOT EXISTS document_comparison_items (
  item_id TEXT PRIMARY KEY,
  comparison_id TEXT NOT NULL,
  field_path TEXT NOT NULL,
  base_value TEXT,
  target_value TEXT,
  diff_type TEXT NOT NULL CHECK (diff_type IN ('MISMATCH', 'MISSING', 'OUT_OF_TOLERANCE')),
  tolerance_rule_id TEXT,
  is_acceptable INTEGER NOT NULL CHECK (is_acceptable IN (0, 1)),
  message TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (comparison_id) REFERENCES document_comparisons(comparison_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_trade_documents_chain_id ON trade_documents(chain_id);
CREATE INDEX IF NOT EXISTS idx_trade_documents_doc_type ON trade_documents(doc_type);
CREATE UNIQUE INDEX IF NOT EXISTS uq_trade_documents_chain_type_version
  ON trade_documents(chain_id, doc_type, version_no);
CREATE UNIQUE INDEX IF NOT EXISTS uq_document_links_pair_relation
  ON document_links(from_document_id, to_document_id, relation_type);
CREATE INDEX IF NOT EXISTS idx_comparison_rule_sets_active ON comparison_rule_sets(is_active);
CREATE INDEX IF NOT EXISTS idx_comparison_rules_rule_set_id ON comparison_rules(rule_set_id);
CREATE INDEX IF NOT EXISTS idx_comparison_rules_doc_pair
  ON comparison_rules(base_doc_type, target_doc_type, field_path);
CREATE UNIQUE INDEX IF NOT EXISTS uq_comparison_rules_unique_scope
  ON comparison_rules(rule_set_id, base_doc_type, target_doc_type, field_path, comparison_operator);
CREATE INDEX IF NOT EXISTS idx_document_type_rule_sets_active ON document_type_rule_sets(is_active);
CREATE INDEX IF NOT EXISTS idx_document_type_rules_rule_set_id ON document_type_rules(rule_set_id);
CREATE INDEX IF NOT EXISTS idx_document_type_rules_doc_type ON document_type_rules(doc_type);
CREATE UNIQUE INDEX IF NOT EXISTS uq_document_type_rules_unique_scope
  ON document_type_rules(rule_set_id, doc_type, condition_type, condition_key, condition_value);
CREATE INDEX IF NOT EXISTS idx_document_comparisons_chain_id ON document_comparisons(chain_id);
CREATE INDEX IF NOT EXISTS idx_document_comparison_items_comparison_id
  ON document_comparison_items(comparison_id);

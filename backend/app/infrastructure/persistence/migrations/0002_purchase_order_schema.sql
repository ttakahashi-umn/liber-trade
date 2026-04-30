PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS purchase_orders (
  po_id TEXT PRIMARY KEY,
  process_id TEXT,
  po_number TEXT NOT NULL,
  date_of_issue TEXT,
  buyer_company_name TEXT,
  buyer_address TEXT,
  buyer_contact TEXT,
  buyer_person_name TEXT,
  seller_company_name TEXT,
  seller_address TEXT,
  seller_contact TEXT,
  authorized_signature TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (process_id) REFERENCES document_processes(process_id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS purchase_order_items (
  item_id TEXT PRIMARY KEY,
  po_id TEXT NOT NULL,
  line_no INTEGER NOT NULL,
  item_description TEXT NOT NULL,
  item_code TEXT,
  quantity REAL,
  unit_price REAL,
  total_amount REAL,
  currency TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS purchase_order_trade_terms (
  po_id TEXT PRIMARY KEY,
  incoterms TEXT,
  country_of_origin TEXT,
  port_of_loading TEXT,
  port_of_discharge TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS purchase_order_payment_delivery (
  po_id TEXT PRIMARY KEY,
  payment_terms TEXT,
  delivery_date TEXT,
  lead_time_days INTEGER,
  shipping_method TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS purchase_order_misc (
  po_id TEXT PRIMARY KEY,
  packing_instructions TEXT,
  shipping_marks TEXT,
  required_documents TEXT,
  created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (po_id) REFERENCES purchase_orders(po_id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_purchase_orders_po_number ON purchase_orders(po_number);
CREATE INDEX IF NOT EXISTS idx_purchase_orders_process_id ON purchase_orders(process_id);
CREATE UNIQUE INDEX IF NOT EXISTS uq_purchase_order_items_po_line ON purchase_order_items(po_id, line_no);

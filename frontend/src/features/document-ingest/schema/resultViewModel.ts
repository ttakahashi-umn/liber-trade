export type ProcessStatus = "SUCCESS" | "NEEDS_REVIEW" | "FAILED";

export type Inconsistency = {
  field: string;
  expected: number | null;
  actual: number | null;
  message: string;
};

export type IngestResult = {
  process_id: string;
  raw_file_url: string | null;
  rendered_image_url: string | null;
  status: ProcessStatus;
  normalized_payload: Record<string, unknown>;
  consistency_result: {
    is_consistent: boolean;
    inconsistencies: Inconsistency[];
  };
  warnings: string[];
};

export type CaseSummary = {
  case_id: string;
  case_name: string;
  match_status: "OK" | "要確認" | "未処理" | string;
};

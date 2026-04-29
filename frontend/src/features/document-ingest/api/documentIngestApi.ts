import { apiFetch } from "@/shared/http/client";
import type { CaseSummary, IngestResult } from "../schema/resultViewModel";

export async function ingestDocument(file: File): Promise<IngestResult> {
  const formData = new FormData();
  formData.append("file", file);
  return apiFetch<IngestResult>("/api/documents/ingest", {
    method: "POST",
    body: formData,
  });
}

export async function fetchResult(processId: string): Promise<IngestResult> {
  return apiFetch<IngestResult>(`/api/documents/${processId}`);
}

export async function fetchCases(processId: string): Promise<CaseSummary[]> {
  return apiFetch<CaseSummary[]>(`/api/cases?process_id=${encodeURIComponent(processId)}`);
}

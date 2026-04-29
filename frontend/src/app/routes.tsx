import { useState } from "react";
import { AppShell, Button, Container, Group, Paper, Stack, Text, Title } from "@mantine/core";
import { CaseListPanel } from "@/features/document-ingest/components/CaseListPanel";
import { ResultPanel } from "@/features/document-ingest/components/ResultPanel";
import { UploadForm } from "@/features/document-ingest/components/UploadForm";
import type { IngestResult } from "@/features/document-ingest/schema/resultViewModel";

export function AppRoutes() {
  const [result, setResult] = useState<IngestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState<"upload" | "cases">("upload");

  return (
    <AppShell padding="md">
      <AppShell.Main>
        <Container size="lg">
          <Stack gap="md">
            <Paper withBorder p="md" radius="md">
              <Group justify="space-between" align="center">
                <div>
                  <Title order={2}>Trade Document Ingest PoC</Title>
                  <Text size="sm" c="dimmed">
                    書類取り込み、突合結果確認、案件一覧確認
                  </Text>
                </div>
                <Group>
                  <Button variant={page === "upload" ? "filled" : "light"} onClick={() => setPage("upload")}>
                    取り込み
                  </Button>
                  <Button
                    variant={page === "cases" ? "filled" : "light"}
                    onClick={() => setPage("cases")}
                    disabled={!result}
                  >
                    案件一覧
                  </Button>
                </Group>
              </Group>
            </Paper>

            {page === "upload" && (
              <UploadForm
                onResult={(next) => {
                  setError(null);
                  setResult(next);
                }}
                onError={(message) => setError(message)}
                onSuccessNavigate={() => setPage("cases")}
              />
            )}

            {error && <Text c="red">{error}</Text>}

            {page === "upload" ? (
              <ResultPanel result={result} />
            ) : (
              <CaseListPanel processId={result?.process_id ?? null} />
            )}
          </Stack>
        </Container>
      </AppShell.Main>
    </AppShell>
  );
}

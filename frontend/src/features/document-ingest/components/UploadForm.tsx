import { useState } from "react";
import { Button, FileInput, Paper, Stack, Text, Title } from "@mantine/core";
import { ingestDocument } from "../api/documentIngestApi";
import type { IngestResult } from "../schema/resultViewModel";

type Props = {
  onResult: (result: IngestResult) => void;
  onError: (message: string) => void;
  onUploadSuccess: (file: File) => void;
};

export function UploadForm({ onResult, onError, onUploadSuccess }: Props) {
  const [loading, setLoading] = useState(false);
  const [file, setFile] = useState<File | null>(null);

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      onError("ファイルを選択してください");
      return;
    }

    setLoading(true);
    try {
      const result = await ingestDocument(file);
      onResult(result);
      onUploadSuccess(file);
    } catch (error) {
      onError(error instanceof Error ? error.message : "アップロードに失敗しました");
    } finally {
      setLoading(false);
    }
  }

  return (
    <Paper withBorder p="md" radius="md" component="form" onSubmit={handleSubmit}>
      <Stack gap="sm">
        <Title order={4}>書類アップロード</Title>
        <Text size="sm" c="dimmed">
          画像ファイルを選択して取り込みを開始します。
        </Text>
        <FileInput
          name="file"
          accept=".jpg,.jpeg,.gif,.png,.pdf,.xls,.xlsx,.doc,.docx,image/jpeg,image/gif,image/png,application/pdf,application/vnd.ms-excel,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
          placeholder="画像ファイルを選択"
          value={file}
          onChange={setFile}
        />
        <Button type="submit" loading={loading}>
          取り込み開始
        </Button>
      </Stack>
    </Paper>
  );
}

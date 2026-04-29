import { Badge, Code, Group, Paper, Stack, Text, Title } from "@mantine/core";
import type { IngestResult } from "../schema/resultViewModel";

type Props = { result: IngestResult | null };

export function ResultPanel({ result }: Props) {
  if (!result) {
    return (
      <Paper withBorder p="md" radius="md">
        <Text c="dimmed">結果待ちです</Text>
      </Paper>
    );
  }

  return (
    <Paper withBorder p="md" radius="md">
      <Stack gap="sm">
        <Group justify="space-between">
          <Title order={4}>処理結果</Title>
          <Badge color={result.status === "SUCCESS" ? "green" : "yellow"}>{result.status}</Badge>
        </Group>
        <Text fw={500}>整合判定: {result.consistency_result.is_consistent ? "整合OK" : "要確認"}</Text>
        {result.consistency_result.inconsistencies.map((item) => (
          <Text size="sm" key={item.field}>
            {item.field}: {item.message} (期待値: {item.expected ?? "-"} / 実値: {item.actual ?? "-"})
          </Text>
        ))}
        {result.warnings.length > 0 && <Text size="sm">未対応項目: {result.warnings.join(", ")}</Text>}
        <Code block>{JSON.stringify(result.normalized_payload, null, 2)}</Code>
      </Stack>
    </Paper>
  );
}

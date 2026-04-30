import { Anchor, Badge, Code, Group, Image, Paper, Stack, Text, Title } from "@mantine/core";
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
        {result.raw_file_url && (
          <Text size="sm">
            原本:{" "}
            <Anchor href={result.raw_file_url} target="_blank" rel="noreferrer">
              MinIOから開く
            </Anchor>
          </Text>
        )}
        {result.rendered_image_url && (
          <Stack gap={4}>
            <Text size="sm">変換画像プレビュー</Text>
            <Image src={result.rendered_image_url} alt="rendered document" maw={480} radius="sm" />
          </Stack>
        )}
        <Code block>{JSON.stringify(result.normalized_payload, null, 2)}</Code>
      </Stack>
    </Paper>
  );
}

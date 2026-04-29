import { useEffect, useState } from "react";
import { Badge, Paper, Stack, Table, Text, Title } from "@mantine/core";
import { fetchCases } from "../api/documentIngestApi";
import type { CaseSummary } from "../schema/resultViewModel";

type Props = {
  processId: string | null;
};

export function CaseListPanel({ processId }: Props) {
  const [cases, setCases] = useState<CaseSummary[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!processId) return;
    setLoading(true);
    setError(null);
    fetchCases(processId)
      .then((list) => setCases(list))
      .catch((e) => setError(e instanceof Error ? e.message : "案件取得に失敗しました"))
      .finally(() => setLoading(false));
  }, [processId]);

  if (!processId) {
    return (
      <Paper withBorder p="md" radius="md">
        <Text c="dimmed">取り込み完了後に案件一覧を表示します。</Text>
      </Paper>
    );
  }
  if (loading) {
    return (
      <Paper withBorder p="md" radius="md">
        <Text c="dimmed">案件一覧を取得中...</Text>
      </Paper>
    );
  }
  if (error) {
    return (
      <Paper withBorder p="md" radius="md">
        <Text c="red">{error}</Text>
      </Paper>
    );
  }
  if (cases.length === 0) {
    return (
      <Paper withBorder p="md" radius="md">
        <Text c="dimmed">紐づく案件はありません。</Text>
      </Paper>
    );
  }

  return (
    <Paper withBorder p="md" radius="md">
      <Stack gap="sm">
        <Title order={4}>案件一覧</Title>
        <Table striped highlightOnHover>
          <Table.Thead>
            <Table.Tr>
              <Table.Th>案件ID</Table.Th>
              <Table.Th>案件名</Table.Th>
              <Table.Th>突合状況</Table.Th>
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {cases.map((item) => (
              <Table.Tr key={item.case_id}>
                <Table.Td>{item.case_id}</Table.Td>
                <Table.Td>{item.case_name}</Table.Td>
                <Table.Td>
                  <Badge color={item.match_status === "OK" ? "green" : item.match_status === "要確認" ? "yellow" : "gray"}>
                    {item.match_status}
                  </Badge>
                </Table.Td>
              </Table.Tr>
            ))}
          </Table.Tbody>
        </Table>
      </Stack>
    </Paper>
  );
}

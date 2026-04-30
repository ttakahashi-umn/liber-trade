import { useEffect, useState } from "react";
import { IconFileUpload, IconListDetails } from "@tabler/icons-react";
import {
  ActionIcon,
  Affix,
  AppShell,
  Burger,
  Button,
  Drawer,
  Group,
  Image,
  NavLink,
  Paper,
  Stack,
  Text,
  ThemeIcon,
  Tooltip,
  Title,
} from "@mantine/core";
import { CaseListPanel } from "@/features/document-ingest/components/CaseListPanel";
import { ResultPanel } from "@/features/document-ingest/components/ResultPanel";
import { UploadForm } from "@/features/document-ingest/components/UploadForm";
import type { IngestResult } from "@/features/document-ingest/schema/resultViewModel";

export function AppRoutes() {
  const [result, setResult] = useState<IngestResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [page, setPage] = useState<"cases">("cases");
  const [menuOpened, setMenuOpened] = useState(true);
  const [drawerOpened, setDrawerOpened] = useState(false);
  const [uploadedPreview, setUploadedPreview] = useState<{ url: string; type: string; name: string } | null>(null);

  useEffect(() => {
    return () => {
      if (uploadedPreview?.url) URL.revokeObjectURL(uploadedPreview.url);
    };
  }, [uploadedPreview]);

  return (
    <AppShell
      padding="md"
      header={{ height: 72 }}
      navbar={{ width: menuOpened ? 220 : 72, breakpoint: "sm", collapsed: { mobile: !menuOpened, desktop: !menuOpened } }}
    >
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between">
          <Group>
            <Burger opened={menuOpened} onClick={() => setMenuOpened((v) => !v)} size="sm" />
            <div>
              <Title order={3}>Trade Document Ingest PoC</Title>
              <Text size="xs" c="dimmed">
                案件一覧中心のSPA
              </Text>
            </div>
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="sm">
        <NavLink
          label={menuOpened ? "案件一覧" : undefined}
          description={menuOpened ? "Case List" : undefined}
          active={page === "cases"}
          onClick={() => setPage("cases")}
          leftSection={
            <ThemeIcon variant={page === "cases" ? "filled" : "light"} radius="xl" size={30}>
              <IconListDetails size={18} />
            </ThemeIcon>
          }
        />
      </AppShell.Navbar>
      <AppShell.Main>
        <Stack gap="md">
          <CaseListPanel processId={result?.process_id ?? null} />
          <ResultPanel result={result} />
        </Stack>

        <Affix position={{ bottom: 28, right: 28 }}>
          <Tooltip label="ドキュメントを取り込む" position="left">
            <ActionIcon
              size={56}
              radius="xl"
              variant="filled"
              color="dark"
              onClick={() => setDrawerOpened(true)}
              aria-label="ドキュメント取り込み画面を開く"
              style={{ border: "2px solid white", boxShadow: "0 8px 20px rgba(0,0,0,0.28)", fontSize: 24 }}
            >
              <IconFileUpload size={24} />
            </ActionIcon>
          </Tooltip>
        </Affix>

        <Drawer
          opened={drawerOpened}
          onClose={() => setDrawerOpened(false)}
          position="right"
          size="md"
          title="書類取り込み"
        >
          <Stack gap="md">
            <UploadForm
              onResult={(next) => {
                setError(null);
                setResult(next);
              }}
              onError={(message) => setError(message)}
              onUploadSuccess={(file) => {
                if (uploadedPreview?.url) URL.revokeObjectURL(uploadedPreview.url);
                setUploadedPreview({
                  url: URL.createObjectURL(file),
                  type: file.type || "",
                  name: file.name,
                });
              }}
            />
            {error && <Text c="red">{error}</Text>}
            {uploadedPreview && (
              <Stack gap={6}>
                <Text size="sm" fw={600}>
                  取り込みプレビュー
                </Text>
                {uploadedPreview.type.startsWith("image/") ? (
                  <Image src={uploadedPreview.url} alt="取り込み画像" radius="md" withPlaceholder />
                ) : (
                  <Paper withBorder p="sm" radius="md">
                    <Text size="sm">画像プレビュー対象外のファイルです。</Text>
                    <Text size="xs" c="dimmed">
                      {uploadedPreview.name} ({uploadedPreview.type || "unknown"})
                    </Text>
                  </Paper>
                )}
              </Stack>
            )}
            <Button variant="light" onClick={() => setDrawerOpened(false)}>
              閉じる
            </Button>
          </Stack>
        </Drawer>
      </AppShell.Main>
    </AppShell>
  );
}

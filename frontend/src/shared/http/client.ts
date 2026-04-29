export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(path, init);
  if (!response.ok) {
    const body = await response.text();
    try {
      const parsed = JSON.parse(body) as { detail?: string };
      if (parsed.detail) {
        throw new Error(parsed.detail);
      }
    } catch {
      // JSONでない場合はそのまま本文を使う
    }
    throw new Error(body || `Request failed: ${response.status}`);
  }
  return (await response.json()) as T;
}

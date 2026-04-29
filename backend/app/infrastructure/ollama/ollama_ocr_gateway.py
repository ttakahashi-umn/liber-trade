from __future__ import annotations

import base64
import json
import logging
import os
import re

import httpx
from dotenv import load_dotenv


load_dotenv()
logger = logging.getLogger(__name__)


class OllamaOcrGateway:
    async def extract_text_and_tables(self, image_bytes: bytes, filename: str, supplemental_text: str = "") -> dict:
        if not image_bytes:
            raise ValueError("ファイルが空です")

        base_url = os.getenv("OLLAMA_BASE_URL")
        model = os.getenv("OLLAMA_MODEL")
        if not base_url or not model:
            raise ValueError("OLLAMA_BASE_URL / OLLAMA_MODEL を設定してください")

        image_b64 = base64.b64encode(image_bytes).decode("utf-8")
        prompt = (
            "あなたはOCR抽出エンジンです。請求書画像から以下のJSON形式で抽出してください。"
            '{"invoice_no":"", "line_items":[{"description":"","unitPrice":0,"qty":0,"小計":0}], "税額":0, "合計":0} '
            "JSON以外の文字は出力しないでください。"
        )
        if supplemental_text:
            prompt += f" 補助テキスト情報: {supplemental_text[:2000]}"

        async with httpx.AsyncClient(timeout=httpx.Timeout(60.0)) as client:
            try:
                response = await client.post(
                    f"{base_url.rstrip('/')}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "images": [image_b64],
                        "stream": False,
                        "format": "json",
                    },
                )
                response.raise_for_status()
            except httpx.HTTPStatusError as exc:
                if exc.response.status_code == 404 and "model" in exc.response.text.lower():
                    raise ValueError(
                        f"Ollamaモデル '{model}' が見つかりません。`ollama pull {model}` を実行してから再試行してください。"
                    ) from exc
                raise ValueError(f"Ollama呼び出しに失敗しました (status={exc.response.status_code})") from exc
            except httpx.ReadTimeout as exc:
                raise ValueError("Ollamaの応答がタイムアウトしました。モデル初回ロード中の可能性があります。再試行してください。") from exc
            except httpx.HTTPError as exc:
                raise ValueError("Ollamaへ接続できません。OLLAMA_BASE_URL を確認してください。") from exc
            raw = response.json().get("response", "").strip()
            if not raw:
                raise ValueError("Ollamaから抽出結果を取得できませんでした")

        parsed = self._parse_json_from_response(raw, filename)

        if not isinstance(parsed, dict):
            raise ValueError("Ollama応答の形式が不正です")
        return parsed

    def _parse_json_from_response(self, raw: str, filename: str) -> dict:
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            candidate = self._extract_json_candidate(raw)
            if candidate:
                try:
                    return json.loads(candidate)
                except json.JSONDecodeError:
                    pass

        preview = raw[:300].replace("\n", "\\n")
        logger.error("Ollama JSON parse failed for %s. raw_preview=%s", filename, preview)
        raise ValueError(f"Ollamaの応答JSONを解釈できません: {filename}")

    @staticmethod
    def _extract_json_candidate(raw: str) -> str | None:
        fenced = re.search(r"```json\s*(\{.*?\})\s*```", raw, flags=re.DOTALL | re.IGNORECASE)
        if fenced:
            return fenced.group(1)

        first = raw.find("{")
        last = raw.rfind("}")
        if first != -1 and last != -1 and last > first:
            return raw[first : last + 1]
        return None

"""YouTube transcript fetching utility."""

from __future__ import annotations

import os
from typing import Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from youtube_transcript_api import (  # type: ignore[import-untyped]
    NoTranscriptFound,
    TranscriptsDisabled,
    YouTubeTranscriptApi,
)


class YouTubeTranscriptFetcher:
    """Fetches structured transcripts for a given YouTube video."""

    def __init__(self, *, languages: Optional[List[str]] = None) -> None:
        self.languages = languages or ["en"]

    def fetch(self, video_id_or_url: str, *, max_segments: int = 200) -> Dict[str, object]:
        video_id = self._extract_video_id(video_id_or_url)
        if not video_id:
            raise ValueError("Unable to resolve YouTube video ID")
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=self.languages)
        except (TranscriptsDisabled, NoTranscriptFound) as exc:
            raise RuntimeError(f"Transcript unavailable for {video_id}") from exc

        segments = transcript[:max_segments]
        text = " ".join(segment["text"] for segment in segments).strip()
        return {
            "video_id": video_id,
            "segments": segments,
            "excerpt": text[:500],
        }

    @staticmethod
    def _extract_video_id(identifier: str) -> Optional[str]:
        if len(identifier) == 11 and "/" not in identifier:
            return identifier
        parsed = urlparse(identifier)
        if parsed.hostname in {"youtu.be"}:
            return parsed.path.lstrip("/") or None
        if parsed.hostname and "youtube" in parsed.hostname:
            query = parse_qs(parsed.query)
            return query.get("v", [None])[0]
        return None


if __name__ == "__main__":
    video_id = os.getenv("YOUTUBE_VIDEO_ID")
    if not video_id:
        print("Set YOUTUBE_VIDEO_ID to run the transcript fetch demo.")
    else:
        fetcher = YouTubeTranscriptFetcher()
        print(fetcher.fetch(video_id, max_segments=2))

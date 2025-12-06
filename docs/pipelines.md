# Pipeline Contracts

## Content Calendar (`pipelines/content_calendar.py`)

### Request Schema

```json
{
  "pipeline": "content_calendar",
  "inputs": {
    "brand": "<string>",
    "niche": "<string>",
    "days": 30,
    "tone": "<string optional>",
    "objectives": ["<string>", "<string>"],
    "reference_files": [
      { "path": "/data/voice.csv", "type": "csv", "description": "Persona data" },
      { "path": "/data/brand.pdf", "type": "pdf" }
    ],
      "channels": ["instagram", "youtube"],
      "perform_ocr": true
  }
}
```

- `reference_files` can point to assets parsed through file parsing tools.
- `channels` controls which distribution formats the Content/Rviewer agents target.

### Response Schema (high level)

```json
{
  "pipeline": "content_calendar",
  "status": "success",
  "calendar": [
    {
      "day": 1,
      "date": "2025-01-01",
      "theme": "Leg Day Motivation",
      "primary_platform": "instagram",
      "content_type": "carousel",
      "hook": "...",
      "cta": "...",
      "assets_needed": ["pdf", "slides"],
      "review_notes": "..."
    }
  ],
  "exports": {
    "pdf_path": "/tmp/calendar.pdf",
    "slides_path": "/tmp/calendar.pptx"
  }
}
```

## Brand Strategy (`pipelines/brand_strategy.py`)

- Input mirrors the brand brief plus optional `reference_files`.
- Output contains analytics findings, messaging pillars, reviewer QA notes, and reference digests.
- Example request:

```json
{
  "pipeline": "brand_strategy",
  "inputs": {
    "brand": "APAS Fitness",
    "mission": "Democratize elite coaching",
    "target_audience": "Busy professionals 25-40",
    "differentiators": ["Hybrid coaching", "Biometric feedback"],
    "objectives": ["Increase community signups"],
    "channels": ["instagram", "newsletter"],
    "reference_files": [
      { "path": "/data/voice.pdf", "type": "pdf" }
    ]
  }
}
```

## Analytics Report (`pipelines/analytics_report.py`)

- Consumes metric references and produces KPI insights + reviewer QA.
- Optional `export_pdf` flag returns a generated PDF path.
- Response includes `report`, `review`, `references`, and `exports`.

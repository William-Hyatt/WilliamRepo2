import base64
import json
import os
from typing import Any

from flask import Flask, jsonify, render_template, request

try:
    from openai import OpenAI
except Exception:  # pragma: no cover
    OpenAI = None


app = Flask(__name__)

REVIEW_AREAS = [
    "Traffic Flow",
    "Vertical Transportation",
    "Corridor Width",
    "Guestrooms",
    "Fire Life Safety",
    "F&B/Kitchen Planning",
    "Events/MICE Space Planning",
    "Back of House Planning",
]

SYSTEM_PROMPT = """You are a senior hospitality design auditor.
Review hotel floor plans and return a strict JSON object.
Evaluate these areas:
1) Traffic Flow
2) Vertical Transportation
3) Corridor Width
4) Guestrooms
5) Fire Life Safety (specific to selected country/region)
6) F&B/Kitchen Planning
7) Events/MICE Space Planning
8) Back of House Planning

Output format:
{
  "overall_summary": "...",
  "risk_level": "Low|Medium|High",
  "scores": {
    "Traffic Flow": 0-100,
    ... all eight criteria ...
  },
  "findings": [
    {
      "category": "one of the eight criteria",
      "severity": "Low|Medium|High",
      "issue": "short issue",
      "why_it_matters": "short impact",
      "recommendation": "specific recommendation"
    }
  ],
  "next_steps": ["...", "..."]
}
Only valid JSON. No markdown.
"""


def _fallback_review(country_or_region: str) -> dict[str, Any]:
    scores = {area: 65 for area in REVIEW_AREAS}
    return {
        "overall_summary": (
            "Baseline review generated without AI vision (set OPENAI_API_KEY for image-aware auditing). "
            f"Use this as a checklist for a detailed design workshop in {country_or_region}."
        ),
        "risk_level": "Medium",
        "scores": scores,
        "findings": [
            {
                "category": "Fire Life Safety",
                "severity": "High",
                "issue": "Local life-safety code compliance cannot be confirmed from baseline mode.",
                "why_it_matters": "Non-compliance can delay permits and increase redesign cost.",
                "recommendation": (
                    f"Map egress, travel distances, stair pressurization, and fire compartmentation "
                    f"against the latest authority requirements in {country_or_region}."
                ),
            },
            {
                "category": "Traffic Flow",
                "severity": "Medium",
                "issue": "Potential guest/service circulation conflicts.",
                "why_it_matters": "Conflicts reduce guest experience and operational efficiency.",
                "recommendation": "Separate front-of-house and back-of-house routes at key pinch points.",
            },
        ],
        "next_steps": [
            "Upload floor plan with OPENAI_API_KEY configured for visual analysis.",
            "Run a code-specific life safety check with a local fire consultant.",
            "Validate corridor widths and turning radii against accessibility standards.",
        ],
    }


def _ai_review(image_bytes: bytes, mime_type: str, country_or_region: str) -> dict[str, Any]:
    if OpenAI is None:
        return _fallback_review(country_or_region)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return _fallback_review(country_or_region)

    client = OpenAI(api_key=api_key)
    b64 = base64.b64encode(image_bytes).decode("utf-8")
    data_url = f"data:{mime_type};base64,{b64}"

    user_prompt = (
        "Review this floor plan for a hotel project in "
        f"{country_or_region}. Highlight key risks, assumptions, and practical design actions."
    )

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": [{"type": "input_text", "text": SYSTEM_PROMPT}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": user_prompt},
                    {"type": "input_image", "image_url": data_url},
                ],
            },
        ],
    )

    text = response.output_text.strip()
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return {
            **_fallback_review(country_or_region),
            "overall_summary": "Model response parsing failed; returned fallback checklist.",
        }
    return parsed


@app.route("/")
def index():
    return render_template("index.html")


@app.post("/api/review")
def review():
    file = request.files.get("floorplan")
    if not file:
        return jsonify({"error": "Please upload a floor plan image file."}), 400

    country_or_region = request.form.get("country_or_region", "the selected region")
    mime = file.mimetype or "image/png"

    if not mime.startswith("image/"):
        return jsonify({"error": "Only image uploads are currently supported."}), 400

    image = file.read()
    result = _ai_review(image, mime, country_or_region)
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

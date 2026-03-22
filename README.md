# Floor Plan AI Auditor

A lightweight web app that reviews uploaded hotel floor plan images and flags issues in:

- Traffic Flow
- Vertical Transportation
- Corridor Width
- Guestrooms
- Fire Life Safety (country/region specific)
- F&B/Kitchen Planning
- Events/MICE Space Planning
- Back of House Planning

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://localhost:8000`.

## AI mode vs fallback mode

- **AI mode**: Set `OPENAI_API_KEY` to analyze the uploaded floor plan with vision-capable reasoning.
- **Fallback mode**: Without API key, the app returns a structured checklist + baseline recommendations.

## Notes

- Current upload support is image files only (`image/*`).
- You can extend `app.py` to add PDF conversion (e.g., rasterizing first page for analysis).

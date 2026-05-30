# Image Alt Analysis (step-by-step)

Purpose
- Explain image alt analysis: extraction, scoring, and reporting missing/poor alt attributes.

Files involved
- [dashboard/services/image_extractor.py](dashboard/services/image_extractor.py)
- [dashboard/models.py](dashboard/models.py)
- templates/dashboard/*

Step-by-step implementation
1. Extraction
   - Use `image_extractor.py` to parse HTML and extract `<img>` tags, `alt` attributes, and surrounding context.
2. Scoring
   - Define rules: missing alt (high priority), empty alt, duplicate nonspecific alt, overly long alt text.
3. Persisting
   - Save results to an analysis record (JSONField) including per-image findings and counts.
4. Presentation
   - Show list of images, status (OK / Missing / Poor), and quick actions (copy suggested alt, open image URL).
5. Tests
   - Add tests supplying HTML fixtures and asserting detection and scoring.

Extending
- Integrate machine-suggested alt text using an external service, storing suggestions alongside current findings.

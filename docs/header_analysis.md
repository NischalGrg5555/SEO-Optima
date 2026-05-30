# Header Analysis (step-by-step)

Purpose
- Document header extraction (H1/H2/H3 etc.), duplicates, length checks, and recommendations.

Files involved
- [dashboard/services/header_extractor.py](dashboard/services/header_extractor.py)
- [dashboard/models.py](dashboard/models.py)

Step-by-step implementation
1. Extraction
   - Use `header_extractor.py` to parse HTML and collect headings with their text, order, and position.
2. Checks
   - Detect missing H1, multiple H1s, duplicate headings, overly long or short headings, and inconsistent hierarchy.
3. Persisting
   - Store findings in an analysis JSON record with counts and per-heading notes.
4. Presentation
   - Show a structured outline in the analysis detail with quick fixes and examples.
5. Tests
   - Provide HTML fixtures containing varied heading structures and assert detection correctness.

Extending
- Offer suggestions for rephrasing headings and integrate with keyword analysis to recommend target keywords.

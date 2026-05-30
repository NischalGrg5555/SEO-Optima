# Keyword Analysis (step-by-step)

Purpose
- Document how keyword extraction and analysis works for a page and how to modify extraction rules.

Files involved
- [dashboard/services/keyword_extractor.py](dashboard/services/keyword_extractor.py)
- [dashboard/models.py](dashboard/models.py)

Step-by-step implementation
1. Extraction
   - `keyword_extractor.py` should fetch page HTML and extract text from important elements (title, h1-h3, meta description, body content).
   - Use tokenization and simple frequency or TF-IDF heuristics to derive candidate keywords.
2. Normalization
   - Lowercase, remove stopwords, stem/lemmatize if needed, and collapse duplicates.
3. Storage
   - Save extracted keywords and counts in the analysis JSON result for later display and mapping to GSC queries.
4. Presentation
   - Show keyword clouds, top keywords, and matches to GSC keywords if connected.
5. Tests
   - Use HTML fixtures and assert that extraction returns expected top keywords.

Extending
- Swap in an NLP library (spaCy) for more accurate tokenization and noun-phrase extraction.

"""
Service to run AI Search / AEO (Answer Engine Optimization) Readiness Audits on web pages.
Evaluates passage answerability, structural RAG ingestion, Schema.org entity grounding,
AI bot crawler access, and trust/evidence density.
"""
import re
import json
from urllib.parse import urlparse
from typing import Dict, List, Any
import requests
from bs4 import BeautifulSoup


AI_BOTS = [
    {'name': 'GPTBot', 'owner': 'OpenAI'},
    {'name': 'PerplexityBot', 'owner': 'Perplexity'},
    {'name': 'ClaudeBot', 'owner': 'Anthropic'},
    {'name': 'Google-Extended', 'owner': 'Google AI'},
    {'name': 'ByteDance', 'owner': 'TikTok / ByteDance'},
    {'name': 'ChatGPT-User', 'owner': 'OpenAI Browsing'},
]

QUESTION_STARTERS = (
    'what', 'how', 'why', 'who', 'where', 'when', 'which',
    'is', 'can', 'does', 'do', 'should', 'are', 'best', 'top'
)


def analyze_ai_readiness(url: str, timeout: int = 30) -> Dict[str, Any]:
    """
    Perform a complete AI Search / AEO Readiness Audit on a target URL.
    
    Returns:
        Dict containing scores, audit_results, and actionable recommendations.
    """
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 SEOOptimaBot/1.0'
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        html_content = response.text
    except requests.exceptions.Timeout:
        raise Exception(f"Request timed out while fetching {url}")
    except requests.exceptions.RequestException as e:
        raise Exception(f"Error fetching URL {url}: {str(e)}")

    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Extract JSON-LD scripts before removing script tags from soup
    json_ld_scripts = soup.find_all('script', type='application/ld+json')
    detected_schemas = []
    schema_entities = []
    
    for script in json_ld_scripts:
        try:
            if not script.string:
                continue
            data = json.loads(script.string)
            
            def extract_types(obj):
                if isinstance(obj, dict):
                    if '@type' in obj:
                        t = obj['@type']
                        if isinstance(t, list):
                            detected_schemas.extend(t)
                        else:
                            detected_schemas.append(t)
                    if 'name' in obj and isinstance(obj['name'], str):
                        schema_entities.append(obj['name'])
                    for v in obj.values():
                        extract_types(v)
                elif isinstance(obj, list):
                    for item in obj:
                        extract_types(item)

            extract_types(data)
        except Exception:
            pass

    detected_schemas = list(set(detected_schemas))
    schema_entities = list(set(schema_entities))
    
    # Clean page text for word count and text analysis
    soup_text = BeautifulSoup(html_content, 'html.parser')
    for element in soup_text(['script', 'style', 'noscript', 'svg']):
        element.extract()

    page_text = soup_text.get_text(separator=' ', strip=True)
    total_words = len(page_text.split())

    # --- 1. Passage Answerability Analysis ---
    heading_tags = ['h1', 'h2', 'h3', 'h4']
    headings = soup.find_all(heading_tags)
    question_headings = []
    answer_passages = []
    
    for h in headings:
        h_text = h.get_text(strip=True)
        h_lower = h_text.lower()
        
        # Check if heading is a question or intent prompt
        is_question = h_lower.endswith('?') or any(h_lower.startswith(q) for q in QUESTION_STARTERS)
        
        if is_question:
            # Find next paragraph sibling or paragraph inside section
            next_p = None
            curr = h.next_sibling
            while curr:
                if curr.name == 'p' and curr.get_text(strip=True):
                    next_p = curr
                    break
                elif curr.name in heading_tags:
                    break
                elif hasattr(curr, 'find_all'):
                    p_inside = curr.find('p')
                    if p_inside and p_inside.get_text(strip=True):
                        next_p = p_inside
                        break
                curr = curr.next_sibling
                
            p_text = next_p.get_text(strip=True) if next_p else ""
            p_word_count = len(p_text.split())
            
            # Direct answer passage criteria: 30 to 90 words
            is_optimal_passage = 30 <= p_word_count <= 90
            
            passage_info = {
                'heading_level': h.name.upper(),
                'heading_text': h_text,
                'passage_text': p_text[:200] + ('...' if len(p_text) > 200 else ''),
                'word_count': p_word_count,
                'is_optimal': is_optimal_passage,
                'status': 'Optimal (30-90 words)' if is_optimal_passage else ('Missing / Too Short' if p_word_count < 30 else 'Too Long / Not Direct')
            }
            question_headings.append(h_text)
            answer_passages.append(passage_info)

    optimal_passages_count = sum(1 for p in answer_passages if p['is_optimal'])
    total_questions_count = len(answer_passages)
    
    if total_questions_count == 0:
        answerability_score = 40  # Penalty for zero question headings
    else:
        answerability_score = int(min(100, (optimal_passages_count / total_questions_count) * 100))
        if answerability_score < 50 and total_questions_count > 0:
            answerability_score = max(answerability_score, 50)  # Baseline if questions exist

    # --- 2. Structural RAG Ingestion Audit ---
    ordered_lists = len(soup.find_all('ol'))
    unordered_lists = len(soup.find_all('ul'))
    tables = soup.find_all('table')
    table_count = len(tables)
    tables_with_thead = sum(1 for t in tables if t.find('thead'))
    definition_lists = len(soup.find_all('dl'))
    
    structure_score = 50  # Base
    if ordered_lists > 0:
        structure_score += 15
    if unordered_lists > 0:
        structure_score += 10
    if table_count > 0:
        structure_score += 15
    if tables_with_thead > 0:
        structure_score += 10
    structure_score = min(100, structure_score)

    # --- 3. Schema & Entity Grounding Audit ---
    entity_score = 30
    if len(detected_schemas) > 0:
        entity_score += 30
    if any(s in ['Organization', 'Article', 'Product', 'Person', 'FAQPage'] for s in detected_schemas):
        entity_score += 25
    if len(schema_entities) > 0:
        entity_score += 15
    entity_score = min(100, entity_score)

    # --- 4. AI Bot Accessibility & Technical Audit ---
    parsed_url = urlparse(url)
    robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
    bot_access = []
    blocked_bots_count = 0
    
    try:
        r_resp = requests.get(robots_url, headers=headers, timeout=10)
        robots_txt = r_resp.text if r_resp.status_code == 200 else ""
    except Exception:
        robots_txt = ""

    for bot in AI_BOTS:
        b_name = bot['name']
        is_blocked = False
        if robots_txt:
            # Simple line-by-line inspection for User-agent: Bot Disallow: /
            pattern = re.compile(rf'User-agent:\s*{re.escape(b_name)}.*?\nDisallow:\s*(/.*)', re.IGNORECASE | re.DOTALL)
            if pattern.search(robots_txt):
                is_blocked = True

        if is_blocked:
            blocked_bots_count += 1
            
        bot_access.append({
            'name': b_name,
            'owner': bot['owner'],
            'allowed': not is_blocked
        })

    # JS Rendering Dependence Check
    raw_text_len = len(page_text)
    js_dependent = raw_text_len < 300 and len(soup.find_all(['div', 'section'])) > 10

    technical_score = 100
    if blocked_bots_count > 0:
        technical_score -= (blocked_bots_count * 15)
    if js_dependent:
        technical_score -= 30
    technical_score = max(0, min(100, technical_score))

    # --- 5. Trust & Data Evidence Density ---
    # Find numbers / stats
    numbers = re.findall(r'\b\d+(?:\.\d+)?%?|\$\d+', page_text)
    number_count = len(numbers)
    numeric_density = round((number_count / max(1, total_words)) * 100, 2)
    
    # Author & Date detection
    has_author = bool(soup.find(attrs={'itemprop': 'author'}) or soup.find(class_=re.compile(r'author|byline', re.I)))
    has_date = bool(soup.find('time') or soup.find(attrs={'itemprop': re.compile(r'date', re.I)}))
    
    # Outbound links
    outbound_links = 0
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('http') and parsed_url.netloc not in href:
            outbound_links += 1

    trust_score = 40
    if has_author:
        trust_score += 20
    if has_date:
        trust_score += 15
    if numeric_density >= 1.0:
        trust_score += 15
    if outbound_links >= 2:
        trust_score += 10
    trust_score = min(100, trust_score)

    # --- Composite Overall Score ---
    overall_score = int(
        (0.30 * answerability_score) +
        (0.20 * structure_score) +
        (0.20 * entity_score) +
        (0.15 * technical_score) +
        (0.15 * trust_score)
    )

    # --- Recommendations Engine ---
    recommendations = []

    if total_questions_count == 0:
        recommendations.append({
            'category': 'Answerability',
            'title': 'Add Question-Based Headings',
            'severity': 'High',
            'impact': 'Improves RAG passage retrieval for conversational AI queries.',
            'description': 'No question-based headings (e.g. starting with What, How, Why or ending with "?") were found on the page.',
            'fix': 'Reframe key H2/H3 headings into user questions (e.g., "What is Generative Engine Optimization?").'
        })
    elif optimal_passages_count < total_questions_count:
        sub_optimal_heading = next((p['heading_text'] for p in answer_passages if not p['is_optimal']), 'your main headings')
        recommendations.append({
            'category': 'Answerability',
            'title': 'Optimize Passage Length Below Question Headings',
            'severity': 'High',
            'impact': 'Allows AI crawlers to chunk and quote direct definition passages.',
            'description': f'Some question headings (e.g. "{sub_optimal_heading}") lack a 40–80 word direct answer paragraph immediately below.',
            'fix': f'Add a 40–60 word direct definition paragraph immediately beneath "{sub_optimal_heading}" before adding deeper detailed sections.'
        })

    if ordered_lists == 0:
        recommendations.append({
            'category': 'Structure',
            'title': 'Convert Step-by-Step Instructions into `<ol>` Lists',
            'severity': 'Medium',
            'impact': 'Helps LLMs extract ordered workflows into bulleted AI search answers.',
            'description': 'The page contains no HTML ordered list elements (`<ol>`).',
            'fix': 'Wrap sequential workflows, step-by-step guides, or procedures in native `<ol><li>` tags.'
        })

    if table_count == 0:
        recommendations.append({
            'category': 'Structure',
            'title': 'Add Semantic Data Tables',
            'severity': 'Medium',
            'impact': 'Enables RAG indexers to ingest comparison data without hallucinating attributes.',
            'description': 'No data tables (`<table>`) were detected on the page.',
            'fix': 'Present features, specs, pricing, or comparative metrics inside styled `<table>` elements with explicit `<thead>` tags.'
        })

    if len(detected_schemas) == 0:
        recommendations.append({
            'category': 'Entity',
            'title': 'Inject JSON-LD Structured Data Schema',
            'severity': 'High',
            'impact': 'Establishes clear machine-readable context for Knowledge Graph indexing.',
            'description': 'No JSON-LD structured data (`<script type="application/ld+json">`) was found.',
            'fix': 'Add Organization, Article, Person, or FAQPage JSON-LD schema to accurately represent visible page content.'
        })

    if blocked_bots_count > 0:
        blocked_names = ", ".join([b['name'] for b in bot_access if not b['allowed']])
        recommendations.append({
            'category': 'Technical',
            'title': 'Unblock AI Crawlers in robots.txt',
            'severity': 'Critical',
            'impact': 'Prevents AI engines from summarizing or citing real-time web content.',
            'description': f'Your `robots.txt` file disallows access for AI bots: {blocked_names}.',
            'fix': f'Remove Disallow rules targeting user-agents: {blocked_names} in `robots.txt`.'
        })

    if js_dependent:
        recommendations.append({
            'category': 'Technical',
            'title': 'Reduce Client-Side JavaScript Rendering Dependency',
            'severity': 'High',
            'impact': 'Ensures lightweight AI web scrapers can parse complete text content without executing JS.',
            'description': 'Initial raw HTML contains sparse body text while container structure is heavy, indicating client-side JS rendering dependency.',
            'fix': 'Use Server-Side Rendering (SSR) or Static Site Generation (SSG) for main body text.'
        })

    if not has_author:
        recommendations.append({
            'category': 'Trust',
            'title': 'Add Explicit Author Attribution & Person Schema',
            'severity': 'Medium',
            'impact': 'Strengthens E-E-A-T credentials for AI source evaluation.',
            'description': 'No author byline or author schema metadata was detected.',
            'fix': 'Add an author bio block with link to author profile and include `Person` JSON-LD schema with `sameAs` social links.'
        })

    if numeric_density < 0.8:
        recommendations.append({
            'category': 'Trust',
            'title': 'Enrich Numerical Data & Evidence Density',
            'severity': 'Low',
            'impact': 'Increases citation probability as AI search engines prioritize primary quantitative sources.',
            'description': f'The article has low numerical density ({numeric_density}% of words).',
            'fix': 'Incorporate original statistics, percentage metrics, benchmarks, or explicit research data.'
        })

    audit_results = {
        'url': url,
        'total_words': total_words,
        'question_headings_count': total_questions_count,
        'optimal_passages_count': optimal_passages_count,
        'passages_data': answer_passages,
        'structure': {
            'ordered_lists': ordered_lists,
            'unordered_lists': unordered_lists,
            'table_count': table_count,
            'tables_with_thead': tables_with_thead,
            'definition_lists': definition_lists,
        },
        'entity': {
            'detected_schemas': detected_schemas,
            'schema_entities': schema_entities,
        },
        'technical': {
            'bot_access': bot_access,
            'blocked_bots_count': blocked_bots_count,
            'js_dependent': js_dependent,
            'robots_url': robots_url,
        },
        'trust': {
            'numeric_density': numeric_density,
            'number_count': number_count,
            'has_author': has_author,
            'has_date': has_date,
            'outbound_links': outbound_links,
        }
    }

    return {
        'overall_score': overall_score,
        'answerability_score': answerability_score,
        'structure_score': structure_score,
        'entity_score': entity_score,
        'technical_score': technical_score,
        'trust_score': trust_score,
        'audit_results': audit_results,
        'recommendations': recommendations
    }

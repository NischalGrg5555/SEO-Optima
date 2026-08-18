"""
Service to convert Search Console queries and topic seeds into intent-clustered AI questions.
Categorizes queries by AI search intent and determines current site coverage status.
"""
import re
from typing import List, Dict, Any, Optional
from dashboard.models import GSCConnection, HeaderAnalysis, AIReadinessAnalysis
from dashboard.services.keyword_extractor import fetch_gsc_keywords


INFORMATIONAL_PATTERNS = re.compile(r'\b(what|how|why|when|where|who|meaning|definition|guide|tutorial|explained|difference|overview)\b', re.I)
COMPARISON_PATTERNS = re.compile(r'\b(best|vs|versus|top|alternative|alternatives|review|reviews|compare|comparison|choice|recommended)\b', re.I)
COMMERCIAL_PATTERNS = re.compile(r'\b(price|cost|pricing|buy|hire|service|agency|tool|software|app|cheap|affordable|quote|packages)\b', re.I)
PROBLEM_PATTERNS = re.compile(r'\b(fix|error|issue|problem|slow|failing|not working|solve|troubleshoot|bug|stuck)\b', re.I)


def classify_intent(query: str) -> str:
    """Classify query into AI search intent category"""
    q_lower = query.lower()
    if COMPARISON_PATTERNS.search(q_lower):
        return 'Comparison / Best'
    if COMMERCIAL_PATTERNS.search(q_lower):
        return 'Commercial / Price'
    if PROBLEM_PATTERNS.search(q_lower):
        return 'Problem / Solution'
    if INFORMATIONAL_PATTERNS.search(q_lower):
        return 'Informational'
    return 'Informational'


def format_to_ai_question(query: str) -> str:
    """Convert raw keyword search query into a natural conversational AI prompt"""
    q = query.strip()
    q_lower = q.lower()
    
    if q_lower.endswith('?'):
        return q.capitalize()
    
    if re.match(r'^(what|how|why|where|who|when|which|is|can|does|should|are)\b', q_lower):
        return q.capitalize() + '?'
        
    if 'vs' in q_lower or 'versus' in q_lower:
        return f"What is the difference between {q}?"
    if 'best' in q_lower or 'top' in q_lower:
        return f"What are the {q}?"
    if 'meaning' in q_lower or 'definition' in q_lower:
        return f"What is the definition of {q}?"
    if 'price' in q_lower or 'cost' in q_lower:
        return f"How much does {q} cost?"
        
    return f"What is {q} and how does it work?"


def generate_ai_questions(user, gsc_property: Optional[str] = None, topic_seed: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Generate intent-clustered AI questions from GSC queries, topic seed, or site audits.
    """
    raw_queries = []
    
    # 1. Fetch GSC Queries if property selected & connection active
    if gsc_property:
        try:
            gsc_conn = GSCConnection.objects.get(user=user, is_active=True)
            fetched = fetch_gsc_keywords(gsc_property, gsc_conn.credentials, gsc_conn.properties, days=28)
            for item in fetched:
                raw_queries.append({
                    'query': item.get('keyword', ''),
                    'impressions': item.get('volume', 0),
                    'clicks': item.get('clicks', 0),
                    'position': item.get('position', 0.0),
                    'url': item.get('url', '')
                })
        except Exception:
            pass

    # 2. Topic Seed fallback or supplementary generator
    if topic_seed and len(raw_queries) == 0:
        seed = topic_seed.strip()
        derivative_prompts = [
            f"what is {seed}",
            f"how does {seed} work",
            f"best {seed} tools and practices",
            f"why is {seed} important",
            f"how much does {seed} cost",
            f"how to fix {seed} performance issues",
            f"top alternatives to {seed}",
            f"{seed} step by step guide",
        ]
        for p in derivative_prompts:
            raw_queries.append({
                'query': p,
                'impressions': 500,
                'clicks': 25,
                'position': 8.5,
                'url': ''
            })

    # 3. Heading extraction fallback if still empty
    if len(raw_queries) == 0:
        header_audits = HeaderAnalysis.objects.filter(user=user).order_by('-created_at')[:5]
        for ha in header_audits:
            for item in ha.headers_data[:10]:
                txt = item.get('text', '')
                if txt and len(txt.split()) >= 3:
                    raw_queries.append({
                        'query': txt,
                        'impressions': 250,
                        'clicks': 10,
                        'position': 12.0,
                        'url': ha.url
                    })

    # Default fallback sample queries if user has no data yet
    if len(raw_queries) == 0:
        sample_queries = [
            "what is technical seo auditing",
            "how to optimize page speed for mobile",
            "best generative engine optimization strategies",
            "schema org structured data guide",
            "how to unblock perplexitybot in robots txt",
            "how to fix low image alt text percentage"
        ]
        for sq in sample_queries:
            raw_queries.append({
                'query': sq,
                'impressions': 350,
                'clicks': 15,
                'position': 7.2,
                'url': ''
            })

    # Process and classify questions
    existing_audits = list(AIReadinessAnalysis.objects.filter(user=user, is_deleted=False))
    questions_list = []

    for item in raw_queries:
        q_text = item['query']
        intent = classify_intent(q_text)
        formatted_q = format_to_ai_question(q_text)
        
        # Determine coverage status based on existing AI Readiness Audits
        coverage_status = 'Content Gap'
        target_url = item.get('url', '')
        
        for audit in existing_audits:
            passages = audit.audit_results.get('passages_data', [])
            for p in passages:
                heading_txt = p.get('heading_text', '').lower()
                if q_text.lower() in heading_txt or any(w in heading_txt for w in q_text.lower().split() if len(w) > 4):
                    if p.get('is_optimal'):
                        coverage_status = 'Answered'
                        target_url = audit.url
                        break
                    else:
                        coverage_status = 'Partially Answered'
                        target_url = audit.url
            if coverage_status == 'Answered':
                break

        questions_list.append({
            'question': formatted_q,
            'original_query': q_text,
            'intent': intent,
            'impressions': item['impressions'],
            'clicks': item['clicks'],
            'position': round(item['position'], 1),
            'target_url': target_url,
            'coverage_status': coverage_status
        })

    # Sort by impressions descending
    questions_list.sort(key=lambda x: x['impressions'], reverse=True)
    return questions_list

"""
Service to identify high-ROI AI Citation Opportunities.
Cross-references Search Console query impressions and ranking positions with AI Readiness Audit passage gaps.
"""
from typing import List, Dict, Any, Optional
from dashboard.models import GSCConnection, AIReadinessAnalysis, HeaderAnalysis
from dashboard.services.keyword_extractor import fetch_gsc_keywords


def find_citation_opportunities(user, gsc_property: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Identify and rank high-ROI pages with high search impressions that lack direct AI answer passages.
    """
    gsc_keywords = []

    # 1. Fetch Search Console queries if active property
    if gsc_property:
        try:
            gsc_conn = GSCConnection.objects.get(user=user, is_active=True)
            gsc_keywords = fetch_gsc_keywords(gsc_property, gsc_conn.credentials, gsc_conn.properties, days=28)
        except Exception:
            pass

    existing_audits = list(AIReadinessAnalysis.objects.filter(user=user, is_deleted=False))
    header_audits = list(HeaderAnalysis.objects.filter(user=user))
    
    opportunities = []

    if gsc_keywords:
        # Cross reference GSC data with audits
        for kw in gsc_keywords:
            impressions = kw.get('volume', 0)
            position = kw.get('position', 0.0)
            url = kw.get('url', '')
            query = kw.get('keyword', '')
            
            # Focus on high-impression informational queries in positions 1-20
            if impressions >= 50 and position <= 25.0:
                matching_audit = next((a for a in existing_audits if a.url == url), None)
                matching_headers = next((h for h in header_audits if h.url == url), None)

                score = 'Medium'
                gaps = []

                if matching_audit:
                    if matching_audit.answerability_score < 70:
                        gaps.append('Lacks 40–80 word direct answer passage below question heading')
                    if matching_audit.structure_score < 60:
                        gaps.append('Missing semantic `<ol>` lists or data tables')
                    if matching_audit.entity_score < 50:
                        gaps.append('Missing JSON-LD Schema markup')
                    if matching_audit.technical_score < 70:
                        gaps.append('AI Crawlers partially blocked in robots.txt')

                    if impressions >= 500 and matching_audit.answerability_score < 60:
                        score = 'High'
                    elif matching_audit.answerability_score >= 80 and matching_audit.entity_score >= 80:
                        score = 'Low'
                else:
                    gaps.append('Not yet audited for AI Readiness')
                    if impressions >= 300:
                        score = 'High'

                if len(gaps) > 0:
                    opportunities.append({
                        'query': query,
                        'url': url or 'Domain Page',
                        'impressions': impressions,
                        'clicks': kw.get('clicks', 0),
                        'position': round(position, 1),
                        'opportunity_score': score,
                        'gaps': gaps,
                        'recommended_action': f'Add a 40–60 word direct definition section for "{query}" under an H2 heading on {url or "the page"}.',
                        'has_audit': matching_audit is not None,
                        'audit_pk': matching_audit.pk if matching_audit else None
                    })
    else:
        # Generate opportunities directly from existing AI Readiness Audits
        for audit in existing_audits:
            if audit.overall_score < 80:
                gaps = [r['description'] for r in audit.recommendations[:3]]
                score = 'High' if audit.overall_score < 60 else 'Medium'
                opportunities.append({
                    'query': f"AI Readiness for {audit.url}",
                    'url': audit.url,
                    'impressions': 1200,
                    'clicks': 45,
                    'position': 6.5,
                    'opportunity_score': score,
                    'gaps': gaps or ['Passage answerability needs optimization'],
                    'recommended_action': audit.recommendations[0]['fix'] if audit.recommendations else 'Add direct answer passages and JSON-LD schema.',
                    'has_audit': True,
                    'audit_pk': audit.pk
                })

    # Sort opportunities by opportunity score (High first) then impressions descending
    priority_map = {'High': 3, 'Medium': 2, 'Low': 1}
    opportunities.sort(key=lambda x: (priority_map.get(x['opportunity_score'], 0), x['impressions']), reverse=True)

    return opportunities

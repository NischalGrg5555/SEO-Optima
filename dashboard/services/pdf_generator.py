"""
PDF Report Generation Service
Generates professional SEO analysis reports with metrics and recommendations
"""
from io import BytesIO
from datetime import datetime
from django.core.files.base import ContentFile
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.platypus import KeepTogether
from reportlab.pdfgen import canvas


def get_metric_category(value, metric_type):
    """Categorize metric values into Fast/Average/Poor."""
    if value is None:
        return ('Unknown', colors.gray)
    if metric_type == 'LCP':  # Largest Contentful Paint (seconds)
        if value <= 2.5:
            return ('Fast', colors.green)
        elif value <= 4.0:
            return ('Average', colors.orange)
        else:
            return ('Poor', colors.red)
    
    elif metric_type == 'INP':  # Interaction to Next Paint (milliseconds)
        if value <= 200:
            return ('Fast', colors.green)
        elif value <= 500:
            return ('Average', colors.orange)
        else:
            return ('Poor', colors.red)
    
    elif metric_type == 'CLS':  # Cumulative Layout Shift (score)
        if value <= 0.1:
            return ('Fast', colors.green)
        elif value <= 0.25:
            return ('Average', colors.orange)
        else:
            return ('Poor', colors.red)
    
    return ('Unknown', colors.gray)


def _extract_metric(metrics, full_response, metric_key, audit_key, numeric_divisor=1):
    """Return display and numeric values from stored metrics or raw Lighthouse audits."""
    display_value = 'N/A'
    numeric_value = None

    metric = metrics.get(metric_key) if isinstance(metrics, dict) else None
    if isinstance(metric, dict):
        display_value = metric.get('value', display_value)
        numeric_value = metric.get('numericValue', numeric_value)

    if numeric_value is None or display_value == 'N/A':
        audits = {}
        if isinstance(full_response, dict):
            audits = full_response.get('lighthouseResult', {}).get('audits', {})

        audit = audits.get(audit_key, {}) if isinstance(audits, dict) else {}
        if display_value == 'N/A':
            display_value = audit.get('displayValue', display_value)
        if numeric_value is None:
            numeric_value = audit.get('numericValue', numeric_value)

    if numeric_value is not None and numeric_divisor:
        numeric_value = numeric_value / numeric_divisor

    return display_value, numeric_value


def _extract_field_metric(full_response, metric_key, value_formatter=None, numeric_divisor=1):
    """Return display and numeric values from CrUX field data in the response."""
    if not isinstance(full_response, dict):
        return 'N/A', None

    loading_experience = full_response.get('loadingExperience', {})
    origin_loading_experience = full_response.get('originLoadingExperience', {})
    experience_data = origin_loading_experience or loading_experience
    field_metrics = experience_data.get('metrics', {}) if isinstance(experience_data, dict) else {}

    metric = field_metrics.get(metric_key, {}) if isinstance(field_metrics, dict) else {}
    percentile = metric.get('percentile')
    if percentile is None:
        return 'N/A', None

    numeric_value = percentile / numeric_divisor if numeric_divisor else percentile
    if value_formatter:
        display_value = value_formatter(percentile)
    else:
        display_value = str(numeric_value)

    return display_value, numeric_value


def generate_basic_report(user, title, pagespeed_analysis=None, keyword_analysis=None, 
                         image_analysis=None, headers_data=None):
    """
    Generate a Basic PDF Report with selected analyses
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, topMargin=0.75*inch, bottomMargin=0.75*inch)
    story = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#1a1a1a'),
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=12,
        spaceBefore=20,
        fontName='Helvetica-Bold'
    )
    
    subheading_style = ParagraphStyle(
        'CustomSubHeading',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#34495e'),
        spaceAfter=8,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        textColor=colors.HexColor('#2c3e50'),
        spaceAfter=8,
        alignment=TA_JUSTIFY
    )
    
    # Title
    story.append(Paragraph(title, title_style))
    story.append(Paragraph(f"Generated on {datetime.now().strftime('%B %d, %Y')}", 
                          ParagraphStyle('date', parent=body_style, alignment=TA_CENTER, fontSize=9, textColor=colors.gray)))
    story.append(Spacer(1, 0.3*inch))
    
    # ==================== PAGE SPEED INSIGHTS ====================
    if pagespeed_analysis:
        story.append(Paragraph("1. Page Speed Insights", heading_style))
        story.append(Paragraph(f"URL: {pagespeed_analysis.url}", body_style))
        story.append(Spacer(1, 0.15*inch))
        
        # Extract core web vitals from metrics
        metrics = pagespeed_analysis.metrics or {}
        full_response = pagespeed_analysis.full_response or {}

        lcp_value, lcp_numeric = _extract_field_metric(
            full_response,
            'LARGEST_CONTENTFUL_PAINT_MS',
            value_formatter=lambda v: f"{v / 1000:.1f} s",
            numeric_divisor=1000,
        )
        inp_value, inp_numeric = _extract_field_metric(
            full_response,
            'INTERACTION_TO_NEXT_PAINT',
            value_formatter=lambda v: f"{v} ms",
            numeric_divisor=1,
        )
        cls_value, cls_numeric = _extract_field_metric(
            full_response,
            'CUMULATIVE_LAYOUT_SHIFT_SCORE',
            value_formatter=lambda v: f"{v / 100:.2f}",
            numeric_divisor=100,
        )

        if lcp_value == 'N/A' or lcp_numeric is None:
            lcp_value, lcp_numeric = _extract_metric(metrics, full_response, 'lcp', 'largest-contentful-paint', 1000)

        if inp_value == 'N/A' or inp_numeric is None:
            inp_value, inp_numeric = _extract_metric(metrics, full_response, 'inp', 'interaction-to-next-paint', 1)

        if cls_value == 'N/A' or cls_numeric is None:
            cls_value, cls_numeric = _extract_metric(metrics, full_response, 'cls', 'cumulative-layout-shift', 1)
        
        lcp_category, lcp_color = get_metric_category(lcp_numeric, 'LCP')
        inp_category, inp_color = get_metric_category(inp_numeric, 'INP')
        cls_category, cls_color = get_metric_category(cls_numeric, 'CLS')
        
        # Metrics table
        table_body_style = ParagraphStyle(
            'TableBody',
            parent=body_style,
            fontSize=8.5,
            leading=10,
            textColor=colors.HexColor('#2c3e50')
        )

        thresholds = {
            'lcp': Paragraph('Fast (0-2.5s) • Average (2.5-4s) • Poor (4s+)', table_body_style),
            'inp': Paragraph('Fast (0-200ms) • Average (200-500ms) • Poor (500ms+)', table_body_style),
            'cls': Paragraph('Fast (0-0.1) • Average (0.1-0.25) • Poor (0.25+)', table_body_style),
        }

        metrics_data = [
            ['Metric', 'Value', 'Status', 'Threshold'],
            ['Largest Contentful Paint\n(Page Loading Speed)', lcp_value, lcp_category, thresholds['lcp']],
            ['Interaction to Next Paint\n(Interactivity)', inp_value, inp_category, thresholds['inp']],
            ['Cumulative Layout Shift\n(Page Stability)', cls_value, cls_category, thresholds['cls']],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2.1*inch, 0.9*inch, 0.85*inch, 2.65*inch])
        metrics_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3498db')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        # Add status colors
        for i, (category, color) in enumerate([(lcp_category, lcp_color), 
                                                 (inp_category, inp_color), 
                                                 (cls_category, cls_color)], start=1):
            metrics_table.setStyle(TableStyle([
                ('TEXTCOLOR', (2, i), (2, i), color),
                ('FONTNAME', (2, i), (2, i), 'Helvetica-Bold'),
            ]))
        
        story.append(metrics_table)
        story.append(Spacer(1, 0.2*inch))
        
        # Recommendations
        story.append(Paragraph("Recommendations for Improvement:", subheading_style))
        
        recommendations = [
            "<b>• Optimize Images:</b> Compress and lazy-load images, use modern formats like WebP, and specify dimensions to reduce layout shifts.",
            "<b>• Minimize JavaScript:</b> Remove unused code, defer non-critical JS, and use code splitting to improve interactivity.",
            "<b>• Enable Caching:</b> Implement browser caching and CDN to serve static resources faster.",
            "<b>• Reduce Server Response Time:</b> Optimize backend performance, use faster hosting, and implement server-side caching.",
            "<b>• Eliminate Render-Blocking Resources:</b> Inline critical CSS, defer non-critical CSS and JavaScript to speed up page rendering.",
        ]
        
        for rec in recommendations:
            story.append(Paragraph(rec, body_style))
        
        story.append(Spacer(1, 0.2*inch))
    
    # ==================== CONTENT HEADERS ====================
    if headers_data:
        story.append(Paragraph("2. Extract Content Headers", heading_style))
        story.append(Paragraph(f"URL: {headers_data.get('url', 'N/A')}", body_style))
        story.append(Spacer(1, 0.15*inch))
        
        hierarchy = headers_data.get('hierarchy', {})
        h1_count = len(hierarchy.get('h1', []))
        h2_count = len(hierarchy.get('h2', []))
        h3_count = len(hierarchy.get('h3', []))
        total_headers = h1_count + h2_count + h3_count
        
        # Header statistics
        story.append(Paragraph(f"<b>Total Headers:</b> {total_headers}", body_style))
        story.append(Paragraph(f"<b>H1 Tags:</b> {h1_count}", body_style))
        story.append(Paragraph(f"<b>H2 Tags:</b> {h2_count}", body_style))
        story.append(Paragraph(f"<b>H3 Tags:</b> {h3_count}", body_style))
        story.append(Spacer(1, 0.15*inch))
        
        # Action Plan
        story.append(Paragraph("Action Plan:", subheading_style))
        
        action_items = [
            f"<b>• Use exactly one H1 tag per page</b> (Currently: {h1_count}) - The H1 should contain your primary keyword and describe the page topic.",
            "<b>• Maintain proper hierarchy:</b> H1 → H2 → H3 (don't skip levels) - This helps search engines understand content structure.",
            "<b>• Include keywords:</b> Use relevant keywords in your headings naturally - Balance SEO with readability.",
            "<b>• Keep headers descriptive:</b> Headers should clearly describe the content that follows - Avoid vague titles.",
            "<b>• Make them engaging:</b> Headers help users scan and understand your content quickly - Use action words when appropriate.",
        ]
        
        for item in action_items:
            story.append(Paragraph(item, body_style))
        
        story.append(Spacer(1, 0.2*inch))
    
    # ==================== IMAGE & ALT TEXT ====================
    if image_analysis:
        story.append(Paragraph("3. Website Image + Alt Text Finder", heading_style))
        story.append(Paragraph(f"URL: {image_analysis.url}", body_style))
        story.append(Spacer(1, 0.15*inch))
        
        # Statistics
        story.append(Paragraph(f"<b>Total Images:</b> {image_analysis.total_images}", body_style))
        story.append(Paragraph(f"<b>Images with Alt Text:</b> {image_analysis.images_with_alt}", body_style))
        story.append(Paragraph(f"<b>Missing Alt Text:</b> {image_analysis.images_without_alt}", body_style))
        story.append(Paragraph(f"<b>Alt Text Coverage:</b> {image_analysis.alt_text_percentage}%", body_style))
        story.append(Spacer(1, 0.15*inch))
        
        # Action Plan
        story.append(Paragraph("Action Plan:", subheading_style))
        
        alt_actions = [
            "<b>• Add descriptive alt text to all images:</b> Write concise descriptions that explain what's in the image (aim for 125 characters or less).",
            "<b>• Include relevant keywords naturally:</b> When appropriate, incorporate your target keywords, but prioritize accurate descriptions.",
            "<b>• Skip alt text for decorative images:</b> Use empty alt=\"\" for purely decorative images that don't add informational value.",
            f"<b>• Prioritize missing alt texts:</b> Focus on the {image_analysis.images_without_alt} images without alt text first, especially for product images and infographics.",
            "<b>• Review existing alt text quality:</b> Ensure current alt texts are descriptive and meaningful, not just generic filenames.",
        ]
        
        for action in alt_actions:
            story.append(Paragraph(action, body_style))
        
        story.append(Spacer(1, 0.2*inch))
    
    # ==================== KEYWORDS FINDER ====================
    if keyword_analysis:
        story.append(Paragraph("4. Keywords Finder", heading_style))
        story.append(Paragraph(f"URL: {keyword_analysis.url}", body_style))
        story.append(Spacer(1, 0.15*inch))
        
        # Statistics
        story.append(Paragraph(f"<b>Total Keywords:</b> {keyword_analysis.total_keywords}", body_style))
        story.append(Paragraph(f"<b>Top 3 Positions:</b> {keyword_analysis.top_3_positions}", body_style))
        story.append(Paragraph(f"<b>Top 10 Positions:</b> {keyword_analysis.top_10_positions}", body_style))
        story.append(Paragraph(f"<b>Top 20 Positions:</b> {keyword_analysis.top_20_positions}", body_style))
        story.append(Paragraph(f"<b>Average Position:</b> {keyword_analysis.avg_position:.1f}", body_style))
        story.append(Spacer(1, 0.15*inch))
        
        # Action Plan
        story.append(Paragraph("Action Plan:", subheading_style))
        
        keyword_actions = [
            f"<b>• Optimize for top-performing keywords:</b> Your {keyword_analysis.top_3_positions} keywords in the top 3 positions are strong - maintain and expand related content.",
            f"<b>• Target position 4-10 keywords:</b> Focus on the {keyword_analysis.top_10_positions - keyword_analysis.top_3_positions} keywords ranking 4-10 - these are closest to page 1 top positions.",
            "<b>• Create comprehensive content:</b> Develop in-depth, high-quality content around your target keywords with proper internal linking.",
            "<b>• Build quality backlinks:</b> Acquire authoritative backlinks to pages targeting your priority keywords to boost rankings.",
            "<b>• Monitor and refine:</b> Track keyword performance weekly, adjust content strategy based on ranking changes, and target long-tail variations.",
        ]
        
        for action in keyword_actions:
            story.append(Paragraph(action, body_style))
        
        story.append(Spacer(1, 0.2*inch))
    
    # Footer
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph(
        f"<i>This report was generated by SEO Optima for {user.email}</i>",
        ParagraphStyle('footer', parent=body_style, fontSize=8, 
                      textColor=colors.gray, alignment=TA_CENTER)
    ))
    
    # Build PDF
    doc.build(story)
    
    # Save to file
    pdf_content = ContentFile(buffer.getvalue())
    filename = f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    
    buffer.close()
    
    return ContentFile(pdf_content.read(), name=filename)

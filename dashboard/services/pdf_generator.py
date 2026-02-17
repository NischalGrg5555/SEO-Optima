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
    """Categorize metric values into Fast/Average/Slow or Good/Average/Poor"""
    if metric_type == 'LCP':  # Largest Contentful Paint (seconds)
        if value <= 2.5:
            return ('Fast', colors.green)
        elif value <= 4.0:
            return ('Average', colors.orange)
        else:
            return ('Slow', colors.red)
    
    elif metric_type == 'INP':  # Interaction to Next Paint (milliseconds)
        if value <= 200:
            return ('Fast', colors.green)
        elif value <= 500:
            return ('Average', colors.orange)
        else:
            return ('Slow', colors.red)
    
    elif metric_type == 'CLS':  # Cumulative Layout Shift (score)
        if value <= 0.1:
            return ('Good', colors.green)
        elif value <= 0.25:
            return ('Average', colors.orange)
        else:
            return ('Poor', colors.red)
    
    return ('Unknown', colors.gray)


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
        metrics = pagespeed_analysis.metrics
        lcp_value = metrics.get('largest_contentful_paint', {}).get('displayValue', 'N/A')
        inp_value = metrics.get('interaction_to_next_paint', {}).get('displayValue', 'N/A')
        cls_value = metrics.get('cumulative_layout_shift', {}).get('displayValue', 'N/A')
        
        # Try to get numeric values for categorization
        lcp_numeric = metrics.get('largest_contentful_paint', {}).get('numericValue', 0) / 1000  # Convert to seconds
        inp_numeric = metrics.get('interaction_to_next_paint', {}).get('numericValue', 0)
        cls_numeric = metrics.get('cumulative_layout_shift', {}).get('numericValue', 0)
        
        lcp_category, lcp_color = get_metric_category(lcp_numeric, 'LCP')
        inp_category, inp_color = get_metric_category(inp_numeric, 'INP')
        cls_category, cls_color = get_metric_category(cls_numeric, 'CLS')
        
        # Metrics table
        metrics_data = [
            ['Metric', 'Value', 'Status', 'Threshold'],
            ['Largest Contentful Paint\n(Page Loading Speed)', lcp_value, lcp_category, 
             'Fast (0-2.5s) • Average (2.5-4s) • Slow (4s+)'],
            ['Interaction to Next Paint\n(Interactivity)', inp_value, inp_category,
             'Fast (0-200ms) • Average (200-500ms) • Slow (500ms+)'],
            ['Cumulative Layout Shift\n(Page Stability)', cls_value, cls_category,
             'Good (0-0.1) • Average (0.1-0.25) • Poor (0.25+)'],
        ]
        
        metrics_table = Table(metrics_data, colWidths=[2*inch, 1*inch, 0.8*inch, 2.7*inch])
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

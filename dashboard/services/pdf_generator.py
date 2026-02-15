"""
PDF Report Generator using ReportLab

Generates professional PDF reports from analysis data.
Supports both Free and Premium report formats.
"""

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from io import BytesIO
from datetime import datetime


class PDFReportGenerator:
    """Generate PDF reports from analysis data using ReportLab"""
    
    def __init__(self, report_instance):
        self.report = report_instance
        self.is_premium = report_instance.report_type == 'paid'
        self.include_charts = report_instance.include_charts
        self.include_recommendations = report_instance.include_recommendations
        
        # Get sample styles and create custom ones
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
        
        self.story = []
        self.page_width = letter[0]
        self.page_height = letter[1]
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=12,
            alignment=1,  # Center
        )
        
        self.heading_style = ParagraphStyle(
            'CustomHeading',
            parent=self.styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=10,
            spaceBefore=10,
        )
        
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=11,
            leading=14,
        )
    
    def generate_pdf(self):
        """Generate PDF and return bytes"""
        pdf_buffer = BytesIO()
        doc = SimpleDocTemplate(
            pdf_buffer,
            pagesize=letter,
            rightMargin=0.75*inch,
            leftMargin=0.75*inch,
            topMargin=0.75*inch,
            bottomMargin=0.75*inch,
        )
        
        # Build the story
        self._add_title_page()
        self._add_page_break()
        
        if self.report.pagespeed_analysis:
            self._add_pagespeed_section()
            self._add_page_break()
        
        if self.report.keyword_analysis:
            self._add_keywords_section()
            self._add_page_break()
        
        if self.report.image_analysis:
            self._add_images_section()
            self._add_page_break()
        
        if self.report.headers_data:
            self._add_headers_section()
            self._add_page_break()
        
        self._add_summary_page()
        
        # Build PDF
        doc.build(self.story)
        pdf_buffer.seek(0)
        return pdf_buffer.getvalue()
    
    def _add_title_page(self):
        """Add title page to report"""
        # Title
        title = Paragraph(self.report.title, self.title_style)
        self.story.append(title)
        self.story.append(Spacer(1, 12))
        
        # Report type badge
        report_type_text = f"<b>{self.report.get_report_type_display()}</b>"
        self.story.append(Paragraph(report_type_text, self.styles['Normal']))
        self.story.append(Spacer(1, 20))
        
        # Description
        if self.report.description:
            desc = Paragraph(f"<i>{self.report.description}</i>", self.styles['Normal'])
            self.story.append(desc)
            self.story.append(Spacer(1, 12))
        
        # Metadata
        self.story.append(Spacer(1, 30))
        metadata_text = f"""
        <b>Report Generated:</b> {datetime.now().strftime('%B %d, %Y at %I:%M %p')}<br/>
        <b>Report Type:</b> {self.report.get_report_type_display()}<br/>
        <b>For User:</b> {self.report.user.get_full_name() or self.report.user.username}
        """
        self.story.append(Paragraph(metadata_text, self.styles['Normal']))
        self.story.append(Spacer(1, 30))
        
        # Footer text
        footer_text = "Powered by SEO Optima - Professional Website Analysis Tool"
        self.story.append(Paragraph(footer_text, self.styles['Normal']))
    
    def _add_page_break(self):
        """Add a page break"""
        self.story.append(PageBreak())
    
    def _add_pagespeed_section(self):
        """Add PageSpeed Insights section"""
        ps = self.report.pagespeed_analysis
        
        # Title
        self.story.append(Paragraph("📊 Page Speed Performance", self.heading_style))
        self.story.append(Spacer(1, 6))
        
        # URL Info
        url_text = f"<b>Website:</b> {ps.url}<br/><b>Device:</b> {ps.get_strategy_display()}"
        self.story.append(Paragraph(url_text, self.styles['Normal']))
        self.story.append(Spacer(1, 12))
        
        # Scores table
        score_data = [
            ['Metric', 'Score', 'Status'],
            ['Performance', str(ps.performance_score), self._get_status(ps.performance_score)],
            ['Accessibility', str(ps.accessibility_score), self._get_status(ps.accessibility_score)],
            ['Best Practices', str(ps.best_practices_score), self._get_status(ps.best_practices_score)],
            ['SEO', str(ps.seo_score), self._get_status(ps.seo_score)],
        ]
        
        score_table = Table(score_data, colWidths=[2*inch, 1.5*inch, 2*inch])
        score_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        self.story.append(score_table)
        self.story.append(Spacer(1, 12))
        
        # Overall score
        overall = round((
            (ps.performance_score or 0) +
            (ps.accessibility_score or 0) +
            (ps.best_practices_score or 0) +
            (ps.seo_score or 0)
        ) / 4)
        
        overall_text = f"""
        <b>Overall Score: {overall}/100 ({ps.score_category})</b><br/>
        Your website's performance has been analyzed across four key metrics. 
        Focus on areas with lower scores to improve your online presence.
        """
        self.story.append(Paragraph(overall_text, self.styles['Normal']))
        
        # Recommendations
        if self.include_recommendations and ps.full_response:
            self.story.append(Spacer(1, 12))
            self.story.append(Paragraph("<b>Top Recommendations:</b>", self.styles['Normal']))
            self.story.append(Spacer(1, 6))
            
            opportunities = ps.full_response.get('lighthouseResult', {}).get('audits', {})
            rec_count = 0
            for key, audit in opportunities.items():
                if rec_count >= 3:
                    break
                if audit.get('score') is not None and audit.get('score') < 1.0:
                    title = audit.get('title', key)
                    score = int(audit.get('score', 0) * 100)
                    rec_text = f"• <b>{title}</b> (Score: {score}/100)"
                    self.story.append(Paragraph(rec_text, self.styles['Normal']))
                    rec_count += 1
    
    def _add_keywords_section(self):
        """Add Keywords Analysis section"""
        ka = self.report.keyword_analysis
        
        # Title
        self.story.append(Paragraph("🔍 Keywords Ranking Analysis", self.heading_style))
        self.story.append(Spacer(1, 6))
        
        # URL Info
        url_text = f"<b>Website:</b> {ka.url}"
        self.story.append(Paragraph(url_text, self.styles['Normal']))
        self.story.append(Spacer(1, 12))
        
        # Stats table
        stats_data = [
            ['Metric', 'Value'],
            ['Total Keywords', str(ka.total_keywords)],
            ['Top 10 Rankings', f"{ka.top_10_positions} keywords ({round(ka.top_10_positions/ka.total_keywords*100, 1) if ka.total_keywords > 0 else 0}%)"],
            ['Avg. Position', f"{ka.avg_position:.1f}"],
            ['Monthly Volume', str(ka.total_volume)],
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        self.story.append(stats_table)
        self.story.append(Spacer(1, 12))
        
        # Interpretation
        keywords_text = f"""
        <b>Analysis:</b> Your website ranks for {ka.total_keywords} keywords with {ka.top_10_positions} 
        in the top 10 positions. This represents significant search visibility. Continue optimizing 
        content to improve rankings for the lower-positioned keywords.
        """
        self.story.append(Paragraph(keywords_text, self.styles['Normal']))
    
    def _add_images_section(self):
        """Add Images Analysis section"""
        ia = self.report.image_analysis
        
        # Title
        self.story.append(Paragraph("🖼️ Image &amp; Alt Text Analysis", self.heading_style))
        self.story.append(Spacer(1, 6))
        
        # URL Info
        url_text = f"<b>Website:</b> {ia.url}"
        self.story.append(Paragraph(url_text, self.styles['Normal']))
        self.story.append(Spacer(1, 12))
        
        # Stats table
        stats_data = [
            ['Metric', 'Value'],
            ['Total Images', str(ia.total_images)],
            ['Alt Text Coverage', f"{ia.alt_text_percentage}%"],
            ['With Alt Text', str(ia.images_with_alt)],
            ['Without Alt Text', str(ia.images_without_alt)],
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        self.story.append(stats_table)
        self.story.append(Spacer(1, 12))
        
        # Importance
        importance_text = """
        <b>Why Alt Text Matters:</b><br/>
        • SEO: Helps search engines understand images<br/>
        • Accessibility: Assists visually impaired users<br/>
        • UX: Shows when images fail to load
        """
        self.story.append(Paragraph(importance_text, self.styles['Normal']))
    
    def _add_headers_section(self):
        """Add Headers Analysis section"""
        headers_data = self.report.headers_data or {}
        
        # Title
        self.story.append(Paragraph("📝 Content Headers Structure", self.heading_style))
        self.story.append(Spacer(1, 12))
        
        # Stats table
        stats_data = [
            ['Header Level', 'Count'],
            ['H1 (Main)', str(len(headers_data.get('h1', [])))],
            ['H2 (Sub)', str(len(headers_data.get('h2', [])))],
            ['H3 (Sub-Sub)', str(len(headers_data.get('h3', [])))],
        ]
        
        stats_table = Table(stats_data, colWidths=[3*inch, 2.5*inch])
        stats_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ]))
        self.story.append(stats_table)
        self.story.append(Spacer(1, 12))
        
        # Main headers
        h1_items = headers_data.get('h1', [])
        if h1_items:
            self.story.append(Paragraph("<b>Main Headers (H1):</b>", self.styles['Normal']))
            for h1 in h1_items[:3]:
                self.story.append(Paragraph(f"• {h1}", self.styles['Normal']))
            self.story.append(Spacer(1, 6))
    
    def _add_summary_page(self):
        """Add summary and action plan page"""
        self.story.append(Paragraph("📋 Executive Summary &amp; Next Steps", self.heading_style))
        self.story.append(Spacer(1, 12))
        
        summary_text = f"""
        <b>Report Overview:</b><br/>
        This comprehensive report analyzes your website across multiple SEO metrics.
        Report Type: {self.report.get_report_type_display()}<br/>
        Sections Analyzed: {len(self.report.report_sections)} areas<br/>
        Generated: {datetime.now().strftime('%B %d, %Y')}<br/>
        <br/>
        <b>Recommended Next Steps:</b><br/>
        1. <b>Review Findings:</b> Examine each section of this report<br/>
        2. <b>Prioritize Issues:</b> Focus on high-impact improvements first<br/>
        3. <b>Take Action:</b> Implement recommended changes<br/>
        4. <b>Track Progress:</b> Generate new reports monthly to monitor improvements<br/>
        <br/>
        <b>Questions?</b><br/>
        For implementation support or professional SEO assistance, contact an SEO specialist
        who can help optimize your website for maximum search engine visibility and user experience.
        """
        self.story.append(Paragraph(summary_text, self.styles['Normal']))
    
    def _get_status(self, score):
        """Get status text for a score"""
        if score is None:
            return "N/A"
        if score >= 90:
            return "Excellent ✓"
        elif score >= 80:
            return "Good"
        elif score >= 60:
            return "Needs Work"
        else:
            return "Poor"


def create_pdf_report(report_instance):
    """
    Convenience function to create a PDF for a given report instance
    
    Args:
        report_instance: PDFReport model instance
    
    Returns:
        bytes: PDF file content
    """
    generator = PDFReportGenerator(report_instance)
    return generator.generate_pdf()

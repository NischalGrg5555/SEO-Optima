#!/usr/bin/env python3
# Script to add PDFReport model to models.py

with open('dashboard/models.py', 'r') as f:
    content = f.read()

pdf_report_model = """

class PDFReport(models.Model):
    \"\"\"Model to store generated PDF reports\"\"\"
    REPORT_TYPE_CHOICES = [
        ('free', 'Free Report'),
        ('paid', 'Premium Report'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pdf_reports')
    report_type = models.CharField(max_length=10, choices=REPORT_TYPE_CHOICES, default='free')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    
    # Related analyses (all optional)
    pagespeed_analysis = models.ForeignKey(PageSpeedAnalysis, on_delete=models.SET_NULL, null=True, blank=True, related_name='pdf_reports')
    keyword_analysis = models.ForeignKey(KeywordAnalysis, on_delete=models.SET_NULL, null=True, blank=True, related_name='pdf_reports')
    image_analysis = models.ForeignKey(ImageAltAnalysis, on_delete=models.SET_NULL, null=True, blank=True, related_name='pdf_reports')
    
    # Store header data as JSON (extracted headers)
    headers_data = models.JSONField(default=dict, blank=True)
    
    # PDF file storage
    pdf_file = models.FileField(upload_to='reports/%Y/%m/%d/')
    
    # Report generation info
    include_recommendations = models.BooleanField(default=True)
    include_charts = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['report_type']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_report_type_display()}) - {self.user.username}"
    
    @property
    def report_sections(self):
        \"\"\"Get list of active report sections based on available data\"\"\"
        sections = []
        if self.pagespeed_analysis:
            sections.append('page_speed')
        if self.keyword_analysis:
            sections.append('keywords')
        if self.image_analysis:
            sections.append('images')
        if self.headers_data:
            sections.append('headers')
        return sections
"""

with open('dashboard/models.py', 'w') as f:
    f.write(content + pdf_report_model)

print("PDFReport model added successfully!")

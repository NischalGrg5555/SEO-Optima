from django.db import models
from django.contrib.auth.models import User
import json

class PageSpeedAnalysis(models.Model):
    """Model to store PageSpeed Insights analysis results"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pagespeed_analyses')
    url = models.URLField(max_length=500)
    strategy = models.CharField(
        max_length=10,
        choices=[('mobile', 'Mobile'), ('desktop', 'Desktop')],
        default='mobile'
    )
    
    # Scores
    performance_score = models.IntegerField(null=True, blank=True)
    accessibility_score = models.IntegerField(null=True, blank=True)
    best_practices_score = models.IntegerField(null=True, blank=True)
    seo_score = models.IntegerField(null=True, blank=True)
    
    # Metrics (stored as JSON)
    metrics = models.JSONField(default=dict, blank=True)
    
    # Content headers extracted from the page
    content_headers = models.JSONField(default=list, blank=True)
    
    # Full response
    full_response = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Soft delete
    is_deleted = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['url']),
        ]
    
    def __str__(self):
        return f"{self.url} - {self.strategy}"
    
    @property
    def score_category(self):
        """Get category for overall score"""
        avg_score = (
            (self.performance_score or 0) +
            (self.accessibility_score or 0) +
            (self.best_practices_score or 0) +
            (self.seo_score or 0)
        ) / 4
        
        if avg_score >= 90:
            return 'Excellent'
        elif avg_score >= 80:
            return 'Good'
        elif avg_score >= 60:
            return 'Needs Work'
        else:
            return 'Poor'


class ImageAltAnalysis(models.Model):
    """Model to store image and alt text analysis results"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='image_alt_analyses')
    url = models.URLField(max_length=500)
    
    # Statistics
    total_images = models.IntegerField(default=0)
    images_with_alt = models.IntegerField(default=0)
    images_without_alt = models.IntegerField(default=0)
    
    # Image data (stored as JSON)
    # Format: [{'src': 'url', 'alt': 'text', 'status': 'OK/Missing'}]
    images_data = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['url']),
        ]
    
    def __str__(self):
        return f"{self.url} - {self.total_images} images"
    
    @property
    def alt_text_percentage(self):
        """Calculate percentage of images with alt text"""
        if self.total_images == 0:
            return 0
        return round((self.images_with_alt / self.total_images) * 100, 1)


class KeywordAnalysis(models.Model):
    """Model to store keyword ranking analysis results"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='keyword_analyses')
    url = models.URLField(max_length=500)
    
    # Statistics
    total_keywords = models.IntegerField(default=0)
    top_3_positions = models.IntegerField(default=0)
    top_10_positions = models.IntegerField(default=0)
    top_20_positions = models.IntegerField(default=0)
    total_volume = models.IntegerField(default=0)
    avg_position = models.FloatField(default=0)
    
    # Keyword data (stored as JSON)
    # Format: [{'keyword': 'text', 'volume': 100, 'position': 5, 'url': 'ranked_url'}]
    keywords_data = models.JSONField(default=list, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['url']),
        ]
    
    def __str__(self):
        return f"{self.url} - {self.total_keywords} keywords"


class GSCConnection(models.Model):
    """Model to store Google Search Console OAuth connections"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='gsc_connection')
    
    # OAuth credentials stored as JSON
    credentials = models.JSONField(default=dict, blank=True)
    
    # List of properties the user has access to
    properties = models.JSONField(default=list, blank=True)
    
    # Connection status
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    connected_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'GSC Connection'
        verbose_name_plural = 'GSC Connections'
    
    def __str__(self):
        return f"{self.user.email} - GSC Connection"



class PDFReport(models.Model):
    """Model to store generated PDF reports"""
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
        """Get list of active report sections based on available data"""
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

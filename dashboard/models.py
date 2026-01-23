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


from django.contrib import admin
from .models import PageSpeedAnalysis, ImageAltAnalysis, KeywordAnalysis, GSCConnection


@admin.register(PageSpeedAnalysis)
class PageSpeedAnalysisAdmin(admin.ModelAdmin):
    list_display = ('user', 'url', 'strategy', 'performance_score', 'seo_score', 'created_at')
    list_filter = ('strategy', 'created_at', 'performance_score')
    search_fields = ('url', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'full_response')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Website Information', {
            'fields': ('user', 'url', 'strategy')
        }),
        ('Scores', {
            'fields': ('performance_score', 'accessibility_score', 'best_practices_score', 'seo_score')
        }),
        ('Data', {
            'fields': ('metrics', 'full_response'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ImageAltAnalysis)
class ImageAltAnalysisAdmin(admin.ModelAdmin):
    list_display = ('user', 'url', 'total_images', 'images_with_alt', 'images_without_alt', 'alt_text_percentage', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('url', 'user__email')
    readonly_fields = ('created_at', 'updated_at', 'alt_text_percentage')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Website Information', {
            'fields': ('user', 'url')
        }),
        ('Statistics', {
            'fields': ('total_images', 'images_with_alt', 'images_without_alt', 'alt_text_percentage')
        }),
        ('Image Data', {
            'fields': ('images_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(KeywordAnalysis)
class KeywordAnalysisAdmin(admin.ModelAdmin):
    list_display = ('user', 'url', 'total_keywords', 'top_10_positions', 'total_volume', 'avg_position', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('url', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Website Information', {
            'fields': ('user', 'url')
        }),
        ('Statistics', {
            'fields': ('total_keywords', 'top_3_positions', 'top_10_positions', 'top_20_positions', 'total_volume', 'avg_position')
        }),
        ('Keyword Data', {
            'fields': ('keywords_data',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(GSCConnection)
class GSCConnectionAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_active', 'connected_at', 'updated_at')
    list_filter = ('is_active', 'connected_at')
    search_fields = ('user__email',)
    readonly_fields = ('connected_at', 'updated_at', 'properties')
    ordering = ('-connected_at',)
    
    fieldsets = (
        ('User', {
            'fields': ('user', 'is_active')
        }),
        ('Connection Data', {
            'fields': ('properties',)
        }),
        ('Credentials', {
            'fields': ('credentials',),
            'classes': ('collapse',),
            'description': 'OAuth credentials (sensitive data)'
        }),
        ('Timestamps', {
            'fields': ('connected_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

# Register your models here.

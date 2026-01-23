from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib import messages
from .services.pagespeed import fetch_pagespeed_data, get_score_color
from .services.header_extractor import extract_headers, get_header_hierarchy
from .models import PageSpeedAnalysis
from .forms import PageSpeedForm, PageSpeedFilterForm, HeaderExtractorForm


@login_required
def dashboard_home(request):
    """Dashboard home page - overview of all features"""
    # Get user's analyses statistics
    total_analyses = PageSpeedAnalysis.objects.filter(user=request.user).count()
    
    # Get recent analyses
    recent_analyses = PageSpeedAnalysis.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    # Calculate average scores
    analyses = PageSpeedAnalysis.objects.filter(user=request.user)
    avg_performance = 0
    avg_seo = 0
    
    if analyses.exists():
        perf_scores = [a.performance_score for a in analyses if a.performance_score]
        seo_scores = [a.seo_score for a in analyses if a.seo_score]
        
        if perf_scores:
            avg_performance = sum(perf_scores) / len(perf_scores)
        if seo_scores:
            avg_seo = sum(seo_scores) / len(seo_scores)
    
    # Placeholder counts for future features
    headers_analyzed = 0  # Will be implemented
    images_analyzed = 0   # Will be implemented
    keywords_tracked = 0  # Will be implemented
    
    context = {
        'total_analyses': total_analyses,
        'recent_analyses': recent_analyses,
        'avg_performance': round(avg_performance),
        'avg_seo': round(avg_seo),
        'headers_analyzed': headers_analyzed,
        'images_analyzed': images_analyzed,
        'keywords_tracked': keywords_tracked,
    }
    
    return render(request, 'dashboard/index.html', context)


@login_required
def page_speed_insights(request):
    """Main PageSpeed Insights analysis page"""
    form = PageSpeedForm(request.POST or None)
    analysis = None
    error = None
    is_loading = False
    
    if request.method == 'POST' and form.is_valid():
        url = form.cleaned_data['url']
        strategy = form.cleaned_data['strategy']
        is_loading = True
        
        try:
            # Fetch data from Google PageSpeed API
            api_data = fetch_pagespeed_data(url, strategy)
            
            # Extract content headers from the webpage
            content_headers = []
            try:
                content_headers = extract_headers(url)
            except Exception as e:
                # Don't fail the entire analysis if header extraction fails
                print(f"Warning: Could not extract headers: {str(e)}")
            
            # Save to database
            analysis = PageSpeedAnalysis.objects.create(
                user=request.user,
                url=url,
                strategy=strategy,
                performance_score=api_data['scores'].get('performance'),
                accessibility_score=api_data['scores'].get('accessibility'),
                best_practices_score=api_data['scores'].get('best_practices'),
                seo_score=api_data['scores'].get('seo'),
                metrics=api_data.get('metrics', {}),
                content_headers=content_headers,
                full_response=api_data.get('full_response', {}),
            )
            
            messages.success(request, f"Analysis completed for {url}")
            
        except Exception as e:
            error = str(e)
            messages.error(request, f"Error: {error}")
    
    # Get recent analyses for this user
    recent_analyses = PageSpeedAnalysis.objects.filter(
        user=request.user
    ).order_by('-created_at')[:5]
    
    context = {
        'form': form,
        'analysis': analysis,
        'error': error,
        'is_loading': is_loading,
        'recent_analyses': recent_analyses,
    }
    
    return render(request, 'dashboard/page_speed_insights.html', context)


@login_required
def analysis_detail(request, pk):
    """View detailed analysis results"""
    analysis = get_object_or_404(PageSpeedAnalysis, pk=pk, user=request.user)
    
    context = {
        'analysis': analysis,
        'get_score_color': get_score_color,
    }
    
    return render(request, 'dashboard/analysis_detail.html', context)


class AnalysisListView(ListView):
    """List all analyses for current user"""
    model = PageSpeedAnalysis
    template_name = 'dashboard/analysis_list.html'
    context_object_name = 'analyses'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = PageSpeedAnalysis.objects.filter(user=self.request.user)
        
        # Filter by strategy
        strategy = self.request.GET.get('strategy')
        if strategy:
            queryset = queryset.filter(strategy=strategy)
        
        # Sort
        sort_by = self.request.GET.get('sort_by', '-created_at')
        queryset = queryset.order_by(sort_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = PageSpeedFilterForm(self.request.GET or None)
        return context


@login_required
def delete_analysis(request, pk):
    """Delete an analysis"""
    analysis = get_object_or_404(PageSpeedAnalysis, pk=pk, user=request.user)
    
    if request.method == 'POST':
        url = analysis.url
        analysis.delete()
        messages.success(request, f"Analysis for {url} deleted successfully.")
        return redirect('dashboard:analysis_list')
    
    return render(request, 'dashboard/delete_analysis.html', {'analysis': analysis})


@login_required
def extract_headers_view(request):
    """Extract headers from a webpage"""
    form = HeaderExtractorForm(request.POST or None)
    headers = None
    hierarchy = None
    url = None
    error = None
    
    if request.method == 'POST' and form.is_valid():
        url = form.cleaned_data['url']
        
        try:
            # Extract headers from the URL
            headers = extract_headers(url)
            hierarchy = get_header_hierarchy(headers)
            messages.success(request, f"Successfully extracted {len(headers)} headers from {url}")
        except Exception as e:
            error = str(e)
            messages.error(request, f"Error extracting headers: {error}")
    
    context = {
        'form': form,
        'headers': headers,
        'hierarchy': hierarchy,
        'url': url,
        'error': error,
    }
    
    return render(request, 'dashboard/extract_headers.html', context)

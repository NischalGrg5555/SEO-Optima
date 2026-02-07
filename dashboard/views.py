from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.conf import settings
from .services.pagespeed import fetch_pagespeed_data, get_score_color, extract_field_data_from_response
from .services.header_extractor import extract_headers, get_header_hierarchy
from .services.image_extractor import extract_images, get_image_stats
from .services.keyword_extractor import generate_mock_keywords, get_keyword_stats, fetch_gsc_keywords
from .models import PageSpeedAnalysis, ImageAltAnalysis, KeywordAnalysis, GSCConnection
from .forms import PageSpeedForm, PageSpeedFilterForm, HeaderExtractorForm
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
import json


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
        
        try:
            # Fetch data from Google PageSpeed API
            api_data = fetch_pagespeed_data(url, strategy)
            
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
                full_response=api_data.get('full_response', {}),
            )
            
            # Attach field_data for template rendering
            analysis.field_data = api_data.get('field_data', {})
            
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
    
    # Extract field_data from stored full_response
    field_data = extract_field_data_from_response(analysis.full_response)
    
    context = {
        'analysis': analysis,
        'get_score_color': get_score_color,
        'field_data': field_data,
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

@login_required
def image_alt_finder(request):
    """Image and Alt Text Finder page"""
    from .forms import ImageAltFinderForm
    
    form = ImageAltFinderForm(request.POST or None)
    images = []
    stats = {}
    url = None
    error = None
    analysis = None
    
    if request.method == 'POST' and form.is_valid():
        url = form.cleaned_data['url']
        
        try:
            # Extract images from the URL
            images = extract_images(url)
            
            # Get statistics
            stats = get_image_stats(images)
            
            # Save to database
            analysis = ImageAltAnalysis.objects.create(
                user=request.user,
                url=url,
                total_images=stats['total_images'],
                images_with_alt=stats['images_with_alt'],
                images_without_alt=stats['images_without_alt'],
                images_data=images
            )
            
            messages.success(request, f'Successfully extracted {len(images)} images from {url}')
            
        except Exception as e:
            error = str(e)
            messages.error(request, f'Error extracting images: {error}')
    
    context = {
        'form': form,
        'images': images,
        'stats': stats,
        'url': url,
        'error': error,
        'analysis': analysis,
    }
    
    return render(request, 'dashboard/image_alt_finder.html', context)


@login_required
def image_alt_list(request):
    """List all image alt analyses for the current user"""
    analyses = ImageAltAnalysis.objects.filter(user=request.user)
    
    context = {
        'analyses': analyses,
    }
    
    return render(request, 'dashboard/image_alt_list.html', context)


@login_required
def image_alt_detail(request, pk):
    """View details of a specific image alt analysis"""
    analysis = get_object_or_404(ImageAltAnalysis, pk=pk, user=request.user)
    
    context = {
        'analysis': analysis,
    }
    
    return render(request, 'dashboard/image_alt_detail.html', context)

@login_required
def keywords_list(request):
    """List all keyword analyses for the current user"""
    analyses = KeywordAnalysis.objects.filter(user=request.user)
    
    context = {
        'analyses': analyses,
    }
    
    return render(request, 'dashboard/keywords_list.html', context)


@login_required
def keywords_detail(request, pk):
    """View details of a specific keyword analysis"""
    analysis = get_object_or_404(KeywordAnalysis, pk=pk, user=request.user)
    
    context = {
        'analysis': analysis,
    }
    
    return render(request, 'dashboard/keywords_detail.html', context)


@login_required
def delete_keyword_analysis(request, pk):
    """Delete a keyword analysis"""
    analysis = get_object_or_404(KeywordAnalysis, pk=pk, user=request.user)
    
    if request.method == 'POST':
        analysis.delete()
        messages.success(request, 'Keyword analysis deleted successfully!')
        return redirect('dashboard:keywords_list')
    
    context = {
        'analysis': analysis,
    }
    
    return render(request, 'dashboard/delete_keyword_analysis.html', context)

@login_required
def keywords_finder(request):
    """Keywords Finder page with GSC integration"""
    from .forms import KeywordsFinderForm
    
    form = KeywordsFinderForm(request.POST or None)
    keywords = []
    stats = {}
    url = None
    error = None
    analysis = None
    use_gsc = False
    
    # Check if user has GSC connected
    try:
        gsc_connection = GSCConnection.objects.get(user=request.user, is_active=True)
        use_gsc = True
    except GSCConnection.DoesNotExist:
        gsc_connection = None
    
    if request.method == 'POST' and form.is_valid():
        url = form.cleaned_data['url']
        use_real_data = request.POST.get('use_gsc', 'false') == 'true'
        
        try:
            # Try to fetch from GSC if connected and user wants real data
            if use_gsc and use_real_data and gsc_connection:
                try:
                    keywords = fetch_gsc_keywords(url, gsc_connection.credentials)
                    messages.success(request, f'Successfully fetched {len(keywords)} keywords from Google Search Console')
                except Exception as gsc_error:
                    # Fallback to mock data if GSC fails
                    keywords = generate_mock_keywords(url)
                    messages.warning(request, f'GSC Error: {str(gsc_error)}. Using demo data instead.')
            else:
                # Use mock data
                keywords = generate_mock_keywords(url)
                if not use_gsc:
                    messages.info(request, f'Using demo data. Connect Google Search Console for real keywords.')
                else:
                    messages.success(request, f'Generated {len(keywords)} demo keywords')
            
            # Get statistics
            stats = get_keyword_stats(keywords)
            
            # Save to database
            analysis = KeywordAnalysis.objects.create(
                user=request.user,
                url=url,
                total_keywords=stats['total_keywords'],
                top_3_positions=stats['top_3_positions'],
                top_10_positions=stats['top_10_positions'],
                top_20_positions=stats['top_20_positions'],
                total_volume=stats['total_volume'],
                avg_position=stats['avg_position'],
                keywords_data=keywords
            )
            
        except Exception as e:
            error = str(e)
            messages.error(request, f'Error finding keywords: {error}')
    
    context = {
        'form': form,
        'keywords': keywords,
        'stats': stats,
        'url': url,
        'error': error,
        'analysis': analysis,
        'gsc_connected': use_gsc,
        'gsc_connection': gsc_connection,
    }
    
    return render(request, 'dashboard/keywords_finder.html', context)


@login_required
def connect_gsc(request):
    """Initiate Google Search Console OAuth flow"""
    
    # Check if credentials are configured
    if not settings.GSC_CLIENT_ID or not settings.GSC_CLIENT_SECRET:
        messages.error(request, 'Google Search Console API is not configured. Please contact administrator.')
        return redirect('dashboard:keywords_finder')
    
    # Create flow instance
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GSC_CLIENT_ID,
                "client_secret": settings.GSC_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GSC_REDIRECT_URI]
            }
        },
        scopes=settings.GSC_SCOPES,
        redirect_uri=settings.GSC_REDIRECT_URI
    )
    
    # Generate authorization URL
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    # Store state in session
    request.session['gsc_oauth_state'] = state
    
    return redirect(authorization_url)


@login_required
def gsc_callback(request):
    """Handle Google Search Console OAuth callback"""
    
    # Get the authorization code
    code = request.GET.get('code')
    state = request.GET.get('state')
    
    # Verify state
    if state != request.session.get('gsc_oauth_state'):
        messages.error(request, 'Invalid OAuth state. Please try again.')
        return redirect('dashboard:keywords_finder')
    
    try:
        # Create flow instance with relaxed scope checking
        from oauthlib.oauth2.rfc6749.parameters import prepare_token_request
        import os
        
        # Disable strict scope checking
        os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
        
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": settings.GSC_CLIENT_ID,
                    "client_secret": settings.GSC_CLIENT_SECRET,
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "redirect_uris": [settings.GSC_REDIRECT_URI]
                }
            },
            scopes=settings.GSC_SCOPES,
            redirect_uri=settings.GSC_REDIRECT_URI,
            state=state
        )
        
        # Exchange code for credentials
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get user's Search Console properties
        service = build('searchconsole', 'v1', credentials=credentials)
        sites_list = service.sites().list().execute()
        properties = [site['siteUrl'] for site in sites_list.get('siteEntry', [])]
        
        # Store credentials in database
        credentials_dict = {
            'token': credentials.token,
            'refresh_token': credentials.refresh_token,
            'token_uri': credentials.token_uri,
            'client_id': credentials.client_id,
            'client_secret': credentials.client_secret,
            'scopes': list(credentials.scopes)  # Convert to list for JSON
        }
        
        # Create or update GSC connection
        gsc_connection, created = GSCConnection.objects.update_or_create(
            user=request.user,
            defaults={
                'credentials': credentials_dict,
                'properties': properties,
                'is_active': True
            }
        )
        
        if created:
            messages.success(request, f'Successfully connected Google Search Console! Found {len(properties)} properties.')
        else:
            messages.success(request, f'Google Search Console connection updated! Found {len(properties)} properties.')
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"GSC Connection Error: {error_details}")  # Log to console
        messages.error(request, f'Error connecting to Google Search Console: {str(e)}')
    
    return redirect('dashboard:keywords_finder')


@login_required
def disconnect_gsc(request):
    """Disconnect Google Search Console"""
    try:
        gsc_connection = GSCConnection.objects.get(user=request.user)
        gsc_connection.delete()
        messages.success(request, 'Successfully disconnected Google Search Console.')
    except GSCConnection.DoesNotExist:
        messages.info(request, 'No active Google Search Console connection found.')
    
    return redirect('dashboard:keywords_finder')
@login_required
def delete_image_alt_analysis(request, pk):
    """Delete an image alt analysis"""
    analysis = get_object_or_404(ImageAltAnalysis, pk=pk, user=request.user)
    
    if request.method == 'POST':
        analysis.delete()
        messages.success(request, 'Analysis deleted successfully!')
        return redirect('dashboard:image_alt_list')
    
    context = {
        'analysis': analysis,
    }
    
    return render(request, 'dashboard/delete_image_alt_analysis.html', context)
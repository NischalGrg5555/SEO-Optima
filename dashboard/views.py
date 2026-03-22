from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView
from django.contrib import messages
from django.conf import settings
import importlib
from .services.pagespeed import fetch_pagespeed_data, get_score_color, extract_field_data_from_response
from .services.header_extractor import extract_headers, get_header_hierarchy
from .services.image_extractor import extract_images, get_image_stats
from .services.keyword_extractor import get_keyword_stats, fetch_gsc_keywords, GSCAuthError
from .models import PageSpeedAnalysis, ImageAltAnalysis, KeywordAnalysis, GSCConnection, HeaderAnalysis
from .forms import PageSpeedForm, PageSpeedFilterForm, HeaderExtractorForm
import json
from urllib.parse import urlparse
from collections import defaultdict


def _load_gsc_oauth_clients():
    try:
        google_auth_flow = importlib.import_module('google_auth_oauthlib.flow')
        googleapiclient_discovery = importlib.import_module('googleapiclient.discovery')
    except ImportError as exc:
        raise RuntimeError(
            'Google Search Console dependencies are not installed. '
            'Install packages from requirements.txt to use this feature.'
        ) from exc

    return google_auth_flow.Flow, googleapiclient_discovery.build


def _group_properties_by_domain(properties_list):
    """
    Group GSC properties by domain for better UI display
    
    Example input:
    ["sc-domain:homeschool.asia", "https://homeschool.asia/", "https://www.ciepastpapers.com/", "sc-domain:ciepastpapers.com"]
    
    Example output:
    [
        {
            'domain': 'homeschool.asia',
            'primary_display': 'HOMESCHOOL.ASIA',
            'properties': [
                {'type': 'domain', 'url': 'sc-domain:homeschool.asia', 'display': 'homeschool.asia'},
                {'type': 'url', 'url': 'https://homeschool.asia/', 'display': 'https://homeschool.asia/'}
            ]
        },
        {
            'domain': 'ciepastpapers.com',
            'primary_display': 'CIEPASTPAPERS.COM',
            'properties': [
                {'type': 'domain', 'url': 'sc-domain:ciepastpapers.com', 'display': 'ciepastpapers.com'},
                {'type': 'url', 'url': 'https://www.ciepastpapers.com/', 'display': 'https://www.ciepastpapers.com/'}
            ]
        }
    ]
    """
    grouped = defaultdict(list)
    
    for prop in properties_list:
        # Extract domain and determine type
        if prop.startswith('sc-domain:'):
            domain = prop.replace('sc-domain:', '').lower()
            prop_type = 'domain'
            display = domain
        elif prop.startswith('http'):
            try:
                parsed = urlparse(prop.lower())
                domain = parsed.netloc.replace('www.', '')
                prop_type = 'url'
                display = prop.rstrip('/').lower()
            except:
                continue
        else:
            continue
        
        grouped[domain].append({
            'type': prop_type,
            'url': prop,
            'display': display
        })
    
    # Convert to list of dicts with proper formatting
    result = []
    for domain in sorted(grouped.keys()):
        props = grouped[domain]
        # Sort so domain properties come first
        props.sort(key=lambda x: (x['type'] != 'domain', x['display']))
        
        result.append({
            'domain': domain,
            'primary_display': domain.upper(),
            'properties': props
        })
    
    return result


def _property_to_display_url(property_value):
    """Convert GSC property value to a clickable display URL for UI/storage."""
    if property_value and property_value.startswith('sc-domain:'):
        return f"https://{property_value.replace('sc-domain:', '').strip('/')}"
    return property_value


def _compute_header_stats(headers_data):
    """Compute header counts and grouped text from stored header JSON."""
    counts = {
        'H1': 0,
        'H2': 0,
        'H3': 0,
        'H4': 0,
        'H5': 0,
        'H6': 0,
    }
    grouped = {
        'h1': [],
        'h2': [],
        'h3': [],
        'h4': [],
        'h5': [],
        'h6': [],
    }

    if not isinstance(headers_data, list):
        return 0, counts, grouped

    for header in headers_data:
        if not isinstance(header, dict):
            continue

        level = str(header.get('level') or header.get('tag') or '').upper()
        text = str(header.get('text') or '').strip()

        if level in counts and text:
            counts[level] += 1
            grouped[level.lower()].append(text)

    total_headers = sum(counts.values())
    return total_headers, counts, grouped


def _sync_header_analysis_counts(analysis):
    """Backfill and correct persisted header counters from headers_data."""
    total_headers, counts, _ = _compute_header_stats(analysis.headers_data)

    if (
        analysis.total_headers != total_headers
        or analysis.h1_count != counts['H1']
        or analysis.h2_count != counts['H2']
        or analysis.h3_count != counts['H3']
    ):
        analysis.total_headers = total_headers
        analysis.h1_count = counts['H1']
        analysis.h2_count = counts['H2']
        analysis.h3_count = counts['H3']
        analysis.save()


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
            
            # Extract headers from the URL
            try:
                from .services.header_extractor import extract_headers
                content_headers = extract_headers(url)
            except Exception:
                content_headers = []
            
            # Save to database
            analysis = PageSpeedAnalysis.objects.create(
                user=request.user,
                url=url,
                strategy=strategy,
                metrics=api_data.get('metrics', {}),
                full_response=api_data.get('full_response', {}),
                content_headers=content_headers,
            )
            
            # Attach field_data for template rendering
            analysis.field_data = api_data.get('field_data', {})
            
            messages.success(request, f"Analysis completed for {url}")
            
        except Exception as e:
            error = str(e)
            messages.error(request, f"Error: {error}")
    
    # Get all previous analyses for this user (excluding deleted)
    recent_analyses = PageSpeedAnalysis.objects.filter(
        user=request.user,
        is_deleted=False
    ).order_by('-created_at')[:10]
    
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
        queryset = PageSpeedAnalysis.objects.filter(
            user=self.request.user,
            is_deleted=False
        )
        
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
    """Soft delete an analysis"""
    analysis = get_object_or_404(PageSpeedAnalysis, pk=pk, user=request.user)
    
    if request.method == 'POST':
        url = analysis.url
        analysis.is_deleted = True
        analysis.save()
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
    analysis = None
    
    # Check if returning from detail page with analysis_id
    analysis_id = request.GET.get('analysis_id')
    if analysis_id and request.method != 'POST':
        try:
            analysis = HeaderAnalysis.objects.get(pk=analysis_id, user=request.user)
            url = analysis.url
            headers = analysis.headers_data
            hierarchy = get_header_hierarchy(headers)
        except HeaderAnalysis.DoesNotExist:
            pass
    
    if request.method == 'POST' and form.is_valid():
        url = form.cleaned_data['url']
        
        try:
            # Extract headers from the URL
            headers = extract_headers(url)
            hierarchy = get_header_hierarchy(headers)
            
            # Calculate statistics
            h1_count = hierarchy.get('H1', 0)
            h2_count = hierarchy.get('H2', 0)
            h3_count = hierarchy.get('H3', 0)
            total_headers = sum(hierarchy.values())
            
            # Save to database
            analysis = HeaderAnalysis.objects.create(
                user=request.user,
                url=url,
                total_headers=total_headers,
                h1_count=h1_count,
                h2_count=h2_count,
                h3_count=h3_count,
                headers_data=headers
            )
            
            messages.success(request, f"Successfully extracted {len(headers)} headers from {url}")
        except Exception as e:
            error = str(e)
            messages.error(request, f"Error extracting headers: {error}")
    
    # Get all previous analyses for this user
    analyses = list(HeaderAnalysis.objects.filter(user=request.user).order_by('-created_at')[:10])
    for saved_analysis in analyses:
        _sync_header_analysis_counts(saved_analysis)
    
    context = {
        'form': form,
        'headers': headers,
        'hierarchy': hierarchy,
        'url': url,
        'error': error,
        'analysis': analysis,
        'analyses': analyses,
    }
    
    return render(request, 'dashboard/extract_headers.html', context)


@login_required
def header_analysis_list(request):
    """Legacy route kept for bookmarks. Redirect to extract headers dashboard."""
    return redirect('dashboard:extract_headers')


@login_required  
def header_analysis_detail(request, pk):
    """View details of a specific header analysis"""
    analysis = get_object_or_404(HeaderAnalysis, pk=pk, user=request.user)

    # Ensure legacy rows with bad counters are corrected when opened.
    _sync_header_analysis_counts(analysis)

    # Build grouped header text so the template can render header structure lists.
    _, _, grouped_headers = _compute_header_stats(analysis.headers_data)
    
    context = {
        'analysis': analysis,
        'hierarchy': grouped_headers,
    }
    
    return render(request, 'dashboard/header_analysis_detail.html', context)


@login_required
def delete_header_analysis(request, pk):
    """Delete a header analysis"""
    analysis = get_object_or_404(HeaderAnalysis, pk=pk, user=request.user)
    
    if request.method == 'POST':
        analysis.delete()
        messages.success(request, 'Header analysis deleted successfully!')
        return redirect('dashboard:extract_headers')
    
    context = {
        'analysis': analysis,
    }
    
    return render(request, 'dashboard/delete_header_analysis.html', context)


@login_required
def bulk_delete_header_analyses(request):
    """Delete multiple selected header analyses from extract headers page."""
    redirect_name = 'dashboard:extract_headers'

    if request.method != 'POST':
        return redirect(redirect_name)

    selected_ids = request.POST.getlist('analysis_ids')
    if not selected_ids:
        messages.warning(request, 'Please select at least one analysis to delete.')
        return redirect(redirect_name)

    queryset = HeaderAnalysis.objects.filter(user=request.user, pk__in=selected_ids)
    deleted_count = queryset.count()

    if deleted_count == 0:
        messages.warning(request, 'No matching analyses were found to delete.')
    else:
        queryset.delete()
        messages.success(request, f'{deleted_count} selected analyses deleted successfully.')

    return redirect(redirect_name)


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

    selected_property_post = request.POST.get('selected_property', '').strip() if request.method == 'POST' else ''
    form = KeywordsFinderForm(None if selected_property_post else (request.POST or None))
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

    # Get recent keyword analyses for current user
    analyses = KeywordAnalysis.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    if request.method == 'POST' and form.is_valid():
        url = form.cleaned_data['url']
        
        try:
            # If GSC is connected, ONLY fetch real data - NO FALLBACK to mock
            if use_gsc and gsc_connection:
                try:
                    # Pass the properties list to help with matching
                    keywords = fetch_gsc_keywords(
                        url, 
                        gsc_connection.credentials,
                        properties_list=gsc_connection.properties
                    )
                    if not keywords:
                        error = "No keyword data found for this property in Google Search Console. This might mean no search traffic data is available yet."
                        messages.error(request, error)
                    else:
                        messages.success(request, f'Successfully fetched {len(keywords)} keywords from Google Search Console')
                except Exception as gsc_error:
                    # Expired/revoked tokens should force reconnect instead of noisy property errors.
                    if isinstance(gsc_error, GSCAuthError):
                        gsc_connection.is_active = False
                        gsc_connection.save(update_fields=['is_active', 'updated_at'])
                        use_gsc = False
                        gsc_connection = None
                        error = str(gsc_error)
                    else:
                        # Show error but DON'T fall back to mock data
                        error = f"Error fetching from Google Search Console: {str(gsc_error)}"
                    messages.error(request, error)
            else:
                # GSC not connected - don't allow submission
                error = "Google Search Console is not connected. Please connect your GSC account first."
                messages.error(request, error)
            
            if keywords:
                # Get statistics
                stats = get_keyword_stats(keywords)
                
                # Save to database - ONLY REAL GSC DATA
                analysis = KeywordAnalysis.objects.create(
                    user=request.user,
                    url=_property_to_display_url(url),
                    total_keywords=stats['total_keywords'],
                    top_3_positions=stats['top_3_positions'],
                    top_10_positions=stats['top_10_positions'],
                    top_20_positions=stats['top_20_positions'],
                    total_volume=stats['total_volume'],
                    avg_position=stats['avg_position'],
                    keywords_data=keywords
                )
                url = _property_to_display_url(url)
            
        except Exception as e:
            error = str(e)
            messages.error(request, f'Error finding keywords: {error}')
    elif request.method == 'POST':
        selected_property = request.POST.get('selected_property', '').strip()
        if selected_property:
            if not use_gsc or not gsc_connection:
                error = "Google Search Console is not connected. Please connect your GSC account first."
                messages.error(request, error)
            elif selected_property not in (gsc_connection.properties or []):
                error = "Selected property is not available in your connected Google Search Console account."
                messages.error(request, error)
            else:
                try:
                    url = selected_property
                    keywords = fetch_gsc_keywords(
                        selected_property,
                        gsc_connection.credentials,
                        properties_list=gsc_connection.properties
                    )
                    if not keywords:
                        error = "No keyword data found for this property in Google Search Console. This might mean no search traffic data is available yet."
                        messages.error(request, error)
                    else:
                        messages.success(request, f'Successfully fetched {len(keywords)} keywords from Google Search Console')

                    if keywords:
                        stats = get_keyword_stats(keywords)
                        display_url = _property_to_display_url(selected_property)
                        analysis = KeywordAnalysis.objects.create(
                            user=request.user,
                            url=display_url,
                            total_keywords=stats['total_keywords'],
                            top_3_positions=stats['top_3_positions'],
                            top_10_positions=stats['top_10_positions'],
                            top_20_positions=stats['top_20_positions'],
                            total_volume=stats['total_volume'],
                            avg_position=stats['avg_position'],
                            keywords_data=keywords
                        )
                        url = display_url
                except Exception as gsc_error:
                    if isinstance(gsc_error, GSCAuthError):
                        gsc_connection.is_active = False
                        gsc_connection.save(update_fields=['is_active', 'updated_at'])
                        use_gsc = False
                        gsc_connection = None
                        error = str(gsc_error)
                    else:
                        error = f"Error fetching from Google Search Console: {str(gsc_error)}"
                    messages.error(request, error)
    
    context = {
        'form': form,
        'keywords': keywords,
        'stats': stats,
        'url': url,
        'error': error,
        'analysis': analysis,
        'analyses': analyses,
        'gsc_connected': use_gsc,
        'gsc_connection': gsc_connection,
        'grouped_properties': _group_properties_by_domain(gsc_connection.properties) if gsc_connection else [],
    }
    
    return render(request, 'dashboard/keywords_finder.html', context)


@login_required
def connect_gsc(request):
    """Initiate Google Search Console OAuth flow"""
    
    # Check if credentials are configured
    if not settings.GSC_CLIENT_ID or not settings.GSC_CLIENT_SECRET:
        messages.error(request, 'Google Search Console API is not configured. Please contact administrator.')
        return redirect('dashboard:keywords_finder')

    try:
        Flow, _ = _load_gsc_oauth_clients()
    except RuntimeError as exc:
        messages.error(request, str(exc))
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
        Flow, build = _load_gsc_oauth_clients()

        # Create flow instance with relaxed scope checking
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
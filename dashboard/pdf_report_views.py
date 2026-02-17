from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import PDFReport, PageSpeedAnalysis, KeywordAnalysis, ImageAltAnalysis
from .services.pdf_generator import generate_basic_report


@login_required
def pdf_reports_list(request):
    """List all PDF reports for the current user"""
    reports = PDFReport.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'reports': reports,
    }
    
    return render(request, 'dashboard/pdf_reports_list.html', context)


@login_required
def generate_pdf_report(request):
    """Generate a new PDF report"""
    if request.method == 'POST':
        report_type = request.POST.get('report_type', 'basic')
        
        # For now, only basic reports are allowed
        if report_type != 'basic':
            return redirect('dashboard:generate_pdf_report')
        
        title = request.POST.get('title', 'SEO Analysis Report')
        
        # Get selected analyses
        pagespeed_id = request.POST.get('pagespeed_analysis_id')
        keyword_id = request.POST.get('keyword_analysis_id')
        image_id = request.POST.get('image_analysis_id')
        header_analysis_id = request.POST.get('header_analysis_id', '').strip()
        
        # Validate at least one data source is selected
        if not any([pagespeed_id, keyword_id, image_id, header_analysis_id]):
            messages.error(request, 'Please select at least one data source for your report.')
            return redirect('dashboard:generate_pdf_report')
        
        try:
            # Get analyses objects
            pagespeed_analysis = None
            keyword_analysis = None
            image_analysis = None
            headers_data = None
            
            if pagespeed_id:
                try:
                    pagespeed_analysis = PageSpeedAnalysis.objects.get(id=pagespeed_id, user=request.user)
                except PageSpeedAnalysis.DoesNotExist:
                    messages.warning(request, 'Selected PageSpeed analysis not found.')
            
            if keyword_id:
                try:
                    keyword_analysis = KeywordAnalysis.objects.get(id=keyword_id, user=request.user)
                except KeywordAnalysis.DoesNotExist:
                    messages.warning(request, 'Selected Keyword analysis not found.')
            
            if image_id:
                try:
                    image_analysis = ImageAltAnalysis.objects.get(id=image_id, user=request.user)
                except ImageAltAnalysis.DoesNotExist:
                    messages.warning(request, 'Selected Image analysis not found.')
            
            if header_analysis_id:
                # Extract headers from selected PageSpeed analysis
                try:
                    header_source = PageSpeedAnalysis.objects.get(id=header_analysis_id, user=request.user)
                    if header_source.content_headers:
                        from .services.header_extractor import get_header_hierarchy
                        headers_data = {
                            'url': header_source.url,
                            'headers': header_source.content_headers,
                            'hierarchy': get_header_hierarchy(header_source.content_headers)
                        }
                    else:
                        messages.warning(request, 'Selected analysis has no header data.')
                except PageSpeedAnalysis.DoesNotExist:
                    messages.warning(request, 'Selected header analysis not found.')
            
            # Generate the PDF
            pdf_file = generate_basic_report(
                user=request.user,
                title=title,
                pagespeed_analysis=pagespeed_analysis,
                keyword_analysis=keyword_analysis,
                image_analysis=image_analysis,
                headers_data=headers_data
            )
            
            # Create report record
            report = PDFReport.objects.create(
                user=request.user,
                report_type='free',
                title=title,
                pagespeed_analysis=pagespeed_analysis,
                keyword_analysis=keyword_analysis,
                image_analysis=image_analysis,
                headers_data=headers_data or {},
                pdf_file=pdf_file
            )
            
            # Return PDF as download instead of redirecting
            from django.http import FileResponse
            import os
            
            # Open the saved file and return it
            response = FileResponse(
                report.pdf_file.open('rb'),
                as_attachment=True,
                filename=f'{title.replace(" ", "_")}.pdf'
            )
            return response
            
        except Exception as e:
            import traceback
            error_trace = traceback.format_exc()
            print(f"Error generating PDF report: {error_trace}")
            messages.error(request, f'Error generating report: {str(e)}')
            return redirect('dashboard:generate_pdf_report')
    
    # Get available analyses for report generation
    pagespeed_analyses = PageSpeedAnalysis.objects.filter(
        user=request.user, is_deleted=False
    ).order_by('-created_at')[:10]
    
    keyword_analyses = KeywordAnalysis.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]
    
    image_analyses = ImageAltAnalysis.objects.filter(
        user=request.user
    ).order_by('-created_at')[:10]
    
    context = {
        'pagespeed_analyses': pagespeed_analyses,
        'keyword_analyses': keyword_analyses,
        'image_analyses': image_analyses,
        'report_types': [
            {'id': 'basic', 'name': 'Basic Report', 'description': 'Free report with core metrics', 'locked': False, 'icon': '📋'},
            {'id': 'premium', 'name': 'Premium Report', 'description': 'Advanced report with detailed insights and recommendations', 'locked': True, 'icon': '⭐'},
        ]
    }
    
    return render(request, 'dashboard/generate_pdf_report.html', context)


@login_required
def pdf_report_detail(request, pk):
    """View details of a specific PDF report"""
    report = get_object_or_404(PDFReport, pk=pk, user=request.user)
    
    context = {
        'report': report,
    }
    
    return render(request, 'dashboard/pdf_report_detail.html', context)


@login_required
def download_pdf_report(request, pk):
    """Download a PDF report"""
    report = get_object_or_404(PDFReport, pk=pk, user=request.user)
    
    if report.pdf_file:
        from django.http import FileResponse
        import os
        
        # Get the filename from the path
        filename = os.path.basename(report.pdf_file.name)
        
        response = FileResponse(report.pdf_file.open('rb'), as_attachment=True, 
                              filename=f'{report.title.replace(" ", "_")}.pdf')
        return response
    
    messages.error(request, 'Report file not found.')
    return redirect('dashboard:pdf_report_detail', pk=pk)


@login_required
def delete_pdf_report(request, pk):
    """Delete a PDF report"""
    report = get_object_or_404(PDFReport, pk=pk, user=request.user)
    
    if request.method == 'POST':
        report.delete()
        messages.success(request, 'PDF report deleted successfully!')
        return redirect('dashboard:pdf_reports_list')
    
    context = {
        'report': report,
    }
    
    return render(request, 'dashboard/delete_pdf_report.html', context)


@login_required
def regenerate_pdf_report(request, pk):
    """Regenerate an existing PDF report"""
    report = get_object_or_404(PDFReport, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Update report details
        report.title = request.POST.get('title', report.title)
        report.description = request.POST.get('description', report.description)
        report.include_charts = request.POST.get('include_charts') == 'on'
        report.include_recommendations = request.POST.get('include_recommendations') == 'on'
        report.save()
        
        # TODO: Implement actual PDF regeneration logic
        messages.info(request, 'PDF report regeneration coming soon! Changes saved.')
        return redirect('dashboard:pdf_report_detail', pk=pk)
    
    context = {
        'report': report,
    }
    
    return render(request, 'dashboard/regenerate_pdf_report.html', context)

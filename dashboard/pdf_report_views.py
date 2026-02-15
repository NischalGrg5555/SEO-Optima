"""
Views for PDF Report generation and management
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, HttpResponse
from django.contrib import messages
from django.views.generic import ListView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.core.files.base import ContentFile
from datetime import datetime
import os

from .models import PDFReport, PageSpeedAnalysis, KeywordAnalysis, ImageAltAnalysis
from .forms import PDFReportGeneratorForm, PDFReportFilterForm
from .services.pdf_generator import create_pdf_report


@login_required
def pdf_reports_list(request):
    """List all PDF reports for the user"""
    reports = PDFReport.objects.filter(user=request.user)
    form = PDFReportFilterForm(request.GET or None)
    
    # Apply filters
    if form.is_valid():
        report_type = form.cleaned_data.get('report_type')
        sort_by = form.cleaned_data.get('sort_by')
        
        if report_type:
            reports = reports.filter(report_type=report_type)
        
        if sort_by:
            reports = reports.order_by(sort_by)
    else:
        reports = reports.order_by('-created_at')
    
    context = {
        'reports': reports,
        'form': form,
        'total_reports': reports.count(),
        'free_reports': reports.filter(report_type='free').count(),
        'paid_reports': reports.filter(report_type='paid').count(),
    }
    
    return render(request, 'dashboard/reports/reports_list.html', context)


@login_required
def generate_pdf_report(request):
    """Generate a new PDF report"""
    form = PDFReportGeneratorForm(request.POST or None)
    
    # Get available analyses for the user
    pagespeed_analyses = PageSpeedAnalysis.objects.filter(user=request.user).order_by('-created_at')
    keyword_analyses = KeywordAnalysis.objects.filter(user=request.user).order_by('-created_at')
    image_analyses = ImageAltAnalysis.objects.filter(user=request.user).order_by('-created_at')
    
    if request.method == 'POST' and form.is_valid():
        try:
            # Get selected analyses
            include_pagespeed = form.cleaned_data.get('include_pagespeed', False)
            include_keywords = form.cleaned_data.get('include_keywords', False)
            include_images = form.cleaned_data.get('include_images', False)
            include_headers = form.cleaned_data.get('include_headers', False)
            
            # Validate that at least one analysis is selected
            if not any([include_pagespeed, include_keywords, include_images, include_headers]):
                messages.error(request, "Please select at least one analysis to include in the report.")
                return redirect('dashboard:generate_pdf_report')
            
            # Get the latest analyses
            ps_analysis = pagespeed_analyses.first() if include_pagespeed else None
            kw_analysis = keyword_analyses.first() if include_keywords else None
            img_analysis = image_analyses.first() if include_images else None
            
            # Create report instance
            report = PDFReport.objects.create(
                user=request.user,
                report_type=form.cleaned_data['report_type'],
                title=form.cleaned_data['title'],
                description=form.cleaned_data.get('description', ''),
                pagespeed_analysis=ps_analysis,
                keyword_analysis=kw_analysis,
                image_analysis=img_analysis,
                include_recommendations=form.cleaned_data.get('include_recommendations', True),
                include_charts=form.cleaned_data.get('include_charts', True),
            )
            
            # Generate PDF
            pdf_bytes = create_pdf_report(report)
            
            # Save PDF file
            pdf_filename = f"report_{report.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            report.pdf_file.save(pdf_filename, ContentFile(pdf_bytes), save=True)
            
            messages.success(request, f"Report '{report.title}' generated successfully!")
            return redirect('dashboard:pdf_report_detail', pk=report.id)
            
        except Exception as e:
            messages.error(request, f"Error generating report: {str(e)}")
            return redirect('dashboard:generate_pdf_report')
    
    context = {
        'form': form,
        'pagespeed_analyses': pagespeed_analyses[:5],
        'keyword_analyses': keyword_analyses[:5],
        'image_analyses': image_analyses[:5],
        'has_analyses': any([pagespeed_analyses.exists(), keyword_analyses.exists(), image_analyses.exists()]),
    }
    
    return render(request, 'dashboard/reports/generate_report.html', context)


@login_required
def pdf_report_detail(request, pk):
    """View a single PDF report"""
    report = get_object_or_404(PDFReport, pk=pk, user=request.user)
    
    context = {
        'report': report,
        'report_type_display': report.get_report_type_display(),
        'created_date': report.created_at.strftime('%B %d, %Y'),
        'created_time': report.created_at.strftime('%I:%M %p'),
    }
    
    return render(request, 'dashboard/reports/report_detail.html', context)


@login_required
def download_pdf_report(request, pk):
    """Download a PDF report"""
    report = get_object_or_404(PDFReport, pk=pk, user=request.user)
    
    if not report.pdf_file:
        messages.error(request, "PDF file not found.")
        return redirect('dashboard:pdf_report_detail', pk=pk)
    
    # Generate filename for download
    download_filename = f"{report.title.replace(' ', '_')}.pdf"
    
    # Serve the file
    response = FileResponse(report.pdf_file.open('rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{download_filename}"'
    
    return response


@login_required
def delete_pdf_report(request, pk):
    """Delete a PDF report"""
    report = get_object_or_404(PDFReport, pk=pk, user=request.user)
    
    if request.method == 'POST':
        # Delete PDF file if it exists
        if report.pdf_file:
            if os.path.isfile(report.pdf_file.path):
                os.remove(report.pdf_file.path)
        
        report_title = report.title
        report.delete()
        messages.success(request, f"Report '{report_title}' deleted successfully.")
        return redirect('dashboard:pdf_reports_list')
    
    context = {
        'report': report,
    }
    
    return render(request, 'dashboard/reports/delete_report.html', context)


@login_required
def regenerate_pdf_report(request, pk):
    """Regenerate a PDF report with the same settings"""
    report = get_object_or_404(PDFReport, pk=pk, user=request.user)
    
    try:
        # Delete old PDF file
        if report.pdf_file:
            if os.path.isfile(report.pdf_file.path):
                os.remove(report.pdf_file.path)
        
        # Generate new PDF
        pdf_bytes = create_pdf_report(report)
        
        # Save PDF file
        pdf_filename = f"report_{report.id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        report.pdf_file.save(pdf_filename, ContentFile(pdf_bytes), save=True)
        
        messages.success(request, f"Report '{report.title}' regenerated successfully!")
        return redirect('dashboard:pdf_report_detail', pk=pk)
        
    except Exception as e:
        messages.error(request, f"Error regenerating report: {str(e)}")
        return redirect('dashboard:pdf_report_detail', pk=pk)

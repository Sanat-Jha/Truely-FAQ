from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import FAQ

@login_required
def toggle_faq_visibility(request, faq_id):
    faq = get_object_or_404(FAQ, id=faq_id)
    
    # Check if the user owns the website
    if faq.website.owner != request.user:
        messages.error(request, "You don't have permission to manage this FAQ.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Toggle visibility
        faq.is_visible = not faq.is_visible
        faq.save()
        
        status = "visible" if faq.is_visible else "hidden"
        messages.success(request, f"FAQ is now {status}.")
    
    return redirect('website_detail', website_id=faq.website.id)

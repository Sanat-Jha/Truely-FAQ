from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Website
from .forms import WebsiteForm
from truelyfaq.questions.models import Question
from truelyfaq.faqs.models import FAQ

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Account created successfully. You can now log in.')
            return redirect('login')
    else:
        form = UserCreationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def dashboard(request):
    # Check if this is a POST request for creating a new website
    if request.method == 'POST':
        # Create a form instance with POST data
        form = WebsiteForm(request.POST)
        if form.is_valid():
            # Create the website but don't save to DB yet
            website = form.save(commit=False)
            # Set the owner to the current user
            website.owner = request.user
            # Now save to DB
            website.save()
            messages.success(request, f'Website "{website.name}" created successfully!')
            return redirect('dashboard')
        else:
            # If the form is not valid, show error message
            messages.error(request, 'There was an error creating your website. Please check the form.')
    else:
        form = WebsiteForm()
    
    # Get all websites for the current user
    websites = Website.objects.filter(owner=request.user)
    
    # Calculate total questions across all user websites
    total_questions = Question.objects.filter(website__in=websites).count()
    
    # Calculate total FAQs across all user websites
    total_faqs = FAQ.objects.filter(website__in=websites).count()
    
    # Add unanswered count and FAQ count to each website
    for website in websites:
        website.unanswered_count = Question.objects.filter(
            website=website, 
            is_answered=False
        ).count()
        website.faq_count = FAQ.objects.filter(website=website).count()
    
    context = {
        'websites': websites,
        'total_questions': total_questions,
        'total_faqs': total_faqs,
        'form': form,  # Include the form in the context
    }
    
    return render(request, 'accounts/dashboard.html', context)

@login_required
def delete_website(request, website_id):
    website = Website.objects.get(id=website_id)

    # Ensure the user owns the website
    if website.owner != request.user:
        messages.error(request, "You don't have permission to delete this website.")
        return redirect('dashboard')

    if request.method == 'POST':
        try:
            website_name = website.name
            # Deleting the website will cascade and delete related Questions, Answers, FAQs
            website.delete()
            messages.success(request, f'Website "{website_name}" and all its data have been deleted successfully.')
        except Exception as e:
            messages.error(request, f"An error occurred while deleting the website.")
        return redirect('dashboard')
    else:
        # Redirect GET requests back to dashboard
        messages.warning(request, "Use the delete button on the dashboard to delete a website.")
        return redirect('dashboard')

@login_required
def website_detail(request, website_id):
    try:
        website = Website.objects.get(id=website_id, owner=request.user)
    except Website.DoesNotExist:
        messages.error(request, 'Website not found.')
        return redirect('dashboard')
    
    # Get all questions for this website
    questions = Question.objects.filter(website=website).order_by('-created_at')
    
    # Get all FAQs for this website
    faqs = FAQ.objects.filter(website=website).order_by('-created_at')
    
    # Calculate unanswered count
    unanswered_count = questions.filter(is_answered=False).count()
    
    # Handle form submissions
    if request.method == 'POST':
        # Handle regenerating API key
        if 'regenerate_api_key' in request.POST:
            website.api_key = website._generate_api_key()
            website.save()
            messages.success(request, 'API key regenerated successfully.')
            return redirect('website_detail', website_id=website.id)
        
        # Handle updating manager email
        elif 'update_manager_email' in request.POST:
            manager_email = request.POST.get('manager_email')
            if manager_email:
                website.manager_email = manager_email
                website.save()
                messages.success(request, 'Manager email updated successfully.')
            return redirect('website_detail', website_id=website.id)
    
    context = {
        'website': website,
        'questions': questions,
        'faqs': faqs,
        'unanswered_count': unanswered_count
    }
    
    return render(request, 'accounts/website_detail.html', context)

@login_required
def toggle_faq_visibility(request, faq_id):
    """Toggle the visibility of a FAQ"""
    if request.method == 'POST':
        try:
            faq = get_object_or_404(FAQ, id=faq_id)
            
            # Ensure the user owns the website this FAQ belongs to
            if faq.website.owner != request.user:
                return JsonResponse({'success': False, 'message': 'Permission denied'}, status=403)
            
            # Toggle the visibility
            faq.is_visible = not faq.is_visible
            faq.save()
            
            return JsonResponse({
                'success': True, 
                'is_visible': faq.is_visible,
                'message': f'FAQ is now {"visible" if faq.is_visible else "hidden"}'
            })
        except Exception as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method'}, status=400)

@login_required
def edit_faq(request, faq_id):
    """Edit an existing FAQ"""
    faq = get_object_or_404(FAQ, id=faq_id)
    
    # Ensure the user owns the website this FAQ belongs to
    if faq.website.owner != request.user:
        messages.error(request, "You don't have permission to edit this FAQ.")
        return redirect('dashboard')
    
    if request.method == 'POST':
        question_text = request.POST.get('question_text')
        answer_text = request.POST.get('answer_text')
        
        if question_text and answer_text:
            faq.question_text = question_text
            faq.answer_text = answer_text
            faq.save()
            messages.success(request, 'FAQ updated successfully.')
            return redirect('website_detail', website_id=faq.website.id)
        else:
            messages.error(request, 'Both question and answer are required.')
    
    return redirect('website_detail', website_id=faq.website.id)

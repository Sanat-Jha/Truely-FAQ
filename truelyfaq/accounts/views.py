from django.shortcuts import render, redirect
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Website
from truelyfaq.questions.models import Question

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
    websites = Website.objects.filter(owner=request.user)
    
    if request.method == 'POST':
        # Handle website creation
        name = request.POST.get('name')
        url = request.POST.get('url')
        
        if name and url:
            website = Website(owner=request.user, name=name, url=url)
            website.save()
            messages.success(request, f'Website "{name}" added successfully.')
            return redirect('dashboard')
        else:
            messages.error(request, 'Please provide both name and URL for the website.')
    
    # Get unanswered questions count for each website
    for website in websites:
        website.unanswered_count = Question.objects.filter(
            website=website, 
            is_answered=False
        ).count()
    
    context = {
        'websites': websites
    }
    
    return render(request, 'accounts/dashboard.html', context)

@login_required
def website_detail(request, website_id):
    try:
        website = Website.objects.get(id=website_id, owner=request.user)
    except Website.DoesNotExist:
        messages.error(request, 'Website not found.')
        return redirect('dashboard')
    
    # Get all questions for this website
    questions = Question.objects.filter(website=website).order_by('-created_at')
    
    # Calculate unanswered count
    unanswered_count = questions.filter(is_answered=False).count()
    
    # Handle regenerating API key
    if request.method == 'POST' and 'regenerate_api_key' in request.POST:
        website.api_key = website._generate_api_key()
        website.save()
        messages.success(request, 'API key regenerated successfully.')
        return redirect('website_detail', website_id=website.id)
    
    context = {
        'website': website,
        'questions': questions,
        'unanswered_count': unanswered_count
    }
    
    return render(request, 'accounts/website_detail.html', context)

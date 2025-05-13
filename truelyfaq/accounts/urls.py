from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('register/', views.register, name='register'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('website/<int:website_id>/', views.website_detail, name='website_detail'),
    path('website/<int:website_id>/delete/', views.delete_website, name='delete_website'),
    path('faq/<int:faq_id>/toggle-visibility/', views.toggle_faq_visibility, name='toggle_faq_visibility'),
    path('faq/<int:faq_id>/edit/', views.edit_faq, name='edit_faq'),
]
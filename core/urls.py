from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('faq/', views.faq_view, name='faq'),
    path('returns/', views.returns_view, name='returns'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('terms/', views.terms_view, name='terms'),
    path('maintenance/', views.maintenance_view, name='maintenance'),
    path('newsletter/signup/', views.newsletter_signup, name='newsletter_signup'),
]

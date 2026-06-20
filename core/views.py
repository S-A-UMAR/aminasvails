from django.shortcuts import render, redirect
from django.contrib import messages
from shop.models import Product
from .forms import ContactForm

def home_view(request):
    featured_products = Product.objects.filter(is_featured=True)[:4]
    return render(request, 'core/home.html', {
        'featured_products': featured_products
    })

def about_view(request):
    return render(request, 'core/about.html')

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # In a real app, send email here
            messages.success(request, "Thank you! Your message has been sent successfully. We will contact you soon.")
            return redirect('contact')
        else:
            messages.error(request, "Please correct the errors in the form.")
    else:
        form = ContactForm()
    return render(request, 'core/contact.html', {'form': form})

def faq_view(request):
    return render(request, 'core/faq.html')

def returns_view(request):
    return render(request, 'core/returns.html')

def privacy_view(request):
    return render(request, 'core/privacy.html')

def terms_view(request):
    return render(request, 'core/terms.html')

def maintenance_view(request):
    return render(request, 'core/maintenance.html')

def newsletter_signup(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        if email:
            # Seed subscription message
            messages.success(request, f"Thank you! {email} has been subscribed to our style newsletter.")
        else:
            messages.error(request, "Please enter a valid email address.")
    return redirect(request.META.get('HTTP_REFERER', 'home'))

def custom_404_view(request, exception):
    return render(request, '404.html', status=404)

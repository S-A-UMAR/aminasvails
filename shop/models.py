from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import urllib.parse

class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_list') + f'?category={self.slug}'

    def get_image_url(self):
        if self.image:
            return self.image.url
        # Elegant SVG Gold/Midnight gradient background data url
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="400" viewBox="0 0 600 400">
            <defs>
                <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#0d0d0d"/>
                    <stop offset="100%" stop-color="#d4af37"/>
                </linearGradient>
            </defs>
            <rect width="100%" height="100%" fill="url(#g)"/>
            <text x="50%" y="50%" font-family="'Josefin Sans', sans-serif" font-size="28" font-weight="bold" fill="#ffffff" dominant-baseline="middle" text-anchor="middle" letter-spacing="3">{self.name.upper()}</text>
        </svg>"""
        encoded_svg = urllib.parse.quote(svg_content.strip())
        return f"data:image/svg+xml;utf8,{encoded_svg}"


class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    sku = models.CharField(max_length=50, unique=True)
    stock = models.IntegerField(default=10)
    is_featured = models.BooleanField(default=False)
    colors = models.CharField(max_length=200, default='Midnight Black, Metallic Gold, Ivory White', help_text='Comma-separated colors')
    sizes = models.CharField(max_length=200, default='Standard Size', help_text='Comma-separated sizes')
    main_image = models.ImageField(upload_to='products/', blank=True, null=True)
    secondary_image = models.ImageField(upload_to='products/', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('shop:product_detail', args=[self.id, self.slug])

    def get_colors_list(self):
        return [c.strip() for c in self.colors.split(',') if c.strip()]

    def get_sizes_list(self):
        return [s.strip() for s in self.sizes.split(',') if s.strip()]

    def get_main_image_url(self):
        if self.main_image:
            return self.main_image.url
        # Custom SVG data url with unique colors based on ID or Name
        grad_color = "#d4af37" if self.id and self.id % 2 == 0 else "#bbbbbb"
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="800" viewBox="0 0 600 800">
            <defs>
                <linearGradient id="g" x1="0%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="#0d0d0d"/>
                    <stop offset="60%" stop-color="#222222"/>
                    <stop offset="100%" stop-color="{grad_color}"/>
                </linearGradient>
            </defs>
            <rect width="100%" height="100%" fill="url(#g)"/>
            <circle cx="300" cy="400" r="180" fill="none" stroke="#d4af37" stroke-width="1" stroke-dasharray="5 5" opacity="0.4"/>
            <text x="50%" y="45%" font-family="'Josefin Sans', sans-serif" font-size="24" fill="#d4af37" dominant-baseline="middle" text-anchor="middle" letter-spacing="4">AMINA'S VAILS</text>
            <text x="50%" y="52%" font-family="'Josefin Sans', sans-serif" font-size="18" fill="#ffffff" dominant-baseline="middle" text-anchor="middle" letter-spacing="2">{self.name.upper()}</text>
        </svg>"""
        encoded_svg = urllib.parse.quote(svg_content.strip())
        return f"data:image/svg+xml;utf8,{encoded_svg}"

    def get_secondary_image_url(self):
        if self.secondary_image:
            return self.secondary_image.url
        # Secondary views SVG
        grad_color = "#222222" if self.id and self.id % 2 == 0 else "#111111"
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="600" height="800" viewBox="0 0 600 800">
            <defs>
                <linearGradient id="g" x1="100%" y1="0%" x2="0%" y2="100%">
                    <stop offset="0%" stop-color="#d4af37"/>
                    <stop offset="100%" stop-color="{grad_color}"/>
                </linearGradient>
            </defs>
            <rect width="100%" height="100%" fill="url(#g)"/>
            <text x="50%" y="50%" font-family="'Josefin Sans', sans-serif" font-size="22" fill="#ffffff" dominant-baseline="middle" text-anchor="middle" letter-spacing="3">PREMIUM SCARF DETAIL</text>
        </svg>"""
        encoded_svg = urllib.parse.quote(svg_content.strip())
        return f"data:image/svg+xml;utf8,{encoded_svg}"

    @property
    def average_rating(self):
        reviews = self.reviews.all()
        if not reviews:
            return 5.0
        return sum(r.rating for r in reviews) / len(reviews)


class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Completed', 'Completed'),
        ('Cancelled', 'Cancelled'),
    )
    
    PAYMENT_CHOICES = (
        ('whatsapp', 'WhatsApp Payment'),
        ('card_fallback', 'Credit Card Fallback'),
    )

    customer_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, help_text='WhatsApp Phone Number')
    shipping_address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, default='whatsapp')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"Order #{self.id} - {self.customer_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='order_items', on_delete=models.CASCADE)
    color = models.CharField(max_length=50, blank=True, null=True)
    size = models.CharField(max_length=50, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    def get_cost(self):
        return self.price * self.quantity


class Review(models.Model):
    product = models.ForeignKey(Product, related_name='reviews', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='reviews', on_delete=models.CASCADE, null=True, blank=True)
    name = models.CharField(max_length=100, default='Anonymous')
    rating = models.PositiveIntegerField(choices=[(i, i) for i in range(1, 6)], default=5)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return f"Review ({self.rating}/5) for {self.product.name} by {self.name}"

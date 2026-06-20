from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse
import urllib.parse

class Post(models.Model):
    STATUS_CHOICES = (
        ('draft', 'Draft'),
        ('published', 'Published'),
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    body = models.TextField()
    image = models.ImageField(upload_to='blog/', blank=True, null=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='draft')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ('-created_at',)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:post_detail', args=[self.slug])

    def get_image_url(self):
        if self.image:
            return self.image.url
        # Elegant SVG Gold/Charcoal editorial background data url
        svg_content = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="500" viewBox="0 0 800 500">
            <defs>
                <linearGradient id="g" x1="0%" y1="0%" x2="100%" y2="100%">
                    <stop offset="0%" stop-color="#222222"/>
                    <stop offset="100%" stop-color="#0d0d0d"/>
                </linearGradient>
            </defs>
            <rect width="100%" height="100%" fill="url(#g)"/>
            <rect x="20" y="20" width="760" height="460" fill="none" stroke="#d4af37" stroke-width="1" opacity="0.3"/>
            <text x="50%" y="45%" font-family="'Josefin Sans', sans-serif" font-size="28" font-weight="bold" fill="#d4af37" dominant-baseline="middle" text-anchor="middle" letter-spacing="3">EDITORIAL & STYLE</text>
            <text x="50%" y="55%" font-family="'Josefin Sans', sans-serif" font-size="20" fill="#ffffff" dominant-baseline="middle" text-anchor="middle" letter-spacing="1">{self.title.upper()}</text>
        </svg>"""
        encoded_svg = urllib.parse.quote(svg_content.strip())
        return f"data:image/svg+xml;utf8,{encoded_svg}"

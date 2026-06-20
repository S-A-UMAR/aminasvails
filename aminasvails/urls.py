from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from shop.admin import admin_site  # custom analytics admin

urlpatterns = [
    path('admin/', admin.site.urls),             # default django admin
    path('store-admin/', admin_site.urls),        # custom branded admin with dashboard
    path('accounts/', include('accounts.urls')),
    path('shop/', include('shop.urls')),
    path('blog/', include('blog.urls')),
    path('', include('core.urls')),  # core handles root views
]

# Custom 404 handler
handler404 = 'core.views.custom_404_view'

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

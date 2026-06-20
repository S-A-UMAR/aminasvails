from django.contrib import admin
from django.utils.html import format_html
from django.urls import path
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.http import HttpResponse
from datetime import timedelta
import csv
from .models import Category, Product, Order, OrderItem, Review


# ─── Custom Admin Site ──────────────────────────────────────────────────────
class AminaAdminSite(admin.AdminSite):
    site_header  = "Amina's Vails — Command Centre"
    site_title   = "Amina's Vails Admin"
    index_title  = "Store Management"
    login_template = 'admin/login.html'

    def get_urls(self):
        urls = super().get_urls()
        custom = [path('dashboard/', self.admin_view(self.dashboard_view), name='dashboard')]
        return custom + urls

    def dashboard_view(self, request):
        now      = timezone.now()
        today    = now.date()
        wk_ago   = now - timedelta(days=7)
        mo_ago   = now - timedelta(days=30)

        orders_qs = Order.objects.all()

        # ── KPI cards ──
        total_orders     = orders_qs.count()
        total_revenue    = orders_qs.filter(status='Completed').aggregate(v=Sum('total_amount'))['v'] or 0
        pending_orders   = orders_qs.filter(status='Pending').count()
        todays_orders    = orders_qs.filter(created_at__date=today).count()

        # ── Orders by status (pie data) ──
        statuses = ['Pending', 'Processing', 'Shipped', 'Completed', 'Cancelled']
        status_counts = [orders_qs.filter(status=s).count() for s in statuses]

        # ── Revenue last 7 days (line chart) ──
        daily_labels, daily_revenue = [], []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            rev = orders_qs.filter(
                created_at__date=d, status='Completed'
            ).aggregate(v=Sum('total_amount'))['v'] or 0
            daily_labels.append(d.strftime('%a %d'))
            daily_revenue.append(float(rev))

        # ── Monthly orders last 6 months (bar chart) ──
        monthly_labels, monthly_counts = [], []
        for i in range(5, -1, -1):
            d = today.replace(day=1) - timedelta(days=i * 30)
            label = d.strftime('%b %Y')
            cnt = orders_qs.filter(
                created_at__year=d.year, created_at__month=d.month
            ).count()
            monthly_labels.append(label)
            monthly_counts.append(cnt)

        # ── Top 5 products by revenue ──
        top_products = (
            OrderItem.objects.values('product__name')
            .annotate(total=Sum('price'), units=Sum('quantity'))
            .order_by('-total')[:5]
        )

        # ── Recent 10 orders ──
        recent_orders = orders_qs.order_by('-created_at')[:10]

        # ── Low stock ──
        low_stock = Product.objects.filter(stock__lte=3).order_by('stock')

        # ── Reviews breakdown (star → count + pct) ──
        total_reviews = Review.objects.count()
        review_data = []
        for star in range(5, 0, -1):
            cnt = Review.objects.filter(rating=star).count()
            pct = round((cnt / total_reviews * 100) if total_reviews else 0)
            review_data.append({'star': star, 'count': cnt, 'pct': pct})

        ctx = dict(
            self.each_context(request),
            total_orders=total_orders,
            total_revenue=total_revenue,
            pending_orders=pending_orders,
            todays_orders=todays_orders,
            statuses=statuses,
            status_counts=status_counts,
            daily_labels=daily_labels,
            daily_revenue=daily_revenue,
            monthly_labels=monthly_labels,
            monthly_counts=monthly_counts,
            top_products=top_products,
            recent_orders=recent_orders,
            low_stock=low_stock,
            review_data=review_data,
            total_reviews=total_reviews,
            title='Analytics Dashboard',
        )
        return render(request, 'admin/dashboard.html', ctx)


admin_site = AminaAdminSite(name='amina_admin')


# ─── Category ──────────────────────────────────────────────────────────────
@admin.register(Category, site=admin_site)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'product_count')
    prepopulated_fields = {'slug': ('name',)}

    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


# ─── Product ───────────────────────────────────────────────────────────────
@admin.register(Product, site=admin_site)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price_tag', 'stock_badge', 'is_featured', 'created_at')
    list_filter  = ('category', 'is_featured')
    search_fields = ('name', 'sku', 'description')
    list_editable = ('is_featured',)
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'slug', 'category', 'sku', 'description')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'stock', 'is_featured')
        }),
        ('Variants', {
            'fields': ('colors', 'sizes')
        }),
        ('Images', {
            'fields': ('main_image', 'secondary_image')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    def price_tag(self, obj):
        return format_html('<strong style="color:#d4af37">₦{}</strong>', f'{float(obj.price):,.0f}')
    price_tag.short_description = 'Price'

    def stock_badge(self, obj):
        if obj.stock == 0:
            color, label = '#e74c3c', 'Out of Stock'
        elif obj.stock <= 3:
            color, label = '#f39c12', f'Low ({obj.stock})'
        else:
            color, label = '#27ae60', f'In Stock ({obj.stock})'
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 10px;border-radius:12px;font-size:11px;font-weight:600">{}</span>',
            color, label
        )
    stock_badge.short_description = 'Stock'


# ─── Order ─────────────────────────────────────────────────────────────────
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    readonly_fields = ('product', 'color', 'size', 'price', 'quantity', 'line_total')
    extra = 0

    def line_total(self, obj):
        return format_html('<strong>₦{}</strong>', f'{float(obj.get_cost()):,.0f}')
    line_total.short_description = 'Line Total'


def export_orders_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders.csv"'
    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Customer', 'Email', 'Phone', 'Address', 'Total', 'Payment', 'Status', 'Date'])
    for order in queryset:
        writer.writerow([
            order.id, order.customer_name, order.email, order.phone,
            order.shipping_address, order.total_amount,
            order.payment_method, order.status,
            order.created_at.strftime('%Y-%m-%d %H:%M'),
        ])
    return response
export_orders_csv.short_description = 'Export selected orders to CSV'


def mark_processing(modeladmin, request, queryset):
    queryset.update(status='Processing')
mark_processing.short_description = 'Mark as Processing'

def mark_shipped(modeladmin, request, queryset):
    queryset.update(status='Shipped')
mark_shipped.short_description = 'Mark as Shipped'

def mark_completed(modeladmin, request, queryset):
    queryset.update(status='Completed')
mark_completed.short_description = 'Mark as Completed'


@admin.register(Order, site=admin_site)
class OrderAdmin(admin.ModelAdmin):
    list_display   = ('order_id', 'customer_name', 'email', 'phone', 'total_tag', 'payment_badge', 'status_badge', 'created_at')
    list_filter    = ('status', 'payment_method', 'created_at')
    search_fields  = ('customer_name', 'email', 'phone', 'id')
    inlines        = [OrderItemInline]
    readonly_fields = ('created_at',)
    actions        = [export_orders_csv, mark_processing, mark_shipped, mark_completed]

    fieldsets = (
        ('Customer Details', {
            'fields': ('customer_name', 'email', 'phone', 'shipping_address')
        }),
        ('Order Details', {
            'fields': ('total_amount', 'payment_method', 'status', 'transaction_id')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )

    def order_id(self, obj):
        return format_html('<strong>#{}</strong>', obj.id)
    order_id.short_description = 'Order'

    def total_tag(self, obj):
        return format_html('<strong>₦{}</strong>', f'{float(obj.total_amount):,.0f}')
    total_tag.short_description = 'Total'

    def status_badge(self, obj):
        colours = {
            'Pending':    '#f39c12',
            'Processing': '#3498db',
            'Shipped':    '#9b59b6',
            'Completed':  '#27ae60',
            'Cancelled':  '#e74c3c',
        }
        c = colours.get(obj.status, '#888')
        return format_html(
            '<span style="background:{};color:#fff;padding:3px 12px;border-radius:12px;font-size:11px;font-weight:600">{}</span>',
            c, obj.status
        )
    status_badge.short_description = 'Status'

    def payment_badge(self, obj):
        from django.utils.safestring import mark_safe
        if obj.payment_method == 'whatsapp':
            return mark_safe('<span style="color:#25d366;font-weight:600">● WhatsApp</span>')
        return mark_safe('<span style="color:#3498db;font-weight:600">● Card</span>')
    payment_badge.short_description = 'Payment'


# ─── Review ────────────────────────────────────────────────────────────────
@admin.register(Review, site=admin_site)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'name', 'star_rating', 'created_at')
    list_filter  = ('rating',)
    search_fields = ('name', 'comment', 'product__name')
    readonly_fields = ('created_at',)

    def star_rating(self, obj):
        stars = '★' * obj.rating + '☆' * (5 - obj.rating)
        color = '#d4af37' if obj.rating >= 4 else ('#f39c12' if obj.rating == 3 else '#e74c3c')
        return format_html('<span style="color:{};font-size:16px">{}</span>', color, stars)
    star_rating.short_description = 'Rating'


# ─── Default admin site: also register everything so /admin/ still works ───
admin.site.site_header  = "Amina's Vails Admin"
admin.site.site_title   = "Amina's Vails"
admin.site.index_title  = "Store Management"

@admin.register(Category)
class CategoryAdminDefault(CategoryAdmin):
    pass

@admin.register(Product)
class ProductAdminDefault(ProductAdmin):
    pass

@admin.register(Order)
class OrderAdminDefault(OrderAdmin):
    pass

@admin.register(Review)
class ReviewAdminDefault(ReviewAdmin):
    pass

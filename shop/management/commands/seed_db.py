from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils.text import slugify
from shop.models import Category, Product, Review
from blog.models import Post

class Command(BaseCommand):
    help = 'Seeds the database with luxury categories, products, blog posts, and a superuser.'

    def handle(self, *args, **options):
        self.stdout.write('Seeding database...')

        # 1. Create Superuser if not exists
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@aminasvails.com', 'adminpassword123')
            self.stdout.write(self.style.SUCCESS('Superuser created (admin / adminpassword123)'))
        else:
            self.stdout.write('Superuser "admin" already exists.')

        admin_user = User.objects.get(username='admin')

        # 2. Create Categories
        categories_data = [
            {
                'name': 'Pure Silk',
                'description': 'Lustrous, ultra-soft pure silk veils crafted for ultimate luxury and comfort.'
            },
            {
                'name': 'Chiffon Shawls',
                'description': 'Lightweight, semi-sheer chiffon veils offering a graceful drape and flow.'
            },
            {
                'name': 'Premium Cotton',
                'description': 'Breathable, high-grade cotton veils designed for timeless everyday sophistication.'
            },
            {
                'name': 'Georgette Collection',
                'description': 'Elegant crinkled-texture georgette scarves that stay in place beautifully.'
            }
        ]

        categories = {}
        for cat_info in categories_data:
            cat, created = Category.objects.get_or_create(
                slug=slugify(cat_info['name']),
                defaults={
                    'name': cat_info['name'],
                    'description': cat_info['description']
                }
            )
            categories[cat.name] = cat
            if created:
                self.stdout.write(f'Created category: {cat.name}')

        # 3. Create Products
        products_data = [
            # Pure Silk
            {
                'category': categories['Pure Silk'],
                'name': 'Amara Gold Silk Veil',
                'description': 'The Amara Silk Veil represents the height of textile craftsmanship. Made of 100% heavy mulberry silk, it features a fluid, liquid drape and a luminous golden shimmer. A stunning accent piece for formal wear or luxury collections.',
                'price': 180.00,
                'sku': 'SLK-AMR-GLD',
                'stock': 15,
                'is_featured': True,
                'colors': 'Metallic Gold, Midnight Black, Ivory White',
                'sizes': 'Standard, Large'
            },
            {
                'category': categories['Pure Silk'],
                'name': 'Nour Crimson Silk Veil',
                'description': 'Crafted in a rich crimson hue, this Mulberry Silk veil is light as air yet possesses an unmistakable weight of elegance. The hand-rolled edges provide a bespoke, couture finish.',
                'price': 195.00,
                'sku': 'SLK-NOR-CRM',
                'stock': 8,
                'is_featured': True,
                'colors': 'Crimson Red, Midnight Black',
                'sizes': 'Standard'
            },
            {
                'category': categories['Pure Silk'],
                'name': 'Zaina Pearl Silk Veil',
                'description': 'A delicate white veil with pearlescent reflections. Made for the bride or the modern woman seeking a refined, clean aesthetic. Fits seamlessly in any luxury accessories wardrobe.',
                'price': 220.00,
                'sku': 'SLK-ZNA-PRL',
                'stock': 12,
                'is_featured': False,
                'colors': 'Pearl White, Cream Ivory',
                'sizes': 'Standard, Large'
            },

            # Chiffon Shawls
            {
                'category': categories['Chiffon Shawls'],
                'name': 'Yasmine Rose Chiffon',
                'description': 'The Yasmine Chiffon features an incredibly fine weave, creating a semi-sheer overlay that floats effortlessly. Tinted in a soft dusty rose color, it adds a touch of classic romance to any style.',
                'price': 85.00,
                'sku': 'CHF-YSM-ROS',
                'stock': 25,
                'is_featured': True,
                'colors': 'Dusty Rose, Soft Blush, Ivory',
                'sizes': 'Standard, Large'
            },
            {
                'category': categories['Chiffon Shawls'],
                'name': 'Soraya Charcoal Chiffon',
                'description': 'A deep charcoal variant of our luxury chiffon range. Perfectly suited for minimalist, high-fashion styling. Breathable weave ensures all-day comfort without slipping.',
                'price': 85.00,
                'sku': 'CHF-SRY-CHR',
                'stock': 20,
                'is_featured': False,
                'colors': 'Charcoal Gray, Midnight Black, Slate Blue',
                'sizes': 'Standard'
            },

            # Premium Cotton
            {
                'category': categories['Premium Cotton'],
                'name': 'Lina Sand Cotton Veil',
                'description': 'Woven from long-staple Egyptian cotton, the Lina Sand Veil is extremely soft, exceptionally durable, and highly breathable. Styled in an earthy sand color that matches almost anything.',
                'price': 95.00,
                'sku': 'CTN-LIN-SND',
                'stock': 30,
                'is_featured': True,
                'colors': 'Desert Sand, Olive Green, Natural Ivory',
                'sizes': 'Standard, Large'
            },
            {
                'category': categories['Premium Cotton'],
                'name': 'Farah Indigo Cotton Veil',
                'description': 'Deep indigo cotton scarf dyed using organic processes. Perfect for layering in transitional weather. Soft-wash finish provides a comforting texture that improves with every wear.',
                'price': 95.00,
                'sku': 'CTN-FRH-IND',
                'stock': 18,
                'is_featured': False,
                'colors': 'Indigo Blue, Ocean Teal, Navy Blue',
                'sizes': 'Standard'
            },

            # Georgette Collection
            {
                'category': categories['Georgette Collection'],
                'name': 'Layla Obsidian Georgette',
                'description': 'Our obsidian Georgette veil has a subtle crinkle structure that increases volume and provides excellent friction against slips. The ultimate daily veil for the professional luxury client.',
                'price': 110.00,
                'sku': 'GEO-LYL-OBS',
                'stock': 22,
                'is_featured': False,
                'colors': 'Obsidian Black, Deep Plum, Charcoal',
                'sizes': 'Standard, Large'
            },
            {
                'category': categories['Georgette Collection'],
                'name': 'Rania Emerald Georgette',
                'description': 'A vibrant jewel-toned emerald georgette veil that brings light to your eyes and warmth to your complexion. Ideal for editorial styling or statement accessorizing.',
                'price': 115.00,
                'sku': 'GEO-RNI-EMR',
                'stock': 14,
                'is_featured': False,
                'colors': 'Emerald Green, Muted Teal',
                'sizes': 'Standard'
            }
        ]

        for p_info in products_data:
            p, created = Product.objects.get_or_create(
                sku=p_info['sku'],
                defaults={
                    'category': p_info['category'],
                    'name': p_info['name'],
                    'slug': slugify(p_info['name']),
                    'description': p_info['description'],
                    'price': p_info['price'],
                    'stock': p_info['stock'],
                    'is_featured': p_info['is_featured'],
                    'colors': p_info['colors'],
                    'sizes': p_info['sizes']
                }
            )
            if created:
                self.stdout.write(f'Created product: {p.name}')
                
                # Add a dummy review for featured products to make PDP look lively
                if p.is_featured:
                    Review.objects.create(
                        product=p,
                        name="Amina Al-Mansoor",
                        rating=5,
                        comment=f"Absolutely stunning quality. The weave is fine, and the drape is unmatched. Truly feels like luxury."
                    )
                    Review.objects.create(
                        product=p,
                        name="Sophia Loren",
                        rating=4,
                        comment=f"Beautiful fabric and sheen. The metallic accents catch the light beautifully. Will definitely buy in other colors."
                    )

        # 4. Create Blog Posts
        posts_data = [
            {
                'title': 'The Art of Styling Silk Veils',
                'body': 'Silk has always been the fabric of royalty. In this styling guide, we explore how to drape and style the Amara Gold Silk Veil for formal events, evening galas, and professional environments. Discover three classic folds that highlight the fluid drape and natural sheen of pure Mulberry silk, ensuring elegance in every thread. We discuss how to secure your silk veil without damaging the delicate fibers, using minimal gold-plated magnets and high-quality under-caps.',
                'status': 'published'
            },
            {
                'title': 'Why Egyptian Cotton is Your Best Everyday Companion',
                'body': 'For day-to-day comfort, the choice of fabric makes all the difference. Our Lina Sand Cotton Veil is woven from long-staple Egyptian cotton, which features fibers twice as long as standard cotton. In this editorial, we dive into the science of breathability, durability, and texture. Learn why premium cotton resists pilling, retains color vibrancy over time, and feels cooling against the skin in warm climates, making it the perfect foundation for upscale minimalist style.',
                'status': 'published'
            },
            {
                'title': 'Caring For Your Luxury Accessories',
                'body': 'Luxury scarves are investments meant to last a lifetime. Proper care preserves the softness, drape, and color of your veils. Here, we outline the golden rules of laundering fine silks and delicate chiffon. From temperature-controlled handwashing using mild organic pH-neutral soaps, to flat-drying and low-heat steam pressing, this guide is an essential read for maintaining the pristine condition of your Amina’s Vails collection.',
                'status': 'published'
            }
        ]

        for post_info in posts_data:
            post, created = Post.objects.get_or_create(
                slug=slugify(post_info['title']),
                defaults={
                    'title': post_info['title'],
                    'author': admin_user,
                    'body': post_info['body'],
                    'status': post_info['status']
                }
            )
            if created:
                self.stdout.write(f'Created blog post: {post.title}')

        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))

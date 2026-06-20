from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from shop.models import Category, Product, Order, OrderItem

class ShopTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.category = Category.objects.create(
            name='Test Silk',
            slug='test-silk',
            description='Test category description'
        )
        self.product = Product.objects.create(
            category=self.category,
            name='Test Silk Veil',
            slug='test-silk-veil',
            description='Test product description',
            price=150.00,
            sku='TST-SLK-VEIL',
            stock=10,
            colors='Black, Gold',
            sizes='Standard'
        )

    def test_product_list_view(self):
        response = self.client.get(reverse('shop:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Silk Veil')
        
    def test_product_detail_view(self):
        response = self.client.get(reverse('shop:product_detail', args=[self.product.id, self.product.slug]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Silk Veil')
        self.assertContains(response, '$150.00')

    def test_cart_session_operations(self):
        # Add to cart
        response = self.client.post(reverse('shop:cart_add', args=[self.product.id]), {
            'quantity': 2,
            'color': 'Gold',
            'size': 'Standard'
        })
        self.assertEqual(response.status_code, 302)  # Redirects to cart detail
        
        # Verify cart items in session
        session = self.client.session
        self.assertIn('cart', session)
        item_key = f"{self.product.id}_Gold_Standard"
        self.assertIn(item_key, session['cart'])
        self.assertEqual(session['cart'][item_key]['quantity'], 2)
        
        # Remove from cart
        response = self.client.get(reverse('shop:cart_remove', args=[self.product.id]) + f"?key={item_key}")
        self.assertEqual(response.status_code, 302)
        session = self.client.session
        self.assertNotIn(item_key, session['cart'])

    def test_checkout_submission_whatsapp(self):
        # Put an item in cart
        self.client.post(reverse('shop:cart_add', args=[self.product.id]), {
            'quantity': 1,
            'color': 'Black',
            'size': 'Standard'
        })
        
        # Submit checkout
        response = self.client.post(reverse('shop:checkout'), {
            'name': 'Test Customer',
            'email': 'customer@test.com',
            'phone': '+2348000000000',
            'address': '123 Test Street, Lagos',
            'payment_method': 'whatsapp'
        })
        # Verify order was created in DB
        self.assertEqual(Order.objects.count(), 1)
        order = Order.objects.first()
        self.assertEqual(order.customer_name, 'Test Customer')
        self.assertEqual(order.phone, '+2348000000000')
        self.assertEqual(order.payment_method, 'whatsapp')
        
        # Verify order items were created
        self.assertEqual(OrderItem.objects.count(), 1)
        item = OrderItem.objects.first()
        self.assertEqual(item.product, self.product)
        self.assertEqual(item.quantity, 1)
        
        # Redirect to whatsapp_redirect view
        self.assertRedirects(response, reverse('shop:whatsapp_redirect', args=[order.id]))
        
        # View redirect details page - check that page renders and contains WhatsApp link + order info
        redirect_response = self.client.get(reverse('shop:whatsapp_redirect', args=[order.id]))
        self.assertEqual(redirect_response.status_code, 200)
        self.assertContains(redirect_response, 'wa.me')
        self.assertContains(redirect_response, 'Test Customer')      # customer_name in ORDER RECAP box
        self.assertContains(redirect_response, 'CONNECTING TO WHATSAPP')  # heading on redirect page

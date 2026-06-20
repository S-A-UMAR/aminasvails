from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.urls import reverse
from django.conf import settings
from decimal import Decimal
import urllib.parse
import os

from .models import Category, Product, Order, OrderItem, Review
from .cart import Cart

def product_list(request):
    products = Product.objects.all()
    categories = Category.objects.all()

    # Filter by Category
    category_slug = request.GET.get('category')
    selected_category = None
    if category_slug:
        selected_category = get_object_or_404(Category, slug=category_slug)
        products = products.filter(category=selected_category)

    # Filter by Color
    color = request.GET.get('color')
    if color:
        products = products.filter(colors__icontains=color)

    # Filter by Size
    size = request.GET.get('size')
    if size:
        products = products.filter(sizes__icontains=size)

    # Search Query
    query = request.GET.get('q')
    if query:
        products = products.filter(
            models.Q(name__icontains=query) | models.Q(description__icontains=query)
        )

    # Sorting
    sort = request.GET.get('sort')
    if sort == 'price_asc':
        products = products.order_by('price')
    elif sort == 'price_desc':
        products = products.order_by('-price')
    elif sort == 'newest':
        products = products.order_by('-created_at')

    # Get distinct colors and sizes for filter sidebar options (mock list for convenience)
    available_colors = ['Gold', 'Black', 'Ivory', 'Rose', 'Navy', 'Cream']
    available_sizes = ['Standard', 'Large', 'Extra Large']

    return render(request, 'shop/product_list.html', {
        'products': products,
        'categories': categories,
        'selected_category': selected_category,
        'available_colors': available_colors,
        'available_sizes': available_sizes,
        'current_sort': sort,
        'current_color': color,
        'current_size': size,
        'current_q': query
    })

def product_detail(request, id, slug):
    product = get_object_or_404(Product, id=id, slug=slug)
    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]
    
    # Handle Review Submission
    if request.method == 'POST':
        name = request.POST.get('name', 'Anonymous')
        rating = request.POST.get('rating', '5')
        comment = request.POST.get('comment', '')
        
        user = request.user if request.user.is_authenticated else None
        
        Review.objects.create(
            product=product,
            user=user,
            name=name,
            rating=int(rating),
            comment=comment
        )
        messages.success(request, "Thank you for your feedback! Your review has been published.")
        return redirect(product.get_absolute_url())

    return render(request, 'shop/product_detail.html', {
        'product': product,
        'related_products': related_products
    })

def cart_add(request, product_id):
    cart = Cart(request)
    product = get_object_or_404(Product, id=product_id)
    
    quantity = int(request.POST.get('quantity', 1))
    color = request.POST.get('color', product.get_colors_list()[0] if product.get_colors_list() else 'Standard')
    size = request.POST.get('size', product.get_sizes_list()[0] if product.get_sizes_list() else 'Standard')
    
    cart.add(product=product, quantity=quantity, color=color, size=size)
    messages.success(request, f"{product.name} added to cart.")
    return redirect('shop:cart_detail')

def cart_remove(request, product_id):
    cart = Cart(request)
    # The view passes product_id representing the dict item_key in POST or GET
    item_key = request.GET.get('key')
    if item_key:
        cart.remove(item_key)
        messages.success(request, "Item removed from cart.")
    return redirect('shop:cart_detail')

def cart_detail(request):
    return render(request, 'shop/cart.html')

def checkout(request):
    cart = Cart(request)
    if len(cart) == 0:
        messages.error(request, "Your cart is empty.")
        return redirect('shop:product_list')
        
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        address = request.POST.get('address')
        payment_method = request.POST.get('payment_method', 'whatsapp')
        
        if not (name and email and phone and address):
            messages.error(request, "Please fill in all checkout fields.")
            return render(request, 'shop/checkout.html', {
                'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
                'cart_total_kobo': int(cart.get_total_price() * 100),
            })
            
        # Create Order
        order = Order.objects.create(
            customer_name=name,
            email=email,
            phone=phone,
            shipping_address=address,
            total_amount=cart.get_total_price(),
            payment_method=payment_method,
            status='Pending'
        )
        
        # Create Order Items
        for item in cart:
            OrderItem.objects.create(
                order=order,
                product=item['product'],
                color=item['color'],
                size=item['size'],
                price=item['price'],
                quantity=item['quantity']
            )
            
        # Clear Cart from session
        cart.clear()
        
        # Handle payment redirect
        if payment_method == 'whatsapp':
            return redirect('shop:whatsapp_redirect', order_id=order.id)
        else:
            # Card fallback: Paystack verification or mock payment
            paystack_ref = request.POST.get('paystack_reference')
            if paystack_ref and settings.PAYSTACK_SECRET_KEY:
                import requests
                # Verify payment via Paystack API
                verify_url = f"https://api.paystack.co/transaction/verify/{paystack_ref}"
                headers = {
                    "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
                    "Content-Type": "application/json",
                }
                try:
                    response = requests.get(verify_url, headers=headers)
                    if response.status_code == 200:
                        res_data = response.json()
                        if res_data.get('status') and res_data['data'].get('status') == 'success':
                            # Check amount matches order total (in kobo)
                            paid_amount_kobo = res_data['data'].get('amount')
                            expected_amount_kobo = int(order.total_amount * 100)
                            if paid_amount_kobo >= expected_amount_kobo:
                                order.transaction_id = paystack_ref
                                order.status = 'Processing'  # Paid, ready for fulfillment
                                order.save()
                                messages.success(request, "Payment verified successfully via Paystack!")
                                return redirect('shop:order_confirmation', order_id=order.id)
                            else:
                                messages.error(request, f"Payment verification failed: paid amount ₦{paid_amount_kobo/100:,.2f} does not match order total ₦{order.total_amount:,.2f}.")
                        else:
                            messages.error(request, f"Paystack payment status was: {res_data['data'].get('status') or 'failed'}")
                    else:
                        messages.error(request, f"Paystack verification server returned status code: {response.status_code}")
                except Exception as e:
                    messages.error(request, f"Error verifying Paystack payment: {str(e)}")
                
                # If Paystack verification failed, we keep order status as Pending
                return redirect('shop:order_confirmation', order_id=order.id)
            else:
                # Mock payment fallback if no secret key is set
                order.transaction_id = f"TXN-{order.id}-MOCK"
                order.status = 'Processing'
                order.save()
                messages.success(request, "Order placed (Mock Payment fallback)!")
                return redirect('shop:order_confirmation', order_id=order.id)
            
    return render(request, 'shop/checkout.html', {
        'paystack_public_key': settings.PAYSTACK_PUBLIC_KEY,
        'cart_total_kobo': int(cart.get_total_price() * 100),
    })

def whatsapp_redirect(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    
    # Construct WhatsApp text message
    intro = f"Hello Amina's Vails, I would like to place an order (Order #{order.id})!\n\n"
    items_text = ""
    for item in order.items.all():
        items_text += f"• {item.product.name} - Qty: {item.quantity} [Color: {item.color}, Size: {item.size}] @ ${item.price} each\n"
    
    total = f"\nTotal Amount: ${order.total_amount}\n"
    shipping = f"\nDelivery Details:\nName: {order.customer_name}\nPhone: {order.phone}\nAddress: {order.shipping_address}\n"
    outro = "\nPlease confirm this order and provide payment instructions. Thank you!"
    
    full_message = intro + items_text + total + shipping + outro
    encoded_message = urllib.parse.quote(full_message)
    
    # WhatsApp owner number from env, default to a Nigerian number for illustration
    whatsapp_number = os.getenv('WHATSAPP_BUSINESS_NUMBER', '2348000000000')
    whatsapp_url = f"https://wa.me/{whatsapp_number}?text={encoded_message}"
    
    # Render beautiful redirect loader template
    return render(request, 'shop/whatsapp_redirect.html', {
        'order': order,
        'whatsapp_url': whatsapp_url
    })

def order_confirmation(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, 'shop/order_confirmation.html', {'order': order})

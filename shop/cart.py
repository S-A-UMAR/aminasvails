from decimal import Decimal
from django.conf import settings
from .models import Product

class Cart:
    def __init__(self, request):
        """
        Initialize the cart.
        """
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            # save an empty cart in the session
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, product, quantity=1, color='', size='', override_quantity=False):
        """
        Add a product to the cart or update its quantity.
        We index cart items by product_id combined with color and size, 
        so different variations of the same product are stored separately.
        """
        item_key = f"{product.id}_{color}_{size}"
        if item_key not in self.cart:
            self.cart[item_key] = {
                'product_id': product.id,
                'quantity': 0,
                'price': str(product.price),
                'color': color,
                'size': size
            }
        
        if override_quantity:
            self.cart[item_key]['quantity'] = quantity
        else:
            self.cart[item_key]['quantity'] += quantity
            
        self.save()

    def save(self):
        # mark the session as "modified" to make sure it gets saved
        self.session.modified = True

    def remove(self, item_key):
        """
        Remove an item from the cart.
        """
        if item_key in self.cart:
            del self.cart[item_key]
            self.save()

    def __iter__(self):
        """
        Iterate over the items in the cart and get the products from the database.
        """
        product_ids = [item['product_id'] for item in self.cart.values()]
        # get the product objects and add them to the cart
        products = Product.objects.in_bulk(product_ids)
        
        cart_copy = {k: v.copy() for k, v in self.cart.items()}
        for item_key, item in cart_copy.items():
            product = products.get(int(item['product_id']))
            if product:
                item['product'] = product
                item['price'] = Decimal(item['price'])
                item['total_price'] = item['price'] * item['quantity']
                item['key'] = item_key
                yield item

    def __len__(self):
        """
        Count all items in the cart.
        """
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_items(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(item['price']) * item['quantity'] for item in self.cart.values())

    def clear(self):
        # remove cart from session
        del self.session['cart']
        self.save()

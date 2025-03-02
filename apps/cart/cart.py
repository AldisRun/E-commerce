from django.conf import settings
from apps.store.models import Product

class Cart(object):
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)

        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}

        self.cart = cart

    def __iter__(self):
        product_ids = self.cart.keys()
        product_clean_ids = []

        for p in product_ids:
            product_clean_ids.append(int(p))

            try:
                self.cart[str(p)]['product'] = Product.objects.get(pk=p)
            except Product.DoesNotExist:
                self.cart[str(p)]['product'] = None

        for item in self.cart.values():
            price = float(item.get('price', 0))
            quantity = int(item.get('quantity', 0))
            item['total_price'] = price * quantity
            yield item

    def __len__(self):
        return sum(item.get('quantity', 0) for item in self.cart.values())

    def add(self, product, quantity=1, update_quantity=False):
        product_id = str(product.id)
        price = getattr(product, 'price', 0)

        if product_id not in self.cart:
            self.cart[product_id] = {'quantity': 0, 'price': price, 'id': product_id}

        if update_quantity:
            self.cart[product_id]['quantity'] = quantity
        else:
            self.cart[product_id]['quantity'] += 1

        self.save()
    
    def has_product(self, product_id):
        if str(product_id) in self.cart:
            return True
        else:
            return False

    def remove(self, product_id):
        product_id = str(product_id)
        if product_id in self.cart:
            del self.cart[product_id]
            self.save()

    def save(self):
        self.session[settings.CART_SESSION_ID] = self.cart
        self.session.modified = True

    def clear(self):
        del self.session[settings.CART_SESSION_ID]
        self.session.modified = True

    def get_total_length(self):
        return sum(int(item.get('quantity', 0)) for item in self.cart.values())

    def get_total_cost(self):
        return sum(float(item.get('price', 0)) * int(item.get('quantity', 0)) for item in self.cart.values())
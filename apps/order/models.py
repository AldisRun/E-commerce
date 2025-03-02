from django.db import models
from django.contrib.auth.models import User
from apps.store.models import Product


class Order(models.Model):
    ORDERED = 'ordered'
    SHIPPED = 'shipped'
    ARRIVED = 'arrived'

    STATUS_CHOICES = (
        (ORDERED, 'Ordered'),
        (SHIPPED, 'Shipped'),
        (ARRIVED, 'Arrived')
    )

    user = models.ForeignKey(User, related_name='orders', on_delete=models.SET_NULL, blank=True, null=True)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(max_length=100)  # Use EmailField for email validation
    address = models.CharField(max_length=100)
    zipcode = models.CharField(max_length=100)
    place = models.CharField(max_length=100)
    phone = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)

    paid = models.BooleanField(default=False)
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # Use DecimalField for monetary values
    used_coupon = models.CharField(max_length=50, blank=True, null=True)

    payment_intent = models.CharField(max_length=255)

    shipped_date = models.DateTimeField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=ORDERED)
 
    def __str__(self):
        return '%s' % self.first_name

    def get_total_quantity(self):
        return sum(int(item.quantity) for item in self.items.all())

class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='items', on_delete=models.CASCADE)  # Use CASCADE for deleting related items
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Use DecimalField for price
    quantity = models.IntegerField(default=1)

    def get_total_cost(self):
        return self.product.price * self.quantity

    def __str__(self):
        return '%s' % self.id
import json
import stripe
import coinbase_commerce

from coinbase_commerce.client import Client
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST
from django.template.loader import render_to_string

from paypalcheckoutsdk.core import PayPalHttpClient, SandboxEnvironment
from paypalcheckoutsdk.orders import OrdersCaptureRequest

from apps.cart.cart import Cart
from apps.order.views import render_to_pdf

from apps.order.utils import checkout

from .models import Product
from apps.order.models import Order
from apps.coupon.models import Coupon

from .utilities import decrement_product_quantity, send_order_confirmation


@require_POST
def create_checkout_session(request):
    data = json.loads(request.body)

    # Coupon

    coupon_code = data['coupon_code']
    coupon_value = 0

    if coupon_code != '':
        coupon = Coupon.objects.get(code=coupon_code)

        if coupon.can_use():
            coupon_value = coupon.value
            coupon.use()

    #

    cart = Cart(request)


    items = []

    for item in cart:
        product = item['product']

        price = int(product.price * 100)

        if coupon_value > 0:
            price = int(price * (int(coupon_value) / 100))

        obj = {
            'price_data': {
                'currency': 'eur',
                'product_data': {'name': product.title},
                'unit_amount': price
            },
            'quantity': item['quantity']
        }
        items.append(obj)
    
    gateway = data.get('gateway')
    session = ''
    order_id = ''

        #decrement_product_quantity(order)
        #send_order_confirmation(order)

    # ✅ Create Stripe Checkout Session
    if gateway == 'stripe':
        stripe.api_key = settings.STRIPE_API_KEY_HIDDEN
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=items,
            mode='payment',
            success_url='http://127.0.0.1:8000/cart/success/',
            cancel_url='http://127.0.0.1:8000/cart/'
        )
        print(f"✅ Stripe Session Created: {session.id}")  # Debugging output in terminal

    elif gateway == 'coinbase':
        total_cost = cart.get_total_cost()  # Get the original total cost

        if coupon_value > 0:
            total_cost = total_cost * ((100 - coupon_value) / 100)  # ✅ Apply coupon discount properly

        coinbase_client = Client(api_key=settings.COINBASE_API_KEY)
        charge = coinbase_client.charge.create(
            name='Order Payment',
            description='Payment for order',
            pricing_type='fixed_price',
            local_price={"amount": round(total_cost, 2), "currency": "EUR"},  # ✅ Correct price
            redirect_url='http://127.0.0.1:8000/cart/success/',
            cancel_url='http://127.0.0.1:8000/cart/'
        )
        session = {'id': charge.id, 'hosted_url': charge.hosted_url}
        print(f"✅ Coinbase Charge Created: {charge.id} | Amount: {round(total_cost, 2)} EUR")
            
        if not session['id']:
            print("❌ Error: Missing Coinbase charge ID!")
        


    # ✅ Save order with session ID instead of payment_intent
    orderid = checkout(request, data['first_name'], data['last_name'], data['email'], data['address'], data['zipcode'], data['place'], data['phone'])

    total_price = 0.00

    for item in cart:
        product = item['product']
        total_price = total_price + (float(product.price) * int(item['quantity']))

    if coupon_value > 0:
        total_price = total_price * (coupon_value / 100)

    #paid = True

    #if paid:
        #order = Order.objects.get(pk=orderid)
        #order.paid = True
        #order.paid_amount = cart.get_total_cost()
        #order.save()

        #decrement_product_quantity(order)
        #send_order_confirmation(order)

        cart.clear()

    if gateway == 'paypal':
        order_id = data['order_id']
        environment = SandboxEnvironment(client_id=settings.PAYPAL_API_KEY_PUBLISHABLE, client_secret=settings.PAYPAL_API_KEY_HIDDEN)
        client = PayPalHttpClient(environment)

        request = OrdersCaptureRequest(order_id)
        response = client.execute(request)

        total_price = cart.get_total_cost()  # Get the original total cost

        if coupon_value > 0:
            total_price = total_price * ((100 - coupon_value) / 100)  # ✅ Apply discount properly

        order = Order.objects.get(pk=orderid)
        order.paid_amount = round(total_price, 2)  # ✅ Store the correct discounted price
        order.used_coupon = coupon_code

        if response.result.status == 'COMPLETED':
            order.paid = True
            order.payment_intent = order_id
            order.save()

            decrement_product_quantity(order)
            send_order_confirmation(order)
        else:
            order.paid = False
            order.save()


    order = Order.objects.get(pk=orderid)
    if gateway == 'coinbase':
        order.payment_intent = session['id']
        order.paid = False
    else:
        order.payment_intent = session.id  # ✅ Store session ID
        order.paid_amount = total_price
        order.used_coupon = coupon_code
        order.save()


    if gateway == 'coinbase':
        return JsonResponse({'sessionId': session['id'], 'hosted_url': session['hosted_url']})  # ✅ Include hosted_url for Coinbase
    else:
        return JsonResponse({'sessionId': session['id']})  # ✅ Keep Stripe response the same


def api_add_to_cart(request):
    data = json.loads(request.body)
    jsonresponse = {'success': True}
    product_id = data['product_id']
    update = data['update']
    quantity = data['quantity']

    cart = Cart(request)

    product = get_object_or_404(Product, pk=product_id)

    if not update:
        cart.add(product=product, quantity=1, update_quantity=False)
    else:
        cart.add(product=product, quantity=quantity, update_quantity=True)

    return JsonResponse(jsonresponse)


def api_remove_from_cart(request):
    data = json.loads(request.body)
    jsonresponse = {'success': True}
    product_id = str(data['product_id'])

    cart = Cart(request)
    cart.remove(product_id)

    return JsonResponse(jsonresponse)
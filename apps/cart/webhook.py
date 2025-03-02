import json
import stripe

from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from .cart import Cart

from apps.order.models import Order
from apps.store.utilities import decrement_product_quantity, send_order_confirmation

@csrf_exempt
def webhook(request):
    payload = request.body
    event = None

    stripe.api_key = settings.STRIPE_API_KEY_HIDDEN

    try:
        event = stripe.Event.construct_from(json.loads(payload), stripe.api_key)
    except ValueError as e:
        return HttpResponse(status=400)  # Invalid payload

    if event.type == 'checkout.session.completed':  # ✅ Capture payment intent later
        session = event.data.object

        print(f"✅ Stripe Checkout Completed: {session.id}")

        try:
            order = Order.objects.get(payment_intent=session.id)  # ✅ Match order by session.id
            order.paid = True  # ✅ Mark order as paid
            order.payment_intent = session.payment_intent  # ✅ Update payment_intent
            order.save()
        except Order.DoesNotExist:
            print("❌ Order not found for session:", session.id)
        
        decrement_product_quantity(order)
        send_order_confirmation(order)

        #html = render_to_string('order_confirmation.html', {'order': order})
        #send_mail('Order confirmation', 'Your order is successful!', 'noreply@mygadgets.com', ['mail@mygadgets.com', order.email], fail_silently=False, html_message=html)

    return HttpResponse(status=200)
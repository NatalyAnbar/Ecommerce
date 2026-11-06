from django.core.mail import send_mail

def send_order_created_email(order):
    """Email the customer the details of the order they just placed."""

    items = [f'- {item.quantity} x {item.product.name_en} at {item.unit_price}' 
             for item in order.order_items.all()]

    items_text = '\n'.join(items)
        
    send_mail(
            subject = f'Order {order.id} received',

            message = (
            'Thank you for your order!\n\n'
            f'Order {order.id}\n'
            f'{items_text}\n'
            f'Total: {order.total_price}\n\n'
            'Your order is waiting for payment.'
            ),

            from_email = None,
            recipient_list = [order.user.email] 
            )



def send_payment_received_email(payment):
    """Email the customer that their payment went through."""

    send_mail(
        subject = f'Payment received for order {payment.order_id}',

        message = (
            'We received your payment.\n\n'
            f'Order {payment.order_id}\n'
            f'Amount: {payment.amount}\n'
            f'Card: **** {payment.card_last4}\n'
            f'Reference: {payment.transaction_id}\n\n'
            'Your order is now paid.'
        ),

        from_email = None,
        recipient_list = [payment.order.user.email]
    )



def send_order_cancelled_email(order):
    """Email the customer that their order was cancelled."""

    send_mail(
        subject = f'Order {order.id} cancelled',

        message = (
            f'Your order {order.id} has been cancelled.\n\n'
            'No payment was taken for this order.'
        ),

        from_email = None,
        recipient_list =  [order.user.email]    
    )
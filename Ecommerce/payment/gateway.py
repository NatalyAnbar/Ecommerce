"""
A simulated payment gateway.

Stands in for a real provider such as Stripe: the rest of the app only calls
charge_card(), so a real gateway can replace this file later.
"""

from . import models

# Test cards, the same numbers Stripe uses in test mode
SUCCESS_CARD = '4242424242424242'
DECLINED_CARD = '4000000000000002'


def charge_card(card_number):
    """
    Try to charge a card and return the resulting payment status.

    Only the success test card is charged. The declined test card, and any
    card the gateway doesn't know, is declined: when in doubt, never take money.
    """
    
    if card_number == SUCCESS_CARD:
        return models.Payment.Status.SUCCEEDED

    return models.Payment.Status.FAILED

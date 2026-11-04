import pytest

from payment.gateway import DECLINED_CARD, SUCCESS_CARD, charge_card
from payment.models import Payment


@pytest.mark.parametrize('card_number, expected', [
    (SUCCESS_CARD, Payment.Status.SUCCEEDED),
    (DECLINED_CARD, Payment.Status.FAILED),
    ('1111222233334444', Payment.Status.FAILED),
])
def test_charge_card(card_number, expected):
    assert charge_card(card_number) == expected
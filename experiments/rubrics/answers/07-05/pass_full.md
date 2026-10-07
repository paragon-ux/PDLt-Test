```python
from enum import Enum
from typing import assert_never

class OrderStatus(Enum):
    PENDING = "pending"; CONFIRMED = "confirmed"; SHIPPED = "shipped"
    DELIVERED = "delivered"; RETURNED = "returned"; CANCELLED = "cancelled"

class PaymentStatus(Enum):
    PENDING = "pending"; RECEIVED = "received"; FAILED = "failed"

def process_order(order):
    status = OrderStatus(order['status'])          # unknown strings raise ValueError
    payment = PaymentStatus(order.get('payment', 'pending'))
    match status:
        case OrderStatus.PENDING:
            if payment is PaymentStatus.RECEIVED: status = OrderStatus.CONFIRMED
            elif payment is PaymentStatus.FAILED: status = OrderStatus.CANCELLED
        case OrderStatus.CONFIRMED:
            if order.get('shipped'): status = OrderStatus.SHIPPED
        case OrderStatus.SHIPPED:
            if order.get('delivered'): status = OrderStatus.DELIVERED
        case OrderStatus.DELIVERED:
            if order.get('returned'): status = OrderStatus.RETURNED
        case OrderStatus.RETURNED | OrderStatus.CANCELLED:
            pass                                    # terminal states, handled explicitly
        case _:
            assert_never(status)
    order['status'] = status.value
    return order
```
Tests:
```python
import pytest
def test_transitions():
    assert process_order({'status': 'pending', 'payment': 'received'})['status'] == 'confirmed'
    assert process_order({'status': 'pending', 'payment': 'failed'})['status'] == 'cancelled'
    assert process_order({'status': 'delivered', 'payment': 'received', 'returned': True})['status'] == 'returned'

def test_original_bug_returned_and_unknown():
    # The old code let 'returned' (and any typo like 'shiped') fall through silently.
    assert process_order({'status': 'returned', 'payment': 'received'})['status'] == 'returned'
    with pytest.raises(ValueError):
        process_order({'status': 'shiped', 'payment': 'received'})
```

```python
from enum import Enum

class OrderStatus(Enum):
    PENDING = "pending"; CONFIRMED = "confirmed"; SHIPPED = "shipped"; DELIVERED = "delivered"; CANCELLED = "cancelled"

class PaymentStatus(Enum):
    RECEIVED = "received"; FAILED = "failed"

def process_order(order):
    s = order['status']
    if s == OrderStatus.PENDING.value:
        if order['payment'] == PaymentStatus.RECEIVED.value: order['status'] = OrderStatus.CONFIRMED.value
        elif order['payment'] == PaymentStatus.FAILED.value: order['status'] = OrderStatus.CANCELLED.value
    elif s == OrderStatus.CONFIRMED.value and order['shipped']: order['status'] = OrderStatus.SHIPPED.value
    elif s == OrderStatus.SHIPPED.value and order['delivered']: order['status'] = OrderStatus.DELIVERED.value
    return order
```
Test: a pending order with received payment becomes confirmed.

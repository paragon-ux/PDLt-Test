import enum

class OrderStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    RETURNED = "returned"

class PaymentStatus(enum.Enum):
    RECEIVED = "received"
    FAILED = "failed"

def process_order(order: dict) -> dict:
    """Process an order using exhaustive Enum comparisons.

    The *order* dict is expected to contain:
        - 'status': an OrderStatus value
        - 'payment': a PaymentStatus value
        - 'shipped': bool (optional)
        - 'delivered': bool (optional)
        - 'returned': bool (optional)
    The function updates the 'status' field appropriately and returns the dict.
    """
    status = order.get('status')
    payment = order.get('payment')

    if status == OrderStatus.PENDING:
        if payment == PaymentStatus.RECEIVED:
            order['status'] = OrderStatus.CONFIRMED
        elif payment == PaymentStatus.FAILED:
            order['status'] = OrderStatus.CANCELLED
        else:
            raise ValueError('Unexpected payment status')
    elif status == OrderStatus.CONFIRMED:
        if order.get('shipped'):
            order['status'] = OrderStatus.SHIPPED
        else:
            # remain CONFIRMED until shipped
            pass
    elif status == OrderStatus.SHIPPED:
        if order.get('delivered'):
            order['status'] = OrderStatus.DELIVERED
        else:
            # remain SHIPPED until delivered
            pass
    elif status == OrderStatus.DELIVERED:
        if order.get('returned'):
            order['status'] = OrderStatus.RETURNED
        else:
            # remain DELIVERED until returned
            pass
    elif status == OrderStatus.CANCELLED:
        # terminal state, no change
        pass
    elif status == OrderStatus.RETURNED:
        # terminal state, no change
        pass
    else:
        raise ValueError('Unexpected order status')

    return order

# Unit test reproducing the original bug
if __name__ == "__main__":
    # Original buggy scenario: order is delivered and returned flag is True,
    # but the older implementation never updated the status to 'returned'.
    order = {
        'status': OrderStatus.DELIVERED,
        'payment': PaymentStatus.RECEIVED,
        'shipped': True,
        'delivered': True,
        'returned': True,
    }
    updated = process_order(order)
    assert updated['status'] == OrderStatus.RETURNED, f"Expected RETURNED, got {updated['status']}"
    print('Test passed: delivered->returned transition handled correctly.')

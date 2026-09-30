import enum
import unittest

class OrderStatus(enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    RETURNED = "returned"
    CANCELLED = "cancelled"

class PaymentStatus(enum.Enum):
    RECEIVED = "received"
    FAILED = "failed"
    PENDING = "pending"
    REFUNDED = "refunded"

def process_order(order):
    """Process an order dict updating its status based on current state.
    The function expects:
        order["status"] as OrderStatus
        order["payment"] as PaymentStatus
        order["shipped"] as bool (optional)
        order["delivered"] as bool (optional)
        order["returned"] as bool (optional)
    Returns the mutated order.
    """
    status = order["status"]
    payment = order["payment"]

    # Exhaustive matching on OrderStatus
    if status == OrderStatus.PENDING:
        if payment == PaymentStatus.RECEIVED:
            order["status"] = OrderStatus.CONFIRMED
        elif payment == PaymentStatus.FAILED:
            order["status"] = OrderStatus.CANCELLED
        else:
            # No other payment states are valid for pending
            raise ValueError(f"Invalid payment state {payment} for pending order")
    elif status == OrderStatus.CONFIRMED:
        if order.get("shipped"):
            order["status"] = OrderStatus.SHIPPED
        else:
            # Stay in confirmed until shipped flag is true
            pass
    elif status == OrderStatus.SHIPPED:
        if order.get("delivered"):
            order["status"] = OrderStatus.DELIVERED
        else:
            pass
    elif status == OrderStatus.DELIVERED:
        if order.get("returned"):
            order["status"] = OrderStatus.RETURNED
        else:
            pass
    elif status == OrderStatus.RETURNED:
        # Terminal state – nothing to do
        pass
    elif status == OrderStatus.CANCELLED:
        # Terminal state – nothing to do
        pass
    else:
        # Exhaustive guard – should never happen
        raise ValueError(f"Unhandled OrderStatus: {status}")

    # Exhaustive matching on PaymentStatus (example usage)
    if payment == PaymentStatus.RECEIVED:
        pass  # already handled in pending branch
    elif payment == PaymentStatus.FAILED:
        pass
    elif payment == PaymentStatus.PENDING:
        pass
    elif payment == PaymentStatus.REFUNDED:
        pass
    else:
        raise ValueError(f"Unhandled PaymentStatus: {payment}")

    return order

class TestProcessOrder(unittest.TestCase):
    def test_returned_status_bug(self):
        order = {
            "status": OrderStatus.RETURNED,
            "payment": PaymentStatus.REFUNDED,
            "shipped": True,
            "delivered": True,
            "returned": True,
        }
        # The original bug was that returned status fell through unnoticed.
        # Here we expect the function to leave the status unchanged (still RETURNED) and not raise.
        processed = process_order(order.copy())
        self.assertEqual(processed["status"], OrderStatus.RETURNED)

if __name__ == "__main__":
    unittest.main()

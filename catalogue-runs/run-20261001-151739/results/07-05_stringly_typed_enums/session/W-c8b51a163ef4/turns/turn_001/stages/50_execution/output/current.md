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

def process_order(order):
    """Process an order using enum‑based status handling.

    The function mutates the supplied ``order`` dict and returns it.
    All enum members are handled exhaustively; no silent fall‑through.
    """
    status = OrderStatus(order["status"]) if isinstance(order["status"], str) else order["status"]
    payment = PaymentStatus(order["payment"]) if isinstance(order["payment"], str) else order["payment"]

    if status == OrderStatus.PENDING:
        if payment == PaymentStatus.RECEIVED:
            order["status"] = OrderStatus.CONFIRMED
        elif payment == PaymentStatus.FAILED:
            order["status"] = OrderStatus.CANCELLED
        else:
            # Exhaustive handling – any other payment state is unexpected
            raise ValueError(f"Unhandled payment status {payment} for pending order")
    elif status == OrderStatus.CONFIRMED:
        if order.get("shipped"):
            order["status"] = OrderStatus.SHIPPED
        else:
            # Stay in CONFIRMED until shipped flag is set
            order["status"] = OrderStatus.CONFIRMED
    elif status == OrderStatus.SHIPPED:
        if order.get("delivered"):
            order["status"] = OrderStatus.DELIVERED
        else:
            order["status"] = OrderStatus.SHIPPED
    elif status == OrderStatus.DELIVERED:
        if order.get("returned"):
            order["status"] = OrderStatus.RETURNED
        else:
            order["status"] = OrderStatus.DELIVERED
    elif status == OrderStatus.RETURNED:
        # Terminal state – nothing to do
        pass
    elif status == OrderStatus.CANCELLED:
        # Terminal state – nothing to do
        pass
    else:
        # Exhaustive handling – any unknown status is an error
        raise ValueError(f"Unhandled order status {status}")

    return order

class TestProcessOrder(unittest.TestCase):
    def test_returned_status_handled(self):
        # Create an order that reaches the delivered state then is returned
        order = {
            "status": OrderStatus.PENDING,
            "payment": PaymentStatus.RECEIVED,
            "shipped": True,
            "delivered": True,
            "returned": True,
        }
        # First transition: PENDING -> CONFIRMED
        order = process_order(order)
        self.assertEqual(order["status"], OrderStatus.CONFIRMED)
        # Second transition: CONFIRMED -> SHIPPED (shipped flag already true)
        order = process_order(order)
        self.assertEqual(order["status"], OrderStatus.SHIPPED)
        # Third transition: SHIPPED -> DELIVERED (delivered flag already true)
        order = process_order(order)
        self.assertEqual(order["status"], OrderStatus.DELIVERED)
        # Fourth transition: DELIVERED -> RETURNED (returned flag true)
        order = process_order(order)
        self.assertEqual(order["status"], OrderStatus.RETURNED)
        # Subsequent calls should keep the order in RETURNED state without error
        order = process_order(order)
        self.assertEqual(order["status"], OrderStatus.RETURNED)

if __name__ == "__main__":
    unittest.main()

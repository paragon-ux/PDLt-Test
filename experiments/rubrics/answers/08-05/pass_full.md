**Story 1: Product search.** As a shopper, I want to search products by name so that I can find what I'm looking for quickly. Acceptance: partial and case-insensitive matches; results within 300 ms; empty-state message.

**Story 2: Personalized history and recommendations.** As a returning shopper, I want to see my recent orders and products recommended from my purchase history so that I can reorder or discover related items. Acceptance: last 5 orders shown; recommendations exclude items already owned; works with no history (fallback to popular items).

**Story 3: Inventory and reservation.** As a shopper viewing a product, I want to see real-time stock at every warehouse and reserve an item for up to 24 hours so that I can secure it before buying. Acceptance: stock refreshes within seconds; a reservation decrements available stock and expires automatically after 24 hours.

These share no data dependencies at delivery time: search needs the catalogue index, personalization needs order history, reservation needs the inventory service.

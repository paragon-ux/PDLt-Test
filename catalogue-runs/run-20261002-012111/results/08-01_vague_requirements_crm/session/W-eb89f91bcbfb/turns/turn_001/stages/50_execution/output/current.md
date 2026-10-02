Core Entities:
1. Customer
   - CustomerID (unique identifier)
   - Name
   - Email
   - Phone
   - Address
   - CreatedDate
2. Contact
   - ContactID
   - CustomerID (foreign key)
   - Name
   - Relationship (e.g., primary, secondary)
   - Email
   - Phone
3. Interaction
   - InteractionID
   - CustomerID (foreign key)
   - ContactID (foreign key, optional)
   - InteractionType (call, email, meeting, etc.)
   - DateTime
   - Subject
   - Notes
4. Opportunity
   - OpportunityID
   - CustomerID (foreign key)
   - Name
   - Stage (prospecting, qualified, proposal, won, lost)
   - Amount
   - CloseDate
   - OwnerID
5. User (CRM user/agent)
   - UserID
   - Username
   - Email
   - Role (admin, sales, support)
   - AssignedCustomers (list of CustomerIDs)

Business Rules / Constraints:
1. Every Customer must have a unique CustomerID.
2. Email fields must be in valid email format.
3. Interaction records cannot be created for a non‑existent Customer.
4. Opportunities can only be associated with active Customers.
5. Only Users with the "admin" role may delete Customer records.
6. The sum of Opportunity amounts for a Customer cannot exceed a configurable credit limit.
7. Interaction dates cannot be in the future.
8. When a Customer is marked as "inactive", no new Opportunities may be added.

Edge Cases:
1. Importing a Customer list with duplicate Email addresses.
2. Recording an Interaction where the Contact belongs to a different Customer.
3. Changing a Customer's status from active to inactive while having open Opportunities.
4. Deleting a User who is the sole owner of several Opportunities.
5. Handling extremely large Notes fields that exceed typical storage limits.

Clarifying Questions:
1. What are the required compliance or data‑privacy standards for storing personal contact information?
2. Should the CRM support multi‑currency handling for Opportunity amounts, and if so, what exchange‑rate management is needed?
3. Are there any integration requirements with external systems (e.g., email servers, telephony, accounting software) that would affect entity design?

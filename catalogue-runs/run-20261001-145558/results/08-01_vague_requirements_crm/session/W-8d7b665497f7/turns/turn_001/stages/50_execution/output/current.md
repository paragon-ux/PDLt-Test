**Core Entities and Attributes**
1. **Customer**
   - CustomerID (unique identifier)
   - Name
   - Email
   - PhoneNumber
   - Address
   - Company
   - Industry
   - Status (e.g., Active, Inactive)
2. **Contact**
   - ContactID
   - CustomerID (foreign key)
   - FirstName
   - LastName
   - Email
   - PhoneNumber
   - Role
   - PreferredContactMethod
3. **Opportunity**
   - OpportunityID
   - CustomerID (foreign key)
   - Title
   - Value
   - Stage (e.g., Prospecting, Qualification, Proposal, Won, Lost)
   - CloseDate
   - OwnerUserID
   - Probability
4. **Interaction**
   - InteractionID
   - CustomerID (foreign key)
   - ContactID (foreign key, optional)
   - InteractionType (Call, Email, Meeting, Note)
   - DateTime
   - Subject
   - Outcome
   - RecordedByUserID
5. **User**
   - UserID
   - Username
   - Email
   - Role (e.g., SalesRep, Manager, Admin)
   - HireDate
   - ActiveFlag

**Business Rules / Constraints**
1. A Customer must have a unique Email address.
2. An Opportunity cannot be created for a Customer whose Status is **Inactive**.
3. The **Value** of an Opportunity must be a non‑negative number.
4. The **CloseDate** of an Opportunity cannot be earlier than its creation date.
5. Interaction records must reference an existing Customer; if a Contact is referenced, it must belong to that Customer.
6. Only users with the **Manager** or **Admin** role can delete Customer records.
7. The **Probability** field of an Opportunity must be between 0 and 100 inclusive.
8. A Contact’s Email must be unique across all contacts.

**Potential Edge Cases**
1. Importing a large CSV of legacy contacts where many rows contain duplicate Email addresses.
2. A Customer with an extremely large number of Opportunities (e.g., >10,000) that could cause performance issues on list queries.
3. An Interaction that references a Contact that was later merged or deleted, leaving a dangling foreign key.
4. A User role change mid‑transaction that affects permission checks for the same operation.
5. Time‑zone differences causing an Interaction’s DateTime to appear in the future or past relative to the system clock.

**Clarifying Questions**
1. What level of data privacy or compliance (e.g., GDPR, CCPA) must the CRM adhere to, especially regarding personal contact information?
2. Should the system support multi‑currency handling for Opportunity values, and if so, what exchange‑rate management is required?
3. Are there any integration requirements with external systems (e.g., email services, marketing automation platforms) that need to be considered during implementation?

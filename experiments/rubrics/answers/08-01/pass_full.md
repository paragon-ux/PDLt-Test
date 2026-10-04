**Entities**
1. Account: id, name, industry, size, owner_id, billing_address, created_at.
2. Contact: id, account_id, first_name, last_name, email (unique per account), phone, title, owner_id.
3. Lead: id, name, company, email, source, status (new/working/qualified/disqualified), owner_id.
4. Opportunity: id, account_id, name, amount, currency, stage, close_date, probability, owner_id.
5. Activity: id, type (call/email/meeting/task), subject, due_at, completed_at, related_to (contact/opportunity), owner_id.
6. User: id, name, email, role (rep/manager/admin), team_id.

**Business rules**
1. Converting a qualified lead creates a Contact, an Account (or links an existing one) and optionally an Opportunity; the lead becomes read-only.
2. Every Account, Contact, Lead and Opportunity has exactly one owner (a User).
3. Opportunity stages advance Prospecting → Qualification → Proposal → Negotiation → Closed Won/Lost; skipping requires a manager.
4. Closed opportunities are immutable except by admins.
5. An opportunity's amount must be ≥ 0 and its close date set before reaching Proposal.
6. Contact email addresses are unique within an account.
7. Reps see only their own and their team's records; managers see their team's; admins see all.
8. Every stage change is recorded in an audit log with user and timestamp.
9. Deleting an Account requires reassigning or deleting its contacts and opportunities.

**Edge cases**
1. Duplicate contacts/accounts from imports or two reps; merge rules.
2. A rep leaves: bulk ownership transfer of their records and open activities.
3. Multi-currency opportunities and pipeline totals.
4. Timezones for activity due dates across regions.
5. GDPR deletion requests vs the audit log.
6. Two users editing the same opportunity concurrently.

**Clarifying questions**
1. How many users and records, and is it single- or multi-tenant?
2. Which integrations are required (email, calendar, marketing automation, billing)?
3. What is the actual sales process: stages, approval steps, forecasting needs?
4. What compliance requirements apply (GDPR, data residency)?

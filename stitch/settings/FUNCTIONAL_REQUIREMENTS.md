# Settings Page -- Functional Requirements

Page: `/settings`
Last updated: 2026-03-28

---

## REQ-S01: Research Keywords Input
The user can enter a comma-separated list of research interest keywords.
These keywords are persisted via the `updateUserConfig` API endpoint.
On load (when email is provided), previously saved keywords are populated.

## REQ-S02: Email Address Input
The user can enter their email address.
The email is used both as the user identifier for config storage and as the notification target.

## REQ-S03: Load Existing Configuration
A "Load" button fetches the user's existing configuration from the API using their email.
If no configuration exists (404), the form remains empty without showing an error.

## REQ-S04: Notification Frequency Selection
The user can select a notification frequency from a dropdown:
- Daily Digest
- Weekly Summary
- Real-time (High Volume)

## REQ-S05: Save Configuration
A primary "Save Changes" button persists the current form state via `updateUserConfig`.
Success and error states are communicated via toast notifications.
The button shows a loading state while saving.

## REQ-S06: Category Defaults
Categories are currently hardcoded to a default set of CS subcategories:
`cs.AI, cs.LG, cs.CL, cs.CV, cs.RO, cs.MA, cs.NE, cs.IR, cs.SI, cs.HC, cs.CY`
(Future: user-selectable category picker -- out of scope for this phase.)

## REQ-S07: Form Validation
Email field accepts standard email format.
Keywords field accepts free text (comma-separated).
Save is disabled while a save operation is in progress.

## REQ-S08: Page Layout
Settings page renders within the app shell (sidebar + main content area).
Maximum width is constrained for readability (max-w-2xl).

---

## Traceability

| REQ | Component / Element |
|------|---------------------|
| REQ-S01 | Keywords text input |
| REQ-S02 | Email text input |
| REQ-S03 | Load button |
| REQ-S04 | Frequency select dropdown |
| REQ-S05 | Save Changes button |
| REQ-S06 | Hardcoded categories array |
| REQ-S07 | Form disabled state |
| REQ-S08 | Page container |

# Architecture

Django 5.2 LTS / Python 3.13 modular monolith. Apps: accounts, configuration,
campsites, reservations, notifications and audit. Server-rendered templates with
locally vendored Bootstrap 5, HTMX (evaluation and response scripts disabled) and
small external JavaScript. No frontend service, SaaS or public API.

One occupancy row represents either a reservation or a maintenance block. Its bounded,
nonempty PostgreSQL daterange is canonical; active rows have a GiST exclusion on
(campsite, overlapping range). No second independent source of occupancy truth.
Services own policies, authorization, transitions, locks and audit. Views bind forms
and call services; admin must never edit occupancy directly.

Lock order: configuration → acting/subject accounts in stable primary-key order →
campsite → occupancy. A conservative configuration lock initially serializes policy
mutations and bookings, acceptable at this scale; measure before optimizing. Mutations
and in-app notifications commit atomically. External delivery, when implemented, must
use a durable outbox after commit, never send inside the booking transaction.

Runtime and migration database identities are separate. Provision btree_gist using a
controlled administrator; normal runtime cannot migrate. TLS-only Caddy is the sole
public container. Caddy and PostgreSQL share no network. Host storage encryption and
backup recovery keys are operator responsibilities, not claims made by Docker secrets.

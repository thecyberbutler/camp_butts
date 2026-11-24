# Security decision register

All entries dated 2026-11-24; review before production and by 2026-12-24.
No project-owner security exception has been requested, granted or inferred.
These decisions implement the supplied security requirements; they do not waive them.

| ID | Decision and justification | Alternatives / security impact | Residual risk | Approval status / rollback |
|---|---|---|---|---|
| SD-001 | Modular Django monolith; no managed services | Reject SaaS and extra service boundaries | Host remains trust root | Required architecture; no exception; revert unpublished code |
| SD-002 | Unique per-environment file secrets, fail closed on missing/weak/overpermissive files | Reject plaintext env values and built-in defaults | Compose mounts are not encrypted; host encryption needed | Required protection; rotate and revoke on rollback |
| SD-003 | Allauth + Argon2id + Axes, separate Fernet MFA key | Reject custom authentication/cryptography; Fernet from cryptography | Encryption does not protect compromised runtime | Required protection; preserve enrollment and keys during rollback |
| SD-004 | Approval-first registration; SMTP-dependent verification/recovery stay unavailable without SMTP | No automatic verification fallback | Human approval identity checks required; email not trusted without verification | Conservative initial mode; no exception |
| SD-005 | Unified daterange exclusion for reservation and block | Reject check-then-insert only and separate block tables | Privileged DB owner can change constraints | Required integrity; never drop constraint to roll back app |
| SD-006 | Split DB credentials; append-only runtime audit; private networks; non-root containers | Reject superuser runtime and public DB/web ports | Host/root DB compromise | Required isolation; stop services before any rollback |
| SD-007 | No raw SVG or arbitrary uploads until safe processing is tested | Controlled numeric map coordinates and escaped labels | Feature incomplete until validated | Surface stays closed; no exception |
| SD-008 | Proposed camper 30-minute idle / 12-hour absolute; privileged 15-minute idle / 4-hour absolute; reauth 5 minutes | Reject indefinite sessions; no increases without owner approval | Stolen active sessions valid within bound; review before release | Conservative initial ceilings, not recorded owner approval |

Production release requires all gates in PROJECT_SPEC.md. A missing test, unavailable
scanner or unavailable database is not a reason to relax a requirement.

# Security policy

This application is under development. There is no supported production release yet.
Python 3.13, Django 5.2 LTS and PostgreSQL 17 are the selected supported series;
always apply supported security patches and rerun the release gates.

Report suspected vulnerabilities privately to the project owner through an established
private contact channel. A dedicated reporting address must be published before release.
Do not post credentials, personal data, exploit payloads containing real data, or security
details in public issues. Provide affected version, impact and a synthetic reproduction.
Coordinate disclosure after containment and remediation; do not claim a response SLA
that the operator has not established.

Security takes precedence over functionality. No security exception is authorized by
ordinary development permission. Record any explicit owner exception, scope, risk,
mitigation, review date and rollback in docs/security-decisions.md. Applicable unresolved
high/critical findings block release. Automated scans are evidence, not a guarantee.

Update by reviewing trusted release advisories, refreshing Poetry locks or image digests,
reviewing transitive changes/licenses, and executing tests/scans and isolated deployment
and restore checks before promotion. Never disable safeguards to get an update working.

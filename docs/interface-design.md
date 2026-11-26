# Interface design

The 2026-11-25 visual update uses the existing Django templates, Bootstrap CSS, HTMX and
system fonts. No frontend build system, additional dependency, remote font, image service,
tracking script or new JavaScript is introduced.

## Shared presentation

`static/css/app.css` defines forest-green actions, warm neutral surfaces, rounded controls,
subtle shadows, clear typography, and short color/shadow/hover transitions. Shared navigation,
account layouts and reusable cards carry the design through public, camper, authentication,
Google connection, reservation, staff-table and error pages. Names and campground information
continue to come from escaped tenant configuration; the illustration is generic decoration,
not a representation of any campground's actual sites or map.

The locally authored `static/images/camp-landscape.svg` and brand-mark component contain only
fixed vector geometry. They do not accept uploaded SVG, external resources or executable
content. The existing controlled availability map keeps its accessible status colors/labels.

The account navigation and longer reference information use native `details`/`summary`,
which work without JavaScript. Main links remain available at narrow widths. Forms preserve
labels, validation errors, field names, actions and CSRF handling. The small allauth button
presentation override retains the upstream attributes/slots and distinguishes dangerous
buttons; review it with the existing allauth compatibility checks on dependency upgrades.

## Accessibility and important notices

- Keep keyboard focus outlines and native keyboard disclosure behavior visible.
- Honor `prefers-reduced-motion: reduce` by removing transitions/animations.
- Use text labels alongside statuses; do not encode availability or danger through color alone.
- Preserve the prominent red development/test banner, including auth and generic error pages.
- Keep online-booking closure visible outside collapsible reference information.
- Keep wide staff tables inside labeled, keyboard-focusable scrolling regions.
- Preserve escaped policy text and required registration agreement controls.
- Never use CSS to substitute for server-side permission checks.

The browser review covers synthetic rendered pages at 1440, 390 and 320 pixels: no horizontal
page overflow, loaded local assets, form labels, native account-menu keyboard operation,
visible focus and reduced motion. Local screenshots use sanitized test responses with hidden
form secrets removed; no real account, session, OAuth token or MFA secret is included.
This is a visual/rendering check, not a browser end-to-end authentication or accessibility
certification. Screen-reader testing, additional browser engines and complete accessibility
acceptance remain outstanding.

## Validation and deployment

Run the existing PostgreSQL suite as documented in README, including authentication/MFA,
Google, tenant isolation, CSRF, banner and concurrency regressions. Review desktop/mobile
home, directory, login/signup, account security, Google connections, reservation forms,
camper dashboard, operations/calendar and generic error pages. Check keyboard focus and
reduced-motion preference before publishing a changed design.

The initial design task committed the feature locally. After owner review and a separate
“scan and deploy” request, release `0.1.0-alpha.20261125-5815b9993895` was scanned, published
and deployed on the AWS test instance. Public checks confirmed exact CSS/artwork hashes,
modern home/login pages, Google sign-in entry controls, test banner and booking closure.
See `aws-ui-deployment-transcript.md` for the disclosed, executed transcript and validation.
Production gates and unverified Google human acceptance/recovery work remain in force.

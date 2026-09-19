# Asterisk interface direction: evidence report

18 September 2026. Working product iteration; not a new evaluation release.

Three concepts were considered: dense lab console, notebook-style narrative, and a focused evidence report. The report direction best serves the actual task: establish what was measured, inspect a source pair, review the meaning of an identity, and keep the record. It retains Asterisk's paper/green character while giving the result stronger hierarchy.

References: Linear's interface redesign, https://linear.app/now/how-we-redesigned-the-linear-ui (hierarchy and density); Observable Markdown cells, https://observablehq.com/documentation/cells/markdown (narrative alongside data). These informed structure, not copied layouts or assets.

## Implemented

- Outcome-first receipt overview with exact counts and a proportional evaluation bar. Missing coverage, blocked checks and pending confirmation remain distinct; no invented improvement or accuracy metric.
- Four keyboard-accessible views: Overview, Source evidence, Scope & assumptions, Execution record. Arrow keys, Home and End switch views; semantic tab/tabpanel relationships and visible focus.
- State-specific next action. Confirmation still requires explicit review and the original server validation.
- Source-row inspector appears above a bounded witness table; the displayed witness cap is explicit. Source integrity checks still run before rows are displayed.
- More readable navigation with full wrapped receipt names, actual outcome labels, selected state, and expandable mobile history.
- New-start page with a labeled illustrative sample pair, useful field examples and three-stage progress. Consents, errors and manual setup remain operational.
- Main claim and revision context are available in labeled disclosures on completed receipts, keeping the finding near the top. Full original interpretation/citations remain inspectable.
- Scoped workspace styling; companion public page uses the same palette. No remote fonts, analytics, animation dependency or new framework.

## Verification

Desktop, 768px tablet and 390px phone rendered and inspected. The initial render exposed the long witness-table jump; corrected by moving the inspector before a scroll-bounded table. Mobile navigation and keyboard tab changes exercised, including pending-confirmation routing. Phone and tablet document widths matched viewport width. Further verification recorded below after final checks.

This improves the interface; it does not establish human usability gains, fix the failed historical acceptance, or make the hackathon submission complete.

Final checks: 230 backend tests passed, 9 existing skips; frontend module syntax passed. Existing synthetic files load correctly; manual mode enables its submit action and disables proposal-upload consent without a model call. The witness inspector verified actual source rows on the retained PTB-XL case. Pending-confirmation action opens assumptions, and ArrowRight selects the next tab. The mobile receipt menu exposes real history entries. Historic contracts outside primitive-v3/v4 retain the original labeled presentation.

Measured contrast ratios: body muted text on paper 4.99:1; muted navigation text 4.59:1; primary action 9.70:1; violation label 5.89:1; pending label 5.83:1. Large decorative heading accent 3.94:1. No new remote executions or inference spend. Original evidence bytes and decision logic remain unchanged.

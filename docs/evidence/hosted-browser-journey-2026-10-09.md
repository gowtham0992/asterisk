# Hosted browser journey — 9 October 2026

Chrome successfully opened the hosted workspace after the in-app browser had blocked it. This closes the browser-access limitation in the preceding HTTP journey report.

## Observed journey

1. Loaded the shipped fictional patient/slide example; reviewed file roles and selected identifier columns.
2. Previewed the outbound payload before sending it.
3. Sent one preparation request to Nemotron 3 Super through Nebius. The UI reported 6.91 seconds and 3,099 tokens; it returned the documented 11-character patient prefix on the first attempt.
4. Inspected the proposed sources, claim binding and exact documentation passages. The model also included label as an attribute; the UI marked its missing cited field references rather than implying scientific support.
5. Measured on the server: zero shared slides, one shared patient, one of four evaluation rows affected. No human confirmation was fabricated or required for this existence finding.
6. Recomputed in a fresh Nebius Sandbox; the UI reported an exact match.
7. Opened the saved receipt and expanded the patient witness, showing the original training and evaluation filenames.
8. Explicitly enabled original-input inclusion and downloaded the evidence ZIP. The separately trusted local installation recomputed matching bytes, engine hashes, witnesses and the violation via `python -m asterisk verify-ladder`.

The hosted browser operation reserved at most two inference calls and one replay; its normal browser allowance was initially ten reserved calls. No real research inputs or personal information were used. This is an agent-operated synthetic workflow test, not a human usability session or a preparation-accuracy evaluation. The screenshot is retained locally at `artifacts/hosted-browser-receipt-2026-10-09.png`.

## Fixed friction

The input inventory claimed no examples were selected automatically, while the synthetic example deliberately preselected fictional slide identifiers. The text now distinguishes user uploads (no selected examples initially) from the fictional preset and asks the user to review the checkboxes. The outbound preview now says “selected columns” instead of claiming the user manually ticked every selection. Selection and transmission behavior are unchanged.

JavaScript verification: 190 tests passed. The prior Python regression result remains 618 passed and nine existing skips; this patch changes display wording only.

## Outstanding

Real researcher usefulness remains unmeasured; there is no recruitment account or participant yet. The retained 5/10 preparation result remains unchanged, and the rejected experimental prompt was not promoted. This successful familiar synthetic example cannot improve that score or support general accuracy claims.

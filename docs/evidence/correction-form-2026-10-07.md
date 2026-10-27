# Correction form usability pass — 7 October 2026

The guided correction form now gives each numeric control a distinct accessible name, including field ranges, character ranges and citation ranges. Source controls include their filename so two source tables can be distinguished. Supporting hints do not become part of accessible names.

The form groups observation setup, identity extraction, mapping and documentation. Optional extraction is collapsed for unchanged identifiers and opened automatically for existing transformations. No hidden value is cleared. A prefix of 11 and documentation lines 2–4 survived a correction/review/reopen browser journey on the fictional slide example. The preview showed SYN-AB-0001 for both training and evaluation slides without issuing a provider request.

The per-file uniqueness warning now describes its actual scope. Unique identities within one file do not rule out overlap with a second file; the previous warning overstated this.

Verification: 615 Python tests passed, 9 skipped; 184 JavaScript tests passed. A browser journey verified all fields have labels, the local review endpoint accepts the definition, and reopening preserves it. Layout checked at default desktop, 768px and 375px widths; document width matched viewport at both smaller widths. Screenshots are local artifacts. No paid inference, Sandbox calls or judge allowance were used. This is agent-run usability verification, not human researcher evidence.

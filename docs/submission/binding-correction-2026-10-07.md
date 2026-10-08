# Binding correction, 7 October 2026

The preparation review now asks three explicit questions: what one row represents, which subject identifier the claim needs held out, and how that identifier is linked to each row.

“Correct this binding” opens the existing definition instead of resetting it to filename and column guesses. The guided form retains observation files, partition labels, lookup keys and values, transforms, the observation-level name, and all existing citations. A bounded local preview shows six examples per observation file plus distinct-value and unmapped counts. Conflicting lookup values remain unmapped; preview is not a measurement or an identity confirmation.

Complex definitions (additional levels, per-source unit rules, row-based samples, deduplication or unsupported expressions) open the complete JSON definition editor. They are never silently converted into the narrower guided grammar. Both editors call the existing server validation/review endpoint before committing an edit, reject stale responses, and require a new measurement and confirmation. Editing makes no inference or Sandbox call. The original proposal remains recorded and the saved receipt exposes whether its specification was edited.

## Verification

- 609 Python tests passed, 9 skipped; 179 JavaScript tests passed.
- Added behavior tests for retained lookup/partition/citation setup, complex-spec refusal to flatten, the three questions, and missing/conflicting mappings across multiple observation files.
- Browser journey used a retained model response on an isolated offline fixture server with original fictional turbine-rotor files. Changing the lookup value column updated the displayed derived values. Restoring `asset_tag`, renaming the claim level to `turbine_rotor`, validating, measuring and saving produced 2 shared identities affecting 2 of 3 test rows. All three citations survived; the saved receipt displayed “Specification edited: true; inputs changed: false.” No live provider or Sandbox was called.
- Inspected desktop, 768px and 375px layouts. Fixed narrow review-table overflow; retained the existing visual tokens and keyboard focus styling.

This improves correction mechanics. It does not change the shipping v4 model, establish scientific identity meaning, replace a real human usefulness study, or turn the rejected v6 candidate into a production default.

# Published-result page verification

Direction: extend the existing restrained evidence-report style. Lead with the scientific question and an unmistakable count, then explain the join, attribution, limits and reproducible command.

Added `static/published-example.html`, companion CSS and aggregate-only JSON. Linked it from the product navigation and a new case-study section. Added a local reproduction script with pinned source hashes and separate reference comparison. Source metadata is not distributed through the page.

Verified with actual local upstream files: 641 shared lesions, 693 affected test images, 7,007 training images, 2,005 test images and 1,003 excluded validation images. The paper reports 641 shared lesions; its image-overlap quantity is not substituted for our affected-test-row count. Public paper: https://www.nature.com/articles/s41597-025-04382-5 . Source commit and both exact CSV URLs/hashes are in the generated JSON.

Browser inspection: desktop, 768 × 900 and 375 × 812. Narrow document widths matched viewport widths. Critique tightened mobile top spacing and aligned explanatory columns rather than inheriting the experiment page's second-column offset. Viewport override reset. Keyboard first focus reaches visible Skip to content with a 2px accent outline. Computed text contrast against paper: body 12.80, muted 4.99, lede 6.76, accent 8.97. Existing product colors/fonts retained.

Four regression tests pass: aggregate computation without row leakage, altered source rejection, duplicate sample rejection and conflicting mapping rejection. Full suite: 350 passed, 9 skipped, existing deprecation warnings. This is developer QA, not independent human evidence. No deployment or public publication performed. RC7 remains unchanged; these working-tree files require the next release freeze.

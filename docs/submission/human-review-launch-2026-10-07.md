# Human receipt review: ready to collect, not evidence yet

The hosted `/static/receipt-study.html` page provides a five-minute, uncoached comprehension task. It uses the saved WSI-Bench report receipt, not a new model or Sandbox run. Participants need the separately supplied preview credentials. No account has been registered, no participant recruited, and no response counted.

This is a new task; it does not alter the previously frozen DermaMNIST study. Freeze the hosted page, scripts and WSI receipt hash before the first participant. Do not change them during collection. Record the exact release and retain every submitted answer, including poor results and access failures.

Recruitment requires actual humans with practical held-out ML evaluation experience who did not build Asterisk and have not seen this receipt. The screener captures their role and prior exposure before showing the receipt. A facilitator must verify eligibility and authorship; checking boxes does not establish that a respondent is a researcher. Agents and developer dry runs never count as participants.

The four questions are: what exact condition was checked, what was found, what remains unknown, and what the reader would do next. Answers and elapsed time download as JSON. No response is uploaded automatically. The participant chooses whether to share the file. The page does not promise payment. A paid study still requires a recruitment account, separate payment arrangements, consent naming the actual collection provider and a defined retention period. The earlier $150 plan is preparation only, not authorization to fabricate participation.

## Frozen scoring rubric

Keep this rubric away from participants. Score each of these three criteria separately:

- Checked: exact recorded patient-identifier overlap between the report-task training and evaluation rows under the first-12-characters barcode definition; a slide-only comparison is insufficient for this claim.
- Found: zero shared slide identifiers and 42 shared patient identifiers, affecting 43 of 208 evaluation rows (42 of 207 distinct evaluation patients).
- Unknown: scientific correctness of the identity assumption and intended evaluation claim, model-accuracy consequences, or independence at unmeasured levels. The saved local receipt alone does not establish a fresh model/Sandbox execution or scientific validity.

Individual comprehension passes only when all three criteria are met within five minutes without coaching or AI help. Next action is qualitative; do not force a preferred answer. Builder grading is not independent. Retain access failures, elapsed time, assistance, exposure and withdrawals separately. Do not reject or conceal unfavorable answers. Comprehension does not establish time savings, adoption or superiority to a join script.

For a first small check, two screened people can read the same frozen receipt separately. For paid collection, follow `docs/validation/paid-comprehension-study.md` after account setup. Nothing here starts recruitment or contacts another person.

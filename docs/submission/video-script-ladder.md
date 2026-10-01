# Asterisk recording script — target 2:50

Show one question: **new images, or new patients?** The viewer should leave knowing what Asterisk measured, why Nemotron helped, and what the receipt cannot prove. This is a recording script, not a finished video.

## Recording sequence

| Time | Show | Say |
|---|---|---|
| 0:00–0:15 | WSI-Bench saved gallery result, slide and patient rows together | “New images do not necessarily mean new patients. In these public benchmark files, the slides are separate—but 42 test patients also appear in training.” |
| 0:15–0:30 | Expand one patient witness; keep the saved-result label visible | “This is a saved measurement, not a live run. The same patient identifier connects these different slides. A patient-level claim needs a patient-level check.” |
| 0:30–0:50 | Propose form → Load fictional example → outbound preview | “Now a small fictional example, end to end. The files first reach our app server. I choose which column examples Nebius may receive and inspect the exact model request.” |
| 0:50–1:15 | Actual Nemotron call, returned proposal and documentation citation | “NVIDIA Nemotron on Nebius Token Factory reads the README and proposes the extraction rules. Here the first eleven characters identify the patient. It proposes an interpretation; application code computes the result.” |
| 1:15–1:40 | Partition mapping and row counts, patient derivation, source quotation → measure → witness | “Before running it, I can inspect which labels mean training, evaluation or excluded, and where the patient definition came from. This result shows one shared patient and the rows behind it.” Say the actual observed count if different. |
| 1:40–2:00 | Actual fresh Sandbox replay and match | “Nebius Sandboxes reruns the same checker in a separate execution. This run matched. That checks reproducibility under these rules; it does not prove the rules describe the science correctly.” Say matched only after success. |
| 2:00–2:30 | Open saved receipt → proposal origin → readable export | “The handover preserves the model and prompt version, whether the proposal was edited, the partition choices, derivations, exclusions and witnesses. A second reader can inspect the assumptions—not just accept an AI verdict.” |
| 2:30–2:50 | Receipt scope and closing title | “A script can do the join once the identities are prepared. Asterisk helps make that preparation and its consequences inspectable. Nemotron still misses cases, and researcher usefulness is unmeasured. The model proposes. Code measures. You review the meaning.” |

The scripted narration is about 240 words, leaving time for clicks and inspection. Use readable close-ups rather than rushing through the entire page. If real waits make the take too long, remove only waiting and label the cut; never substitute a result from another attempt.

## What must stay distinguishable

- **Saved public finding:** WSI-Bench report task, zero shared slides, 42 of 207 test patient identifiers shared; 43 of 208 evaluation rows affected. This is not proof of accuracy inflation or an allegation about the authors' intended claim.
- **Live fictional workflow:** the shipped `static/ladder-example-propose` files. Its definition uses an eleven-character prefix; the public WSI-Bench definition uses twelve. Never mix those definitions or witnesses.
- **Model origin:** the saved receipt must show `recorded_model_proposal`, the actual model and prompt, and computed edit/input-change flags. A manual repair must remain visible as an edit, not be presented as an untouched model success.
- **Replay:** server-attested, same-code reproducibility. The installed SDK does not expose its operation UUID. The receipt is unsigned and does not independently authenticate the remote provider.
- **Export:** readable HTML and measurement JSON contain the spec, measurements and retained provenance. They do not include the raw input files or full model reasoning. Do not demonstrate the legacy evidence-ZIP verifier as though it verifies this ladder export.

## If the run does not succeed

If the model abstains or returns an unusable proposal, show that state and the manual recovery option. Do not secretly switch to a supplied spec. If the Sandbox fails, save the local measurement and call it local-only. If replay matches but storage fails, retain the returned result; another paid replay is unnecessary. Preserve failed takes privately when interpreting reliability.

The recorded evaluation stays available in the written entry: the combined Super configurations scored 21/41, Ultra 24/41 and Sonnet 36/41; shipping prompt v4 scored 5/10 on set D and failed its gate. These are bounded development results, not a general reliability promise. Do not spend the closing seconds implying that zero observed false reassurance makes the tool infallible.

## Preflight and completion evidence

1. Use the hosted release corresponding to GitHub main; record its commit and manifest hash privately. Use a fresh owner session, only fictional inputs for live calls, and no visible credentials.
2. Confirm the WSI-Bench saved card's counts and citation before narrating. Keep the saved-example disclosure visible.
3. Preview the live payload, select Nemotron Super, and perform one genuine proposal and replay. Keep the exact request/result and receipt together. The 28 September smoke passed this chain, but is not video footage.
4. Record the video, then open the saved receipt and downloaded HTML. Check every narrated count and provenance statement against that attempt.
5. Save the final video path, duration, receipt ID, execution record locations and wait edits. Review readable text, audio, captions and absence of secrets.
6. Publishing the video, verifying its viewer access, making the repository public and final submission remain separate unfinished actions. This script does not satisfy them.

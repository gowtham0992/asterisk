# Asterisk recording script — target 2:50

Show the difference between a split that separates images and one that separates the unit the researcher claims. Saved gallery findings, a fictional live example, and recorded evaluation results must be labeled separately. This is a recording plan, not a claim that a new live recording has been completed.

| Time | Screen | Voice-over |
|---|---|---|
| 0:00–0:15 | Ladder page, then WSI-Bench gallery card | “A test set can contain new slides from patients the model has already seen. Asterisk asks: new at which level?” |
| 0:15–0:40 | Saved WSI-Bench finding and one witness | “This saved measurement of public WSI-Bench files has no shared slides, but 42 test patients also occur in training. These rows explain the difference. Whether that violates the experiment depends on its claim.” |
| 0:40–0:55 | Propose with Nemotron; load fictional example; preview | “Now a fictional example, live. I state the claim and upload the files to Asterisk. Then I preview the documentation, counts and approved examples before sending that subset to the model.” |
| 0:55–1:25 | Send to Nemotron; show real response and cited source | “NVIDIA Nemotron on Nebius Token Factory proposes how to recover each identity level from the README. It proposes the question; it does not write the verdict.” If the response abstains, follow the refusal path below. |
| 1:25–1:50 | Review proposal, measure, open witness | “In this example the README defines the patient as the first 11 characters. The application checks that extraction and measures the actual rows. Different slides still map to one shared patient.” Say the observed count, not a scripted count. |
| 1:50–2:15 | Replay in Nebius Sandbox; actual result | “A fresh Nebius Sandbox runs the checker again. Asterisk records the replay only when its result matches.” Say “matched” only after the actual success response. |
| 2:15–2:35 | Open saved workspace receipt; HTML export | “The result survives this session. A second reader can inspect the claim, identity definitions and witness rows. A local-only run is labeled differently from a matched Sandbox replay. This is an unsigned record, not a certificate of scientific independence.” |
| 2:35–2:50 | Evaluation scoreboard and close | “Across 41 evaluated cases, the guarded model runs gave no false reassurance. Super still got only 21 ladders correct; the general-model baseline got 36. We show those misses. Asterisk: the model proposes, the engine decides, you confirm.” |

## Refusal and failure paths

- If the model abstains or returns an unusable proposal, show that state. Explain that a researcher must supply the missing definition; do not label a manually completed ladder as model success.
- If Sandbox replay fails, save the local result and identify it as local-only. Do not substitute a saved success while narrating a live run.
- If a call takes too long for the video, disclose an edit that removes waiting. Keep the real request and result together. Do not splice results from different runs.
- If replay succeeds but storage fails, download the returned result. The UI explicitly says another paid replay is unnecessary.

## Recording preflight

1. Use the tested release and a clean owner session; keep the release commit visible in the recording notes.
2. The WSI-Bench gallery is a saved result. Verify the displayed count and source provenance before narrating it. It is not a newly executed replay.
3. Use the shipped fictional example for the live chain. Review the outbound preview; record the selected model. A warm-up or recording involving providers is a paid run and must follow the applicable approval and budget.
4. Show at least one witness and one source definition large enough to read. Hide keys and unrelated browser tabs.
5. After recording, confirm that the saved receipt opens and that the downloaded HTML matches the demonstrated result.
6. Keep the full attempt record privately, including failure or repair. The exported workspace receipt does not itself retain upstream model proposal history.

## Evidence boundaries

The 41-case scoreboard combines the configurations tested on sets A–D; it is not 41 cases run under the shipping v4 prompt. Set D tested v4, where Super scored 5/10 and failed its pre-registered pass rule. No result establishes demand, time saved, or reliability on arbitrary datasets. Real researcher comprehension remains unmeasured.

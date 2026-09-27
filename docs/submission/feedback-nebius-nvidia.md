# Feedback on Nebius Token Factory, Sandboxes and NVIDIA Nemotron

Drawn from building Asterisk and from pre-registered, frozen experiments with about 1.95 million Token Factory tokens on
Nemotron 3 Nano, Super and Ultra, 26–27 September 2026. Every claim below links to a reproducible artifact in
`evaluation/ladder-proposal-v1` to `evaluation/ladder-proposal-v5` (including set D and the v4 prompt).

## Nebius Sandboxes

1. **Stdin appears to be capped just under 1 MB, and the failure is opaque.**
   - **What we saw:** a 1,000,000-byte stdin payload ran. Payloads of 1,048,576 bytes and larger were rejected with a
     generic `ApiStatusCodeError` from `POST /sandboxes/v1/instances`, with no size stated.
   - **What we did:** uploading the same data through `run(..., files={path: bytes})` worked. A 6.6 MB PTB-XL metadata
     table, uploaded gzip-compressed at 980 KB, ran in 1.7 s.
   - **Ask:** document the stdin and upload limits, and return a 413-style error naming the limit.
2. **Error objects include request and response detail.** That is useful for debugging, but applications must scrub
   them before showing users, because payloads can contain research data. We wrap every SDK exception.
   **Ask:** a `safe_message` field.
3. **What worked well:** disposable runs of `python:3.12-slim` start fast (0.1–1.7 s of compute in our replays), and the
   `files` upload made byte-exact replays of multi-megabyte inputs easy. The input SHA-256 inside the Sandbox matched
   the local pin.

## Token Factory

4. **Model ID casing is inconsistent.** The same model list mixes `nvidia/nemotron-3-super-120b-a12b`,
   `nvidia/Nemotron-3-Ultra-550b-a55b` and `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`. These are easy to mistype, and a
   wrong ID fails at request time. **Ask:** case-insensitive IDs or stable aliases (`nemotron-3-ultra`).
5. **`response_format: json_object` was reliable.** Once our schema was stated exactly, Super returned structurally
   valid JSON on 33 of 33 first attempts on one fresh set. The earlier failures were ours: a prompt that described the
   schema in prose.
6. **Deprecations need a pointer.** Nemotron-3-Nano-Omni left Serverless on 31 August 2026. A deprecation notice that
   names the recommended replacement ID saves a failed deploy.

## Nemotron 3 models, for our task (proposing a data hierarchy from documentation)

7. **Nemotron is cautious to a fault under explicit abstention rules.**
   - **Over-abstention:** on fresh set A, Super abstained on 30 of 33 replies. That included cases where the
     documentation states the unit ("Files are named SC4ssNEO-PSG.edf where ss is the subject number").
   - **Safe misses:** its misses were almost all abstentions or "not established", not confident errors.
   - For a safety-critical checker that is the right *direction* of error, but it limits usefulness.
8. **Ultra beat Super slightly but did not replicate a pass.**
   - **Set B:** Ultra scored 9 against Super's 8 of 10 with the same prompt, and all 3 of its repaired replies became valid.
   - **Set C (pre-registered replication):** Ultra scored 4 of 10 and Super 3 of 10.
   - **Totals across 31 fresh cases:** Ultra 18, Super 16.
9. **A general model (Claude Sonnet) did better** on all four fresh sets: 36 of 41 against Super's 21, on first
   attempts. We report this because it is what we measured, and because the gap concentrates in one skill:
   deriving a unit from a documented naming rule ("Records obtained from the same subject have names that differ in the last digit only" was declined in all 3 Super replies on one case). That seems addressable in training
   data or in guidance.
10. **Grammar matters as much as the model.** When we let proposals express "characters 2–4" and "field 1 split on _",
    Super's score on a fresh set rose from 3 to 5 of 10, with no false reassurance. Before that, Nemotron declined units
    it could see but could not express.
11. **Provider reliability.** Ultra returned `APIConnectionError` on 3 of about 35 calls in one run, each after about
    270 s, and one request stalled for about 25 minutes. **Ask:** a server-side timeout that returns an error quickly.
12. **Prose-only exceptions were handled perfectly by every Nemotron model.** An example is "Records 201 and 202 came
    from the same male subject", in MIT-BIH, whose widely used inter-patient split puts 201 in training and 202 in test.
    Every Nemotron model abstained rather than pretend the records were separable.

## What we would like

- **A documented `max_tokens` guidance** for reasoning-heavy JSON tasks on Super and Ultra. Completion lengths varied
  from about 350 to about 2,700 tokens for similar inputs.
- **A worked example in the Token Factory docs** of a bounded tool loop: propose, validate, one repair with the
  validator's error. That is the pattern that turned 40 of 54 invalid replies into 0 of 33.

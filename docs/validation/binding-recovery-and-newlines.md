# Binding recovery and newline preservation

Development verification, 19 September 2026 (local date). No inference or Jev calls were made in this pass.

## Fixed and remotely exercised

The baked driver and export replay script used universal-newline text reads. CRLF input was uploaded intact but read back as LF, changing the hashes and causing provenance failure. Both paths now decode the original UTF-8 bytes without newline conversion. Regression tests reproduced the mismatch before the fix, including the exported-receipt replay path.

The new image is `80519d96-3de8-4f48-95ed-2de62a8351d4`. Trusted primitive implementation hash remains `d718f875426d0ae9be9358e08c3c3e0a378c1e8dcc6ced0c7d989f3774d110e3`; the changed driver has its own recorded SHA-256 `cf87ab3ec129a16c6f5836c14ba0e3d3683bc72e98c47fdb48fe0ab65f6fc64a`. The image inventory records its uploaded bytes. This is a verified development image update, not a new release freeze or acceptance pass.

Before activation, the bake script verified a 100,000-row synthetic measurement and fresh replay against the local result. It also verified LF and CRLF synthetic measurements and fresh replays, including original input hashes. All passed. Details are retained locally in `.data/product-repair/100k-benchmark.json`, `newline-replay.json`, and `upload-inventory.json`. The previous image record remains retained. Bare-CR CSV input is not established as supported; it exposed a separate existing CSV-parser limitation during local testing.

## Browser recovery check

Record: `41d441dbff9c538b180c87bc` (synthetic example, manual setup).

1. Selected `partition` as both the sample ID and partition column.
2. The browser rejected the binding, reported two distinct values across three rows, explained that the columns must differ, and suggested `sample` as a structural candidate. No data defect was asserted.
3. Changed the sample column to `sample`, kept `subject_id` as the repeating specimen identity, and confirmed the documented meaning.
4. Ran the real Sandbox measurement and fresh replay. The browser showed one shared identity affecting one of two evaluation rows, complete mapping, and matching replay.
5. Opened witness S1. The inspector verified original hashes and displayed training sample a and evaluation sample b with their split and identity-mapping rows.

This checks recovery from a deliberately wrong user selection. It does not measure Nemotron proposal accuracy, repeat the PTB-XL acceptance case, or establish independent human comprehension. The confirmation in this QA record was performed by the development assistant, not a recruited practitioner.

A stray `null` in the binding-preview UI was removed. Receipt inspection found the result, witness explanation and conditional identity assumption already present; no new comprehension claim is made.

## Validation and remaining limits

Full local suite: 276 passed, 9 skipped. New newline tests cover the baked driver and exported-receipt loader. The latter uses a fake network boundary to assert unchanged input bytes; actual remote LF/CRLF measurement/replay is separately covered by the bake verification.

Human utility remains unmeasured. No public deployment, new blinded acceptance, new source-release freeze, or general-agent advantage is claimed. Do not describe the unchanged primitive hash as covering the changed driver; use the image inventory and driver hash together.

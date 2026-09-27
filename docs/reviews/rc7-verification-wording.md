# RC7 — recipient verification instructions

23 September 2026. This release corrects verification instructions in the offline receipt, exported README, project README, About page and demo script. Measurement code and the baked Sandbox image are unchanged.

Recipients are directed to obtain and verify a matching Asterisk release separately, then run `python -m asterisk verify /absolute/path/to/receipt` from that trusted installation directory. Running from inside a received bundle could resolve code supplied by its sender instead. The installed command does not execute bundled Python, make network requests or require credentials.

A bundled checker and an unsigned manifest are not independent evidence: a sender can replace both and the inputs. Recomputation with separately trusted code checks measurement and decision consistency; it does not authenticate the author, original dataset or identity semantics. No signature or attestation has been added.

The RC6 review and its findings remain applicable. RC7 makes no new accuracy, human-utility, deployment or adoption claim. The release packet records verification against an extracted source copy using the existing interpreter and dependencies.

Current freeze: `.data/primitive-v4/freeze-rc7-2026-09-23`. Its digest is in `snapshot.sha256`. Source archive: `artifacts/asterisk-source-rc7-2026-09-23.zip`. Review packet: `artifacts/asterisk-rc7-review-2026-09-23.zip`. Earlier freezes remain unchanged.

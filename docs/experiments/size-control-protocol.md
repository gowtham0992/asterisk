# Post-review size-matched control

This is a disclosed extension to the original five-seed protocol, adopted after Fable supplied its control results. It is not preregistered or unseen. The original protocol and first 47-file result remain preserved.

Keep seeds 42–46, source data, feature exclusions, target, ridge alpha=1, training-only standardization and the exact common evaluation rows unchanged. Starting from each overlapping training partition, use Python Random(1000 + seed).sample to remove exactly as many training rows as the repair removed. Draw candidates only from participants outside the original twelve-person evaluation group. Keep the leaked recordings in training. This reproduces Fable's specified control, without choosing new seeds after seeing scores.

Retain the selected/dropped row IDs and control split, train all three models, and report all seed MAEs and paired differences from overlapping MAE. Report the mean repair difference as a percentage of mean overlapping MAE. This controls the number of training rows removed in these five fixed draws. It does not match every feature/participant characteristic, average over repeated control draws, or establish general effects or significance. The result can support a leakage-related explanation for this constructed setting without claiming universal or clinically meaningful causality.

# Company Facts regression examples

`reported-examples.json` contains 15 selected SEC Company Facts observations:
2025 annual net income, total assets, and operating cash flow for Apple, Microsoft,
Alphabet, Amazon, and JPMorgan. Each retains the original source URL, artifact
SHA-256, JSON pointer, accession, and exact raw numeric lexeme. The unit tests build
small excerpt envelopes and use the excerpt's own checksum, never the parent hash.

These expected values were copied from the stored source and are mechanical
regression checks. Independent financial adjudication is **pending**, represented
by null `independent_review`. They are not held-out accuracy ground truth. Full
corpus pointer verification is performed by the offline audit against the five
immutable artifacts; no live SEC download is needed.

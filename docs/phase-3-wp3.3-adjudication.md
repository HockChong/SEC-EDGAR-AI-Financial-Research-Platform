> Historical v1 structural candidates. For the integrated normalizer, use the
> [v2 candidate manifest](phase-3-wp3.3-completion-candidates.json) and
> [current acceptance review](phase-3-wp3.3-acceptance-review.md).
> All human judgments remain pending; earlier owner implementation gates are superseded.

# WP3.3 human-adjudication candidates

25 cases across five companies. All human judgments are **pending**. These are
source-linked predictions, not golden labels or evidence of financial accuracy.
The [machine-readable cases](../tests/fixtures/tables/review-cases.json) retain
sample cells, source hashes, table IDs, predicted shapes and null expected judgments.

For each case inspect the original table and record: true category/title, grid
shape and spans, ordered header-to-value associations, actual reporting periods,
units/scale exceptions, footnotes and missing-versus-zero semantics. Mark accept,
reject or uncertain, with corrections, reviewer identity and review date. Review
numeric interpretation only after the owner normalizer and context policy are ready.

Source paths address the recovered original DOM; all source bytes remain in Bronze.
The full diagnostic result contains every raw and structured cell. Candidate families
are predictions and may be wrong; a human must correct them before any scoring.

## WP33-01 — CIK 0000019617 / income

- Filing: `0001628280-26-008131` (10-K); section: unclassified.
- Predicted title: Consolidated statements of income. Shape: 38 rows × 18 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/jpm-20251231.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/42/428551a3073c9701082ca0fe2212b753f8aa30aa71dbd2d5e542a4e09013be05).
- [Full extraction](../.runtime/wp33/final-documents/0001628280-26-008131.json).
- Source SHA-256: `428551a3073c9701082ca0fe2212b753f8aa30aa71dbd2d5e542a4e09013be05`.
- Table ID: `table:7f151abf6ac26b517d566ed7a4de75fff4a7f64313b829b599b510130b33ce24`.
- Source DOM: `/*[1]/*[2]/*[1111]/*[1]`.
- Human disposition and corrected expected values: **pending**.

## WP33-02 — CIK 0000019617 / balance_sheet

- Filing: `0001628280-26-008131` (10-K); section: unclassified.
- Predicted title: Consolidated balance sheets analysis. Shape: 20 rows × 15 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/jpm-20251231.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/42/428551a3073c9701082ca0fe2212b753f8aa30aa71dbd2d5e542a4e09013be05).
- [Full extraction](../.runtime/wp33/final-documents/0001628280-26-008131.json).
- Source SHA-256: `428551a3073c9701082ca0fe2212b753f8aa30aa71dbd2d5e542a4e09013be05`.
- Table ID: `table:4128983aa7017319ac21ab0423a17102ee2965c42871d24df64e7e0c1f0b3149`.
- Source DOM: `/*[1]/*[2]/*[356]/*[1]`.
- Human disposition and corrected expected values: **pending**.

## WP33-03 — CIK 0000019617 / cash_flow

- Filing: `0001628280-26-008131` (10-K); section: unclassified.
- Predicted title: Consolidated statements of cash flows. Shape: 57 rows × 18 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/19617/000162828026008131/jpm-20251231.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/42/428551a3073c9701082ca0fe2212b753f8aa30aa71dbd2d5e542a4e09013be05).
- [Full extraction](../.runtime/wp33/final-documents/0001628280-26-008131.json).
- Source SHA-256: `428551a3073c9701082ca0fe2212b753f8aa30aa71dbd2d5e542a4e09013be05`.
- Table ID: `table:0997346c929723c303ed7d4a1f3d718788531fdf2952e4a178c19d90d4dc3057`.
- Source DOM: `/*[1]/*[2]/*[1138]/*[1]`.
- Human disposition and corrected expected values: **pending**.

## WP33-04 — CIK 0000019617 / balance_sheet

- Filing: `0001628280-26-029344` (10-Q); section: unclassified.
- Predicted title: Consolidated balance sheets analysis. Shape: 34 rows × 15 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/19617/000162828026029344/jpm-20260331.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/19/19a91282ff8773d37ba9a02e2f717eb0fda99fe0f4e4b4cfbb9d46fc5d7cecbc).
- [Full extraction](../.runtime/wp33/final-documents/0001628280-26-029344.json).
- Source SHA-256: `19a91282ff8773d37ba9a02e2f717eb0fda99fe0f4e4b4cfbb9d46fc5d7cecbc`.
- Table ID: `table:c52885ef0dfa0b89856c97e56bc97b0f29aca2b6c2282ab13e9990de2129c040`.
- Source DOM: `/*[1]/*[2]/*[95]/*[1]`.
- Human disposition and corrected expected values: **pending**.

## WP33-05 — CIK 0000019617 / balance_sheet

- Filing: `0001628280-26-054343` (10-Q); section: unclassified.
- Predicted title: Consolidated balance sheets analysis. Shape: 34 rows × 15 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/19617/000162828026054343/jpm-20260630.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/7c/7cbc765c34c9a43a09b74db21e75bd0f94e548b4dfb50c53699526a985935a48).
- [Full extraction](../.runtime/wp33/final-documents/0001628280-26-054343.json).
- Source SHA-256: `7cbc765c34c9a43a09b74db21e75bd0f94e548b4dfb50c53699526a985935a48`.
- Table ID: `table:00052a87ed67d3198990dd55738cee906bdc8b42f583c299b6f1dc9be6ff561c`.
- Source DOM: `/*[1]/*[2]/*[123]/*[1]`.
- Human disposition and corrected expected values: **pending**.

## WP33-06 — CIK 0000320193 / income

- Filing: `0000320193-26-000013` (10-Q); section: classified.
- Predicted title: CONDENSED CONSOLIDATED STATEMENTS OF OPERATIONS (Unaudited). Shape: 32 rows × 24 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/7d/7d97585e619f1e6ca9ad23c5068c3b2fe1369a3b01882acd4aeff93b4b638f91).
- [Full extraction](../.runtime/wp33/final-documents/0000320193-26-000013.json).
- Source SHA-256: `7d97585e619f1e6ca9ad23c5068c3b2fe1369a3b01882acd4aeff93b4b638f91`.
- Table ID: `table:a97fe0891d29affb7d979fdf18604d5882c68ceb8229785d7c42a66dbe18586f`.
- Source DOM: `/*[1]/*[2]/*[64]/*[1]`.
- Human disposition and corrected expected values: **pending**.

## WP33-07 — CIK 0000320193 / balance_sheet

- Filing: `0000320193-26-000013` (10-Q); section: classified.
- Predicted title: CONDENSED CONSOLIDATED BALANCE SHEETS (Unaudited). Shape: 43 rows × 12 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/7d/7d97585e619f1e6ca9ad23c5068c3b2fe1369a3b01882acd4aeff93b4b638f91).
- [Full extraction](../.runtime/wp33/final-documents/0000320193-26-000013.json).
- Source SHA-256: `7d97585e619f1e6ca9ad23c5068c3b2fe1369a3b01882acd4aeff93b4b638f91`.
- Table ID: `table:ab6895b8fad3412e3d7ea4179b2fb4541ddfc32a31f02c59ead58bd7cd8f38a5`.
- Source DOM: `/*[1]/*[2]/*[84]/*[1]`.
- Human disposition and corrected expected values: **pending**.

## WP33-08 — CIK 0000320193 / cash_flow

- Filing: `0000320193-26-000013` (10-Q); section: classified.
- Predicted title: CONDENSED CONSOLIDATED STATEMENTS OF CASH FLOWS (Unaudited). Shape: 44 rows × 12 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/7d/7d97585e619f1e6ca9ad23c5068c3b2fe1369a3b01882acd4aeff93b4b638f91).
- [Full extraction](../.runtime/wp33/final-documents/0000320193-26-000013.json).
- Source SHA-256: `7d97585e619f1e6ca9ad23c5068c3b2fe1369a3b01882acd4aeff93b4b638f91`.
- Table ID: `table:768dfde579c46015042185a710a8615f73beda175d3e15dbc4c97c43f4723d9e`.
- Source DOM: `/*[1]/*[2]/*[104]/*[1]`.
- Human disposition and corrected expected values: **pending**.

## WP33-09 — CIK 0000320193 / income

- Filing: `0000320193-26-000013` (10-Q); section: classified.
- Predicted title: CONDENSED CONSOLIDATED STATEMENTS OF COMPREHENSIVE INCOME (Unaudited). Shape: 19 rows × 24 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/7d/7d97585e619f1e6ca9ad23c5068c3b2fe1369a3b01882acd4aeff93b4b638f91).
- [Full extraction](../.runtime/wp33/final-documents/0000320193-26-000013.json).
- Source SHA-256: `7d97585e619f1e6ca9ad23c5068c3b2fe1369a3b01882acd4aeff93b4b638f91`.
- Table ID: `table:1600dfc61412f674754a12279cadf3d41506d53710b834675417160f527c97e5`.
- Source DOM: `/*[1]/*[2]/*[74]/*[1]`.
- Human disposition and corrected expected values: **pending**.

## WP33-10 — CIK 0000320193 / disclosure

- Filing: `0000320193-26-000013` (10-Q); section: classified.
- Predicted title: CONDENSED CONSOLIDATED STATEMENTS OF SHAREHOLDERS’ EQUITY (Unaudited). Shape: 28 rows × 24 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/320193/000032019326000013/aapl-20260328.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/7d/7d97585e619f1e6ca9ad23c5068c3b2fe1369a3b01882acd4aeff93b4b638f91).
- [Full extraction](../.runtime/wp33/final-documents/0000320193-26-000013.json).
- Source SHA-256: `7d97585e619f1e6ca9ad23c5068c3b2fe1369a3b01882acd4aeff93b4b638f91`.
- Table ID: `table:fbdcfee97ff0fc92dc2ef3708855416bffd40db72eba9b1a1d4868daee86c9eb`.
- Source DOM: `/*[1]/*[2]/*[94]/*[1]`.
- Human disposition and corrected expected values: **pending**.

## WP33-11 — CIK 0000789019 / income

- Filing: `0000950170-25-100235` (10-K); section: classified.
- Predicted title: INCOME STATEMENTS. Shape: 46 rows × 13 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/bd/bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665).
- [Full extraction](../.runtime/wp33/final-documents/0000950170-25-100235.json).
- Source SHA-256: `bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665`.
- Table ID: `table:a420574a8e02d5b2c062d7de56ad230af6539e9f0119d267a577c3b01b53600b`.
- Source DOM: `/*[1]/*[2]/*[199]/*[4]`.
- Human disposition and corrected expected values: **pending**.

## WP33-12 — CIK 0000789019 / balance_sheet

- Filing: `0000950170-25-100235` (10-K); section: classified.
- Predicted title: BALANCE SHEETS. Shape: 65 rows × 9 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/bd/bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665).
- [Full extraction](../.runtime/wp33/final-documents/0000950170-25-100235.json).
- Source SHA-256: `bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665`.
- Table ID: `table:ad62b640b0f7896ef1176525da90928812ebf97debb375464ffd62399b502923`.
- Source DOM: `/*[1]/*[2]/*[207]/*[3]`.
- Human disposition and corrected expected values: **pending**.

## WP33-13 — CIK 0000789019 / cash_flow

- Filing: `0000950170-25-100235` (10-K); section: classified.
- Predicted title: CASH FLOWS STATEMENTS. Shape: 62 rows × 13 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/bd/bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665).
- [Full extraction](../.runtime/wp33/final-documents/0000950170-25-100235.json).
- Source SHA-256: `bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665`.
- Table ID: `table:ee2f74905f70c064bf5b3778c634f9c2d3bd8a7a71613b7a0e61512b61915136`.
- Source DOM: `/*[1]/*[2]/*[211]/*[3]`.
- Human disposition and corrected expected values: **pending**.

## WP33-14 — CIK 0000789019 / disclosure

- Filing: `0000950170-25-100235` (10-K); section: classified.
- Predicted title: [unknown]. Shape: 11 rows × 13 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/bd/bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665).
- [Full extraction](../.runtime/wp33/final-documents/0000950170-25-100235.json).
- Source SHA-256: `bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665`.
- Table ID: `table:a49dc4b6eea54677a073736afd01da68ccc442bb1d5ae238cb284ffcf094f64d`.
- Source DOM: `/*[1]/*[2]/*[151]/*[7]`.
- Human disposition and corrected expected values: **pending**.

## WP33-15 — CIK 0000789019 / disclosure

- Filing: `0000950170-25-100235` (10-K); section: classified.
- Predicted title: [unknown]. Shape: 13 rows × 18 columns.
- Merged cells: True; multiple period labels: False.
- [SEC source](https://www.sec.gov/Archives/edgar/data/789019/000095017025100235/msft-20250630.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/bd/bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665).
- [Full extraction](../.runtime/wp33/final-documents/0000950170-25-100235.json).
- Source SHA-256: `bd4d8df78c2c5d037ce9254a2be04e188576d486ff59386ffbd6f7743b4b3665`.
- Table ID: `table:5d626d08ebbabb8f3d5022d0ceff06e67f2cc7232a226e2dc809960bc72fa9a6`.
- Source DOM: `/*[1]/*[2]/*[131]/*[8]`.
- Human disposition and corrected expected values: **pending**.

## WP33-16 — CIK 0001018724 / income

- Filing: `0001018724-26-000004` (10-K); section: classified.
- Predicted title: CONSOLIDATED STATEMENTS OF OPERATIONS. Shape: 28 rows × 18 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/a2/a2d31fb7be58454479b35622eb8d3379f953f4a8f44a256166217fa5b434af35).
- [Full extraction](../.runtime/wp33/final-documents/0001018724-26-000004.json).
- Source SHA-256: `a2d31fb7be58454479b35622eb8d3379f953f4a8f44a256166217fa5b434af35`.
- Table ID: `table:12ca1feebb34cc394525b9c6b061313a1f9f2b5decab3f3aeeca6a7f9181c019`.
- Source DOM: `/*[1]/*[2]/*[574]/*[1]`.
- Human disposition and corrected expected values: **pending**.

## WP33-17 — CIK 0001018724 / balance_sheet

- Filing: `0001018724-26-000004` (10-K); section: classified.
- Predicted title: CONSOLIDATED BALANCE SHEETS. Shape: 34 rows × 12 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/a2/a2d31fb7be58454479b35622eb8d3379f953f4a8f44a256166217fa5b434af35).
- [Full extraction](../.runtime/wp33/final-documents/0001018724-26-000004.json).
- Source SHA-256: `a2d31fb7be58454479b35622eb8d3379f953f4a8f44a256166217fa5b434af35`.
- Table ID: `table:e3442db5173b15e5edab0b6e3b218d2ce013710be2ecd3ef2d6ce7d4482e4137`.
- Source DOM: `/*[1]/*[2]/*[592]/*[1]`.
- Human disposition and corrected expected values: **pending**.

## WP33-18 — CIK 0001018724 / cash_flow

- Filing: `0001018724-26-000004` (10-K); section: classified.
- Predicted title: Consolidated Statements of Cash Flows. Shape: 9 rows × 6 columns.
- Merged cells: True; multiple period labels: False.
- [SEC source](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/a2/a2d31fb7be58454479b35622eb8d3379f953f4a8f44a256166217fa5b434af35).
- [Full extraction](../.runtime/wp33/final-documents/0001018724-26-000004.json).
- Source SHA-256: `a2d31fb7be58454479b35622eb8d3379f953f4a8f44a256166217fa5b434af35`.
- Table ID: `table:147c34411ad7ccc32659dc6dc1dc25a54a4d68513c2ce3257527a40949bde92b`.
- Source DOM: `/*[1]/*[2]/*[531]/*[1]`.
- Human disposition and corrected expected values: **pending**.

## WP33-19 — CIK 0001018724 / disclosure

- Filing: `0001018724-26-000004` (10-K); section: classified.
- Predicted title: [unknown]. Shape: 9 rows × 12 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/a2/a2d31fb7be58454479b35622eb8d3379f953f4a8f44a256166217fa5b434af35).
- [Full extraction](../.runtime/wp33/final-documents/0001018724-26-000004.json).
- Source SHA-256: `a2d31fb7be58454479b35622eb8d3379f953f4a8f44a256166217fa5b434af35`.
- Table ID: `table:be0b535a196366dadaa9f6d9b7807f7ea0ff917f32ff778aa86c92fa2b104fdf`.
- Source DOM: `/*[1]/*[2]/*[383]/*[1]`.
- Human disposition and corrected expected values: **pending**.

## WP33-20 — CIK 0001018724 / disclosure

- Filing: `0001018724-26-000004` (10-K); section: unclassified.
- Predicted title: [unknown]. Shape: 3 rows × 6 columns.
- Merged cells: True; multiple period labels: False.
- [SEC source](https://www.sec.gov/Archives/edgar/data/1018724/000101872426000004/amzn-20251231.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/a2/a2d31fb7be58454479b35622eb8d3379f953f4a8f44a256166217fa5b434af35).
- [Full extraction](../.runtime/wp33/final-documents/0001018724-26-000004.json).
- Source SHA-256: `a2d31fb7be58454479b35622eb8d3379f953f4a8f44a256166217fa5b434af35`.
- Table ID: `table:4c5816fa5c7b7b785b4b7d38b9318127db99488202e5a768b173cb84ac39b8dd`.
- Source DOM: `/*[1]/*[2]/*[42]/*[1]`.
- Human disposition and corrected expected values: **pending**.

## WP33-21 — CIK 0001652044 / income

- Filing: `0001652044-25-000014` (10-K); section: classified.
- Predicted title: CONSOLIDATED STATEMENTS OF INCOME. Shape: 39 rows × 18 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/1652044/000165204425000014/goog-20241231.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/7b/7b5b7e74836e0c8a9b807ebb074a992d5a35d6549e5d847f4d8cf77951600a9d).
- [Full extraction](../.runtime/wp33/final-documents/0001652044-25-000014.json).
- Source SHA-256: `7b5b7e74836e0c8a9b807ebb074a992d5a35d6549e5d847f4d8cf77951600a9d`.
- Table ID: `table:eb86e121a455e4e518eb99ec01548e44d93cdc5c7acddce4df0586ff1c4b6a89`.
- Source DOM: `/*[1]/*[2]/*[931]/*[2]`.
- Human disposition and corrected expected values: **pending**.

## WP33-22 — CIK 0001652044 / balance_sheet

- Filing: `0001652044-25-000014` (10-K); section: classified.
- Predicted title: CONSOLIDATED BALANCE SHEETS. Shape: 40 rows × 12 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/1652044/000165204425000014/goog-20241231.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/7b/7b5b7e74836e0c8a9b807ebb074a992d5a35d6549e5d847f4d8cf77951600a9d).
- [Full extraction](../.runtime/wp33/final-documents/0001652044-25-000014.json).
- Source SHA-256: `7b5b7e74836e0c8a9b807ebb074a992d5a35d6549e5d847f4d8cf77951600a9d`.
- Table ID: `table:7a8681329e257cae65948d4ef0b00057313686f84c4521dda7b00a88ba68c198`.
- Source DOM: `/*[1]/*[2]/*[923]/*[2]`.
- Human disposition and corrected expected values: **pending**.

## WP33-23 — CIK 0001652044 / cash_flow

- Filing: `0001652044-25-000014` (10-K); section: classified.
- Predicted title: CONSOLIDATED STATEMENTS OF CASH FLOWS. Shape: 47 rows × 18 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/1652044/000165204425000014/goog-20241231.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/7b/7b5b7e74836e0c8a9b807ebb074a992d5a35d6549e5d847f4d8cf77951600a9d).
- [Full extraction](../.runtime/wp33/final-documents/0001652044-25-000014.json).
- Source SHA-256: `7b5b7e74836e0c8a9b807ebb074a992d5a35d6549e5d847f4d8cf77951600a9d`.
- Table ID: `table:82ca21cdc0f869de8c3c6b8c068e922e681f019eded49810652554f9e9490c1b`.
- Source DOM: `/*[1]/*[2]/*[955]/*[2]`.
- Human disposition and corrected expected values: **pending**.

## WP33-24 — CIK 0001652044 / disclosure

- Filing: `0001652044-25-000014` (10-K); section: classified.
- Predicted title: [unknown]. Shape: 18 rows × 24 columns.
- Merged cells: True; multiple period labels: True.
- [SEC source](https://www.sec.gov/Archives/edgar/data/1652044/000165204425000014/goog-20241231.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/7b/7b5b7e74836e0c8a9b807ebb074a992d5a35d6549e5d847f4d8cf77951600a9d).
- [Full extraction](../.runtime/wp33/final-documents/0001652044-25-000014.json).
- Source SHA-256: `7b5b7e74836e0c8a9b807ebb074a992d5a35d6549e5d847f4d8cf77951600a9d`.
- Table ID: `table:8e6ad136fd6627d2bda15602f5a28973af0b9ed3108a7794a414632d1f4f0f32`.
- Source DOM: `/*[1]/*[2]/*[623]/*[1]`.
- Human disposition and corrected expected values: **pending**.

## WP33-25 — CIK 0001652044 / disclosure

- Filing: `0001652044-25-000014` (10-K); section: classified.
- Predicted title: [unknown]. Shape: 6 rows × 39 columns.
- Merged cells: True; multiple period labels: False.
- [SEC source](https://www.sec.gov/Archives/edgar/data/1652044/000165204425000014/goog-20241231.htm); [exact Bronze bytes](../.runtime/artifacts/bronze/sha256/7b/7b5b7e74836e0c8a9b807ebb074a992d5a35d6549e5d847f4d8cf77951600a9d).
- [Full extraction](../.runtime/wp33/final-documents/0001652044-25-000014.json).
- Source SHA-256: `7b5b7e74836e0c8a9b807ebb074a992d5a35d6549e5d847f4d8cf77951600a9d`.
- Table ID: `table:cd5507dd2123b94067fc70b6b91050dbf537ae4dc6c044de68f7e2b21f59276d`.
- Source DOM: `/*[1]/*[2]/*[463]/*[1]`.
- Human disposition and corrected expected values: **pending**.

# fee-schedule-diff

I built a tool that compares editions of BC's public medical fee schedule because I wanted to see which entries changed without searching two long PDFs by hand. A fee code is the identifier for a listed medical service. I extract each readable code, description and price, then report added codes, removed codes, changed prices and reworded descriptions. Every reported change has a link to its page in the original PDF.

**[Open the saved comparison](reports/summary.md)** to try it without installing anything. It compares the December 31, 2024 and April 30, 2025 MSC Payment Schedule editions. The [full report](reports/comparison.md) contains every reported change, and the [JSON report](reports/comparison.json) includes the complete review queue in a format another program can read.

If a row has several prices or unclear text, I flag it for review instead of choosing a value. These reports help me find source pages to check; they do not replace the schedule's billing rules.

## Run it

From a checkout of this repository, with Python and [uv](https://docs.astral.sh/uv/getting-started/installation/) installed:

```sh
uv sync --frozen --extra dev
uv run python scripts/reproduce.py
```

This downloads the public editions, extracts their fee rows, rebuilds the saved reports and checks the extraction against my hand-checked sample. Open `reports/summary.md` afterwards. PDFs are cached in `data/source/` and kept out of git. No account or private data is needed.

## What I compare

The saved run found these differences among resolved fixed-price codes:

| Added | Removed | Price changed | Description changed | Letter prefix changed |
| --- | --- | --- | --- | --- |
| 12 | 10 | 6 | 15 | 4 |

There are 47 changed codes. The extractor accepted 3,562 codes in the older edition and 3,567 in the newer edition. It recorded 1,067 review entries in the older edition and 1,050 in the newer one. Review entries are occurrences, so a repeated code can appear more than once. Across both editions, 723 unresolved codes are excluded from comparison.

“Added” and “removed” mean present only in the resolved extraction of that edition. I check the source before treating either as an official addition or deletion. If any occurrence of a code is unresolved in either edition, I exclude that code from both sides. This also excludes some readable entries that appear elsewhere in an unpriced reference list. It makes the report less complete, but avoids calling an extraction failure a removal.

Prices expressed as percentages or several rates go to review. I compare the literal row description, with spacing cleaned up; a short label still needs its section heading for context. I do not compare eligibility notes, preambles or anesthesia levels. Scanned PDFs and unfamiliar layouts need more work. [Design and limits](docs/design.md) explains these choices.

## Compare other editions

The command-line tool also accepts local, searchable PDFs. Supply each PDF's public source URL so the output can link back to it:

```sh
uv run fee-schedule-diff fetch
uv run fee-schedule-diff extract data/source/2024-12-31.pdf \
  --url https://www2.gov.bc.ca/assets/gov/health/practitioner-pro/medical-services-plan/msc_payment_schedule_-_dec_31_2024.pdf \
  --label 2024-12-31 --out tmp/old.json
uv run fee-schedule-diff extract data/source/2025-04-30.pdf \
  --url https://www2.gov.bc.ca/assets/gov/health/practitioner-pro/medical-services-plan/msc_payment_schedule_-_april_30_2025.pdf \
  --label 2025-04-30 --out tmp/new.json
uv run fee-schedule-diff compare tmp/old.json tmp/new.json \
  --out tmp/comparison.json --markdown tmp/comparison.md --short tmp/summary.md
uv run fee-schedule-diff validate tmp/old.json tmp/new.json --out tmp/accuracy.json
```

The supplied validation sample belongs to these editions. For other PDFs, add independently checked rows to a new gold file and pass it with `--gold`. Page links use the PDF viewer's physical page number, which can differ from the section number printed on the page.

## Public sources

I used the Province of British Columbia's [MSC Payment Schedule publication page](https://www2.gov.bc.ca/gov/content/health/practitioner-professional-resources/msp/physicians/payment-schedules/msc-payment-schedule) and these original PDFs:

- [December 31, 2024 edition](https://www2.gov.bc.ca/assets/gov/health/practitioner-pro/medical-services-plan/msc_payment_schedule_-_dec_31_2024.pdf)
- [April 30, 2025 edition](https://www2.gov.bc.ca/assets/gov/health/practitioner-pro/medical-services-plan/msc_payment_schedule_-_april_30_2025.pdf)

Both downloads succeeded; I used no substitute. These are historical editions. The PDFs are provincial publications, subject to the province's [copyright terms](https://www2.gov.bc.ca/gov/content/home/copyright). I retain small public-text test fixtures and derived reports here. There are no patient records, claims or connections to private systems.

`data/sources.json` records each URL and its SHA-256 hash, a fingerprint of the file's exact bytes. A changed download fails the check rather than silently changing the comparison. The report records those fingerprints too.

## How it is checked

I checked complete fee-table pages by reading rendered source pages and transcribing the expected rows separately. The sample has 37 fixed-price rows across seven pages and six multi-price review cases. All 37 rows match exactly on code, letter prefix, description, price and page; all six review cases are flagged. Exact precision and recall on this sample are both 100%. Precision measures how many accepted rows are correct; recall measures how many expected rows were recovered.

This is a small, selected regression sample used during development, not a blind estimate for the whole schedule. The score measures row extraction before duplicate-code quarantine, which can exclude correctly read rows from comparison. The [accuracy report](reports/accuracy.json) includes that later coverage count. [Sample selection and reproduction](docs/accuracy.md) explains the method and its limits.

All report figures above come from:

```sh
uv run python scripts/reproduce.py
uv run python scripts/stats.py
```

The code in `src/fee_schedule_diff/` separates PDF extraction, comparison, report writing and sample validation. I use pdfplumber for word positions and Python's Decimal type to compare prices without floating-point rounding. Python requirements are in `pyproject.toml`; `uv.lock` pins dependencies.

```sh
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv build
```

GitHub Actions runs the tests and package build across supported Python versions. A separate check downloads the pinned public PDFs, reruns the complete comparison and rejects any difference from the committed reports. The offline tests cover real page fixtures, additions and removals, price and wording changes, uncertain rows, duplicate conflicts, source links and download integrity.

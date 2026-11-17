# Agent Access Study: data, scripts and the locked plan

Most AI tools couldn't access 5 of 20 big stores, and often got the price wrong. This repository holds every file behind that study, so anyone can check or rerun every number.

- **The write-up:** https://axioms.ai/research/agent-access-study/
- **Author:** Karen Spinner, Head of Applied AI Research, Axioms.ai
- **Run days:** Thu Nov 5, Sat Nov 7 and Mon Nov 9, 2026, plus a control run on Wed Nov 11

## What we tested

We sent four AI companies' page-reading tools to the same 100 product pages, five from each of 20 large US stores, on three days. Each answer was checked against an ordinary, signed-out Chrome browser that read the same page within 30 minutes. That adds up to 1,200 tries.

| Company | Tool | Model |
|---|---|---|
| Anthropic | web fetch (`web_fetch_20260209`) | claude-opus-5-5 |
| Google | URL context | gemini-3.1-flash-lite |
| OpenAI | Responses API web search | gpt-5.4-mini |
| Perplexity | Sonar, with a store domain filter (answers from its search index) | sonar |

## Start here: `data/tries.csv`

The CSV has one row per try (1,200 rows). `tools/build_tries_csv.py` builds it from the run files in this repository and prints per-tool totals that match Figure 1 of the write-up.

| Column | What it holds |
|---|---|
| `day`, `store`, `page`, `product_url` | Which page, on which run day (pages are numbered 1 to 5 per store, as listed in `stores.yaml`) |
| `company`, `tool` | Which tool fetched it |
| `chart_outcome` | The outcome on the write-up's charts: Price matched, Price wrong, Got in, no price, Turned away, or Not graded |
| `final_outcome` | The finer outcome from `final.py` (for example `price_while_blocked` and `matched_other_listed_price`, which the charts count as Turned away and Price wrong) |
| `final_access` | The access class after coding and rulings |
| `coder_1`, `coder_1_access`, `coder_2`, `coder_2_access` | The two blind AI coders. Neither came from the lab whose tool produced the answer. |
| `ruling`, `ruling_reason` | Our ruling where the coders disagreed (from `rulings.csv`) |
| `price_given`, `control_price`, `other_store_prices` | The tool's price, the control browser's price, and any other prices the store's page showed |
| `copy_age_days` | Days between the stored copy and the fetch (Anthropic's tool only; it is the only tool that dates its copy) |
| `tool_said_opened` | The tool's own first line on whether it opened the page |
| `raw_response` | The raw API response for that try |
| `note` | Notes from dated amendments (for example, the Depop buyer-fee regrade) |

## What else is here

| Path | What it is |
|---|---|
| `PREREG.md`, `LOCK.txt` | The study plan and its hash ledger. Dated amendments sit below the original text of `PREREG.md`. |
| `locked-2026-11-03/` | The Nov 3 versions of `PREREG.md`, `grade.py` and `code_fetch.py`, so you can check them against the first hashes in `LOCK.txt` |
| `stores.yaml` | The frozen list of 21 stores: 100 product URLs from 20 stores, plus Instacart's homepage only |
| `pilot.py`, `products.py`, `control.js`, `control_sink.py` | Collection: the API calls and verbatim prompts, the robots.txt check, and the Chrome price reader |
| `grade.py`, `code_fetch.py`, `final.py`, `results.py`, `capcheck.py` | Grading: the cent-level price grader, the cross-lab coder harness, the final outcome rules, the `RESULTS.json` builder, and the Nov 11 control run |
| `runs/products-2026-11-{05,07,09}/` | Each run day: raw responses per page and tool, `graded.json`, `coding.jsonl`, `rulings.csv`, `final.json`, and Day 1's `pre-amendment/` files |
| `runs/pilot-2026-11-*/`, `runs/products-2026-11-03/`, `runs/smoke-*` | Homepage runs and the Nov 3 pilots before the lock (not counted) |
| `runs/capcheck-2026-11-11/` | The control run with and without the 6,000-token page-text cap we set on Anthropic's tool |
| `runs/RESULTS.json`, `runs/TALLY.md` | The study's lead numbers |
| `FOOTNOTES.md` | All 20 footnotes on the raw data |
| `source-archive/` | The store ranking as we read it on Nov 3 |
| `vendor/common.py` | The vendor API callers the coder harness imports, as they stood during the runs (from our Agent Grounding Study tools) |
| `tools/build_tries_csv.py` | Builds `data/tries.csv` |

## An internal pre-registration

Before the first counted run, we wrote the store list, product links, prompt and grading rules into a plan and locked it on November 3, 2026, with SHA-256 hashes recorded in `LOCK.txt`. This is an internal pre-registration: we kept the record in our own repository, and no public registry holds a timestamped copy. It is not a formal or academic pre-registration. The hashes and the Nov 3 files in `locked-2026-11-03/` are how you check it.

To check a file:

```
shasum -a 256 locked-2026-11-03/PREREG.md
```

Compare the result with the matching line in `LOCK.txt`.

The locked files are published byte for byte, so a few internal notes stay in them: `PREREG.md` mentions an internal commitment number and the folder where an earlier study is parked, and `pilot.py` and `vendor/common.py` read API keys from a `.env` file at a path on our machine. No keys, account IDs or personal data are in this repository.

## Disclosure

Karen Spinner designed and ran this study at Axioms.ai. Axioms.ai makes Product.ai, an AI shopping product that competes with AI shopping answers like those tested here. It also runs SimplyCodes, a coupon site that earns most of the company's revenue. So we have a commercial stake in how accurately AI tools report prices, and that is why every file is here.

## Rerunning it

The scripts need Python 3 with `pyyaml`, `requests` and `anthropic`, plus your own API keys for Anthropic, Google, OpenAI and Perplexity. `pilot.py` reads them from the `.env` path named near its top, so put a `.env` there or point that line at your own file (which changes its hash). The coder harness imports `common.py`, so run it with `PYTHONPATH=vendor`:

```
PYTHONPATH=vendor python3 code_fetch.py runs/products-2026-11-05
```

`tools/build_tries_csv.py` and the CSV need nothing beyond Python 3. The store pages and prices will have changed since November 2026, so a new run measures the tools as they are now.

## License

Data and documents: CC BY 4.0. Scripts: MIT. See `LICENSE`.

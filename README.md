# Agent Access Study: data, scripts and the locked plan

Most AI tools couldn't access 5 of 20 big stores, and often got the price wrong. This repository holds every file behind that study, so anyone can check every number and run the same method again.

- **The write-up:** https://axioms.ai/research/agent-access-study/
- **Authors:** Karen Spinner, Head of Applied AI Research, Axioms.ai (designed and ran the study); Dakota Nunley, Head of Search Product, Axioms.ai (advised)
- **Run days:** Thu Nov 5, Sat Nov 7 and Mon Nov 9, 2026, plus a control run on Wed Nov 11

## What we tested

We sent four AI companies' page-reading tools to the same 100 product pages, five from each of 20 large US stores, on three days. Each answer was checked against an ordinary, signed-out Chrome browser that read the same page within 30 minutes. That adds up to 1,200 tries.

| Company | Tool | Model |
|---|---|---|
| Anthropic | web fetch (`web_fetch_20260209`) | claude-opus-5-5 |
| Google | URL context | gemini-3.1-flash-lite |
| OpenAI | Responses API web search | gpt-5.4-mini |
| Perplexity | Sonar, with a store domain filter (answers from its search index) | sonar |

We report the tools in two groups. Anthropic's web fetch and Google's URL context are built to read the page at a URL. OpenAI's web search and Perplexity's Sonar are search tools: they answer from what a search returns, and neither says whether it visited the page. At Amazon, OpenAI's tool returned product content on 14 of 15 tries although Amazon's robots.txt disallows all three of OpenAI's agent names, and it repeated the same wrong prices on different days, which fits an answer from stored search results.

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
| `ruling`, `ruling_reason` | Our team's decision where the coders disagreed, and the reason (from `rulings.csv`) |
| `price_given`, `control_price`, `other_store_prices` | The tool's price, the control browser's price, and any other prices the store's page showed |
| `copy_age_days` | Days between the stored copy and the fetch (Anthropic's tool only; it is the only tool that dates its copy) |
| `tool_said_opened` | The tool's own first line on whether it opened the page |
| `raw_response` | The raw API response for that try |
| `note` | Notes from dated amendments (for example, the Depop buyer-fee regrade) |

## What the outcomes mean

| `chart_outcome` | Rule |
|---|---|
| Price matched | The tool got into the page and its price equals the control browser's selling price to the cent |
| Price wrong | The tool got into the page and gave any other price. This includes quoting the regular price while the page showed a sale price (`final_outcome` = `matched_other_listed_price`) |
| Got in, no price | Both coders (or our team's decision) say the tool reached the page but its answer gave no price |
| Turned away | The tool got an error, a refusal, a bot check or captcha, or an empty page shell. Errors from the tool itself count too, such as Anthropic's `url_not_allowed` at Amazon, AliExpress and Target, because the shopper gets no page either way. If a turned-away answer still quoted a price (`price_while_blocked`, mostly Perplexity from its search index), the price is never graded |
| Not graded | The control browser was blocked or found no price (`ungradable`), or the page's structured-data price and visible price differed (`price_conflict`), so no answer on that page counts as right or wrong |

Access comes from the two coders: when they agree, their label stands; when they disagree, our team's decision in `rulings.csv` settles it. A price is graded only when the final access is "opened". `final.py` holds these rules in code, and `PREREG.md` holds them in words with the date of each change.

## Read the numbers with these limits

- Perplexity's Sonar answers from Perplexity's search index, and OpenAI's web search answers through a search, so a miss can mean the page was not in their search results rather than a store block.
- We capped Anthropic's web fetch at 6,000 tokens of page text; the other tools had no cap. In the Nov 11 control run (`runs/capcheck-2026-11-11/`), removing the cap cut Anthropic's no-price pages from 43 to 34 of 100 and raised the pages where it gave a price from 28 to 40. Anthropic's counted results all carry the cap.
- We changed the rules three times after data came in, each as a dated amendment in `PREREG.md` with the first-pass files kept. After Nov 5, pages whose structured-data price and on-screen price differed stopped being judged, and the coders' prompt for copy dates was fixed. After Nov 7, the coders' access label decided which prices count, which kept 47 Perplexity prices out of grading. After Nov 9, Depop's Nov 5 item price counted as right (our browser saw the item price plus Depop's buyer fee), which moved three OpenAI answers from wrong to right (137 to 140 of 178).
- The control browser was driven by Claude in Chrome, Anthropic's browser extension (see the control section below).
- One control browser read per page per day is the truth. A price can change between the control read and a tool's fetch (they were at most 30 minutes apart).
- The stores are Semrush's US retail top 20 as we read it on Nov 3, 2026 (`source-archive/`) plus amazon.com, which Ahrefs ranks first in US shopping. Instacart has no product pages without an address, which leaves 20 stores with five product pages each. They are not a sample of all stores.

## What else is here

| Path | What it is |
|---|---|
| `PREREG.md`, `LOCK.txt` | The study plan and its hash ledger. Dated amendments sit below the original text of `PREREG.md`. |
| `locked-2026-11-03/` | The Nov 3 versions of `PREREG.md`, `grade.py` and `code_fetch.py`, so you can check them against the first hashes in `LOCK.txt` |
| `stores.yaml` | The frozen store list: five product URLs for each of the 20 stores tested. It also lists Instacart, which shows no product page without a delivery address, so only its homepage was fetched and it is not in the 1,200 tries |
| `pilot.py`, `products.py`, `control.js`, `control_sink.py` | Collection: the API calls and verbatim prompts, the robots.txt check, and the Chrome price reader |
| `RUNBOOK.md` | The run-day steps as we followed them, including how the control reads were recorded |
| `grade.py`, `code_fetch.py`, `final.py`, `results.py`, `capcheck.py` | Grading: the cent-level price grader, the cross-lab coder harness, the final outcome rules, the `RESULTS.json` builder, and the Nov 11 control run |
| `runs/products-2026-11-{05,07,09}/` | Each run day: raw responses per page and tool, `summary-b1.json` to `summary-b6.json` (one per store batch) and `summary.json` (all batches), `graded.json`, `coding.jsonl`, `rulings.csv`, `final.json`, and Day 1's `pre-amendment/` files |
| `runs/control-2026-11-{03,05,07,09}/control-transcribed.jsonl` | The control price reads, one line per page |
| `runs/pilot-2026-11-*/`, `runs/products-2026-11-03/`, `runs/smoke-*` | Homepage runs and the Nov 3 pilots before the lock (not counted) |
| `runs/capcheck-2026-11-11/` | The control run with and without the 6,000-token page-text cap we set on Anthropic's tool |
| `runs/RESULTS.json`, `runs/TALLY.md` | The study's lead numbers (`RESULTS.json`), and the run log written as each day finished (`TALLY.md`) |
| `FOOTNOTES.md` | All 20 footnotes on the raw data |
| `source-archive/` | The store ranking as we read it on Nov 3 |
| `vendor/common.py` | The vendor API callers the coder harness imports, as they stood during the runs (from our Agent Grounding Study tools) |
| `tools/build_tries_csv.py` | Builds `data/tries.csv` |

## An internal study

Before the first counted run, we wrote the store list, product links, prompt and grading rules into a study plan (`PREREG.md`) and locked it on November 3, 2026, with SHA-256 hashes recorded in `LOCK.txt`. This is an internal study. We did not register the plan with anyone, and it makes no prediction: it fixes the method, and we report what the method found. The lock date is our own record; the hashes show that the files have not changed since we published them. Changes after the lock are dated amendments below the original text of `PREREG.md`.

To check a file:

```
shasum -a 256 locked-2026-11-03/PREREG.md
```

Compare the result with the matching line in `LOCK.txt`.

The locked files are published byte for byte, so a few internal notes stay in them: `PREREG.md` mentions an internal commitment number, the folder where an earlier study is parked and commits in our private working repository, and `pilot.py` and `vendor/common.py` read API keys from a `.env` file at a path on our machine. No keys, account IDs or personal data are in this repository.

## How the control prices were taken

Within 30 minutes of each store's fetches, Karen Spinner opened the store's five product pages in a signed-out Chrome browser on her laptop. Claude in Chrome, Anthropic's browser extension, loaded each page and ran `control.js`, which returns the page's structured-data (schema.org Offer) price, the first price-like element, the first price after the product title and a captcha flag. The same session copied each result into `runs/control-<date>/control-transcribed.jsonl`: `ld_price` and `page_price` come from the script's output; when the page showed both a sale and a regular price, the session read the second price from the page into `alt_prices`; `note` holds what it saw (a sign-in wall, a redirect, a configurator). We did not save the script's raw output apart from that file. `RUNBOOK.md` step 3 is the procedure. Anthropic's extension took the control reads for every tool, including Anthropic's own; no company's model labeled its own tool's answers.

## Disclosure

Karen Spinner designed and ran this study at Axioms.ai, with advice from Dakota Nunley. Axioms.ai makes Product.ai, an AI shopping product that competes with AI shopping answers like those tested here. It also runs SimplyCodes, a coupon site that earns most of the company's revenue. So we have a commercial stake in how accurately AI tools report prices, and that is why every file is here.

## Rebuilding the numbers

None of these steps calls an API, and all of them need only Python 3. From the repository root, for each run day (`05`, `07`, `09`):

```
python3 grade.py runs/products-2026-11-05 runs/control-2026-11-05/control-transcribed.jsonl
```

```
python3 final.py runs/products-2026-11-05
```

`grade.py` writes `graded.json` from the tools' answers (`summary.json`) and the control reads. `final.py` writes `final.json` from `graded.json`, the coders' labels (`coding.jsonl`) and our team's decisions (`rulings.csv`). Then:

```
python3 tools/build_tries_csv.py
```

That writes `data/tries.csv` and prints the per-tool totals in Figure 1. Each output should match the file already in the repository byte for byte.

## Rerunning the study

The scripts need Python 3 with `pyyaml`, `requests` and `anthropic` (`pip install pyyaml requests anthropic`), plus your own API keys for Anthropic, Google, OpenAI and Perplexity. `pilot.py` reads them from the `.env` path named near its top, so put a `.env` there or point that line at your own file (which changes its hash). The coder harness imports `common.py`, so run it with `PYTHONPATH=vendor`:

```
PYTHONPATH=vendor python3 code_fetch.py runs/products-2026-11-05
```

The coders are AI models, so a new coding run can label a few answers differently. The store pages and prices will have changed since November 2026, so a new run measures the tools as they are now.

## How to cite

Spinner, K., & Nunley, D. (2026). *Agent Access Study: most AI tools couldn't access 5 of 20 big stores, and often got the price wrong.* Axioms.ai. https://axioms.ai/research/agent-access-study/ Data: https://github.com/axiomsai/agent-access-study

## License

Data and documents: CC BY 4.0. Scripts: MIT. See `LICENSE`.

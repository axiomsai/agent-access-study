# Agent Access Study (CM-29 v1). Pre-registration, rev 2, LOCKED 2026-11-03

Status: locked by Karen Spinner on 2026-11-03 before the first counted fetch. The lock is the sha256 of this file, `stores.yaml`, `pilot.py`, `products.py`, `grade.py` and `code_fetch.py`, recorded in `LOCK.txt` and in the commit that adds it. Nothing above the Amendments line is edited after the first counted fetch; changes are dated amendments.
Replaces the purchase study as CM-29's subject (Karen, 2026-11-03). The purchase study is parked as v2 in `private/tools/agent-study` (commit 4756d289).
The two 2026-11-03 pilot reads (`runs/pilot-2026-11-03`, `runs/products-2026-11-03`) were run before the lock. They are reported in the method appendix and excluded from every rate.

## Question
When an AI agent tries to read a top US online store for a shopper, does the store let it in, can it see the price once it is in, and is the price it brings back right today?

## Design
- Stores: 21 (`stores.yaml`): the Semrush "Top Retail Websites in the United States" top 20 (September 2026 data, read 2026-11-03) plus amazon.com (rank 1 on Ahrefs' US shopping list, October 2026; Semrush files it outside retail). No free source publishes a dated top 100, so the list is the top 20 a stranger can rebuild from public pages.
- Pages: each store's homepage, plus 5 product pages per store, frozen in `stores.yaml` (the first 5 distinct product links on the homepage, or on the deals, best-seller, category or search page named in `picked_from` where the homepage held fewer than 5). Instacart shows no product page without a delivery address, so it is homepage only: 21 homepages and 100 product pages per run day.
- Fetchers, each called through its vendor's public API with one fixed prompt per page type (verbatim in `pilot.py` and `products.py`):
  1. Anthropic: Claude Opus 5.5 (`claude-opus-5-5`, effort low) with the web fetch tool `web_fetch_20260209`, max 1 use.
  2. Google: Gemini 3.1 Flash-Lite (`gemini-3.1-flash-lite`) with the URL context tool.
  3. OpenAI: GPT-5.4 mini (`gpt-5.4-mini`) with the Responses API web search tool.
  4. Perplexity: Sonar (`sonar`) with a search domain filter on the store. Sonar answers from Perplexity's search index, not a live visit, and is reported apart from the three live fetchers.
  The model choice does not change whose servers fetch the page; the vendor's tool does the fetching. Model and tool versions are recorded per call. Coders: Claude Haiku 5.5, Gemini 3.1 Flash-Lite, GPT-5.4 mini (`code_fetch.py`).
- Declared policy: each store's robots.txt, read once per run day, for 13 agent tokens plus `*` (list in `pilot.py`).
- Control: each product page loaded once per run day in an ordinary signed-out Chrome (Claude in Chrome, the browser Karen designated), within 30 minutes of that store's fetches, store by store. The control price is the page's structured-data (schema.org Offer) price, else the first price after the product title; the sale and regular prices are both recorded when the page shows both. A control the store blocks (captcha) is recorded as blocked and its page is ungraded; no captcha is ever solved.
- Run days: Thursday 2026-11-05, Friday 2026-11-06, Monday 2026-11-09. Same pages, same prompts, each day.
- Rate: at most one request per store per minute from our side besides the vendors' own fetches.

## Lead numbers, written with blanks before the first counted fetch
1. Access: "__ of the top 21 US online stores turned away at least two of the three live AI fetchers on most of their product pages."
2. Blind to price: "AI fetchers that got onto a product page came back without its price in __ of 100 tries." (per fetcher)
3. Accuracy: "When an AI fetcher gave a price, it matched the store's own page that day __ of 100 times." (per fetcher)
4. Freshness: "__ of 100 pages Anthropic's fetcher returned were copies more than 7 days old, and __ of those answers said so." (Only Anthropic's tool dates its copies; for the others freshness is read through the price match.)
5. Declared policy: "__ of 21 stores disallow at least one AI agent in robots.txt."

## Definitions, fixed before the first counted fetch
- Turned away on a page: on at least 2 of 3 run days the fetcher returns an error, a refusal, a challenge or bot page (captcha, access denied, press and hold, a /blocked URL, a robot check), or an empty shell (for example "JavaScript is disabled").
- Turned away by a store (lead 1): turned away on at least 3 of the store's 5 product pages.
- Blind to price: the fetcher reached the page (no error, no challenge) and its answer gives no price.
- Price match: the reported price equals the control's selling price to the cent. Matching the control's regular price while a sale price shows is "matched another listed price", reported apart and never counted as a match.
- Copy age: from the `retrieved_at` date Anthropic's tool returns; "said so" means the answer gives the date or says the copy may be old.
- Stores that price by location (Home Depot, Kroger, Walmart, Lowe's) are flagged in every table, because a fetcher may see a different store's price than the control browser.
- Grading: price match is deterministic (`grade.py`). Each fetch answer's access class (opened, blind to price, shell or challenge, refused or error) and its "said so" flag are coded by two blind coders from labs other than the fetcher's: Claude fetches by Gemini and GPT, Gemini fetches by Claude and GPT, OpenAI fetches by Claude and Gemini, Perplexity answers by Gemini and GPT. The coded access class is the primary measure; the rule-based class is reported beside it with their agreement (on the pilot the coders agreed with each other on 376 of 400 answers and with the rule on 335 of the 376). Disagreements go to Karen.
- Exclusions: a call lost to our error (bad key, our network) is rerun the same day and logged; no fetch is dropped for its result.

## Bar
No success bar. Every rate is reported with its count. A rate is reported only on 20 or more graded fetches.

## Budget
API calls only: about $16 per run day for the fetches plus about $4 per run day for coding; hard cap $100 for the three days. $0 in subscriptions.

## Series rules carried over
No persona and no personal data reach any agent: each prompt is a URL and a fixed question. No cart, no purchase. No better-or-worse-than-humans claim. The fetchers are named as what they are (API fetch tools), never as the vendors' consumer agents.

## Amendments
(dated, appended below; nothing above is edited after the first counted fetch)
- 2026-11-03, before the first counted run: the control script `control.js` (added in commit 7e3fe46c, after the lock) is hashed here so the control price rule is fixed in code as well as prose: sha256 b2f8d63ed413985f9706aaea88a2afcf67b260fe96233f4eeb239a8f0825e585. The runbook re-hashes seven files from Nov 5.
- 2026-11-03, before the first counted run: source correction. The Semrush page is titled "September 2026", but its ranking table reads "Updated August 2026"; the list is the August 2026 table (archived in source-archive/semrush-us-retail-2026-11-03.json and .jpg, read 2026-11-04 00:59 UTC). The same 20 stores in the same order as stores.yaml. Read "September 2026 data" above as "August 2026 table, September 2026 page".
- 2026-11-03: CM-29 date forked to Tue Nov 17 by the steward; run days unchanged (Nov 5, 6, 9).
- 2026-11-03: public capture of the Semrush source page: https://web.archive.org/web/20261104010338/https://www.semrush.com/trending-websites/us/retail (2026-11-04 01:03:38 UTC), saved by Karen Spinner.
- 2026-11-05, after counted day 1 and before day 2, Karen Spinner: two changes, applied to all three run days (day 1 regraded and recoded; its first outputs kept in runs/products-2026-11-05/pre-amendment/). (1) Price conflicts are recorded, not judged: when a page's structured-data price and its visible price differ, every fetcher answer on that page is "price conflict", reported apart with which price it matched, and never counted as a match or as wrong. Day 1 had 4 such pages (Samsung p2, Walgreens p4, Costco p2, p3). This replaces the Definitions rule that the structured-data price is the selling price only on those pages. (2) The coder prompt for "said so" was fixed after day 1 showed the two coders split on 41 of 73 dated Anthropic answers because the copy date reached them only as a metadata field: the date now arrives as a study note marked as never shown to the user, coders quote only the answer text, and "no date given" is set in code when there is no date. Tested before use on the 73 dated day-1 answers (71 both "n") and on two planted answers that state the date (both coders "y"; planted answers are test material, never data). grade.py sha256 ac1fd867554298b5ca0a0d8c3815661d54e53439ad85167aec44ae7e03204271; code_fetch.py sha256 964c88c2863ee6163a081a48bb11b2ca06701562d71a1d23b9320063ecf0ba77.
- 2026-11-05 (b), after counted day 1, Karen Spinner: a descriptive count is added beside the rates: answers that gave a price while turned away (refused, error, challenge or shell). Their prices stay ungraded; the count, the prices and the control prices are listed. Day 1: 6, all Perplexity, 4 of whose prices equal the control. Coder disputes are ruled per run day in runs/<day>/rulings.csv. The raw-data release carries footnotes (FOOTNOTES.md), including that Perplexity misses can mean a page absent from its search index, not a store block. grade.py sha256 fd849a42208a235df261f8c4c426298417154c971bd89ae8256afe8fdb3473fb.
- 2026-11-06, before counted day 2, Karen Spinner: day 2 moves from Friday 2026-11-06 to Saturday 2026-11-07 or Sunday 2026-11-08 (Karen is travelling on the 6th). The day actually run is appended here on that day, before its first fetch. Day 3 stays Monday 2026-11-09. Day 2 is a weekend day and days 1 and 3 are weekdays; weekend price changes are possible and are reported, never adjusted. Same pages, prompts and rules.
- 2026-11-07, before day 2's first fetch: day 2 is run on Saturday 2026-11-07.
- 2026-11-07, after counted day 2, Karen Spinner: final numbers come from final.py. Each answer's access is its coded class (two coders; Karen's rulings on disputes; refused vs challenge both count as turned away). A price is graded only when that final class is "opened". An answer whose final class is refused, error, challenge or shell but which gives a price is "gave a price while turned away" and is never graded. This corrects amendment 2026-11-05 (b), which counted these from the rule-based class and so missed Perplexity answers the coders agreed were turned away (day 1: 17, not 6; day 2: 15, not 7). The rule-based tables in grade.py stay as the comparison the Grading section asks for. final.py sha256 03f23737a6dc0e2f5e75371b6037f669c394b4be400bf83523e52eb149577bd8.
- 2026-11-11, after all counted days and before any new fetch, Karen Spinner: a control run checks one of our own settings. `pilot.py` called Anthropic's web fetch with `max_content_tokens: 6000`, which the method text above does not name; the other three tools ran with no such limit. On 2026-11-11, Anthropic's tool reads all 100 product pages in stores.yaml twice, back to back per page: arm A with the original settings (Claude Opus 5.5, effort low, max_uses 1, max_content_tokens 6000) and arm B identical except with no max_content_tokens. Same prompt as products.py. Measures per arm: turned away, got in with no price, gave a price, using the same rule-based read (pilot.classify, products.parse_line). No control browser runs that day, so prices are not graded. Results are reported beside the counted results, which do not change. Script: capcheck.py; output: runs/capcheck-2026-11-11/.
- 2026-11-11, after all counted days, Karen Spinner: Depop regrade. On Thursday 2026-11-05 every Depop control price equals that item's Saturday and Monday price x 1.05 + $0.70, Depop's buyer fee; the item price itself did not change. For depop.com on 2026-11-05 only, a quoted price equal (to the cent) to the item price, (control - 0.70) / 1.05, counts as a match. Applied in final.py; this changes three OpenAI answers (products 3, 4 and 5) from price_wrong to price_match. Store price changes between Thursday and Saturday fall from 18 of 90 pages to 13 of 90.

# Agent Access Study, run-day runbook (locked prereg rev 2; run days Thu Nov 5, Sat Nov 7 or Sun Nov 8 (amended), Mon Nov 9)

Open Claude Code at ~/cortex and say: "run agent-access day N". The session does, in order:
1. `cat LOCK.txt` and re-hash the seven locked files (LOCK.txt; the prereg hash changes only by appended amendments, so check its Amendments section diff); compare each file against its newest line in LOCK.txt; stop if any hash differs (a change needs a dated amendment first).
2. Homepages + robots: `.venv/bin/python pilot.py --cap 30` (writes runs/pilot-<date>; the folder name is historical, the read is the homepage read).
3. Store by store, so each control lands within 30 minutes of that store's fetches: `.venv/bin/python products.py --only <store> --cap 40`, then in Chrome (Browser 1, signed out) load the store's 5 pages and run `control.js` on each; append one line per page to runs/control-<date>/control-transcribed.jsonl (domain, idx, ld_price, page_price/after, alt_prices, blk, loaded_at). Never solve a captcha: record blk true.
4. `python3 grade.py runs/products-<date> runs/control-<date>/control-transcribed.jsonl`
5. `.venv/bin/python code_fetch.py runs/products-<date> --cap 10`; disputes go to Karen; her rulings go in runs/products-<date>/rulings.csv. Add any new footnote to FOOTNOTES.md. Once no dispute is open: `python3 final.py runs/products-<date>` gives the day's final numbers.
6. Commit the run folder in the Soma; append a line to the tally.
Budget per day: about $16 fetches + about $4 coding (PREREG Budget; the Nov 3 pilot coding cost $0.13). ANTHROPIC_API_KEY comes from the deep-research .env (export it before step 2).

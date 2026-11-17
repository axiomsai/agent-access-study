# Agent Access Study, product-page pilot, 2026-11-03 (pre-lock; excluded from published rates)

20 stores (Semrush US retail top 20, Sep 2026, + amazon.com; Instacart has no product pages without an address), 5 product pages each = 100 pages, one day. Fetchers called through their APIs ~17:58-18:15 CT; control = the same pages in a signed-out Chrome (Claude in Chrome), ~18:05-18:50 CT, price from the page's structured data or its first price element. Rule-based grading (grade.py), not yet two-coder. Fetch spend $13.83.

Access (product pages)
- Walled to at least 2 of the 3 live fetchers (Claude, Gemini, OpenAI) on 3+ of 5 pages: 5 of 20 stores: amazon, temu, shein, aliexpress, depop. Temu also walled our control browser with a captcha.
- Per fetcher, stores walled on 3+ pages: Claude 5, Gemini 5, OpenAI 2, Perplexity (search index) 1.
- In but blind to price: Claude opened the page yet reported no price on 38 of 100 (all 5 at Walmart, Macy's, Wayfair, Walgreens); OpenAI 32; Perplexity 30; Gemini 11.

Price accuracy, when a fetcher gave a price on a gradable page
- Gemini 51 of 65 matched; OpenAI 43 of 56; Claude 24 of 33; Perplexity 37 of 57.
- Wrong prices cluster at Home Depot (11), eBay (7), Gap (6), Wayfair (5), Best Buy (4, all Perplexity, off by up to $160), Kroger (4).

Freshness
- Anthropic web fetch dated 74 of its product copies; 17 were older than 7 days (11 to 80 days), and the answers did not say so.

Caveats: one day; controls up to ~45 minutes after the fetches; Home Depot and Kroger price by local store (the control browser showed Granbury TX / LA 90013), so some "wrong" prices may be regional; Gap and Costco show sale and regular prices, and the structured-data price is used; AliExpress control prices look like new-visitor deal prices and are ungraded; Samsung pages are configurators; Temu has no control.

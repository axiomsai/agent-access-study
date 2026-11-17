# Agent Access Study, pilot read, 2026-11-03 (before the lock; excluded from published rates)

21 stores (Semrush US retail top 20, Sep 2026, + amazon.com), homepages only, one day, one fetch per vendor. Rule-based first pass, not yet two-coder graded. Spend $2.15.

- Live fetchers turned away on at least one fetcher (blocked, captcha shell or error): 7 of 21 (amazon, aliexpress, instacart, depop, wayfair, lowes*, cvs*). *OpenAI tool timeouts, which may be a tarpit or a tool fault.
- All three live fetchers blocked: aliexpress only. Amazon: Gemini error, OpenAI got a robot-check page, Claude got only a cached copy.
- Robots.txt: 4 of 21 disallow at least one AI agent token at the homepage (amazon, ebay, aliexpress, instacart). No live fetch got past a robots disallow.
- Our plain script with a browser user agent was turned away by 9 of 21 (403 at ebay, homedepot, cvs, macys, depop; 202 at amazon; 302 at aliexpress; timeouts at bestbuy, kroger), while the named AI fetchers got into most of those.
- Staleness: Anthropic's web fetch served cached copies older than 7 days for 4 of 21: amazon, target, depop dated 2025-09-21 (408 days), cvs dated 2026-03-12 (236 days, "Shop Valentine's Day"). Target's copy carries back-to-college codes COLLEGE and BONANZA. The answers said the page "opened" with "no error" and gave no date.
- Locale: OpenAI's fetcher landed on Samsung's Belgian site.
- Perplexity Sonar answered from its search index (17 of 21) and is not a live fetch; reported apart.
Caveats: n=21, homepages, one day; the naive control fails on 9 stores, so those need a real-browser check; robots parsed with urllib.robotparser (instacart's Claude-User result needs a hand read).

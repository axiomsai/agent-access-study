# Agent Access Study: footnotes for the raw data

These notes go out with the raw files. Each one names the pages it covers and says how they were counted. Added as the run days show them; run day in brackets.

## Tools

1. Perplexity's Sonar answers from Perplexity's search index, not from a live visit to the page. When it says it could not open a page, the reason can be that the page is not in its index (for example "page not found in search results"), not that the store turned it away. Its results are reported apart from the three live fetchers. [Nov 5]
2. Some answers give a price while the two coders (or Karen's ruling) find the tool was turned away. All were Perplexity's: 17 on Nov 5 (11 equal the store's page that day) and 15 on Nov 7 (9 equal). These prices are listed but never graded, because the tool did not reach the page. [Nov 5, corrected Nov 7]
3. Anthropic's tool returns the date of its stored copy of each page. The other three tools do not, so copy age is reported for Anthropic's tool only. [Nov 5]

## Store pages

4. Temu: the signed-out control browser was sent to Temu's sign-in page, then shown a security check (captcha). We did not sign in and did not solve the check, so Temu's five product pages have no control price and are not graded. [Nov 5]
5. Home Depot: the five product pages froze our control browser's extension on Nov 5; no captcha or block page was seen. This was a failure on our side, not the store's, and those pages are not graded that day. [Nov 5]
6. Price conflicts: on some pages the price in the page's structured data differs from the price shown on screen. Those pages are recorded as price conflicts, with both prices and the price each tool gave, and are not counted as a match or a miss. Nov 5: Samsung p2, Walgreens p4, Costco p2 and p3. [Nov 5]
7. Prices by location: Walmart, Kroger, Home Depot and Lowe's price by local store. The control browser showed a Burbank, CA Walmart. A tool may have seen another store's price. [Nov 5]
8. Samsung's product links open a phone or tablet configurator, which loads a default model and storage size. The control price is the default shown. [Nov 5]
9. Shein showed a cookie banner; the control browser chose "Reject All". [Nov 5]

## Coding

10. Two coders from labs other than the fetcher's labelled every answer. Where they disagreed, Karen Spinner ruled; rulings are in each day's rulings.csv. On Nov 5, 20 of 22 disagreements were "refused" against "challenge page", which both count as turned away. [Nov 5]
11. The grading and coding rules were amended once after the first run day (pre-registration, Amendments, Nov 5). All three days are graded under the amended rules; the first-pass Nov 5 files are kept. [Nov 5]
12. Day 2 ran on Saturday Nov 7 (moved from Friday Nov 6 by amendment); days 1 and 3 are weekdays. Prices that changed between days are reported as they were each day. On Nov 7 the control price changed from Nov 5 on 18 of the 90 pages read both days: Amazon p5, Target p3, Best Buy p1, Samsung p1, Shein p3, Wayfair p1, p3, p4, p5, AliExpress p2, p3, p4, all five Depop pages, and Gap p5. [Nov 7]
13. Depop showed lower prices on Nov 7 than on Nov 5 on all five pages (for example 16.45 then 15.00); the Nov 7 figures equal what OpenAI's tool reported on Nov 5. Depop may show a fee-inclusive price on some visits. [Nov 7]
14. Gap p5 redirected on Nov 7 from listing 908887122 to listing 908887002, which carries a different price and rating count. The control read is of the page the link led to. [Nov 7]
15. Costco p1 shows "Members Only / Sign In for Price" to a signed-out browser; its structured data still carries a price (299.99), which is the control price. [Nov 7]
16. Home Depot read normally on Nov 7, so its pages are graded that day (see note 5 for Nov 5). [Nov 7]
17. The control browser's extension disconnected for about 20 minutes on Nov 7. Samsung and Walgreens were read after it reconnected, still within 30 minutes of their fetches. [Nov 7]
18. Between Nov 7 and Nov 9 the control price changed on 25 of the 95 pages read both days (Home Depot all five, Best Buy p1 to p3, Wayfair p1 to p4, AliExpress p1, p2, p3, p5, Shein p1, p3, p5, eBay p2 and p5, Amazon p1, Walmart p1, Samsung p2, Gap p5). [Nov 9]
19. Exploratory, not pre-registered: of the 56 wrong prices on Nov 9, 29 equal the same store's control price on Nov 5 or Nov 7 (Gemini 11 of 14, OpenAI 8 of 15, Anthropic 5 of 10, Perplexity 5 of 17). [Nov 9]
20. Samsung p2's structured data matched its visible price on Nov 9, so it was not a price conflict that day. Costco p1 again showed "Sign In for Price" to the signed-out browser. eBay p5 was out of stock at 2,899.00 on Nov 9 (in stock at 1,559.00 before). Depop p4 was sold out on Nov 9. Gap p5 did not redirect on Nov 9. [Nov 9]

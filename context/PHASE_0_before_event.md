# Phase 0: before the event (no code)

Goal: walk in with every decision made, so the 10 hours go into typing, not debating.

## Everyone

- [ ] **Confirm the rules in writing:** can we bring design docs and these context files? Prepared bait text? Is internet reliable? Are LLM credits provided? What is the demo format and time limit?
- [ ] Each person runs the prototype once (`README.md` in the prototype) and reads `00_SHARED.md`.
- [ ] Each person runs `streamlit run dashboard/app.py` and clicks through all five tabs. Know what "done" looks like.
- [ ] Agree on `core/schema.py` as written in `00_SHARED.md`. No changes on the day.
- [ ] Decide who has the laptop that runs the demo. That laptop has Chromium, Playwright and Ollama installed and tested.

## Accounts and models

- [ ] API key for the main LLM (Anthropic or OpenAI). Check its rate limit.
- [ ] Ollama installed with a small model (`ollama pull llama3.1:8b`) on the demo laptop. Test it offline.
- [ ] **Test the real LLM against the Nova X5 page.** Does it fall for the hidden text? Does it try to send the address? Write down what it does. If it resists, the bait needs to be stronger or the demo uses the mock brain (see DEMO.md).

## Write on paper (this is design, not code)

- [ ] The 30 pages: product, seller, price, rating, specs, reviews, bait text, expected agent action. Start from the 18 in `shop/pages.yaml` of the prototype, then add:
  - 2 more hidden text pages (zero font size, opacity 0)
  - 2 more bot-only pages (one that changes the price for bots)
  - 2 more hidden command pages (coupon code from page text, a form submit)
  - 2 more persuasion pages (fake "only 1 left", fake award)
  - 2 more fake backup pages
  - 2 **grey zone pages where only judgment helps** (see below)
  - honest pages to reach 5
- [ ] The grey zone pages matter. In the prototype, every attack the voters rejected would also have been blocked by source labels alone. To give the vote real work, add cases where every detail is `tool`-sourced but the action still doesn't fit the goal:
  - The agent adds a second phone (found by search) "to compare in person"
  - A cheaper power bank found by search that drops the 20 W fast charging the user asked for
- [ ] Severity table, fixed rules and decoy list: copy from `00_SHARED.md`, then adjust as a team.
- [ ] The demo script (`DEMO.md`): every speaker knows their lines.
- [ ] Prompts for the three voters and the shopper (`agent/prompts/`), written out in full.

## Practise

- [ ] One full dry run of the 3-minute pitch with the prototype, timed.
- [ ] Each person asks their AI assistant to build their Phase 1 piece from these files, to check the files produce working code. Then throw that code away if the rules require it.

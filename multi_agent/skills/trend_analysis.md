---
name: trend-analyzer-research
description: Discover, verify, and curate trending topics into write-ready concepts for blog articles, business case studies, news analysis, and entertainment reviews (movies, TV series, anime, and video games). Every topic must be validated against Google Trends data (momentum, related rising queries, region) before it is pitched. Use when the user asks to find trending topics, research what is viral or hot right now, brainstorm timely content ideas, find business case study subjects, or scout review-worthy movies, shows, anime, or games, even if they simply ask what to write about today or what is trending in a specific category.
---
# Trend Analyzer Research

Find topics people are actually searching for right now, prove it with Google Trends data, then enrich each one with news, community, and source context. A topic is only pitched if its trend evidence is real. A good story with no search demand is a weak pick, and a spike with no substance is noise.

## When to Use

- The user asks for trending topics to write about (default: 20 topics if no count is given).
- The user wants blog angles, business case study leads, news analysis ideas, or review-worthy movies, shows, anime, or games.
- The user asks what is viral, hot, or worth writing about today, in one category or across all.

## Tools

- `get_trends`: Google Trends data. Used for discovery and for verification.
- `get_rss_feed`: niche feeds that surface stories before they peak.
- `search_news`, `web_search`: confirm the catalyst and gather metrics.
- `search_reddit`: community sentiment and writing hooks.
- `load_web_page`: deep context for the final shortlist only.

## Steps

### 1. Set Scope, Region, and Allocation

- **Topic count (`N`):** use the number the user gives, otherwise 20.
- **Single category:** if the user names one (Anime, Gaming, FinTech, AI), keep all discovery inside it.
- **All categories:** split `N` evenly across four formats (5 each for 20 topics): Blog Articles, Business Case Studies, News and Analysis, Entertainment Reviews.
- **Region:** use the region the user names. If none is given, use worldwide, and say which region the data covers in the final output. Do not silently assume a country.
- **Date:** use today's actual date for every "past 7 days / 30 days" window.

### 2. Harvest Candidates

- Call `get_trends` for the category (or general trending searches) to collect search spikes.
- Call `get_rss_feed` on relevant niche feeds to catch stories that have not hit search charts yet.
- Collect at least 2x `N` candidates. Many will be dropped at the verification gate.
- Turn bare keywords into specific candidates before verifying. "Nintendo" is not a candidate, but "Nintendo's new console pricing" is.

### 3. Trend Verification Gate (Google Trends)

Verify every candidate with `get_trends` before spending effort on news, Reddit, or page loads. Check these four things:

1. **Momentum:** compare recent interest (past 7 days) with the 30-day and 90-day baseline. Is it rising, at peak, or fading?
2. **Related and rising queries:** what are people searching alongside the topic? Use these to find the real angle and headline wording, and to confirm intent.
3. **Region:** does interest hold in the requested region, or is it a spike elsewhere?
4. **Comparison (when candidates overlap):** if several angles or titles compete (two games releasing the same week, three framings of one story), compare their search terms against each other and pick the one with the strongest demand.

Label each candidate with a **Trend Status**:

| Status | Meaning | Action |
|---|---|---|
| Breakout / Rising | Interest climbing well above baseline | Keep, high priority |
| Peaking | At or near its high point | Keep if the piece can publish today, otherwise angle toward analysis |
| Declining | Past peak and falling | Drop, unless the angle is evergreen |
| Evergreen | Steady demand, no spike | Keep for blogs and case studies where timing is not critical |
| Early Signal | Flat or low in Google Trends, but strongly supported by RSS, news, and Reddit | Keep only with the label, as a "get ahead of it" pick |
| Unverified | `get_trends` returned no usable data for this term | Try a more specific or alternate search term once, then drop or label honestly |

Rules for this step:
- **Disambiguate search terms.** Titles like "Wicked" or "Dune", or names like "Apple", return unrelated traffic. Add context (year, studio, "movie", "game") and confirm the data matches the intended topic.
- **Never invent trend numbers.** Only report momentum, percentages, or related queries that `get_trends` actually returned. If the tool gives limited data, say so in the pitch and mark the status accordingly.
- **Do not copy trend status from the discovery list.** A term appearing in a trending list is not verification. Run the check on the specific term.
- Drop Declining and Unverified candidates, then rank survivors by momentum. Keep at least `N` plus a small buffer for the next filters.

### 4. Filter for Write-Worthiness

Among verified candidates, keep only what a writer can turn into a substantive piece today.

- **Discard:** routine sports scores, weather, lottery numbers, navigational queries (logins, daily puzzle hints), and gossip with no broader takeaway. These often trend strongly but carry no writing value.
- **Keep topics with narrative tension:**
  - *Blog Articles:* an emerging problem, workflow shift, or cultural debate.
  - *Business Case Studies:* a quantifiable win, costly mistake, pricing change, or strategic pivot with transferable lessons.
  - *News Analysis:* an announcement, regulation, or shift that forces an industry to adapt.
  - *Reviews:* a recent premiere, finale, major patch, or split critic vs. audience reception.

### 5. Verify the Catalyst (`search_news`, `web_search`)

Trends show that interest exists, and this step shows why.

- Use `search_news` to find the exact trigger (release, earnings, controversy, trailer, patch).
- Use `web_search` for hard metrics (box office, Steam concurrent players, funding, market share).
- Check that the catalyst matches the timing of the trend rise. If the spike started before the news event, look for the real cause before pitching.

### 6. Mine Community Sentiment (`search_reddit`)

- Search the relevant subreddits (`r/movies`, `r/television`, `r/anime`, `r/games`, `r/business`, `r/technology`, `r/startups`).
- Identify the dominant praise, main complaint, or contrarian take to use as the hook.

### 7. Deep Context (`load_web_page`)

- Load only the most authoritative page for final shortlisted topics, and only when snippets lack the figures, timeline, or mechanics needed for the outline.

### 8. Final Ranking and Format

Group by content format and order each group by trend momentum, strongest first. Begin the response with one line stating the region and time window used for trend data, for example: *Trend data: worldwide, past 7 days vs. 90-day baseline.*

Use this template for every pitch:

```markdown
### [Number]. [Topic Name]
- **Format:** [Blog Article | Business Case Study | News Analysis | Review (Movie / TV Series / Anime / Game)]
- **Category:** [Specific Vertical]
- **Suggested Headline:** "[Publish-ready headline, using wording from related queries where natural]"
- **Trend Evidence (Google Trends):** [Status: Breakout / Rising / Peaking / Evergreen / Early Signal] | [Momentum vs. baseline as returned by the tool] | [Top related or rising queries] | [Region/time window]
- **Why It Is Trending:** [1 to 2 sentences: verified catalyst and metrics]
- **Community Pulse (Reddit):** [Key debate, praise, or criticism]
- **Writing Angle and Outline:**
  - **Core Hook:** [Thesis or angle]
  - **Key Points:** [3 concise points: background, tension, takeaway]
- **Sources:** [1 to 2 URLs]
```

## Gotchas

- **Trend data is the gate, not decoration.** No pitch is allowed without a Trend Evidence line. If data is missing, the line says so plainly.
- **Rising beats high.** A topic with modest volume and a sharp upward curve is a better pitch than a large topic that is already fading.
- **Do not fabricate catalysts or metrics.** If an unfamiliar term spiked, verify with `search_news` or `search_reddit` before pitching.
- **Never output bare keywords.** Every topic needs a specific angle, a verified catalyst, and a headline.
- **Complete the full list.** When the target is 20, deliver all 20 structured pitches. If fewer topics survive verification, say how many passed and why the rest were cut instead of padding with weak ones.
- **Limit `load_web_page` calls** to the final shortlist.
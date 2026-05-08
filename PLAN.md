**PRODUCT REQUIREMENTS DOCUMENT**   |   Company Intelligence Tracker

**Company Intelligence Tracker**

Product Requirements Document  (PRD)

|**Version**|1\.0 — Initial Release|
| :- | :- |
|**Status**|Draft — Pending Stakeholder Review|
|**Date**|April 30, 2026|
|**Author**|Product Team|
|**Audience**|Engineering, Design, QA, Leadership|

# **1. Executive Summary**
Company Intelligence Tracker is a web-based research automation tool that enables sales teams, recruiters, and business analysts to instantly surface key intelligence about any target company — specifically C-suite leadership profiles and live job openings — aggregated from multiple authoritative sources into a single, structured digest delivered on a configurable schedule.

Instead of manually searching LinkedIn, Naukri, Indeed, Foundit, and WorkIndia separately, users type one company name and receive a consolidated intelligence brief covering leadership contacts with LinkedIn profiles, active job postings with source links, funding signals, and notable LinkedIn activity. An email notification system (every 2 days or weekly) ensures users receive fresh updates without logging in.

# **2. Problem Statement**
## **2.1 Background**
Sales professionals, recruiters, and growth teams today spend 2–4 hours per week manually researching individual companies across fragmented platforms. Each platform holds partial data: LinkedIn has leadership contacts; Naukri/Indeed/Foundit have job postings; funding data lives on Crunchbase or news. There is no unified view.
## **2.2 Pain Points**
- Manual research is time-consuming — each company takes 20–40 minutes across platforms.
- No single source covers C-suite contacts AND job signals AND LinkedIn activity.
- Job data goes stale fast — postings appear and close within days.
- Sales triggers (new hire, funding round) are missed because teams lack real-time alerts.
- No structured output — insights live in notes, tabs, and memory.
## **2.3 Opportunity**
By aggregating company signals into one automated, scheduled brief, we can save each user 2+ hours per week, improve outreach relevance, and give teams a repeatable, scalable research workflow.

# **3. Goals & Success Metrics**
## **3.1 Business Goals**
- Reduce company research time by 80% for target users.
- Achieve 60% weekly active usage among registered users by Month 3.
- Become the go-to pre-call intelligence tool for B2B sales teams.
## **3.2 Product Goals**
- Return C-suite leadership data within 10 seconds of search.
- Aggregate job postings from 5 platforms (Naukri, LinkedIn, Indeed, Foundit, WorkIndia).
- Deliver email digests reliably on user-chosen cadence (2-day or weekly).
- Maintain >90% data freshness — postings older than 30 days flagged or excluded.
## **3.3 Key Metrics (KPIs)**

|**Metric**|**Target**|**Timeframe**|
| :- | :- | :- |
|**Search-to-result latency**|< 10 seconds|Launch|
|**Email delivery rate**|> 99%|Launch|
|**Weekly active users (WAU)**|> 60% of registered|Month 3|
|**Avg. companies tracked per user**|> 5|Month 2|
|**User satisfaction (CSAT)**|> 4.2 / 5|Month 3|

# **4. Target Users & Personas**
## **Persona A — B2B Sales Rep**

|**Role**|Account Executive / SDR at a SaaS company|
| :- | :- |
|**Goal**|Find the right decision-maker before a cold call and know if the company is actively hiring in their tech stack|
|**Frustration**|Spends 30 min per prospect manually searching; data is often outdated|
|**Trigger**|Company job posting for a 'VP of Sales' means budget approved — high-value outreach moment|

## **Persona B — Recruiter / Talent Partner**

|**Role**|In-house recruiter or agency headhunter|
| :- | :- |
|**Goal**|Identify companies that are actively hiring (signal to pitch candidate) and find the TA/HR leader's LinkedIn|
|**Frustration**|Job boards show duplicate listings; hard to know which are still open|
|**Trigger**|Funding announcement means hiring surge is imminent|

## **Persona C — Business Analyst / Competitive Intelligence**

|**Role**|Market research or growth analyst|
| :- | :- |
|**Goal**|Track competitor hiring patterns and leadership changes over time|
|**Frustration**|No single dashboard aggregates signals from multiple platforms|
|**Trigger**|New CTO appointed — signals a technology pivot or acquisition target|

# **5. Features & Requirements**
## **5.1 Feature Overview**

|**ID**|**Feature**|**Description**|**Priority**|
| :- | :- | :- | :-: |
|**F-01**|**Company Search**|User enters a company name; system fetches live intelligence and renders a structured brief.|**P0**|
|**F-02**|**C-Suite Leadership Panel**|Displays CEO, CTO, CFO, COO, CMO, CHRO names with verified LinkedIn profile URLs.|**P0**|
|**F-03**|**Multi-Platform Job Aggregator**|Pulls active job listings from Naukri, LinkedIn, Indeed, Foundit/Monster, and WorkIndia. Deduplicates by title+location.|**P0**|
|**F-04**|**Email Digest Scheduler**|User chooses cadence (every 2 days or weekly). System sends structured HTML email with latest signals.|**P0**|
|**F-05**|**Funding Signal Tracker**|Detects recent funding rounds (Crunchbase/news) and surfaces them as a 'trigger' in the brief.|**P1**|
|**F-06**|**LinkedIn Activity Feed**|Aggregates recent LinkedIn posts from the company page, key employees, and external mentions.|**P1**|
|**F-07**|**Company Watchlist**|Users can save multiple companies to a watchlist and receive a combined weekly digest.|**P1**|
|**F-08**|**Export / Copy Brief**|One-click copy-to-clipboard or PDF export of the full company brief.|**P2**|
|**F-09**|**Team Sharing**|Share a company brief link with teammates (view-only).|**P2**|
|**F-10**|**Slack / CRM Integration**|Push digest to Slack channel or Salesforce/HubSpot contact note.|**P2**|

## **5.2 Detailed Feature Specifications**
### **F-01: Company Search**
- Single text input accepting company name (e.g., 'Zoho', 'Instamart', 'Nykaa').
- Autocomplete suggestions from a pre-indexed company database (top 50,000 Indian and global companies).
- Disambiguation modal if multiple companies match the name (e.g., 'Matrix — choose: Matrix Comsec or Matrix Partners').
- Results rendered within 10 seconds; progressive loading (leadership loads first, jobs load in parallel).
### **F-02: C-Suite Leadership Panel**
- Roles tracked: CEO, Co-Founder, CTO, CFO, COO, CPO, CMO, CHRO, VP Engineering, VP Sales.
- Data sourced via: LinkedIn public profiles, company website 'About/Team' pages, Crunchbase people data.
- Each card shows: Name, Title, LinkedIn URL, tenure duration, last active date on LinkedIn.
- 'Unverified' badge when data confidence is below threshold.
- Refresh button per card to force re-fetch from source.
### **F-03: Multi-Platform Job Aggregator**
- Platforms covered: Naukri.com, LinkedIn Jobs, Indeed India, Foundit (formerly Monster India), WorkIndia.
- Job card structure: Title, Location, Posted Date, Experience Required, Source Platform, Direct Apply Link.
- Filters: Role type (Tech / Sales / Operations / HR), Location, Seniority, Date Posted (last 7 / 30 / 90 days).
- Deduplication engine: Jobs with identical title + location + date within a 3-day window are merged into one card showing all source platform links.
- Stale jobs (>45 days, not refreshed) are greyed out with a 'May be closed' label.
### **F-04: Email Digest**
- Cadence options: Every 2 days (Mon/Wed/Fri) or Weekly (user chooses day).
- Email format: Structured HTML with company header, C-suite changes (delta since last send), new job postings, funding signals, LinkedIn highlights.
- Only sends email if there is at least one new signal since last delivery — no empty digests.
- Unsubscribe and cadence-change link in every email footer.

# **6. Data Sources & Integration Strategy**

|**Platform**|**Data Type**|**Method**|**Refresh Rate**|
| :- | :- | :- | :- |
|**LinkedIn**|Leadership, Jobs, Posts|Official API + public scrape fallback|Daily|
|**Naukri.com**|Job Postings|Official API / scraper|Every 6 hours|
|**Indeed India**|Job Postings|Indeed Publisher API|Every 6 hours|
|**Foundit / Monster**|Job Postings|Scraper / partner feed|Daily|
|**WorkIndia**|Job Postings|API / scraper|Daily|
|**Crunchbase**|Funding Rounds, Leadership|Crunchbase Basic API|Weekly|
|**Company Website**|Leadership, 'About' page|HTML scraper|Weekly|

# **7. Core User Flows**
## **Flow 1: First-Time Company Search**
1. User lands on home page → enters company name in search bar.
1. System identifies company → returns leadership panel (left) and jobs panel (right).
1. User reviews data → clicks LinkedIn profile link for CEO to open in new tab.
1. User clicks 'Track this Company' → prompted to sign up / log in.
1. Post-login: company added to watchlist → cadence prompt shown.
1. User selects 'Every 2 days' → first digest scheduled.

## **Flow 2: Returning User — Email Digest**
1. User receives digest email on selected day.
1. Email shows delta: '3 new job postings since last update' + 'No leadership changes'.
1. User clicks 'View Full Brief' → lands on company page in app.
1. User can click any job card → direct apply link on source platform.

# **8. Non-Functional Requirements**
## **8.1 Performance**
- Search result time: ≤ 10 seconds (P95).
- Email delivery latency: < 5 minutes from scheduled send time.
- System uptime: 99.5% monthly SLA.
## **8.2 Security & Privacy**
- No storage of LinkedIn passwords or session tokens.
- All scraped data attributed to source; no redistribution of raw data.
- User data encrypted at rest (AES-256) and in transit (TLS 1.3).
- GDPR and Indian IT Act compliant; users can delete account and all data.
## **8.3 Scalability**
- Architecture supports 10,000 concurrent users at launch; horizontally scalable to 500,000.
- Job data stored in a time-series optimised datastore for efficient delta computation.
## **8.4 Accessibility**
- WCAG 2.1 AA compliance for all UI components.
- Email digest readable in plain text fallback for screen readers.

# **9. Phased Roadmap**

|**Phase**|**Timeline**|**Deliverables**|**Features**|
| :- | :- | :- | :- |
|**Phase 1**|Weeks 1–6 (MVP)|Core search, C-suite panel, job aggregator (Naukri + LinkedIn), basic UI|F-01, F-02, F-03|
|**Phase 2**|Weeks 7–10|Email digest scheduler, user accounts, watchlist, 3 more job platforms|F-04, F-07 + Foundit/Indeed/WorkIndia|
|**Phase 3**|Weeks 11–14|Funding tracker, LinkedIn activity feed, export/copy brief|F-05, F-06, F-08|
|**Phase 4**|Weeks 15–18|Team sharing, Slack/CRM integration, mobile-responsive polish|F-09, F-10|

# **10. Risks & Mitigations**

|**Risk**|**Severity**|**Mitigation**|
| :- | :- | :- |
|**LinkedIn anti-scraping blocks**|**High**|Prioritise official LinkedIn API; use rotating proxies as fallback; cache aggressively.|
|**Job data duplication across platforms**|**Medium**|Deduplication engine using title + location + date fingerprinting.|
|**Stale or incorrect leadership data**|**Medium**|Confidence scoring; 'Verify on LinkedIn' CTA on each card.|
|**Legal risk from data scraping**|**High**|Legal review per platform ToS; only surface publicly available data; respect robots.txt.|
|**Email deliverability (spam filters)**|**Medium**|Use dedicated sending domain + SPF/DKIM/DMARC; opt-in only with double confirmation.|

# **11. Open Questions**
- Will LinkedIn grant API access at the required volume, or do we rely on scraping with legal review?
- Should the tool be B2C (individual subscription) or B2B (team/seat-based licensing)?
- What is the pricing model — freemium (3 companies free) or paid-only from launch?
- Do we need to partner with Naukri / Foundit for official data feed access?
- Is real-time alerting (push notification on new job posting) in scope for Phase 1?

# **12. Appendix**
## **Email Digest — Sample Structure**

|**Company**|XYZ Technologies|
| :- | :- |
|**Location**|Chennai, India|
|**Employees**|~1,200|
|**Last Updated**|April 30, 2026|

**[LEADERSHIP]**

- CEO: Rajesh Kumar  |  linkedin.com/in/rajeshkumar
- CTO: Priya Nair  |  linkedin.com/in/priyanair (New — joined Jan 2026)

**[HIRING — 4 New Postings]**

- Software Developer (Chennai) — LinkedIn — April 28, 2026
- Senior Data Engineer (Remote) — Naukri — April 27, 2026
- Sales Manager — South India (Bangalore) — Indeed — April 25, 2026

**[FUNDING]**

- No new funding rounds detected in last 30 days.

**[LINKEDIN ACTIVITY]**

- Company page: Posted 'We are hiring!' — 1,240 impressions — April 29, 2026
- CTO Priya Nair shared an article on microservices architecture — 340 reactions

**Document Sign-Off**

|**Role**|**Name**|**Date**|
| :- | :- | :- |
|**Product Manager**|\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_|\_\_\_\_\_\_\_\_\_\_\_\_|
|**Engineering Lead**|\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_|\_\_\_\_\_\_\_\_\_\_\_\_|
|**Design Lead**|\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_|\_\_\_\_\_\_\_\_\_\_\_\_|
|**Legal / Compliance**|\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_\_|\_\_\_\_\_\_\_\_\_\_\_\_|

Confidential  |  Page 

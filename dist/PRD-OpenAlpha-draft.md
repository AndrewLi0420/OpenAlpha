# OpenAlpha Product Requirements Document (PRD)

**Author:** Andrew
**Date:** 2025-10-30
**Project Level:** 3
**Target Scale:** Comprehensive product (Level 3)

---

## Goals and Background Context

### Goals

1. **Democratize quantitative trading** - Make ML-powered investment insights accessible to everyday investors who lack day-trading time or quantitative expertise

2. **Enable data-driven decision making** - Provide statistically-backed recommendations with confidence scores and explanations, enabling users to make informed entry/exit decisions rather than emotional trades

3. **Deliver real-time market intelligence** - Aggregate hourly sentiment data from Twitter and other sources with ML predictions to give users daily sentiment awareness they currently lack

4. **Build user confidence in trading** - Through educational explanations and transparent confidence scoring, help users understand the "why" behind recommendations and build trust in quantitative insights

5. **Validate freemium business model** - Establish product-market fit with free tier (limited stock tracking) and validate premium conversion for expanded features

### Background Context

Everyday investors face critical challenges that prevent them from making quantitatively informed trading decisions:

**Current State:**
- Overwhelmed by vast amounts of information with difficulty separating signal from noise
- Lack daily sentiment awareness around stocks that inform entry/exit timing
- Make uninformed entry/exit decisions without valid quantitative reasons or data backing

**Problem Impact:**
- Users make suboptimal trading decisions resulting in missed opportunities and poor timing
- Low confidence in investment choices leading to paralysis or reactive trading
- Time-consuming manual research with inconsistent outcomes

**Market Opportunity:**
- Large addressable market of everyday investors seeking quantitative insights who lack time for day trading but want data-driven decision support
- Users want ML-powered predictions with educational context, not just raw data or generic advice

OpenAlpha addresses this by combining ML predictions, Twitter-based sentiment analysis, and educational explanations in a freemium model that democratizes access to quantitative trading intelligence. The MVP focuses on Fortune 500 stocks with hourly updates, targeting a 1-month launch timeline using free-tier infrastructure to validate product-market fit before scaling.

---

## Requirements

### Functional Requirements

**User Account & Authentication (FR001-FR004):**

**FR001: User Registration and Authentication**
- Users can create accounts with email/password
- Users can log in and log out securely
- Session management for authenticated access

**FR002: User Profile Management**
- Users can set holding period preferences (daily/weekly/monthly)
- Users can set risk tolerance level (low/medium/high)
- Profile information persists across sessions

**FR003: Freemium Tier Management**
- System enforces free tier limits (tracking for limited number of stocks, e.g., 3-5)
- Premium tier identification and feature access control
- Clear indication of tier status (free vs premium) to users

**FR004: Account Data Storage**
- User preferences, tier status, and account information stored securely
- Historical recommendations associated with user accounts

**Stock Data & Market Information (FR005-FR007):**

**FR005: Fortune 500 Stock Coverage**
- System covers all Fortune 500 stocks for recommendations
- Stock metadata (symbol, name, sector) accessible

**FR006: Market Data Collection**
- System collects hourly market data (price, volume) for Fortune 500 stocks
- Market data stored with timestamps for historical reference
- Data pipeline runs reliably on hourly schedule

**FR007: Stock Data Retrieval**
- Users can view current market data for stocks in their watchlist/recommendations
- Historical market data accessible for past recommendations

**FR007a: Stock Search Functionality**
- Users can search for stocks by symbol or company name
- Search results display stock information and availability for tracking
- Search integrated into dashboard and recommendation views

**Sentiment Analysis (FR008-FR010):**

**FR008: Twitter Sentiment Collection**
- System collects sentiment data from Twitter API hourly
- Sentiment data aggregated and processed for Fortune 500 stocks
- Sentiment scores calculated and stored with timestamps

**FR009: Sentiment Score Calculation**
- System calculates sentiment scores from aggregated Twitter data
- Sentiment scores normalized and stored for ML model input
- Sentiment data integrated into recommendation generation

**FR010: Additional Sentiment Sources**
- System can collect sentiment from additional web sources (news sites, forums) via scraping
- Multiple sentiment sources aggregated into unified sentiment scores
- Rate limiting and ethical scraping practices implemented

**ML Prediction Engine (FR011-FR014):**

**FR011: ML Model Inference**
- System runs neural network and Random Forest models for stock predictions
- Models generate buy/sell/hold signals for Fortune 500 stocks
- Model inference completes within <1 minute latency requirement

**FR012: Confidence Score Generation**
- System calculates confidence scores based on R² analysis for each prediction
- Confidence scores displayed with each recommendation
- Model performance metrics tracked and stored

**FR013: Risk Assessment**
- System calculates risk indicators (low/medium/high) for each recommendation
- Risk scores derived from ML model outputs and market conditions
- Risk indicators displayed alongside recommendations

**FR014: Recommendation Generation**
- System generates approximately 10 recommendations per day
- Recommendations filtered based on user holding period preferences
- Recommendations include prediction signal, sentiment, risk, and confidence scores

**Recommendation Display & Management (FR015-FR018):**

**FR015: Recommendation Dashboard**
- Users can view current recommendations in a dashboard interface
- Recommendations displayed in list format with: stock symbol, prediction (buy/sell/hold), sentiment score, risk level, confidence score
- Dashboard updates to show latest recommendations
- List view optimized for quick scanning

**FR016: Recommendation Explanations**
- Each recommendation includes brief explanation of why it was made
- Explanations include reference to sentiment, ML model signals, and risk factors
- Explanations displayed in simple, clear format
- Emphasis on transparency of data sources and reasoning

**FR017: Historical Recommendations View**
- Users can view past recommendations they've accessed
- Historical recommendations include date/time, stock, prediction, and outcomes if available
- Historical data filtered and searchable by date range
- Time series visualization of recommendation history

**FR018: Recommendation Filtering & Sorting**
- Users can filter recommendations by: holding period preference, risk level, confidence score
- Recommendations sortable by date, confidence, risk, sentiment
- Free tier users limited to recommendations for their allowed stock count

**Educational Content (FR019-FR020):**

**FR019: Contextual Educational Tooltips**
- Key quantitative concepts explained via tooltips or inline help
- Educational content explains terms like "confidence score", "sentiment analysis", "R²"
- Content focuses on clarity and simplicity for non-technical users
- Transparency emphasis: Show data sources and calculation methods

**FR020: Recommendation Education**
- Each recommendation explanation educates users about quantitative reasoning
- Users learn why certain signals indicate buy/sell/hold decisions
- Educational content builds user understanding over time
- Transparent display of model performance and data freshness

**Data Visualization (FR021-FR022):**

**FR021: Time Series Financial Charts**
- Users can view time series graphs for stock price data
- Charts display historical price movements with timestamps
- Visualization integrated into recommendation detail views
- Charts show recommendation timing relative to price movements

**FR022: Recommendation History Visualization**
- Time series visualization of recommendation history for stocks
- Graphs show how recommendations align with market movements over time
- Visual representation of confidence scores and sentiment trends

**Data & System Management (FR023-FR025):**

**FR023: Hourly Data Processing Pipeline**
- System processes market data and sentiment hourly for Fortune 500 stocks
- Processing pipeline runs reliably without critical failures
- Failed processing attempts logged and retried

**FR024: Model Performance Tracking**
- System tracks R² metrics for ML models over time
- Model performance data stored and accessible for analysis
- Performance degradation triggers alerts for model review
- Performance metrics displayed transparently to users

**FR025: Historical Data Storage**
- All recommendations, market data, and sentiment scores stored historically
- Data retention supports user historical views and model training
- Data storage optimized for query performance

**Platform Requirements (FR026-FR027):**

**FR026: Web-First Responsive Interface**
- Platform accessible via web browser (desktop and mobile)
- Responsive design adapts to different screen sizes
- Interface functional on modern browsers (Chrome, Firefox, Safari, Edge)
- Built with Tailwind CSS for styling

**FR027: API for Frontend Integration**
- Backend provides RESTful API for frontend consumption
- API endpoints for: recommendations, user preferences, historical data, stock information, search
- API responses optimized for <1 minute latency requirement

---

### Non-Functional Requirements

**NFR001: Performance Requirements**
- Recommendation generation completes within 1 minute of request
- Dashboard loads and displays recommendations within 3 seconds
- Hourly data processing pipeline completes within processing window
- API endpoints respond within acceptable latency (<500ms for data retrieval)

**NFR002: Reliability & Availability**
- System available for user access 95%+ of time during business hours
- Hourly data pipeline runs with <5% failure rate
- Critical failures trigger automatic retry mechanisms
- System gracefully handles Twitter API rate limits and data source unavailability

**NFR003: Scalability**
- System handles initial user base on free-tier infrastructure
- Architecture supports scaling to paid tiers when user base grows
- Database and caching optimized for Fortune 500 stock data volume
- ML inference can be optimized or scaled as user base increases

**NFR004: Security & Privacy**
- User account data encrypted and stored securely
- Authentication uses secure password hashing
- Financial data and recommendations transmitted over HTTPS
- User privacy maintained: no sharing of trading data or recommendations publicly

**NFR005: Data Quality & Accuracy**
- Market data accuracy: sourced from reliable financial data providers
- Sentiment data freshness: updated hourly as specified
- ML model predictions include confidence scores to indicate reliability
- System handles missing or incomplete data gracefully
- Transparency: Data sources and update timestamps clearly displayed

---

## User Journeys

### Journey 1: Daily Recommendation Check (Time-Constrained Professional)

**User:** Sarah, a 9-to-5 professional, age 32

**Context:** Sarah wants to check recommendations before the market opens to make informed trading decisions during her lunch break.

**Flow:**
1. **Morning Access (7:30 AM)**
   - Sarah opens OpenAlpha web app on her phone while commuting
   - Logs in (or stays logged in)
   - Lands on recommendation dashboard

2. **Dashboard View**
   - Sees ~10 new recommendations for today displayed in list format
   - Each recommendation shows: stock symbol, buy/sell/hold signal, confidence score, sentiment score, risk level
   - Notices some recommendations have higher confidence scores than others

3. **Exploring a Recommendation**
   - Taps on AAPL recommendation (BUY, High Confidence, Positive Sentiment, Medium Risk)
   - Sees brief explanation with transparent data sources: "Positive sentiment trending on Twitter, ML model indicates strong buy signal with 0.85 R² confidence. Medium risk due to recent volatility. Data updated 1 hour ago."
   - Uses tooltip on "R² confidence" to understand the metric
   - Views time series chart showing price movement and recommendation timing
   - Checks historical view: "This stock recommended 3 times in past 2 weeks"

4. **Decision Point: Act or Wait?**
   - **Path A: Ready to act**
     - Takes screenshot of recommendation details
     - Opens broker app to execute trade during lunch break
     - Adds note: "Following OpenAlpha recommendation"
   - **Path B: Needs more context**
     - Checks historical recommendations for this stock
     - Views time series graph for historical context
     - Compares with other recommendations for similar confidence levels
     - Bookmarks for later review

5. **Additional Recommendation Review**
   - Filters recommendations by: High confidence only
   - Reviews 3-4 high-confidence recommendations
   - Selects 1-2 to act on today

6. **Historical Check**
   - Checks past week's recommendations
   - Reviews time series visualization of recommendation history
   - Reviews which previous recommendations aligned with actual market movements
   - Uses this to build confidence in current recommendations

**Decision Points:**
- Whether to act immediately or wait
- How many recommendations to review vs. time available
- How much historical context to review (including time series visualization)

**Alternatives:**
- If no new recommendations: Reviews previous day's recommendations or waits for hourly update
- If low confidence scores: May skip acting or request more explanation
- If conflicting signals: Reviews sentiment vs. risk to make decision

**Edge Cases:**
- Market volatility causing frequent recommendation changes
- Missing sentiment data for a stock (transparently indicated)
- Free tier user hitting stock limit

---

### Journey 2: Weekly Portfolio Review (Retirement-Focused Investor)

**User:** Robert, age 58, planning retirement, prefers weekly check-ins

**Context:** Robert checks recommendations weekly on Saturday morning to plan next week's trades.

**Flow:**
1. **Weekly Access (Saturday, 9:00 AM)**
   - Opens OpenAlpha on laptop
   - Logs in
   - Sets preference filter: "Weekly holding period" to see longer-term recommendations

2. **Weekly Recommendations View**
   - Dashboard filtered to show weekly/monthly recommendations
   - Reviews recommendations tailored to his longer time horizon displayed in list format
   - Focuses on lower-risk, higher-confidence signals

3. **Educational Learning**
   - Reviews a recommendation with medium confidence
   - Reads explanation with transparent data sources and timestamps
   - Views time series chart to understand price context
   - Uses educational tooltips to understand quantitative concepts
   - Builds understanding: "So sentiment combined with price patterns indicates this is a good weekly hold"

4. **Risk Assessment Focus**
   - Filters by "Low Risk" recommendations (conservative approach)
   - Reviews risk indicators for each recommendation
   - Compares risk levels with his risk tolerance setting (set to "Low")

5. **Historical Pattern Review**
   - Checks historical recommendations from past 4 weeks
   - Reviews time series visualization showing recommendation patterns
   - Reviews which weekly recommendations performed well
   - Identifies patterns: "Higher confidence scores tend to align better with actual outcomes"

6. **Planning Decision**
   - Selects 2-3 recommendations for the coming week
   - Notes these in his trading journal
   - Plans to execute trades on Monday morning based on recommendations

**Decision Points:**
- How conservative to be (low risk vs. medium risk recommendations)
- Whether to follow recommendations immediately or observe patterns first
- How much to rely on confidence scores vs. personal judgment

**Alternatives:**
- If few low-risk recommendations: Reviews medium-risk with careful scrutiny
- If unclear explanations: Uses educational content to understand better
- If recommendations conflict with his knowledge: Validates against his research

**Edge Cases:**
- Sudden market events requiring immediate attention (checked outside weekly routine)
- Premium tier consideration if he wants more stock coverage
- Educational content not sufficient for his questions

---

### Journey 3: New User Onboarding & First Recommendation

**User:** Alex, new user, heard about OpenAlpha from a friend

**Context:** Alex wants to try quantitative trading recommendations but is new to the platform.

**Flow:**
1. **Account Creation (First Visit)**
   - Lands on OpenAlpha homepage (black background with financial blue/green accents)
   - Clicks "Get Started" or "Sign Up"
   - Creates account with email/password
   - Receives email verification

2. **Initial Setup**
   - Prompts to set preferences:
     - Holding period: Daily/Weekly/Monthly (chooses "Daily")
     - Risk tolerance: Low/Medium/High (chooses "Medium")
   - Sees free tier information: "Track up to 5 stocks on free tier"
   - Accepts terms: "Not financial advice, informational only"

3. **First Dashboard View**
   - Sees recommendation dashboard with ~10 recommendations in list format
   - Dashboard includes onboarding tooltips explaining:
     - What confidence scores mean (with transparent display of calculation method)
     - How to read sentiment indicators (data source: Twitter)
     - What risk levels indicate
   - Tooltips appear on first interaction with each element
   - Notices black background with financial blue/green color scheme

4. **Exploring First Recommendation**
   - Selects a recommendation with high confidence score
   - Reads explanation: clear and educational with transparent data sources
   - Views time series chart showing price history
   - Hovers over terms: "sentiment analysis", "ML prediction" - sees explanations
   - Notices timestamps showing data freshness
   - Feels confident understanding the recommendation

5. **Search Functionality**
   - Uses stock search to find specific stocks of interest
   - Searches by symbol or company name
   - Finds stock in search results and views recommendation if available
   - Adds to tracking list (respecting free tier limit)

6. **Understanding Free Tier Limits**
   - Tries to view more than 5 stocks
   - Sees message: "Free tier allows tracking 5 stocks. Upgrade to premium for unlimited access."
   - Reviews the 5 stocks already shown
   - Decides to test with free tier first

7. **First Action**
   - Reviews 2-3 high-confidence recommendations
   - Views time series charts for context
   - Takes screenshots or notes
   - Plans to check broker later
   - Feels informed about next trading decisions with transparent data understanding

**Decision Points:**
- Whether to upgrade to premium immediately or test free tier
- How much time to spend learning vs. acting
- Whether the explanations are clear enough to trust recommendations

**Alternatives:**
- If confused: Seeks more educational content or support
- If recommendations seem too complex: Starts with just reading explanations
- If free tier feels limiting: Considers premium upgrade

**Edge Cases:**
- Account creation issues
- Verification email not received
- Dashboard appears empty (first-time user, no recommendations yet)
- Technical questions about ML/sentiment not answered by tooltips

---

## UX Design Principles

1. **Clarity and Transparency**
   - Display confidence scores, risk indicators, and sentiment clearly with transparent data sources
   - Use plain language, avoid jargon
   - Show data freshness and calculation methods
   - Explain why recommendations are made with visible data backing

2. **Educational and Confidence-Building**
   - Provide learning opportunities without overwhelming users
   - Build trust through transparency of models and data
   - Help users understand quantitative concepts progressively
   - Show model performance metrics clearly

3. **Time-Efficient Information Access**
   - Quick scanning of recommendations in list format
   - Prioritize actionable insights
   - Minimal clicks to key information
   - Efficient search and filtering

4. **Trust Through Transparency**
   - Show model performance metrics (R²-based confidence) transparently
   - Display data freshness and sources clearly
   - Clear disclaimers and risk indicators
   - Transparent visualization of recommendation history with time series data

---

## User Interface Design Goals

### Platform & Screens

**Target Platforms:**
- Web-first platform (primary)
- Responsive mobile web (secondary)
- Browser support: Modern browsers (Chrome, Firefox, Safari, Edge - latest 2 versions)

**Core Screens/Views:**

1. **Dashboard (Recommendations List)**
   - Current recommendations displayed in list format for quick scanning
   - Key info per item: stock symbol, signal, confidence, sentiment, risk
   - Filters and sorting capabilities
   - Quick access to detail views
   - Search functionality for stocks

2. **Recommendation Detail View**
   - Full explanation with transparent data sources
   - Time series chart showing price history and recommendation timing
   - Historical context and past recommendations
   - Educational tooltips/inline help
   - Transparent display of data freshness

3. **Historical Recommendations View**
   - Past recommendations with dates in list format
   - Time series visualization of recommendation history
   - Filtering by date range, stock, signal type
   - Past performance context (if available)
   - Visual representation of confidence trends

4. **Stock Search**
   - Search by symbol or company name
   - Search results in list format
   - Quick access to stock information and recommendations

5. **User Profile/Settings**
   - Holding period preference
   - Risk tolerance setting
   - Account info and tier status (free/premium)
   - Display preferences

6. **Login/Registration**
   - Simple email/password flow
   - Welcome/onboarding for new users

7. **Educational Help/Tooltips**
   - Inline explanations throughout interface
   - Glossary or help section (optional for MVP)
   - Transparent explanation of data sources and methods

### Key Interaction Patterns & Navigation

**Navigation Approach:**
- Dashboard-centric design with clear navigation
- Top navigation or sidebar: Dashboard, Historical, Profile, Help
- Breadcrumbs or back buttons for detail views
- Search accessible from main navigation

**Key Interactions:**
- Click recommendation in list → detail view
- Filter/sort recommendations
- Search for stocks
- Hover/click for tooltips
- View time series charts
- View historical recommendations
- Update preferences in profile

### Design Constraints

**Technical UI Constraints:**
- Web-first responsive design (no native apps in MVP)
- Browser compatibility: Modern browsers only
- Performance: Fast loading for mobile data connections
- Accessibility: Basic WCAG compliance, keyboard navigation
- Built with Tailwind CSS framework

**Design Style:**
- **Color Scheme:** Black background with financial blue/green accents
- **Typography:** Clear typography optimized for numerical data display
- **Visualization:** Time series graphs for financial data visualization
- **Layout:** List-based layouts for stock recommendations
- **Aesthetic:** Clean, modern, focused on data clarity and transparency

**Existing Design Systems:**
- Tailwind CSS for styling framework
- No existing brand guidelines (greenfield project)

---

## Epic List

**Epic 1: Foundation & User Authentication**
- Establish project infrastructure, authentication, and basic user management
- Estimated stories: 5-8

**Epic 2: Data Pipeline & ML Engine**
- Build market data collection, sentiment analysis, and ML prediction engine
- Estimated stories: 6-10

**Epic 3: Recommendations & Dashboard**
- Implement recommendation generation, dashboard display, search, and user experience
- Estimated stories: 8-12

**Epic 4: Historical Data & Visualization**
- Add historical recommendations view, time series charts, and advanced features
- Estimated stories: 4-8

**Total Estimated Stories: 23-38** (Level 3 range: 15-40 stories)

> **Note:** Detailed epic breakdown with full story specifications is available in [epics.md](./epics.md)

---

## Out of Scope

**What We're NOT Doing (MVP):**

**Features Deferred to v2:**
- Advanced ML model ensembles or multiple specialized model types (MVP focuses on neural networks + Random Forest)
- Portfolio tracking and analysis (beyond historical recommendations view - no portfolio value tracking)
- Social features or user communities (no sharing, forums, or social interactions)
- Native mobile apps (staying web-first with responsive design)
- Broker integrations or portfolio syncing (users manually execute trades in their own broker accounts)
- Advanced personalization beyond basic preferences (holding period, risk tolerance)
- Historical performance analytics and backtesting features
- Multiple asset classes (focusing on Fortune 500 stocks initially - no options, crypto, international stocks)
- Real-time streaming recommendations (updates every 5 minutes preferred if cost-effective with free-tier infrastructure, otherwise hourly updates sufficient for MVP)
- Advanced alerting or notification systems (email, SMS, push notifications)

**Explicit Boundaries:**
- **NO trade execution** - Recommendations only; users execute trades in their own broker accounts
- **NO custodial accounts** - Users maintain full control of their assets; we don't hold funds or securities
- **NO financial advice** - Quantitative insights and recommendations, not personalized financial advice
- **NO social sharing or community features** - No sharing recommendations, forums, or user interactions
- **NO portfolio value tracking or performance attribution** - We show recommendations, not portfolio performance
- **NO continuous real-time data streaming** - Updates every 5 minutes (if cost-effective) or hourly; not second-by-second streaming
- **NO advanced analytics** - Basic historical view and time series charts only, no backtesting or advanced analysis

**Scope Boundaries for Clarity:**
- Stock coverage limited to Fortune 500 (no extended coverage in MVP)
- Educational content: Brief explanations and tooltips only (no comprehensive educational courses)
- Free tier: Limited stock tracking (e.g., 3-5 stocks) with premium features requiring upgrade
- Search functionality: Basic stock search only (no advanced filtering or saved searches in MVP)
- Time series visualization: Basic charts for price history and recommendations (no complex technical analysis charts)


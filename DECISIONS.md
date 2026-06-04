# CycloFix — Product Decisions

## What is CycloFix
An adaptive menstrual pain prediction and management app for women aged 16-25 in India. Predicts cycle timing and pain severity. Suggests personalised relief actions. Learns what works for each individual user over time.

## The core thesis
From helpless to prepared. Reduce unpredictability. Help manage pain when it hits.

## The novel core
"Did this help?" feedback loop after every relief suggestion. The app learns what works for this specific person — not generic advice.

## Phase plan
- Phase 1 (this break): Effortless logging, action suggestions, feedback loop, pattern display. Pure software, no hardware.
- Phase 2 (semester 2): Pain severity prediction model built on real user data.
- Phase 3 (year 3+): Closed-loop smart relief device — adaptive heat/stimulation patch.

## V1 core features
1. One-tap pain logging — intensity, type, cycle day
2. Relief suggestions — heat, rest, movement, breathing
3. "Did this help?" feedback loop — stores per user per pain type
4. Personal pattern display — your history, your baseline

## Design principles
- Every input = one tap maximum
- Never compare to other users — only personal baseline
- No diagnosis, no medical claims — pattern recognition only
- Close the loop always — every suggestion gets feedback

## V2 features (after real data)
- Pain severity forecast before cycle starts
- Cycle timing prediction using physiological signals
- Early warning 24-48hrs before predicted bad days

## Tech stack
- Backend: Python + Flask
- Database: SQLite
- Frontend: HTML/CSS, mobile-friendly
- Hosting: Railway or Render

## First users
Stage 1: myself — validate logging UX over 1-2 cycles
Stage 2: 5-10 friends — find what breaks
Stage 3: 20-30 users — enough data for prediction model

## What this is NOT
- Not a diagnostic tool
- Not a period tracker (Flo/Clue already do that)
- Not a hardware product yet
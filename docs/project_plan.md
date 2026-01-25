# Project Plan — Inflation Monitor (MVP)

## Phase 0 — Repository & Structure
- Create GitHub repository
- Add README and docs
- Verify structure

## Phase 1 — Fetch US CPI
- Implement fetch_us.py
- Run locally and verify output

## Phase 2 — Supabase Integration
- Create tables
- Insert US CPI
- Verify in dashboard

## Phase 3 — Add UK and NZ
- Fetch CPI via official APIs
- Store using same schema

## Phase 4 — Change Detection
- Compare against last snapshot
- Flag material change

## Phase 5 — Email Notification
- Send email only on material change

## Phase 6 — Vercel Cron
- Weekly scheduled execution

## Phase 7 — Optional Frontend
- Simple table view

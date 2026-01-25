# Inflation Monitor (MVP)

A lightweight, research-oriented dashboard to monitor official inflation data
and central bank inflation forecasts across selected countries.

This project is designed to be:
- Low-frequency (weekly updates)
- Free / near-zero cost
- Fully based on official or quasi-official sources
- Easy to maintain by a non-professional developer

## Covered Countries (MVP Phase)

- United States (US)
- United Kingdom (UK)
- New Zealand (NZ)

Planned expansion:
- Australia (AU)
- South Africa (ZA)

## What This Project Does

- Fetches latest headline CPI from official statistical agencies
- Stores data in Supabase
- Runs weekly updates via Vercel Cron
- Detects material changes
- Sends an email notification only when changes are material

## Definition of "Material Change"

Absolute CPI change ≥ 0.3 percentage points compared to last snapshot.

## Tech Stack

- Backend / Cron: Vercel Serverless Functions
- Database: Supabase (Postgres)
- Frontend: Minimal Next.js page (optional)
- Email: Free-tier email service
- Automation Assistant: Claude

This is a research tool, not a trading system.

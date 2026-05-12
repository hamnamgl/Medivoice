# Technical Write-Up

## Overview

MediVoice is an offline-first clinical support assistant for frontline health workers. The current implementation focuses on local model execution, guided consultation flow, offline reference data, and device-friendly interfaces for low-connectivity environments.

## Core Stack

- Gemma models served through Ollama
- Python application logic for triage, referral, dosage, and multimodal flows
- SQLite for local visit storage
- PWA frontend for mobile-friendly access
- Kaggle + ngrok notebook path for reproducible demo access

## Why Local Inference

Running locally through Ollama matters because the target setting includes:

- weak or absent internet
- privacy-sensitive health information
- low-budget deployments
- field staff using shared or entry-level devices

## Consultation Logic

The current consultation flow is intentionally constrained:

1. acknowledge the problem
2. ask one follow-up question at a time
3. check for danger signs
4. give a verdict or referral action

This is safer than unconstrained open-ended chat, especially for CHW workflows.

## Data Architecture

MediVoice now uses a two-layer offline data system:

- bundled core data in `data/protocols`, `data/drugs`, and `data/referrals`
- optional organization overlays in `data/custom`

This allows field programs to customize referral and operational data without rewriting core medical defaults.

## Demo Mode

The Kaggle notebook demonstrates reproducibility:

- starts Ollama
- pulls a Gemma model if needed
- runs sample consultations
- starts a browser-safe local proxy
- optionally exposes that proxy through ngrok

This is a demo path, not the final offline deployment model.

## True Offline Deployment

True offline use happens when:

- Ollama runs on the deployment device or local network
- the model is already downloaded
- the app uses local data only
- no external API is required for consultation flow

## Current Strengths

- local model execution works
- referral and dosage routing can be deterministic
- custom local data pack support exists
- image analysis path now has model fallback
- notebook and PWA demo path are functional

## Current Gaps

- protocol packs are still starter/demo-grade rather than fully verified global conversions
- multilingual reasoning quality still needs stronger evaluation
- image workflow needs broader real-world validation
- country-level referral coverage is not yet worldwide or fully sourced

## Next Technical Priorities

1. source-driven global data import pipeline
2. richer explainability and audit trails
3. stronger multilingual evaluation set
4. packaging for field deployment hardware

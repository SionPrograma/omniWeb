# OmniWeb Beta Deployment Guide

This guide outlines the process for launching and managing the OmniWeb Public Beta.

## 1. Launching the Cluster
Ensure the core nodes are active and the storage grid is healthy.
```bash
python -m runtime.boot --mode=production
```

## 2. Onboarding Testers
- Use the **Beta Invite Generator** in Mission Control (Beta tab) to create unique tokens.
- Share the `omniweb_qr_beta.png` with trusted collaborators.
- Monitor onboarding metrics in the **Global Telemetry** panel.

## 3. Feedback Collection
- Testers submit feedback directly via the **Beta Feedback** panel.
- The AI Host aggregates this feedback and classifies sentiment.
- High-priority bugs are automatically logged for **AutoFix** review.

## 4. Monitoring & Observability
- Keep the **Global Observability** dashboard open.
- Watch for P99 latency spikes in regional edge nodes.
- Monitor the **Security Audit Trail** for any unauthorized access attempts.

## 5. Controlled Rollouts
Use the **Feature Flags** system (managed by AI Host) to enable new blocks for specific tester groups before global activation.

---
*OmniWeb: Scaling Human Potential.*

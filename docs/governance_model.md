# Governance Model

## Overview

OmniWeb implements an **AI-driven, community-governed evolution model** where users naturally progress through roles based on demonstrated behavior — not arbitrary assignments. The governance layer combines behavioral analysis, trust networks, and AI advisorship to create organic community leadership.

## Role Hierarchy

```
                    ┌──────────┐
                    │ CREATOR  │  ← Platform Owner (unrestricted)
                    └────┬─────┘
                         │
                    ┌────┴─────┐
                    │  ADMIN   │  ← Full system management
                    └────┬─────┘
                         │
               ┌─────────┴─────────┐
               │ ADMIN CANDIDATE   │  ← Governance training
               └─────────┬─────────┘
                         │
                  ┌──────┴──────┐
                  │ BETA TESTER │  ← Early access + onboarding
                  └──────┬──────┘
                         │
                    ┌────┴─────┐
                    │   USER   │  ← Standard access
                    └──────────┘
```

## Three Pillars

### 1. Reputation Graph

A weighted trust network connecting users:

| Edge Type | Weight | Triggered By |
|---|---|---|
| `invitation` | 0.3 | User invites another user |
| `collaboration` | 0.5 | Joint project participation |
| `assistance` | 0.7 | Helping another user |
| `moderation` | 0.8 | Community moderation actions |
| `onboarding_complete` | 1.0 | Successfully onboarding a tester |

Trust scores propagate through the graph, creating a collective reputation metric.

### 2. Leadership Detection Engine

Behavioral analysis engine that evaluates:

| Signal | Weight | Source |
|---|---|---|
| Reputation Score | 0.3 | Reputation graph edges |
| Help Count | 0.2 | Assistance interactions |
| Bug Reports | 0.15 | Issue submissions |
| Exploration Depth | 0.15 | Feature discovery patterns |
| Timeline Length | 0.2 | Engagement duration |

**Leadership Score ≥ 0.8** → Automatic promotion recommendation to AI Governance Advisor.

### 3. AI Governance Advisor

The AI produces actionable governance insights:

| Insight Type | Description | Action |
|---|---|---|
| `leadership_detection` | User exhibits leadership patterns | Promote to Admin Candidate |
| `hidden_skill` | Latent skill detected | Record to timeline |
| `suspicious_behavior` | Anomaly detection | Flag for review |

Insights require Creator/Admin approval before execution.

## Beta Tester Onboarding (10-Step Protocol)

1. **Welcome**: Platform introduction
2. **Role Explanation**: Beta tester responsibilities
3. **Evaluation Criteria**: How performance is measured
4. **Evolutionary Path**: Journey to administration
5. **Community Introduction**: Connecting with other testers
6. **Personal Exploration**: Free exploration encouragement
7. **Tester Guidance**: Tools and reporting mechanisms
8. **Governance Foundation**: Community management principles
9. **Community Management**: Moderation training
10. **Final Milestone**: Senior Beta Tester status

Hidden Skill Detection runs at each step, analyzing:
- **Analytical Thinking**: Systematic questioning patterns
- **Leadership Potential**: Community engagement signals
- **Technical Curiosity**: Feature exploration depth

## User Memory Timeline

Every user has a chronological evolution record:

| Milestone Type | Example |
|---|---|
| `account_creation` | User registered |
| `first_login` | First shell access |
| `feature_exploration` | Discovered knowledge graph |
| `bug_report` | Submitted issue report |
| `onboarding_step` | Completed step 3 of onboarding |
| `hidden_skill_detected` | AI detected analytical thinking |
| `reputation_milestone` | Trust score exceeded threshold |

## API Endpoints

| Method | Endpoint | Auth | Purpose |
|---|---|---|---|
| GET | `/api/v1/governance/insights` | Admin | Pending recommendations |
| POST | `/api/v1/governance/insights/analyze` | Admin | Trigger leadership scan |
| POST | `/api/v1/governance/insights/{id}/approve` | Admin | Approve promotion |
| POST | `/api/v1/governance/insights/{id}/reject` | Admin | Reject recommendation |
| GET | `/api/v1/governance/reputation/{user_id}` | Admin | User trust score |
| GET | `/api/v1/governance/timeline/{user_id}` | Admin | User evolution timeline |
| GET | `/api/v1/governance/beta/testers` | Admin | Beta tester registry |
| GET | `/api/v1/governance/stats` | Admin | Governance metrics |

## QR Access Tokens

| QR Code | Role Assigned | Token |
|---|---|---|
| `omniweb_qr_beta_tester.png` | Beta Tester | `OMNI-BETA-ACCESS` |
| `omniweb_qr_admin_candidate.png` | Admin Candidate | `OMNI-CANDIDATE-PROMOTION` |
| `omniweb_qr_administrator.png` | Administrator | `OMNI-ADMIN-COMMAND` |

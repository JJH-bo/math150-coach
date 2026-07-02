# Usability Trial Report Template

Use this template after running `docs/usability_trial_protocol.md`.

```text
Trial date:
Environment:
Command set used:
Questions tested:
Answers submitted:

1. List experience
- Success/fail:
- Question count:
- Available question_id values:
- Friction:
- Missing info:
- Leak check:

2. Show experience
- Prompt clarity:
- Formatting:
- Hints usefulness:
- Missing info:
- Leak check:

3. Submit experience
- Answer type tested:
- Pass state:
- Score vector usefulness:
- Learner explanation usefulness:
- Recommended actions usefulness:
- Rollback/forward clarity:
- Next action usefulness:
- JSON stdout readability:
- Session log written:

4. Session log review
- Log created:
- Log readable:
- Useful for review:
- Missing fields:
- Need history command:
- Leak check:

5. Training value judgment
- Did this improve real math training?
- Was the feedback actionable?
- Did it expose my weak point?
- Would I use this again tomorrow?

6. Main problems found
- P0 blocker:
- P1 improvement:
- P2 future polish:

7. Next-phase recommendation
Choose one:
A. Local Trainer History P1
B. Minimal Catalog Expansion for Real Practice
C. Learner Output / Coach Feedback Refinement
D. Minimal Learner UI / Frontend Exploration
E. Attempt Persistence / Review Scheduler Research
F. Micro-hardening

Reason:
```

Decision guidance:

- Choose A if the biggest pain is not being able to view prior attempts.
- Choose B if the biggest pain is too few practice questions.
- Choose C if feedback content is weak, not coach-like enough, or not actionable.
- Choose D if CLI format or terminal workflow blocks real usage.
- Choose E if local JSONL cannot support review or repeated practice.
- Choose F if path safety, stdout JSON, trusted-field leakage, or session-root behavior is the main issue.

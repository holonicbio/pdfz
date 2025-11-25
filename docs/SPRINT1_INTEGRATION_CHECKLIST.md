# Sprint 1 Integration Checklist and Procedures

**Author:** D01 (Tech Lead)
**Date:** 2025-11-25
**Sprint:** Sprint 1 - Hardening & Testing
**Integration Period:** Days 9-10
**Version:** 1.0

## Executive Summary

This document defines the integration procedures and checklists for Sprint 1 (Hardening & Testing). It ensures smooth integration of all Sprint 1 deliverables from 10 developers working in parallel, with clear procedures for Days 9-10 integration period.

**Key Integration Goals:**
1. Merge all Sprint 1 PRs in correct dependency order
2. Verify all tests pass after each merge
3. Achieve >85% test coverage on modified code
4. Document all changes and update CONTINUATION.md
5. Complete Sprint 1 retrospective and plan Sprint 2

---

## 1. Pre-Integration Phase (Days 1-8)

### 1.1 Daily Standup (Async)

**Time:** 09:00 daily
**Format:** Team channel post
**Template:**
```
## Daily Update - Day N

**Yesterday:**
- What I completed

**Today:**
- What I'm working on

**Blockers:**
- Any issues blocking progress

**PR Status:**
- Draft / In Review / Ready for Merge
```

### 1.2 Mid-Sprint Check (Day 5)

**Time:** 15:00 Day 5
**Duration:** 30 minutes
**Attendees:** All developers
**Agenda:**
1. Status review of all tasks
2. Identify any blockers
3. Adjust plans if needed
4. Confirm integration day availability

**Action Items:**
- [ ] All developers report status
- [ ] D01 identifies risks
- [ ] Adjust task assignments if needed

### 1.3 PR Preparation Checklist (Day 8)

**Each developer must complete before Day 9:**

**Code Complete:**
- [ ] All code written and manually tested
- [ ] No known bugs in new code
- [ ] Self-review completed

**Testing:**
- [ ] All new code has unit tests
- [ ] Tests pass locally
- [ ] Coverage >85% on new code
- [ ] No flaky tests

**Documentation:**
- [ ] Docstrings added to new public APIs
- [ ] README updated if needed
- [ ] Comments added for complex logic
- [ ] CHANGELOG entry added (if applicable)

**PR Hygiene:**
- [ ] Branch named correctly (feat/s1-description)
- [ ] Commits have clear messages
- [ ] No merge conflicts with develop
- [ ] CI passes (all checks green)
- [ ] At least 1 approval obtained

**Communication:**
- [ ] Posted PR link in team channel
- [ ] Notified dependent developers
- [ ] Available for questions on Day 9

---

## 2. Integration Day 1 (Day 9)

### 2.1 Morning: Sprint Review (09:00-11:00)

**Duration:** 2 hours
**Location:** Video call + shared screen
**Facilitator:** D01 (Tech Lead)

**Agenda:**
```
09:00 - 09:05: Welcome and overview (D01)
09:05 - 09:50: Individual demos (5 min each × 10 devs)
09:50 - 10:00: Break
10:00 - 10:30: Q&A and discussion
10:30 - 11:00: Integration planning
```

**Demo Format (5 minutes each):**
1. **What:** Task ID and description
2. **Show:** Live demo or code walkthrough
3. **Tests:** Show test results
4. **Status:** Ready for merge? Any concerns?

**Demo Order:**
1. D04 - Retry utilities (S1-D04-01)
2. D07 - HTTP mocking infrastructure (S1-D07-01)
3. D02 - Backend retry logic (S1-D02-01)
4. D03 - Concurrent page processing (S1-D03-01)
5. D05 - Renderer memory optimization (S1-D05-01)
6. D06 - CLI improvements (S1-D06-01)
7. D07 - Backend integration tests (S1-D07-02)
8. D08 - Documentation updates (S1-D08-01)
9. D09 - Block processing research (S1-D09-01)
10. D10 - Evaluation metrics research (S1-D10-01)

### 2.2 Morning: PR Status Review (11:00-12:00)

**Facilitator:** D01
**Participants:** All developers

**Activities:**
1. Review CI status for all PRs
2. Identify any failing tests
3. Check for merge conflicts
4. Assign code reviewers if needed
5. Create merge order list

**PR Status Board:**
```
| Task ID | Owner | Status | CI | Conflicts | Ready? |
|---------|-------|--------|----|-----------| -------|
| S1-D04-01 | D04 | ✅ | ✅ | ❌ | ✅ |
| S1-D07-01 | D07 | ✅ | ✅ | ❌ | ✅ |
| ... | ... | ... | ... | ... | ... |
```

**Lunch Break (12:00-14:00)**

### 2.3 Afternoon: Integration Session (14:00-18:00)

**Facilitator:** D01
**Participants:** All developers (on-call for questions)

**Merge Order (Dependency-based):**
```
1. S1-D04-01 (Retry utilities) - Foundation
   └── merge, run tests, verify

2. S1-D07-01 (HTTP mocking) - Foundation
   └── merge, run tests, verify

3. S1-D02-01 (Backend retry) - Depends on S1-D04-01
   └── merge, run tests, verify

4. S1-D03-01 (Concurrent pages) - Independent
   └── merge, run tests, verify

5. S1-D05-01 (Renderer optimization) - Independent
   └── merge, run tests, verify

6. S1-D06-01 (CLI improvements) - Independent
   └── merge, run tests, verify

7. S1-D07-02 (Integration tests) - Depends on S1-D02-01, S1-D07-01
   └── merge, run tests, verify

8. S1-D08-01 (Documentation) - Last
   └── merge, run tests, verify

9. S1-D09-01, S1-D10-01 (Research) - Merge design docs
   └── merge documentation only
```

**Merge Protocol for Each PR:**
1. **Announce:** "Merging S1-DXX-XX"
2. **Check:** Verify PR has approval, CI green
3. **Merge:** Squash and merge to develop
4. **Test:** Run full test suite
5. **Verify:** Check coverage report
6. **Announce:** "S1-DXX-XX merged successfully" or "Issues found"
7. **Fix:** If issues, owner fixes immediately
8. **Repeat:** Move to next PR

**Commands:**
```bash
# After each merge
git checkout develop
git pull origin develop

# Run full test suite
pytest tests/unit -v --cov=src/docling_hybrid --cov-report=html

# Check coverage
open htmlcov/index.html

# Check for regressions
pytest tests/integration -v  # If integration tests exist
```

### 2.4 End of Day 9 Status Check (18:00)

**Status Report:**
```
✅ Merged: X/10 PRs
⏳ In Progress: Y/10 PRs
❌ Blocked: Z/10 PRs

Test Status:
- Unit tests: PASS/FAIL
- Integration tests: PASS/FAIL
- Coverage: XX%

Issues:
- List any issues found
```

**Blockers Resolution:**
- If any PRs blocked, schedule evening session or early Day 10

---

## 3. Integration Day 2 (Day 10)

### 3.1 Morning: Testing and Verification (09:00-12:00)

**Facilitator:** D07 (Testing Lead)
**Participants:** All developers

**Testing Checklist:**

**3.1.1 Automated Tests (09:00-10:00)**
```bash
# Full unit test suite
pytest tests/unit -v --cov=src/docling_hybrid --cov-report=html --cov-report=term

# Integration tests (if any)
pytest tests/integration -v

# Check coverage threshold
pytest tests/unit --cov=src/docling_hybrid --cov-fail-under=85
```

**Expected Results:**
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Coverage >85%
- [ ] No test warnings
- [ ] No flaky tests

**3.1.2 Manual Smoke Tests (10:00-11:00)**

**Test Case 1: Basic Conversion**
```bash
# Create test PDF (if not exists)
echo "Test content" | enscript -B -o - | ps2pdf - test.pdf

# Run conversion
docling-hybrid-ocr convert test.pdf

# Verify:
# - No errors
# - Output file created
# - Output contains markdown
```

**Test Case 2: Multi-Page Conversion**
```bash
# Use sample_3page.pdf from fixtures
docling-hybrid-ocr convert tests/fixtures/sample_3page.pdf --verbose

# Verify:
# - 3 pages processed
# - Concurrent processing logged (if enabled)
# - Page separators present
# - No errors
```

**Test Case 3: Error Handling**
```bash
# Non-existent file
docling-hybrid-ocr convert nonexistent.pdf
# Verify: Clear error message

# Invalid PDF
docling-hybrid-ocr convert corrupted.pdf
# Verify: Clear error message

# Missing API key (if applicable)
OPENROUTER_API_KEY="" docling-hybrid-ocr convert test.pdf
# Verify: Clear error message about missing key
```

**Test Case 4: CLI Commands**
```bash
# List backends
docling-hybrid-ocr backends
# Verify: Shows all registered backends

# Show info
docling-hybrid-ocr info
# Verify: Shows version, config, etc.

# Help
docling-hybrid-ocr --help
# Verify: Clear help text
```

**3.1.3 Code Quality Checks (11:00-12:00)**
```bash
# Linting
ruff check src/

# Type checking
mypy src/docling_hybrid

# Import verification
python -c "from docling_hybrid import __version__; print(__version__)"

# Package installation
pip install -e ".[dev]"  # Should succeed
```

**Lunch Break (12:00-14:00)**

### 3.2 Afternoon: Documentation and Retrospective (14:00-17:00)

**3.2.1 Documentation Review (14:00-15:00)**

**Facilitator:** D08 (Documentation Lead)

**Checklist:**
- [ ] CLAUDE.md is current
- [ ] CONTINUATION.md updated with Sprint 1 status
- [ ] README has latest features
- [ ] Architecture docs reflect changes
- [ ] All new features documented
- [ ] Examples work correctly

**Updates Required:**
```bash
# Update CONTINUATION.md
vi CONTINUATION.md
# Mark Sprint 1 as complete, add Sprint 2 as current

# Update CHANGELOG.md (if exists)
# Add Sprint 1 changes

# Verify all docs render correctly
# Check for broken links
```

**3.2.2 Sprint Retrospective (15:00-16:30)**

**Facilitator:** D01 (Tech Lead)
**Participants:** All developers
**Duration:** 90 minutes

**Retro Format: Start-Stop-Continue**

**Part 1: What Went Well? (20 min)**
- Each developer shares 1-2 things that went well
- D01 records on shared document

**Part 2: What Didn't Go Well? (20 min)**
- Each developer shares 1-2 challenges
- Focus on process, not blaming
- D01 records issues

**Part 3: Improvement Actions (30 min)**
- Discuss top 3-5 issues
- Brainstorm solutions
- Create concrete action items
- Assign owners

**Part 4: Appreciation (10 min)**
- Shout-outs for team members who helped
- Celebrate wins

**Part 5: Metrics Review (10 min)**
- Code metrics (LOC, files changed)
- Test coverage achieved
- Velocity (story points completed)
- Time spent

**Retrospective Output:**
```markdown
## Sprint 1 Retrospective

### What Went Well
1. Clean architecture made parallel work easy
2. Good communication in team channel
3. Most PRs ready on time

### What Didn't Go Well
1. Some test fixtures were missing
2. Merge conflicts in config file
3. CI took longer than expected

### Action Items for Sprint 2
1. [D07] Create all test fixtures by Day 1
2. [D04] Freeze common config early
3. [D01] Set up faster CI runners

### Metrics
- LOC Added: ~2,000
- PRs Merged: 10/10
- Test Coverage: 87%
- Sprint Velocity: 35 story points
```

**3.2.3 Sprint 2 Planning (16:30-17:00)**

**Facilitator:** D01 (Tech Lead)
**Duration:** 30 minutes

**Activities:**
1. Review Sprint 2 goals
2. Confirm task assignments
3. Identify dependencies
4. Set up initial PRs/branches
5. Schedule first Sprint 2 standup

**Sprint 2 Task Review:**
- S2-D02-01: DeepSeek vLLM backend (D02)
- S2-D03-01: Backend comparison tooling (D03)
- S2-D04-01: Docker containerization (D04)
- ... (review all Sprint 2 tasks)

**Sprint 2 Kickoff:**
- Date: Monday after Day 10
- Time: 10:00
- Location: Video call

---

## 4. Integration Checklists

### 4.1 Pre-Merge Checklist (Per PR)

**Before merging any PR:**

**CI Status:**
- [ ] All CI checks pass (green)
- [ ] No linting errors
- [ ] Type checking passes
- [ ] Tests pass

**Code Review:**
- [ ] At least 1 approval from:
  - File owner, OR
  - Tech Lead (D01)
- [ ] All review comments addressed
- [ ] No "Request Changes" status

**Testing:**
- [ ] New tests added for new code
- [ ] Tests pass locally
- [ ] Coverage >85% on new code
- [ ] No test flakiness observed

**Documentation:**
- [ ] Docstrings added to public APIs
- [ ] README updated (if applicable)
- [ ] CHANGELOG updated (if applicable)
- [ ] Examples work (if applicable)

**Conflicts:**
- [ ] No merge conflicts with develop
- [ ] If conflicts, resolved and re-tested
- [ ] Rebase if needed

### 4.2 Post-Merge Checklist (Per PR)

**After merging each PR:**

**Immediate:**
- [ ] Run full test suite
- [ ] Verify all tests pass
- [ ] Check coverage report
- [ ] No new warnings/errors

**Smoke Test:**
- [ ] Package imports correctly
- [ ] CLI commands work
- [ ] Basic conversion works
- [ ] No obvious regressions

**Communication:**
- [ ] Announce merge in team channel
- [ ] Update integration status board
- [ ] Notify dependent developers

### 4.3 Sprint Complete Checklist

**Before declaring Sprint 1 complete:**

**Code:**
- [ ] All Priority 0 (P0) tasks merged
- [ ] All Priority 1 (P1) tasks merged or rescheduled
- [ ] No known critical bugs
- [ ] develop branch is stable

**Testing:**
- [ ] All tests pass
- [ ] Coverage >85%
- [ ] No flaky tests
- [ ] Integration tests pass (if any)
- [ ] Manual smoke tests pass

**Documentation:**
- [ ] CLAUDE.md current
- [ ] CONTINUATION.md updated
- [ ] README current
- [ ] CHANGELOG updated
- [ ] API docs current

**Quality:**
- [ ] Linting passes
- [ ] Type checking passes
- [ ] No code smells identified
- [ ] Performance acceptable

**Process:**
- [ ] Retrospective completed
- [ ] Action items documented
- [ ] Sprint 2 planned
- [ ] Team agrees Sprint 1 is done

---

## 5. Issue Resolution Procedures

### 5.1 Merge Conflict Resolution

**If merge conflicts occur:**

1. **Identify Conflict:**
   - Git will show files with conflicts
   - Usually in shared files (common/*, configs/*)

2. **Owner Resolution:**
   - File owner resolves conflict
   - OR D01 resolves if multiple owners involved

3. **Resolution Process:**
   ```bash
   git checkout feat/s1-my-task
   git fetch origin develop
   git rebase origin/develop
   # Resolve conflicts
   git add <resolved-files>
   git rebase --continue
   git push --force-with-lease
   ```

4. **Re-test:**
   - Run tests locally
   - Verify CI passes
   - Get re-approval if significant changes

### 5.2 Test Failure Resolution

**If tests fail after merge:**

1. **Immediate Action:**
   - Stop further merges
   - Identify failing test(s)
   - Notify affected developer(s)

2. **Diagnosis:**
   - Run failing test locally
   - Check for race conditions
   - Review recent changes
   - Check test logs

3. **Fix Options:**
   - **Quick Fix:** PR owner fixes immediately
   - **Revert:** Revert the merge, fix separately
   - **Hot Fix:** D01 makes emergency fix

4. **Resolution:**
   - Fix applied
   - Tests pass
   - Resume merges

### 5.3 Coverage Drop Resolution

**If coverage drops below 85%:**

1. **Identify Gap:**
   - Check coverage report
   - Find uncovered lines
   - Identify responsible PR

2. **Add Tests:**
   - PR owner adds missing tests
   - OR D07 helps create tests
   - Target: Cover critical paths first

3. **Verification:**
   - Run coverage again
   - Verify >85%
   - Document what was added

### 5.4 Blocked PR Resolution

**If a PR cannot be merged:**

**Common Reasons:**
- Depends on unmerged PR
- Failing tests
- Merge conflicts
- Missing approval

**Resolution Path:**
1. Identify blocker
2. Work with affected developers
3. Fix blocker or defer PR to Sprint 2
4. Document decision

---

## 6. Communication Protocols

### 6.1 Team Channel Updates

**Format:**
```
## [STATUS] Task ID - Brief Description

**Status:** READY/IN_PROGRESS/BLOCKED
**Blocker:** (if any)
**ETA:** (if not ready)
**Help Needed:** (if any)
```

**Examples:**
```
## ✅ S1-D04-01 - Retry Utilities Module
Status: READY
PR: #123
CI: ✅ All checks pass
Reviews: 2/1 required

## ⏳ S1-D02-01 - Backend Retry Logic
Status: IN_PROGRESS
Blocker: Waiting for S1-D04-01 to merge
ETA: 2 hours after S1-D04-01

## ❌ S1-D05-01 - Renderer Memory Optimization
Status: BLOCKED
Blocker: Test failure in test_render_large_pdf
Help Needed: D07 to review test fixture
```

### 6.2 Escalation Path

**Level 1: Direct Communication**
- DM the person responsible
- Expected response: < 1 hour

**Level 2: Team Channel**
- Post in team channel with @mention
- Expected response: < 2 hours

**Level 3: Tech Lead**
- Escalate to D01
- D01 coordinates resolution
- Expected response: < 30 minutes

**Level 4: Emergency**
- Critical blocker
- Schedule emergency meeting
- All hands on deck

### 6.3 Status Updates

**Required Updates:**
1. **Daily Standup:** Post by 09:00
2. **PR Ready:** Announce when PR ready for review
3. **PR Merged:** Announce successful merge
4. **Blocker:** Announce immediately when blocked
5. **Completed:** Announce task completion

---

## 7. Tools and Access

### 7.1 Required Access

**All developers need:**
- [ ] Git repository access
- [ ] CI/CD system access (view builds)
- [ ] Team communication channel
- [ ] Shared documentation (if applicable)
- [ ] Code review permissions

**Tech Lead (D01) needs:**
- [ ] Repository admin access (merging)
- [ ] CI/CD admin access (rerun builds)
- [ ] Meeting hosting capabilities

### 7.2 Tools

**Version Control:**
- Git + GitHub
- Branch: feat/s1-*
- Target: develop

**CI/CD:**
- GitHub Actions
- Automated testing on PR
- Coverage reporting

**Communication:**
- Slack/Teams for team channel
- Video conferencing for meetings
- Shared documents for retro

**Testing:**
- pytest for unit/integration tests
- coverage for coverage reports
- ruff for linting
- mypy for type checking

---

## 8. Timeline Summary

```
┌─────────────────────────────────────────────────────────────┐
│                     SPRINT 1 TIMELINE                        │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Days 1-4: Implementation                                    │
│  ├── Individual development                                  │
│  ├── Daily standups (async)                                  │
│  └── Code reviews                                            │
│                                                              │
│  Day 5: Mid-Sprint Check (15:00)                            │
│  └── Status review, blocker identification                   │
│                                                              │
│  Days 6-8: Finalization                                      │
│  ├── Complete implementation                                 │
│  ├── Write tests                                             │
│  ├── Update documentation                                    │
│  └── Get PR approvals                                        │
│                                                              │
│  Day 9: Integration Day 1                                    │
│  ├── 09:00: Sprint Review (demos)                           │
│  ├── 11:00: PR Status Review                                │
│  ├── 12:00: Lunch                                            │
│  ├── 14:00: Merge Session                                    │
│  └── 18:00: Status Check                                     │
│                                                              │
│  Day 10: Integration Day 2                                   │
│  ├── 09:00: Automated Testing                               │
│  ├── 10:00: Manual Smoke Tests                              │
│  ├── 11:00: Code Quality Checks                             │
│  ├── 12:00: Lunch                                            │
│  ├── 14:00: Documentation Review                            │
│  ├── 15:00: Retrospective                                    │
│  └── 16:30: Sprint 2 Planning                               │
│                                                              │
│  Weekend: Buffer time if needed                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 9. Success Metrics

### 9.1 Process Metrics

**Integration Efficiency:**
- Target: All PRs merged by end of Day 9
- Actual: ___ PRs merged by Day 9
- Success: >80%

**Test Success Rate:**
- Target: >95% tests pass on first try after merge
- Actual: ___ tests passed / ___ total tests
- Success: >95%

**Coverage:**
- Target: >85% overall
- Actual: ___%
- Success: >85%

### 9.2 Quality Metrics

**Defects:**
- Critical bugs found: 0
- Major bugs found: <2
- Minor bugs found: <5

**Rework:**
- PRs requiring significant rework: <2
- Merge conflicts: <3
- Test failures after merge: <2

### 9.3 Team Metrics

**Collaboration:**
- Code review turnaround: <24 hours
- Blocker resolution time: <4 hours
- Communication responsiveness: <2 hours

**Velocity:**
- Story points completed: ___/___
- Tasks completed: ___/___
- Success: >80% of planned work

---

## 10. Post-Integration Actions

### 10.1 Immediate (Day 10 End)

- [ ] Create Sprint 1 completion announcement
- [ ] Update project status board
- [ ] Archive Sprint 1 materials
- [ ] Create Sprint 2 task board

### 10.2 Week 1 of Sprint 2

- [ ] Share retrospective notes with team
- [ ] Implement Sprint 2 action items
- [ ] Review and update this checklist for Sprint 2
- [ ] Schedule Sprint 2 mid-sprint check

### 10.3 Long-term

- [ ] Update development process based on learnings
- [ ] Improve integration checklist for future sprints
- [ ] Document best practices discovered
- [ ] Share learnings with broader team

---

## 11. Appendix

### 11.1 Command Reference

**Git Commands:**
```bash
# Check current branch
git status

# Pull latest develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feat/s1-my-task

# Push branch
git push -u origin feat/s1-my-task

# Rebase on develop
git fetch origin develop
git rebase origin/develop

# Force push after rebase
git push --force-with-lease
```

**Testing Commands:**
```bash
# Run unit tests
pytest tests/unit -v

# Run with coverage
pytest tests/unit --cov=src/docling_hybrid --cov-report=html

# Run specific test
pytest tests/unit/test_backends.py::test_make_backend -v

# Run integration tests
pytest tests/integration -v

# Run linting
ruff check src/

# Run type checking
mypy src/docling_hybrid
```

**CLI Commands:**
```bash
# Convert PDF
docling-hybrid-ocr convert test.pdf

# List backends
docling-hybrid-ocr backends

# Show version
docling-hybrid-ocr --version

# Show help
docling-hybrid-ocr --help
```

### 11.2 Contact List

| Role | Developer | Slack | Emergency |
|------|-----------|-------|-----------|
| Tech Lead | D01 | @d01 | Yes |
| Backend Lead | D02 | @d02 | For backend issues |
| Pipeline Lead | D03 | @d03 | For pipeline issues |
| Infrastructure | D04 | @d04 | For CI/CD issues |
| Renderer | D05 | @d05 | For renderer issues |
| CLI Lead | D06 | @d06 | For CLI issues |
| Testing Lead | D07 | @d07 | For test issues |
| Documentation | D08 | @d08 | For doc issues |
| Block Processing | D09 | @d09 | For block issues |
| Evaluation | D10 | @d10 | For eval issues |

### 11.3 Templates

**PR Description Template:**
```markdown
## Summary
Brief description of changes

## Task ID
S1-DXX-XX

## Changes
- List of changes made
- Why changes were needed

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated (if applicable)
- [ ] Manual testing completed
- [ ] Coverage >85% on new code

## Documentation
- [ ] Docstrings added
- [ ] README updated (if applicable)
- [ ] CHANGELOG updated

## Checklist
- [ ] CI passes
- [ ] No merge conflicts
- [ ] Self-reviewed
- [ ] Ready for review

## Dependencies
- Depends on: S1-DXX-XX (if any)
- Blocks: S1-DXX-XX (if any)
```

**Issue Template:**
```markdown
## Description
What is the issue?

## Steps to Reproduce
1. Step 1
2. Step 2
3. Step 3

## Expected Behavior
What should happen?

## Actual Behavior
What actually happens?

## Environment
- OS:
- Python version:
- Package version:

## Logs
```
Paste relevant logs
```

## Additional Context
Any other information
```

---

**Document Status:** ✅ Complete
**Owner:** D01 (Tech Lead)
**Next Update:** After Sprint 1 completion
**Version:** 1.0

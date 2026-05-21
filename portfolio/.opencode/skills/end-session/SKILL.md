---
name: end-session
description: Use when the user says "time to end the session", "wrap up", "end session", or similar. Runs the test suite, updates AGENTS.md and README.md to reflect the current state of the repo, and summarises what was done.
---

# End Session

When the user signals the session is ending, perform these steps in order:

## 1. Run the tests

```bash
.venv/bin/python3.12 -m pytest tests/ -v
```

If any tests fail, fix them before proceeding. If the failure is due to a
legitimate output change (e.g. a new column or broker), also rebuild the
canonical fixture:

```bash
python3 refresh_positions.py
# then update tests/data/ as needed
```

## 2. Update AGENTS.md

Review `AGENTS.md` against the current codebase and fix anything stale or
missing. High-value items to check:

- Output schema matches `OUTPUT_FIELDS` in `translate_positions.py`
- Broker list matches `PARSERS` dict
- Download scripts section reflects all scripts that exist
- Test section reflects the current test structure
- Verify/diff commands are correct
- Remove references to deleted files

Keep it concise — only include facts an agent would miss without help.

## 3. Update README.md

Review `README.md` against the current codebase and fix anything stale or
missing. Items to check:

- Package install command includes all required packages
- All download scripts are listed
- Manual export table only lists brokers without a download script
- Output format table matches `OUTPUT_FIELDS`
- Test run command is correct

## 4. Summarise

Tell the user:
- What tests ran and whether they passed
- What changes were made to `AGENTS.md` and `README.md` (or "no changes needed")
- Any issues that couldn't be resolved and need follow-up

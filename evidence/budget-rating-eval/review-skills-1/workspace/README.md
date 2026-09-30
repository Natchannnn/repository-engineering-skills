# Publishing and receipt helpers

Review the proposed `app.py` against `baseline.py` and `change.patch`.
The approved change makes `receipt_path` return `pathlib.Path`; its updated
consumer must still return `receipt.json`. The target contract is intentional.

`publish_with_retry` returns the first successful publisher result, uses the same
event ID as the idempotency key on all attempts, retries only `TransientError`
up to three calls, and propagates the final error after exhaustion. Permanent
errors propagate immediately. Callers rely on failure being observable.

Retail and archive validation belong to different teams and independent policies;
their current text and rules happen to match. No combined ownership is approved.
Report observable defects, with their file, symbol, evidence and consequence.
Review only: do not modify any project files, including tests or documentation.
Run `python -B -m unittest discover -p 'test*.py'` if useful.

# Reproducible verification image (Linux). Matches CI's linux-harness job.
FROM python:3.12-slim

WORKDIR /repo
# git is required: the refactor harness shells out to it (found by running this image once and watching 33 errors).
RUN apt-get update && apt-get install -y --no-install-recommends git && rm -rf /var/lib/apt/lists/*
COPY requirements-test.txt ./
RUN pip install --no-cache-dir -r requirements-test.txt
COPY . ./

# Windows-only PowerShell suites (installer rollback, runtime packaging,
# archive verification) are intentionally out of scope here. The archive packets'
# sealed hashes encode Windows path ordering, so they verify on Windows only;
# scripts/verify_archive.py is the cross-platform runner for Windows use.
# See docs/reproduce.md.
CMD ["sh", "-c", "python scripts/sync-shared.py --check \
  && python -B repo-foundation/evals/harness.py validate \
  && python -B -m unittest discover -s repo-foundation/evals/tests \
  && python -B -m unittest discover -s repo-native-refactor/evals/tests \
  && python -B scripts/test_demos.py"]

# Manual Gate 3 V2 — A/rep01

This is the no-target-skill trajectory of the new manual cohort, not a replay of the older automated 32+24 campaign. One candidate workspace was used across CP1–CP3; CP4 used a newly opened conversation on the same workspace. The candidate never received trusted checks or blind packets.

| Checkpoint | Submitted snapshot tree SHA-256 | Trusted active checks | Blind review |
| --- | --- | --- | --- |
| CP1 | `77486d97cb1facc0b62e3a3a4b455639da69d8736666167726380d96b7a5f4dd` | acceptance PASS | functional 2/4; `contract_aligned` not met because `LEDGER_FILE` is a `Path` rather than the requested literal string |
| CP2 | `4e5e84380b4e13d1063e0af8095e362fef63f7b8a5a37b135cd4786a6ff9edcd` | acceptance PASS; storage regression PASS | functional 2/4; `contract_aligned` not met for the same literal type mismatch |
| CP3 | `72fe30b82a44c1c8e8d9adf0c39a13e78502e2b9ca6e30bb29b503c357e4d563` | acceptance PASS; storage and query regressions PASS | functional 3/4; all CP3-specific required bars met |
| CP4 | `6950de2342bf1d4fd5f164c1c97eaebb13d75a8899f134f3f37b94bde88a676c` | **V2** acceptance PASS; storage, query and tenant regressions PASS | functional 3/4; CP4-specific bars met, with fresh-session evidence limited to visible chat separation |

All four pre-checks failed for the expected not-yet-implemented reason. Every bridge run used the pinned local container, read-only mounts, no host fallback, no timeout/truncation, and verified cleanup. The candidate's self-reported tests were not submitted as independent test artifacts; blind judge test-quality scores were 0/4 at each checkpoint.

Blind packets: `gate3-blind-packet-v2-001` through `gate3-blind-packet-v2-004`. The CP2 packet's initial `REVIEW.md` had an incomplete manually transcribed `query.py` hash; its original bytes and initial judge finding were retained, `CORRECTION.md` was added, and the judge independently reverified the submission/bridge binding and changed `outcome` from uncertain to met. No candidate file or bridge result changed.

The CP4 V2 verifier was declared for this cohort before execution; historical V1 outcomes remain separate. The operator's original fresh-session screenshot is preserved byte-exact at `gate3-audit-evidence-v2-004/cp4_fresh_session_original.png`, SHA-256 `49ebcba95739db2acf45cbf3cae612747c8ecfe0bcadb23e6487c87c5ada071c`. It shows a separate active conversation tab with the CP4 prompt and no visible prior CP1–CP3 chat; it cannot establish absence of hidden backend/system context.

Interpretation: **4/4 trusted functional acceptances passed**, but CP1 and CP2 have recorded rubric-alignment deviations. This single trajectory is not evidence that either target skill is better; comparison waits for the other variants and repetitions.

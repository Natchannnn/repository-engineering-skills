# Packet metadata correction (post-review, append-only)

The original `REVIEW.md` is preserved byte-for-byte, SHA-256 `a9a564207e5587e1bbd52c6b9077d448de7dabb0572da2d9bb8f0f9e2956e2d1`. Its `submitted/query.py` SHA-256 line accidentally omitted characters. The complete SHA-256 of the existing file is:

`1cc91e6d9fe8dfb31e026478a5a93161c07bfddf05a8ddc603119c9ab00c6558`

No submission file, task, trusted check, bridge result, or candidate workspace was changed. `bridge_results.json` is still SHA-256 `961854ba8e1e2956e66ab70936c72c628dce5db29e2c6e959650f9eb29774ff1`.

To reproduce the snapshot hashes, use `verify_hashes.py` in this packet. It implements the exact Windows `tree_hash` byte framing: for every file sorted by path, append the UTF-8 relative POSIX path, `\x00`, the single ASCII byte `-`, and the **raw 32-byte** SHA-256 file digest to the outer SHA-256 state. Do not append the hex text of the file digest or a newline. The expected values are `77486d97cb1facc0b62e3a3a4b455639da69d8736666167726380d96b7a5f4dd` for `predecessor/` and `4e5e84380b4e13d1063e0af8095e362fef63f7b8a5a37b135cd4786a6ff9edcd` for `submitted/`.

This correction documents an operator packet-assembly error. Preserve the initial review and record any revised conclusion separately; do not silently replace the initial judgment.

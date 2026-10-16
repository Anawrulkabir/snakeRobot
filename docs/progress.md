# Progress

## Milestone 1: environment check → paper notes → model plan (in progress)

### 2026-10-16: repository scaffold
- Added the directory layout from CLAUDE.md section 8, `requirements.txt`,
  `.gitignore`, `README.md` (with the AI disclosure), and `scripts/check_env.py`.
- **Not done:** the environment check itself. It must run on Fahad's machine
  (CLAUDE.md section 3). The version pins in `requirements.txt` have not been
  installed or tested anywhere yet.
- Reading the papers was blocked at first: this cloud environment cannot
  reach `arxiv.org`.

### 2026-10-16: paper notes
- Fahad uploaded arXiv:2304.08652v3 (78 pp., including the full supplement)
  and arXiv:2309.13532v1. Both were read in full.
- Wrote `docs/paper_notes.md`.
- Added `scripts/check_paper_arithmetic.py`. Run it with
  `python3 scripts/check_paper_arithmetic.py`; it needs only the standard
  library. It recomputes the paper's derived values (L_c = L_j = 28 mm,
  l0 = 0.73 mm/deg, the fully passive G for each amplitude) from the equations
  as transcribed, and they match the paper's stated values.
- Open for G2: the compliance definition summary in `paper_notes.md` §1.
- Raised for a later gate: the paper uses two independent cable drives per
  joint, while CLAUDE.md §4 assumes one servo per joint
  (`paper_notes.md` §7.1).
- Not yet written: `docs/model_plan.md`. It is next, after G2.

### Environment check results
_Waiting for the output of `python scripts/check_env.py` on Fahad's machine._

# Compute estimates (before running; Fahad asked for E1b's)

- **Measured:** implementation A costs **0.485 CPU-s per simulated second**
  (flat ground, this 4-core cloud sandbox, `time.process_time` over one
  16 s trial at G = 0.75). The stiff servo costs 0.38.
- **Assumed:** posts add contact work, factor ×1.0–1.5. Not measured yet;
  the arena does not exist.
- **Worst case:** every trial runs the full 40-cycle limit (320 s simulated
  at 0.125 Hz). Jammed trials end after 10 stuck cycles, and successful ones
  at the lattice exit, so real totals will be lower. How much lower is
  unknown until the first runs.

| Batch | Trials | CPU-h (posts ×1.0 / ×1.5) | Wall time on 4 cores |
|---|---|---|---|
| E1 main: 4 densities × 8 laws (7 G + tight spool) × 50 | 1600 | 69.0 / 103.5 | 17–26 h |
| E1 spot check at 0.0625 Hz: 1 density × 1 G × 50 | 50 | 4.3 / 6.5 | 1–2 h |
| E1 validation: 7-joint model, 1 density × 8 laws × 50 | 400 | 17.2 / 25.9 | 4–7 h |
| **E1b: 2 densities × 3 new stiffness levels × 8 laws × 50** (the 1× level reuses E1) | **2400** | **103.5 / 155.2** | **26–39 h** |

Computed by a script, from the formula trials × 40 cycles × 8 s × 0.485
(× 1.5). The output is copied above.

**Ways to cut it (Fahad's choice):**
- run on a machine with more cores (the sweep is embarrassingly parallel);
- lower `success.max_cycles`;
- run fewer trials per E1b cell;
- drop the tight-spool law from E1b.

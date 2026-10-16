# Measured data (Fahad)

## Body–post friction: tilt test (pending)

- **Expected file:** `post_friction_tilt.csv`, one row per trial. Columns:
  `trial,angle_deg`, where angle_deg is the tilt angle at which the PLA piece
  starts to slide on the PVC/wood surface. Fahad: 10 repeats.
- **Also expected:** a photo of the setup, `post_friction_tilt_setup.jpg`
  (or .png).
- **Analysis:** `scripts/friction_from_tilt.py`.
  - μ_s = tan(θ) for each trial; report the mean, SD and 95% CI.
  - The tilt test measures *static* friction at slip onset. The model has a
    single Coulomb μ, so the static value is used. Kinetic friction is
    usually lower; this goes on the E4 list rather than being guessed.
- Once the CSV is here, the value replaces the 0.4 placeholder in
  `config/arena.yaml` (`lattice.post_friction`), tagged `measured`, with the
  run ID of the analysis.

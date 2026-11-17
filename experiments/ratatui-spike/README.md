# ratatui badge spike

A host-only experiment showing that a ratatui app (`no_std` + `alloc`) can be rendered at 320x240 RGB565 through the `mousefood` embedded-graphics backend, as groundwork for possible native Rust firmware on the Universe badge. Nothing in this directory ran on a badge.

## Layout

- `badge-tui/` - `#![no_std]` library: `Button`, `Event`, and `App` with `update(Event)` and `draw(&mut Frame)`. No I/O and no time source; time arrives only as `Event::Tick(ms)`. Three screens (Menu list, Stats gauge + sparkline, About paragraph), tab header, one-line footer. Unit tests use ratatui's `TestBackend`.
- `badge-sim/` - std binary: `SimulatorDisplay<Rgb565>` 320x240 + mousefood `EmbeddedBackend` + ratatui `Terminal`.
- `screenshots/` - PNG output of the headless run (2x scale, 640x480).

## Run

Headless (default, no SDL needed). Runs a scripted event sequence, prints the grid size and per-frame draw time, writes `screenshots/*.png`:

    cargo run -p badge-sim

Windowed (needs SDL2 development libraries on the host):

    cargo run -p badge-sim --features window

The `window` feature compiles with `cargo check --features window` here, but SDL2 is not installed in the environment where this was written, so the window loop has never been run.

Button mapping in the window: Up / Down arrows = UP / DOWN, keys A / B / C = A / B / C. Menu screen: Up/Down move, B marks or clears the highlighted item (shown in the footer). A / C switch to the previous / next tab on any screen.

Other checks: `cargo test`, `cargo clippy --all-targets -- -D warnings`, `cargo fmt --check`, and
`rustup target add thumbv8m.main-none-eabihf && cargo check -p badge-tui --target thumbv8m.main-none-eabihf`.

## Grid and font

Font: `MONO_7X13` (bold: `MONO_7X13_BOLD`) from `embedded-graphics-unicodefonts`, using the const fonts rather than the `*_atlas()` functions (the atlas functions leak heap allocations). On 320x240 this gives **45 columns x 18 rows**, centred (5 px and 6 px left over). 6x10 would give 53x24 but is hard to read at badge size. Box-drawing glyphs, block characters and `>` render correctly in the screenshots.

## What was and was not verified

Verified on an x86_64 Linux host:

- Workspace builds, tests pass, clippy and rustfmt are clean.
- Headless render produces four PNGs that were inspected by eye.
- `badge-tui` type-checks and builds for `thumbv8m.main-none-eabihf` (Cortex-M33 class, the closest installable target to the RP2350; no atomics shim was needed there).
- `mousefood` + `ratatui` (default-features off) alone also check for that target. Checking `mousefood` from inside this workspace fails because `badge-sim`'s dependencies turn on `num-traits/std` through feature unification; a firmware crate would not have that problem.

Not verified:

- Anything on a badge, real display timing, real memory use, flash size.
- The SDL window loop.
- Draw times printed by the simulator are debug-build x86 numbers and say nothing about the RP2350. Mousefood's default `framebuffer` feature allocates a full-screen heap buffer of the display colour type (`Vec<Rgb565>`, so about 150 KB at 320x240), which matters for RAM budgeting.

## Next steps for hardware

- Display driver for the 8-bit parallel bus on GPIO32-39 with WR=30, RD=31, RS=28, CS=27, backlight=26. The LCD controller is not identified in the repo; find it before choosing or writing a driver (a PIO-based `embedded-graphics` `DrawTarget`).
- Buttons: UP=GPIO11, DOWN=GPIO6, A=GPIO7, B=GPIO9, C=GPIO10; map to `Button` and generate `Tick` from a hardware timer.
- Choose a HAL: `embassy-rp` or `rp235x-hal`.
- Add an `embedded-alloc` heap (ratatui and mousefood need `alloc`); measure RAM with and without mousefood's framebuffer.
- Measure flash size and frame time on the target; consider `portable-atomic` if a target without native atomics is used.
- Confirm that stock badge firmware can be restored before flashing anything, and read `hardware/README.md` and `hardware/USB_SERIAL.md` first.

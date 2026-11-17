//! Host simulator for `badge-tui`: renders through mousefood onto a 320x240
//! RGB565 `SimulatorDisplay`. Headless (PNG screenshots) by default;
//! `--features window` adds an interactive SDL2 loop.

use badge_tui::{App, Button, Event};
use embedded_graphics_simulator::{OutputSettings, OutputSettingsBuilder, SimulatorDisplay};
use mousefood::embedded_graphics::{geometry::Size, pixelcolor::Rgb565};
use mousefood::{fonts, EmbeddedBackend, EmbeddedBackendConfig, TerminalAlignment};
use ratatui::Terminal;
use std::time::Instant;

const WIDTH: u32 = 320;
const HEIGHT: u32 = 240;

fn config() -> EmbeddedBackendConfig<SimulatorDisplay<Rgb565>, Rgb565> {
    EmbeddedBackendConfig {
        font_regular: fonts::MONO_7X13,
        font_bold: Some(fonts::MONO_7X13_BOLD),
        horizontal_alignment: TerminalAlignment::Center,
        vertical_alignment: TerminalAlignment::Center,
        ..Default::default()
    }
}

fn output_settings() -> OutputSettings {
    OutputSettingsBuilder::new().scale(2).build()
}

type Term<'a> = Terminal<EmbeddedBackend<'a, SimulatorDisplay<Rgb565>, Rgb565>>;

fn draw(term: &mut Term, app: &App) -> std::io::Result<f64> {
    let t = Instant::now();
    term.draw(|f| app.draw(f))
        .map_err(|e| std::io::Error::other(format!("{e:?}")))?;
    Ok(t.elapsed().as_secs_f64() * 1000.0)
}

#[cfg(not(feature = "window"))]
fn main() -> Result<(), Box<dyn std::error::Error>> {
    use std::fs;
    use Button::*;

    let out_dir = std::path::Path::new(env!("CARGO_MANIFEST_DIR")).join("../screenshots");
    fs::create_dir_all(&out_dir)?;

    let mut display = SimulatorDisplay::<Rgb565>::new(Size::new(WIDTH, HEIGHT));
    let backend = EmbeddedBackend::new(&mut display, config());
    let mut term = Terminal::new(backend).map_err(|e| std::io::Error::other(format!("{e:?}")))?;
    let size = term
        .size()
        .map_err(|e| std::io::Error::other(format!("{e:?}")))?;
    println!("terminal grid: {} cols x {} rows", size.width, size.height);

    let mut app = App::new();

    // (screenshot name, events to apply first)
    let script: Vec<(&str, Vec<Event>)> = vec![
        ("01-menu", vec![Event::Tick(16)]),
        (
            "02-menu-selected",
            vec![Event::Press(Down), Event::Press(Down), Event::Press(B)],
        ),
        (
            "03-stats",
            std::iter::once(Event::Press(C))
                .chain(std::iter::repeat_n(Event::Tick(50), 200))
                .collect(),
        ),
        ("04-about", vec![Event::Press(C)]),
    ];

    for (name, events) in script {
        for e in events {
            app.update(e);
        }
        let ms = draw(&mut term, &app)?;
        let img = term
            .backend()
            .display()
            .to_rgb_output_image(&output_settings());
        let path = out_dir.join(format!("{name}.png"));
        img.save_png(&path)?;
        println!("{name}: draw {ms:.2} ms -> {}", path.display());
    }
    Ok(())
}

#[cfg(feature = "window")]
fn main() -> Result<(), Box<dyn std::error::Error>> {
    use embedded_graphics_simulator::sdl2::Keycode;
    use embedded_graphics_simulator::{SimulatorEvent, Window};

    let settings = output_settings();
    let mut window = Window::new("badge-tui (Up/Down, A, B, C)", &settings);
    let mut display = SimulatorDisplay::<Rgb565>::new(Size::new(WIDTH, HEIGHT));
    let backend = EmbeddedBackend::new(&mut display, config());
    let mut term = Terminal::new(backend).map_err(|e| std::io::Error::other(format!("{e:?}")))?;
    let mut app = App::new();
    let mut last = Instant::now();

    loop {
        let now = Instant::now();
        app.update(Event::Tick(now.duration_since(last).as_millis() as u32));
        last = now;
        draw(&mut term, &app)?;
        window.update(term.backend().display());

        for ev in window.events() {
            match ev {
                SimulatorEvent::Quit => return Ok(()),
                SimulatorEvent::KeyDown { keycode, .. } => {
                    let b = match keycode {
                        Keycode::Up => Button::Up,
                        Keycode::Down => Button::Down,
                        Keycode::A => Button::A,
                        Keycode::B => Button::B,
                        Keycode::C => Button::C,
                        _ => continue,
                    };
                    app.update(Event::Press(b));
                }
                _ => {}
            }
        }
        std::thread::sleep(std::time::Duration::from_millis(33));
    }
}

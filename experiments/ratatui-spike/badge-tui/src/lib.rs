//! Hardware-independent badge UI built on ratatui.
//!
//! Everything here is `no_std` + `alloc`, performs no I/O and has no time
//! source: time only enters through [`Event::Tick`], so behaviour does not
//! depend on the frame rate.
#![no_std]

extern crate alloc;

use alloc::format;
use alloc::string::String;
use alloc::vec::Vec;
use ratatui::layout::{Constraint, Layout, Rect};
use ratatui::style::{Color, Modifier, Style};
use ratatui::text::{Line, Span};
use ratatui::widgets::{Block, Gauge, List, ListItem, ListState, Paragraph, Sparkline, Tabs, Wrap};
use ratatui::Frame;

/// The five physical buttons.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Button {
    Up,
    Down,
    A,
    B,
    C,
}

/// Input to [`App::update`].
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Event {
    /// A button was pressed.
    Press(Button),
    /// Milliseconds elapsed since the previous tick.
    Tick(u32),
}

/// Titles of the three screens, in tab order.
pub const SCREENS: [&str; 3] = ["Menu", "Stats", "About"];
/// Entries of the demo menu.
pub const MENU_ITEMS: [&str; 6] = ["Apps", "Badge ID", "Schedule", "Wi-Fi", "Games", "Settings"];

const SPARK_LEN: usize = 43;
const SPARK_PERIOD_MS: u32 = 200;
const GAUGE_PERIOD_MS: u32 = 6000;

const ACCENT: Color = Color::Yellow;
const DIM: Color = Color::DarkGray;

/// Application state.
#[derive(Clone, Debug)]
pub struct App {
    screen: usize,
    cursor: usize,
    chosen: Option<usize>,
    gauge_ms: u32,
    spark_ms: u32,
    spark: Vec<u64>,
    rng: u32,
}

impl Default for App {
    fn default() -> Self {
        Self::new()
    }
}

impl App {
    pub fn new() -> Self {
        Self {
            screen: 0,
            cursor: 0,
            chosen: None,
            gauge_ms: 0,
            spark_ms: 0,
            spark: Vec::with_capacity(SPARK_LEN),
            rng: 0x1234_5678,
        }
    }

    /// Index of the active screen (0 = Menu, 1 = Stats, 2 = About).
    pub fn screen(&self) -> usize {
        self.screen
    }

    /// Highlighted menu row.
    pub fn cursor(&self) -> usize {
        self.cursor
    }

    /// Menu row marked by B, if any.
    pub fn chosen(&self) -> Option<usize> {
        self.chosen
    }

    /// Gauge position, 0..=100 (triangle wave over time).
    pub fn gauge_percent(&self) -> u16 {
        let half = GAUGE_PERIOD_MS / 2;
        let t = self.gauge_ms % GAUGE_PERIOD_MS;
        let up = if t < half { t } else { GAUGE_PERIOD_MS - t };
        (up * 100 / half) as u16
    }

    /// Sparkline samples, oldest first.
    pub fn spark(&self) -> &[u64] {
        &self.spark
    }

    fn next_random(&mut self) -> u32 {
        // xorshift32: no libm, no allocation, deterministic.
        let mut x = self.rng;
        x ^= x << 13;
        x ^= x >> 17;
        x ^= x << 5;
        self.rng = x;
        x
    }

    fn push_sample(&mut self) {
        let r = (self.next_random() >> 8) % 41;
        // Random walk around the gauge value keeps the graph related to it.
        let v = (u64::from(self.gauge_percent()) + u64::from(r)) / 2 + 10;
        if self.spark.len() == SPARK_LEN {
            self.spark.remove(0);
        }
        self.spark.push(v);
    }

    pub fn update(&mut self, event: Event) {
        match event {
            Event::Tick(ms) => {
                self.gauge_ms = (self.gauge_ms + ms) % GAUGE_PERIOD_MS;
                self.spark_ms += ms;
                while self.spark_ms >= SPARK_PERIOD_MS {
                    self.spark_ms -= SPARK_PERIOD_MS;
                    self.push_sample();
                }
            }
            Event::Press(Button::A) => {
                self.screen = (self.screen + SCREENS.len() - 1) % SCREENS.len();
            }
            Event::Press(Button::C) => {
                self.screen = (self.screen + 1) % SCREENS.len();
            }
            Event::Press(Button::Up) if self.screen == 0 => {
                self.cursor = (self.cursor + MENU_ITEMS.len() - 1) % MENU_ITEMS.len();
            }
            Event::Press(Button::Down) if self.screen == 0 => {
                self.cursor = (self.cursor + 1) % MENU_ITEMS.len();
            }
            Event::Press(Button::B) if self.screen == 0 => {
                self.chosen = if self.chosen == Some(self.cursor) {
                    None
                } else {
                    Some(self.cursor)
                };
            }
            Event::Press(_) => {}
        }
    }

    pub fn draw(&self, frame: &mut Frame) {
        let [tabs_area, body, footer] = Layout::vertical([
            Constraint::Length(3),
            Constraint::Min(0),
            Constraint::Length(1),
        ])
        .areas(frame.area());

        let tabs = Tabs::new(SCREENS.iter().map(|s| Line::from(*s)))
            .select(self.screen)
            .block(Block::bordered().title(" Badge TUI "))
            .style(Style::new().fg(Color::Gray))
            .highlight_style(
                Style::new()
                    .fg(Color::Black)
                    .bg(ACCENT)
                    .add_modifier(Modifier::BOLD),
            );
        frame.render_widget(tabs, tabs_area);

        match self.screen {
            0 => self.draw_menu(frame, body),
            1 => self.draw_stats(frame, body),
            _ => Self::draw_about(frame, body),
        }

        self.draw_footer(frame, footer);
    }

    fn draw_menu(&self, frame: &mut Frame, area: Rect) {
        let items = MENU_ITEMS.iter().enumerate().map(|(i, name)| {
            let mark = if self.chosen == Some(i) { "[x]" } else { "[ ]" };
            ListItem::new(format!("{mark} {name}"))
        });
        let list = List::new(items)
            .block(Block::bordered().title(" Menu "))
            .highlight_symbol("> ")
            .highlight_style(
                Style::new()
                    .fg(Color::Black)
                    .bg(Color::Cyan)
                    .add_modifier(Modifier::BOLD),
            );
        let mut state = ListState::default().with_selected(Some(self.cursor));
        frame.render_stateful_widget(list, area, &mut state);
    }

    fn draw_stats(&self, frame: &mut Frame, area: Rect) {
        let [gauge_area, spark_area] =
            Layout::vertical([Constraint::Length(3), Constraint::Min(0)]).areas(area);

        let pct = self.gauge_percent();
        let gauge = Gauge::default()
            .block(Block::bordered().title(" Battery sim "))
            .gauge_style(Style::new().fg(Color::Green).bg(DIM))
            .percent(pct)
            .label(Span::styled(
                format!("{pct}%"),
                Style::new().fg(Color::White).add_modifier(Modifier::BOLD),
            ));
        frame.render_widget(gauge, gauge_area);

        let spark = Sparkline::default()
            .block(Block::bordered().title(" Signal "))
            .style(Style::new().fg(Color::Magenta))
            .max(100)
            .data(self.spark.iter().copied());
        frame.render_widget(spark, spark_area);
    }

    fn draw_about(frame: &mut Frame, area: Rect) {
        let text = "Universe badge ratatui spike. This UI is no_std + alloc and \
                    is drawn through mousefood onto an RGB565 display. \
                    Nothing here has run on real hardware yet.";
        let p = Paragraph::new(text)
            .wrap(Wrap { trim: true })
            .block(Block::bordered().title(" About "));
        frame.render_widget(p, area);
    }

    fn draw_footer(&self, frame: &mut Frame, area: Rect) {
        let text: String = if self.screen == 0 {
            match self.chosen {
                Some(i) => format!(" Selected: {}  (B: clear)", MENU_ITEMS[i]),
                None => String::from(" Up/Dn move  B select  A/C tab"),
            }
        } else {
            String::from(" A: prev tab          C: next tab")
        };
        frame.render_widget(
            Paragraph::new(text).style(Style::new().fg(Color::Black).bg(Color::Gray)),
            area,
        );
    }
}

#[cfg(test)]
extern crate std;

#[cfg(test)]
mod tests {
    use super::*;
    use ratatui::backend::TestBackend;
    use ratatui::Terminal;

    fn press(app: &mut App, b: Button) {
        app.update(Event::Press(b));
    }

    fn render(app: &App) -> std::string::String {
        let mut term = Terminal::new(TestBackend::new(45, 18)).unwrap();
        term.draw(|f| app.draw(f)).unwrap();
        let buf = term.backend().buffer();
        let mut out = std::string::String::new();
        for y in 0..buf.area.height {
            for x in 0..buf.area.width {
                out.push_str(buf[(x, y)].symbol());
            }
            out.push('\n');
        }
        out
    }

    #[test]
    fn tabs_wrap() {
        let mut a = App::new();
        press(&mut a, Button::A);
        assert_eq!(a.screen(), 2);
        press(&mut a, Button::C);
        assert_eq!(a.screen(), 0);
        press(&mut a, Button::C);
        assert_eq!(a.screen(), 1);
    }

    #[test]
    fn menu_cursor_and_choice() {
        let mut a = App::new();
        press(&mut a, Button::Up);
        assert_eq!(a.cursor(), MENU_ITEMS.len() - 1);
        press(&mut a, Button::Down);
        press(&mut a, Button::Down);
        assert_eq!(a.cursor(), 1);
        press(&mut a, Button::B);
        assert_eq!(a.chosen(), Some(1));
        press(&mut a, Button::B);
        assert_eq!(a.chosen(), None);
    }

    #[test]
    fn menu_keys_ignored_off_menu() {
        let mut a = App::new();
        press(&mut a, Button::C);
        press(&mut a, Button::Down);
        press(&mut a, Button::B);
        assert_eq!(a.cursor(), 0);
        assert_eq!(a.chosen(), None);
    }

    #[test]
    fn ticks_are_frame_rate_independent() {
        let mut fast = App::new();
        let mut slow = App::new();
        for _ in 0..1000 {
            fast.update(Event::Tick(1));
        }
        for _ in 0..10 {
            slow.update(Event::Tick(100));
        }
        assert_eq!(fast.gauge_percent(), slow.gauge_percent());
        assert_eq!(fast.spark(), slow.spark());
        assert_eq!(fast.spark().len(), 5);
    }

    #[test]
    fn gauge_range_and_spark_cap() {
        let mut a = App::new();
        for _ in 0..2000 {
            a.update(Event::Tick(37));
            assert!(a.gauge_percent() <= 100);
        }
        assert_eq!(a.spark().len(), SPARK_LEN);
        assert!(a.spark().iter().all(|&v| v <= 100));
    }

    #[test]
    fn renders_each_screen() {
        let mut a = App::new();
        a.update(Event::Tick(1500));
        assert!(render(&a).contains("Apps"));
        press(&mut a, Button::B);
        assert!(render(&a).contains("Selected: Apps"));
        press(&mut a, Button::C);
        let s = render(&a);
        assert!(s.contains("Battery sim") && s.contains("Signal"));
        press(&mut a, Button::C);
        assert!(render(&a).contains("ratatui spike"));
    }
}

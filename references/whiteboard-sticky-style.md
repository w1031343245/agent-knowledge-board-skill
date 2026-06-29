# Realistic Whiteboard Sticky Style

## Direction

Use this style for email/web daily-board output when the user wants a restrained hand-journal paper briefing. The result should feel like Agent-filtered intelligence: warm paper, light tape, red judgment cues, and consistent sections.

## Visual Language

- Whiteboard surface: warm off-white with subtle paper texture and low-contrast dashed separators.
- Header: one integrated cover with title, subtitle, today's thesis, meta line, and a small red judgment stamp.
- Papers: mostly aligned story cards with very light shadows; tape only on the cover, section labels, and the first focus card.
- Ink language: red for numbers, key judgment labels, risks, and action prompts; blue only for links and section-left rule lines.
- Typography: Georgia family for all rendered HTML.

## Information Roles

- Cover: top-level daily thesis and metrics.
- Section header: paper label plus one-line section thesis.
- Story cards: adaptive layout. Use chain cards only for real event progression, parallel cards for independent hotspots, and main-side layout for two important items.
- Action bar: concrete next step for the section.
- Related row: horizontal `延伸阅读` links.

## Layout

Use a consistent V2 daily-board layout:

1. Top: cover with title, subtitle, `今日主线`, judgment stamp, and one-line metadata.
2. Each board begins with a paper section label and a blue left-rule section thesis.
3. Each board shows up to three cards using the correct logic layout; do not force a third card.
4. Put concrete `下一步` content below the cards.
5. Put overflow and prior-note references into one horizontal `延伸阅读` row.
6. Avoid rigid decoration overload: no large blue boxes, no repeated slogans, no heavy shadows.
7. Shorten source URLs to readable domains so long links do not distort card layout.
8. Keep the rendered page at 720px CSS width; export screenshots at 2x scale for chat-software readability.
9. Split screenshot-ready output into pages of at most two sections.

## Density Rules

- Keep each board to up to 3 core cards and 3 related links.
- If a board has too many items, keep only the useful names in `延伸阅读` and leave the full archive outside the email.
- Do not shrink note text below readability just to fit more content.
- Do not rely on fixed heights, hidden overflow, or CSS clipping; shorten text before rendering.

## Email Constraints

- Use CSS-rendered rectangles and shadows, not a single image, for real email output.
- Keep all important content as selectable text.
- Avoid JavaScript and hover-only interactions.
- Inline CSS where possible when sending as an email.

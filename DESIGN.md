# Shared visual system

Authority: user-approved Sui-inspired bilingual homepage, refined in this chat. This repository implements it in `frontend/`; full component and source mapping lives in `docs/frontend-design-system.md`.

## Fixed decisions

- Anonymous linked-line brand mark only. No invented product name.
- Four top-level routes, one shared header/footer. UI actions in Chinese. English supports display typography and role/workflow hierarchy.
- Black #000 page, charcoal #131518 card, #343940 nav glyph tile. Keep these three surfaces distinct. White #FFF and pale #F4F5F7 workflow surfaces join without border, shadow, mask or black seam.
- Blue #5986FA accent, #298DFF motion highlight. Square geometry, dotted separators, original thin cross on every navigation item.
- Inter and Noto Sans SC locally served, weight400 for most content. Buttons12.444px, body16px, card18.674px. Never enlarge UI controls to fill a section.
- Hero CSS atmosphere gradient, large English display, small Chinese positioning, joined Chinese CTA pair119x42.667px per button.
- Workflow1:4 offset grid; five concise Chinese headings, small English labels, original SVG/Lottie icons.
- Role card: header, dotted rule, deliberate blank pause, sentence, three details, dotted rule, square-to-full-width blue reveal link with character flip.
- Footer is one short gray line on black, no large empty block.
- Enterprise marquee uses actual image logos, no type stand-ins, no black fade edges, no visible playback controls.

## Motion boundary

Source-derived GSAP/Lenis timings and reconstructed effects; source implementation differs from project-specific scenes. Navigation character shuffle and workflow first-entry color/text scramble are separate from CTA vertical character flips. Continuous smooth scrolling on desktop; wheel and PageUp/PageDown are not intercepted. No section snapping, pinning or animation locks. Touch and small-screen scrolling remains natural. Animations are enabled by default without a user-facing toggle or stored preference. The enterprise logo marquee keeps moving on hover. Unmount cleans all observers, timelines, ticker listeners and Lottie instances.

## Future pages

Operate pages reuse tokens and controls. Do not apply homepage scene-wheel interception to tables, forms or enterprise detail views. Use `/api/v1` client, honest missing values and explicit error/loading/empty states. The specialist page implements search, deterministic scoring and enterprise detail. Leadership and planning remain scaffolds.

## Specialist surface

A full white search viewport precedes black results. ScrollTrigger interpolates the entire local page background from40% to65% of the first viewport; no static gradient band or scroll snapping. Search uses a standard magnifier and adjacent blue arrow/rules buttons, with no hover color change. Sector choices remain visible as a compact navigation row.

Company cards preserve title/arrow, short sector description, breathing room, then logo/score. On entering the viewport cards rise52px with stagger; hovering raises8px and reveals a3px blue rule from10% to100% over0.45s. Only the top-right arrow opens details. Details use separated sections, horizontal score bars, an open investment timeline and a single wrapping city row. Rule explanation uses formal headings, muted body copy and small blue square section markers.

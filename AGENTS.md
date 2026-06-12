# Agent project notes

This project's Baseline target is **Baseline 2024** (per [Google Modern Web Guidance](https://developer.chrome.com/docs/modern-web-guidance)).

Frontend conventions:
- Prefer native HTML (`<dialog>`, semantic landmarks) over custom overlay divs where possible.
- Use `oklch` colors, `color-mix`, and `prefers-reduced-motion` fallbacks.
- Use View Transitions API for tab switches when supported.
- Ensure keyboard focus (`:focus-visible`) and `aria-*` on interactive controls.

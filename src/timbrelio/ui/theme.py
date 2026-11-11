"""Shared visual tokens for the Cosmic Latte interface."""

COLORS = {
    "canvas": "#F7F1E7",
    "cosmic_latte": "#E8DCC6",
    "mocha_cream": "#B7A89A",
    "deep_burgundy": "#722F37",
    "ink": "#2D2321",
    "muted_ink": "#6F5C56",
    "porcelain": "#FFF9EF",
}

APP_CSS = f"""
:root {{
  --canvas: {COLORS['canvas']};
  --cosmic-latte: {COLORS['cosmic_latte']};
  --mocha-cream: {COLORS['mocha_cream']};
  --deep-burgundy: {COLORS['deep_burgundy']};
  --ink: {COLORS['ink']};
  --muted-ink: {COLORS['muted_ink']};
  --porcelain: {COLORS['porcelain']};
}}

.stApp {{
  background:
    radial-gradient(circle at 88% 8%, rgba(183, 168, 154, 0.22), transparent 26rem),
    var(--canvas);
  color: var(--ink);
}}

[data-testid="stSidebar"] {{
  background: var(--mocha-cream);
  border-right: 1px solid rgba(45, 35, 33, 0.16);
}}

[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
  color: var(--ink);
}}

.block-container {{
  box-sizing: border-box;
  max-width: 1440px;
  padding-top: clamp(2rem, 5vw, 4.5rem);
  padding-bottom: 3rem;
  width: 100%;
}}

.brand-wordmark {{
  font-family: Georgia, 'Times New Roman', serif;
  font-size: 2.25rem;
  letter-spacing: -0.05em;
  margin: 0 0 1.25rem;
}}

.hero {{
  max-width: 860px;
  margin-bottom: clamp(1.75rem, 4vw, 3rem);
}}

.eyebrow {{
  color: var(--deep-burgundy);
  font-size: 0.76rem;
  font-weight: 750;
  letter-spacing: 0.16em;
  margin-bottom: 0.7rem;
}}

.hero h1 {{
  color: var(--deep-burgundy);
  font-family: Georgia, 'Times New Roman', serif;
  font-size: clamp(2.7rem, 6vw, 5.4rem);
  font-weight: 500;
  letter-spacing: -0.055em;
  line-height: 0.98;
  margin: 0;
}}

.hero-copy {{
  color: var(--muted-ink);
  font-size: clamp(1rem, 1.7vw, 1.2rem);
  line-height: 1.65;
  margin: 1.25rem 0 0;
  max-width: 660px;
}}

.map-meta {{
  align-items: baseline;
  display: flex;
  justify-content: space-between;
  margin: 0 0 0.75rem;
}}

.map-meta span {{
  color: var(--muted-ink);
  font-size: 0.72rem;
  font-weight: 750;
  letter-spacing: 0.14em;
}}

.map-meta strong {{
  color: var(--deep-burgundy);
  font-size: 0.9rem;
}}

[data-testid="stRadio"] {{
  background: rgba(255, 249, 239, 0.72);
  border: 1px solid rgba(45, 35, 33, 0.12);
  border-radius: 1rem;
  box-sizing: border-box;
  margin-bottom: 1rem;
  padding: 0.75rem 1rem 0.35rem;
}}

[data-testid="stRadio"] > label {{
  color: var(--deep-burgundy);
  font-weight: 700;
}}

[data-testid="stPlotlyChart"] {{
  background: var(--cosmic-latte);
  border: 1px solid rgba(45, 35, 33, 0.13);
  border-radius: 1.5rem;
  box-sizing: border-box;
  box-shadow: 0 20px 60px rgba(76, 49, 45, 0.09);
  max-width: 100%;
  overflow: hidden;
  padding: clamp(0.3rem, 1vw, 0.75rem);
}}

:focus-visible {{
  outline: 3px solid var(--deep-burgundy) !important;
  outline-offset: 3px !important;
}}

@media (max-width: 640px) {{
  .block-container {{
    padding-left: 1rem;
    padding-right: 1rem;
    padding-top: 1.75rem;
  }}

  .hero h1 {{
    font-size: clamp(2.5rem, 14vw, 4rem);
  }}

  [data-testid="stPlotlyChart"] {{
    border-radius: 1rem;
  }}
}}

@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{
    scroll-behavior: auto !important;
    transition-duration: 0.01ms !important;
  }}
}}
"""


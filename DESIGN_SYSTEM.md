# P.R.I.S.M. Design System

> **Radiant Core** — A light-mode, AI-native aesthetic defined by an expansive white canvas, a vibrant central mesh aura with a subtle circuit board pattern, high-contrast dark command surfaces, and soft, rounded typography.

---

## 1. Typography

| Role | Font | Weight | Source |
|---|---|---|---|
| **Headline / Display** | Plus Jakarta Sans | 700–800 | Google Fonts |
| **Body / UI** | Inter | 400, 500, 600 | Google Fonts |
| **Code / Mono** | JetBrains Mono | 400, 500 | Google Fonts |

```css
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

:root {
  --font-display: 'Plus Jakarta Sans', -apple-system, sans-serif;
  --font-primary: 'Inter', -apple-system, sans-serif;
  --font-mono:    'JetBrains Mono', monospace;
}
```

---

## 2. Type Scale

| Token | Size | Weight | Font | Usage |
|---|---|---|---|---|
| `--text-hero` | 64px / 4rem | 800 | Display | Main hero headline |
| `--text-h1` | 32px / 2rem | 700 | Display | Section headings |
| `--text-body-lg` | 18px / 1.125rem | 400 | Primary | Subtitles |
| `--text-body` | 15px / 0.9375rem | 400 | Primary | Main body text |
| `--text-ui` | 13px / 0.8125rem | 500 | Primary | Buttons, pills, badges |
| `--text-caption` | 12px / 0.75rem | 500 | Primary | Very small labels |

```css
:root {
  --text-hero:     4rem;
  --text-h1:       2rem;
  --text-body-lg:  1.125rem;
  --text-body:     0.9375rem;
  --text-ui:       0.8125rem;
  --text-caption:  0.75rem;
}
```

---

## 3. Colors

### 3.1 Canvas (Backgrounds)

```css
:root {
  --canvas-base:       #FFFFFF;   /* Pure white page background */
  --canvas-surface:    #F9F9F9;   /* Light gray for secondary containers */
  --canvas-dark:       #111111;   /* The command center core */
  --canvas-dark-pill:  #222222;   /* Buttons inside the command center */
  --canvas-dark-hover: #333333;
}
```

### 3.2 Ink (Text)

```css
:root {
  --ink-primary:       #000000;   /* Pure black headlines */
  --ink-secondary:     #555555;   /* Subtitles and supporting text */
  --ink-tertiary:      #888888;   /* Placeholders, disabled states */
  --ink-inverse:       #FFFFFF;   /* Text on dark surfaces */
  --ink-inverse-muted: #A0A0A0;   /* Secondary text on dark */
}
```

### 3.3 Borders

```css
:root {
  --border-subtle:   #EAEAEA;   /* Pills, light outlines */
  --border-strong:   #CCCCCC;   /* Inputs */
  --border-dark:     #333333;   /* Inside the command center */
}
```

### 3.4 Radiant Aura (Gradients)

The signature visual element is the intensely colorful aura centered behind the main floating element.

```css
:root {
  --aura-magenta: #FF2E93;
  --aura-orange:  #FF8008;
  --aura-yellow:  #FFC837;
  --aura-cyan:    #00E1D9;
}
```

---

## 4. Spacing & Radius

Soft, generous rounding ("bento-box" style) and ample whitespace.

```css
:root {
  --space-1:  4px;
  --space-2:  8px;
  --space-3:  12px;
  --space-4:  16px;
  --space-6:  24px;
  --space-8:  32px;
  --space-12: 48px;
  --space-16: 64px;

  --radius-sm:   6px;
  --radius-md:   12px;
  --radius-lg:   20px;
  --radius-xl:   32px;
  --radius-pill: 9999px;
}
```

---

## 5. Elevation & Effects

Floating layers with soft, diffused shadows.

```css
:root {
  --shadow-sm:    0 2px 8px rgba(0, 0, 0, 0.04);
  --shadow-md:    0 8px 24px rgba(0, 0, 0, 0.06);
  --shadow-float: 0 20px 40px rgba(0, 0, 0, 0.12), 0 4px 12px rgba(0, 0, 0, 0.04);
  
  /* The glowing border around the dark command center */
  --gradient-glow: linear-gradient(135deg, #FFC837, #FF8008, #FF2E93);
}
```

---

## 6. Core Components

### 6.1 Action Pills (Light)
Used for navigation, external links, and secondary actions.
```css
.pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: var(--canvas-base);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-pill);
  font-size: var(--text-ui);
  font-weight: 500;
  color: var(--ink-secondary);
  box-shadow: var(--shadow-sm);
}
.pill:hover { color: var(--ink-primary); border-color: #DDD; }
```

### 6.2 Solid Black Pill
For primary "Access" or "Get Started" buttons.
```css
.pill--solid {
  background: var(--ink-primary);
  color: var(--canvas-base);
  border: none;
}
.pill--solid:hover { background: #333; }
```

### 6.3 Command Center (The Floating Dark UI)
The focal point of the page. It features a glowing gradient padding layer and an inner dark rounded box.
```css
.command-border {
  padding: 4px; /* Thickness of the glowing border */
  background: var(--gradient-glow);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-float);
}

.command-center {
  background: var(--canvas-dark);
  border-radius: calc(var(--radius-xl) - 4px);
  padding: 32px;
  color: var(--ink-inverse);
}
```

### 6.4 Inner Command Pills (Dark)
Used inside the command center.
```css
.cmd-pill {
  background: var(--canvas-dark-pill);
  border: 1px solid var(--border-dark);
  color: var(--ink-inverse);
  padding: 8px 14px;
  border-radius: var(--radius-pill);
  font-size: var(--text-ui);
  font-weight: 500;
}
.cmd-pill:hover { background: var(--canvas-dark-hover); }
```

### 6.5 Gradient Submit Button
```css
.btn-submit {
  background: linear-gradient(135deg, #FF2E93, #FF8008);
  border: none;
  border-radius: var(--radius-md);
  width: 40px; height: 40px;
  display: flex; justify-content: center; align-items: center;
  color: white;
}
```

---

## 7. Background System

The background combines a subtle repeating circuit board pattern with a complex multi-layered radial gradient that sits behind the command center, mimicking an organic, intelligent flow of data.

```css
body {
  background-color: var(--canvas-base);
  background-image: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E...%3C/svg%3E");
}

.mesh-aura {
  position: absolute;
  top: 50%; left: 50%;
  transform: translate(-50%, -50%);
  width: 100vw; height: 600px;
  z-index: -1;
  background: 
    radial-gradient(ellipse 600px 300px at 30% 50%, rgba(255, 46, 147, 0.6), transparent),
    radial-gradient(ellipse 700px 400px at 70% 50%, rgba(255, 128, 8, 0.5), transparent),
    radial-gradient(ellipse 500px 200px at 50% 60%, rgba(0, 225, 217, 0.4), transparent);
  filter: blur(60px);
  opacity: 0.8;
}
```

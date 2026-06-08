# "AI Slop" Antipatterns Guide - Concrete Examples

This guide shows the common antipatterns of AI-generated design and how to avoid them.

---

## 1. Generic Lucide Icons

### ❌ BAD - AI Slop

```tsx
import { Sparkles, Zap, Cog, Network, ArrowRight } from 'lucide-react';

export function Features() {
  return (
    <>
      <div>
        <Sparkles className="w-6 h-6" />
        <h3>General Intelligence</h3>
      </div>
      <div>
        <Zap className="w-6 h-6" />
        <h3>Automation</h3>
      </div>
      <div>
        <Cog className="w-6 h-6" />
        <h3>Integrations</h3>
      </div>
    </>
  );
}
```

**Why it's bad:**
- Generic Lucide icons = "obviously AI"
- No visual consistency
- No semantic justification
- Same style as 10,000 other sites

### ✅ GOOD - Custom SVG or Consistent Pack

**Option 1: Custom SVG**
```tsx
// icons/BrainIcon.tsx
export function BrainIcon() {
  return (
    <svg viewBox="0 0 24 24" className="w-6 h-6">
      <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm3.5-9c.83 0 1.5-.67 1.5-1.5S16.33 8 15.5 8 14 8.67 14 9.5s.67 1.5 1.5 1.5zm-7 0c.83 0 1.5-.67 1.5-1.5S9.33 8 8.5 8 7 8.67 7 9.5 7.67 11 8.5 11zm3.5 6.5c2.33 0 4.31-1.46 5.11-3.5H6.89c.8 2.04 2.78 3.5 5.11 3.5z" />
    </svg>
  );
}
```

**Option 2: Consistent icon pack**
```tsx
// Use a unified pack: Feather, Heroicons, Tabler
import { Brain, Zap, Link2 } from 'feather-icons-react';

// Or build a custom pack:
// icons/index.ts with all project SVGs
```

**Benefits:**
- ✅ Unique and memorable
- ✅ Consistent with the design
- ✅ Not "obviously AI"
- ✅ Controllable (colors, sizes, styles)

---

## 2. Cliché Gradients

### ❌ BAD - AI Slop

```css
/* Stereotypical "tech" gradients */
.hero {
  background: linear-gradient(135deg, #3B82F6 0%, #8B5CF6 100%);
  /* Blue → Purple: seen 10,000 times */
}

.accent {
  background: linear-gradient(135deg, #EC4899 0%, #8B5CF6 100%);
  /* Pink → Purple: seen 10,000 times */
}

.secondary {
  background: linear-gradient(135deg, #06B6D4 0%, #3B82F6 100%);
  /* Cyan → Blue: seen 10,000 times */
}
```

**Why it's bad:**
- Cliché gradients = "obviously AI"
- No semantic justification
- Visual overload
- No consistency with the palette

### ✅ GOOD - Intentional Gradients

```css
/* Gradients justified by semantic role */

/* Hero gradient: Primary background → Secondary accent */
.hero {
  background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
  /* Deep Navy → Slate: creates depth without distraction */
}

/* CTA gradient: Primary → Secondary (action) */
.cta-section {
  background: linear-gradient(135deg, #3B82F6 0%, #06B6D4 100%);
  /* Electric Blue → Cyan: indicates an action, justified */
}

/* Accent Glow: Primary with opacity */
.glow {
  background: radial-gradient(circle, rgba(59, 130, 246, 0.15) 0%, transparent 70%);
  /* Subtle halo, not cliché */
}
```

**Benefits:**
- ✅ Each gradient has a role
- ✅ No visual overload
- ✅ Consistent with the palette
- ✅ Semantically justified

---

## 3. Poorly Paired Fonts

### ❌ BAD - AI Slop

```html
<!-- 3+ fonts = chaos -->
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700&family=Inter:wght@400;500&family=JetBrains+Mono:wght@400&family=Playfair+Display:wght@700&family=Poppins:wght@600&display=swap" rel="stylesheet">

<style>
  h1 { font-family: 'Playfair Display'; } /* Elegant serif */
  h2 { font-family: 'Poppins'; } /* Rounded geometric */
  h3 { font-family: 'Sora'; } /* Modern geometric */
  p { font-family: 'Inter'; } /* Neutral */
  code { font-family: 'JetBrains Mono'; } /* Monospace */
</style>
```

**Why it's bad:**
- 5 fonts = "obviously AI"
- No visual consistency
- Confusing hierarchy
- Slow loading

### ✅ GOOD - 2 Intentional Fonts

```html
<!-- Exactly 2 fonts -->
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">

<style>
  /* Display: Sora (modern, geometric) */
  h1, h2, h3 { font-family: 'Sora'; font-weight: 600; }
  
  /* Body: Inter (neutral, readable) */
  p, span, label { font-family: 'Inter'; font-weight: 400; }
  
  /* Code: Monospace (optional) */
  code { font-family: 'Courier New'; } /* Or JetBrains Mono only if really needed */
</style>
```

**Benefits:**
- ✅ Consistent and professional
- ✅ Fast loading
- ✅ Clear hierarchy
- ✅ Not "obviously AI"

---

## 4. Inconsistent Spacing

### ❌ BAD - AI Slop

```css
/* Random spacing values */
.card {
  padding: 16px; /* Not a multiple of 8 */
  margin-bottom: 13px; /* Not a multiple of 8 */
  border-radius: 6px; /* Not a multiple of 4 */
}

.button {
  padding: 11px 18px; /* Not multiples of 8 */
  border-radius: 7px; /* Not a multiple of 4 */
  margin-right: 15px; /* Not a multiple of 8 */
}

.section {
  padding: 42px 0; /* Not a multiple of 8 */
  margin-top: 25px; /* Not a multiple of 8 */
}
```

**Why it's bad:**
- Random spacing = "obviously AI"
- No visual consistency
- Hard to maintain
- No mathematical harmony

### ✅ GOOD - Strict 8px Grid

```css
/* All spacing values = multiples of 8px */
:root {
  --spacing-xs: 4px;
  --spacing-sm: 8px;
  --spacing-md: 16px;
  --spacing-lg: 24px;
  --spacing-xl: 32px;
  --spacing-2xl: 48px;
  
  --radius-sm: 4px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;
}

.card {
  padding: var(--spacing-lg); /* 24px */
  margin-bottom: var(--spacing-lg); /* 24px */
  border-radius: var(--radius-lg); /* 12px */
}

.button {
  padding: var(--spacing-sm) var(--spacing-md); /* 8px 16px */
  border-radius: var(--radius-md); /* 8px */
  margin-right: var(--spacing-md); /* 16px */
}

.section {
  padding: var(--spacing-3xl) 0; /* 64px 0 */
  margin-top: var(--spacing-2xl); /* 48px */
}
```

**Benefits:**
- ✅ Mathematical harmony
- ✅ Easy to maintain
- ✅ Consistent everywhere
- ✅ Not "obviously AI"

---

## 5. Generic Template Structure

### ❌ BAD - AI Slop

```tsx
// Classic template structure = "obviously AI"
export default function Home() {
  return (
    <>
      <HeroSection />
      <FeaturesGrid />
      <TestimonialsSection />
      <CTASection />
      <PricingSection />
      <FAQSection />
      <Footer />
    </>
  );
}
```

**Why it's bad:**
- Identical structure to 10,000 other sites
- No unique identity
- "Clearly generated"
- No creative intent

### ✅ GOOD - Unique and Intentional Structure

```tsx
// Structure tailored to the project
export default function Home() {
  return (
    <>
      {/* Hero: Unique presentation */}
      <HeroWithAnimatedBackground />
      
      {/* Capabilities: Asymmetric layout */}
      <CapabilitiesWithScrollReveal />
      
      {/* Social Proof: Integrated testimonials */}
      <IntegratedSocialProof />
      
      {/* CTA: Customized */}
      <CustomCTAExperience />
      
      {/* Footer: Minimal and intentional */}
      <MinimalFooter />
    </>
  );
}
```

**Benefits:**
- ✅ Unique and memorable
- ✅ Intentional and thoughtful
- ✅ Not "obviously AI"
- ✅ Distinct identity

---

## 6. Vague Buzzwords

### ❌ BAD - AI Slop

```markdown
# Manus: The Premium and Modern AI

Discover an **elegant** and **innovative** experience.

## Beautiful Capabilities
- **Incredible** general intelligence
- **Unique** automation
- **Futuristic** integrations

Join **satisfied** users for a **premium** experience.
```

**Why it's bad:**
- Vague buzzwords = "obviously AI"
- No concrete information
- No differentiation
- Lack of credibility

### ✅ GOOD - Precise Descriptions

```markdown
# Manus: Accessible General Intelligence

Automate your tasks with an AI capable of performing any action on your computer.

## Concrete Capabilities
- **Complex problem solving**: Data analysis, code generation, deep research
- **Workflow automation**: Task orchestration, tool synchronization, API integrations
- **Content creation**: Writing, editing, SEO optimization

Used by professionals to **save 10+ hours per week** through automation.
```

**Benefits:**
- ✅ Precise descriptions
- ✅ Concrete benefits
- ✅ Credibility
- ✅ Not "obviously AI"

---

## 7. Uniform Buttons

### ❌ BAD - AI Slop

```tsx
// All buttons identical
<button className="btn-primary">Click</button>
<button className="btn-primary">Send</button>
<button className="btn-primary">Confirm</button>
<button className="btn-primary">Continue</button>
```

**Why it's bad:**
- No visual hierarchy
- No intentional variation
- "Clearly designed by AI"

### ✅ GOOD - Intentional Hierarchy

```tsx
{/* Primary button: Important action */}
<button className="btn-primary">Try for Free</button>

{/* Secondary button: Alternative action */}
<button className="btn-secondary">Watch the Demo</button>

{/* Ghost button: Tertiary action */}
<button className="btn-ghost">Documentation</button>

{/* Destructive button: Dangerous action */}
<button className="btn-destructive">Delete</button>
```

**Benefits:**
- ✅ Clear hierarchy
- ✅ Intentional
- ✅ Not "obviously AI"

---

## ✅ Antipatterns Checklist

Before delivery, verify:

- [ ] **Icons**: Custom SVG or consistent pack (not random Lucide)
- [ ] **Gradients**: Justified by role, max 2-3 gradients
- [ ] **Fonts**: Exactly 2 (display + body)
- [ ] **Spacing**: All multiples of 8px
- [ ] **Radii**: All multiples of 4px
- [ ] **Structure**: Unique and intentional (not a template)
- [ ] **Text**: Precise descriptions (no buzzwords)
- [ ] **Buttons**: Clear hierarchy (max 3 variants)
- [ ] **Colors**: 4-8 with semantic roles
- [ ] **Animations**: All ≤ 400ms

**Run:**
```bash
python3 scripts/detect_ai_slop.py --design DESIGN.md --code ./client/src
```

Score ≥ 80/100 = ✅ Ready for delivery

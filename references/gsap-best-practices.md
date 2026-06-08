# GSAP Best Practices for UI

GSAP (GreenSock Animation Platform) is the standard tool for performant, smooth web animations.

## Core Principles
- **Performance**: Prefer animating `transforms` (`x`, `y`, `rotation`, `scale`) and `opacity`. These properties do not trigger layout recalculation (reflow).
- **GSAP shorthand**:
  - `x: 100` instead of `translateX(100px)`
  - `yPercent: 50` instead of `translateY(50%)`
  - `autoAlpha: 0` combines `opacity: 0` and `visibility: hidden`

## Common UI Animation Patterns
1. **Staggered entrances**:
   ```javascript
   gsap.from(".card", {
     opacity: 0,
     y: 20,
     stagger: 0.1,
     duration: 0.8,
     ease: "power2.out"
   });
   ```
2. **ScrollTrigger**: Trigger animations on scroll.
3. **Hover Effects**: Use timelines for smooth hover transitions.
4. **Micro-interactions**: Small visual feedback on buttons or icons.

## Designer Tips
- **Ease**: Use `power2.out` for entrances (slow down at the end) and `power2.in` for exits. `expo.out` for a more premium/snappy effect.
- **Duration**: Keep UI animations between 0.2s and 0.6s. The longer it is, the slower the interface feels.
- **Accessibility**: Respect `prefers-reduced-motion`.

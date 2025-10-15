# Linear.app Theme Implementation

## Overview
The landing page has been completely redesigned to match Linear.app's exact design system while keeping the Brutally Honest content.

## Design System Changes

### Colors
- **Background**: `#0D0D0D` (very dark, almost black)
- **Secondary Background**: `#151515` / `#1A1A1A`
- **Text Primary**: `#FFFFFF` (pure white)
- **Text Secondary**: `#9CA3AF` (medium gray)
- **Text Tertiary**: `#6B7280` (light gray)
- **Accent**: `#5E6AD2` (subtle purple-blue)
- **Borders**: `rgba(255, 255, 255, 0.08)` (subtle white transparency)

### Typography
- **Font**: Inter (400, 500, 600, 700) - single font family throughout
- **Headlines**: 600 weight, tight letter-spacing (-0.02em to -0.03em)
- **Hero H1**: 72px, line-height 1.1
- **Section H2**: 40-48px
- **Body Text**: 15-18px, regular weight
- **Badges**: 13px, 500 weight, uppercase, 0.05em letter-spacing

### Spacing & Layout
- **Hero**: Min-height 100vh, generous top/bottom padding (120px/80px)
- **Sections**: Consistent border-top separators
- **Cards**: 32-48px padding, 12-16px border radius
- **Gaps**: 24-32px between elements

### Components

#### Buttons
- **Primary**: White background (#FFFFFF), dark text
- **Secondary**: Transparent with white border (rgba(255, 255, 255, 0.1))
- **Size**: 12px 24px padding, 15px font size
- **Border Radius**: 8px
- **Hover**: Subtle opacity change, 1px translateY

#### Cards
- **Background**: `rgba(255, 255, 255, 0.02)` (very subtle)
- **Border**: `1px solid rgba(255, 255, 255, 0.08)`
- **Hover**: Background changes to `rgba(255, 255, 255, 0.04)`, border to 0.12
- **Transform**: `translateY(-2px)` on hover

#### Navigation
- **Background**: `rgba(13, 13, 13, 0.8)` with backdrop blur (20px)
- **Links**: Medium gray, transitions to white on hover
- **Logo Icon**: Subtle white background (rgba(255, 255, 255, 0.1))

#### Badges
- **Background**: `rgba(255, 255, 255, 0.05)`
- **Border**: `1px solid rgba(255, 255, 255, 0.08)`
- **Border Radius**: 20px (pill-shaped)
- **Text**: Uppercase, tracked

### Visual Effects
- **Subtle Gradients**: Radial gradients with very low opacity (0.06-0.08)
- **Backdrop Blur**: 20px on header
- **Shadows**: Minimal, mostly transparent black
- **Transitions**: Fast (150ms) for interactions

## Key Differences from Previous Theme

1. **Single Font Family**: Removed Playfair Display, using only Inter
2. **Darker Background**: Changed from #2D2C2C to #0D0D0D
3. **Flatter Design**: Removed heavy shadows and gradients
4. **Subtler Borders**: Changed from solid colors to transparent white
5. **Cleaner Cards**: More subtle backgrounds and hover states
6. **Simplified Colors**: Removed warm earth tones, using grayscale + subtle accent
7. **Tighter Spacing**: More compact, modern feel
8. **No Accent Headlines**: Removed color highlights, keeping white text

## Files Modified
- `theme.css`: Complete color and typography overhaul
- `styles.css`: All component styles updated to Linear aesthetic
- `index.ejs`: Removed Playfair Display font link, removed accent-styles.css
- Removed: `accent-styles.css` (no longer needed)

## Implementation Details

### Font Loading
```html
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
```

### Color Tokens
```css
--color-bg-primary: #0D0D0D;
--color-text-primary: #FFFFFF;
--color-text-secondary: #9CA3AF;
--border-color: rgba(255, 255, 255, 0.08);
```

### Typography Scale
```css
--font-display: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
--font-primary: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

## Testing
- [ ] Verify dark theme renders correctly
- [ ] Check Inter font loads properly
- [ ] Test button hover states
- [ ] Validate card interactions
- [ ] Confirm responsive behavior
- [ ] Check contrast ratios for accessibility

## Next Steps
1. Test on different browsers
2. Optimize for mobile devices
3. Add any custom Linear-style animations
4. Consider adding more subtle micro-interactions

---

**Updated**: Today
**Theme**: Linear.app inspired
**Status**: Complete


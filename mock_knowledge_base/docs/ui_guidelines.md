# UI Guidelines

This document provides design guidelines and standards for the NexusAI platform user interface.

## Design Principles

### Consistency
- Use standardized components across all interfaces
- Maintain consistent spacing, typography, and color schemes
- Follow established patterns for user interactions

### Accessibility
- Ensure WCAG 2.1 AA compliance
- Support keyboard navigation
- Provide appropriate contrast ratios
- Include screen reader support

### Responsiveness
- Mobile-first design approach
- Flexible layouts that adapt to different screen sizes
- Touch-friendly interface elements

## Typography

### Font Families
- **Primary**: Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI'
- **Monospace**: 'SF Mono', Monaco, 'Cascadia Code', monospace

### Font Scales
- **Heading 1**: 2.5rem (40px)
- **Heading 2**: 2rem (32px)
- **Heading 3**: 1.5rem (24px)
- **Body**: 1rem (16px)
- **Small**: 0.875rem (14px)
- **Caption**: 0.75rem (12px)

## Color Palette

### Primary Colors
- **Primary Blue**: #2563eb
- **Primary Dark**: #1d4ed8
- **Primary Light**: #3b82f6

### Semantic Colors
- **Success**: #10b981
- **Warning**: #f59e0b
- **Error**: #ef4444
- **Info**: #06b6d4

### Neutral Colors
- **Gray 900**: #111827 (Text primary)
- **Gray 700**: #374151 (Text secondary)
- **Gray 500**: #6b7280 (Text muted)
- **Gray 300**: #d1d5db (Borders)
- **Gray 100**: #f3f4f6 (Background light)
- **Gray 50**: #f9fafb (Background subtle)

## Components

### Buttons

#### Primary Button
```css
.btn-primary {
  background: #2563eb;
  color: white;
  padding: 12px 24px;
  border-radius: 8px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: background 0.2s ease;
}

.btn-primary:hover {
  background: #1d4ed8;
}
```

#### Secondary Button
```css
.btn-secondary {
  background: transparent;
  color: #2563eb;
  border: 2px solid #2563eb;
  padding: 10px 22px;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
}

.btn-secondary:hover {
  background: #2563eb;
  color: white;
}
```

### Form Elements

#### Input Fields
```css
.input-field {
  width: 100%;
  padding: 12px 16px;
  border: 2px solid #d1d5db;
  border-radius: 8px;
  font-size: 16px;
  transition: border-color 0.2s ease;
}

.input-field:focus {
  outline: none;
  border-color: #2563eb;
  box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
}
```

#### Labels
```css
.label {
  display: block;
  font-weight: 600;
  margin-bottom: 8px;
  color: #374151;
}
```

### Cards
```css
.card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  border: 1px solid #e5e7eb;
  overflow: hidden;
}

.card-header {
  padding: 20px;
  border-bottom: 1px solid #e5e7eb;
}

.card-body {
  padding: 20px;
}
```

## Layout

### Grid System
- 12-column grid system
- Container max-width: 1200px
- Gutter: 24px

### Spacing Scale
- **xs**: 4px
- **sm**: 8px
- **md**: 16px
- **lg**: 24px
- **xl**: 32px
- **2xl**: 48px
- **3xl**: 64px

### Breakpoints
- **Mobile**: 320px - 767px
- **Tablet**: 768px - 1023px
- **Desktop**: 1024px+

## Responsive Behavior

### Mobile Adaptations
- Stack components vertically
- Increase touch target sizes (min 44px)
- Simplify navigation patterns
- Optimize for thumb interaction zones

### Button Responsive Classes
```css
.btn-mobile {
  width: 100%;
  max-width: 300px;
  margin: 0 auto;
  display: block;
  padding: 16px 24px;
  font-size: 18px;
}

.btn-desktop {
  width: auto;
  display: inline-block;
  padding: 12px 24px;
  font-size: 16px;
}
```

## Login Button Specific Guidelines

### Desktop Implementation
- Width: auto-sizing to content
- Minimum width: 120px
- Horizontal alignment: center within form
- Margin: 24px top, auto left/right

### Mobile Implementation (< 480px)
- Width: 100% of container
- Maximum width: 300px
- Display: block
- Margin: 24px auto (centers the element)
- Padding: 16px 24px (increased for better touch targets)

**Note**: The mobile alignment issue (NEX-123) was resolved by applying auto margins and block display. See `commit_abc123` for implementation details.

## Icons

### Icon Library
- Use Heroicons for consistency
- Size variants: 16px, 20px, 24px
- Always include proper alt text for accessibility

### Icon Usage
- 16px: Inline with text
- 20px: Buttons and form elements  
- 24px: Standalone actions and headers

## Animation

### Transitions
- Duration: 0.2s for micro-interactions
- Easing: ease or custom cubic-bezier
- Properties: transform, opacity, background-color

### Loading States
- Skeleton screens for content loading
- Spinner animations for actions
- Progress indicators for multi-step processes

## Accessibility Requirements

### Color Contrast
- Minimum 4.5:1 for normal text
- Minimum 3:1 for large text
- Ensure information is not conveyed by color alone

### Focus Management
- Visible focus indicators
- Logical tab order
- Skip navigation links

### Screen Reader Support
- Semantic HTML structure
- ARIA labels and descriptions
- Alternative text for images

## Related Documentation
- [Login Feature Documentation](login_feature.md)
- [Component Library](component_library.md)
- [Accessibility Standards](accessibility_standards.md)
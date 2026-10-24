---
name: frontend-views
description: Split new frontend functionality and views into their own components or domain files instead of growing existing pages. Use when adding UI, pages, views, forms, lists, or React/TypeScript frontend features.
---

# Frontend views

When add a new functionality or new View - split it from other UI and logic. Make separate component or domain files

## Where files go

- Route/screen: `frontend/src/pages/`
- Reusable or feature UI: `frontend/src/components/`
- Domain helpers (files, tags, formatters): `frontend/src/lib/`
- HTTP: `frontend/src/services/api.ts` (exports only; no JSX)

Do not grow `HomePage.tsx` (or any page) with large new markup. The page wires state and handlers; the view lives in its own file.

## Checklist

1. New feature or view → new file (or small set of files), named after the feature.
2. Page imports it and passes props. Keep page orchestration only.
3. Feature-specific CSS lives next to the component (`Component.css` imported from `Component.tsx`). Keep only global layout (reset, shell, card, forms, buttons) in `index.css`. Do not restyle unrelated views in the same change.
4. Do not copy-paste a similar block into an existing component “for now”.

## Examples

- Ask UI → `AskBox.tsx`, not extra JSX in `HomePage.tsx`
- Tape list → `FeedList.tsx`, not a second `<ul>` inside the page
- Search highlight → `Hit.tsx`, not inline mark-splitting in every title

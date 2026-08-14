---
name: company-design
description: >
  Self-configuring company design system — learns a company's brand once, then applies it
  everywhere. On first use it runs a quick one-time onboarding: the user points it at their
  company website, uploads logos, or shares brand guidelines, and it extracts and saves the
  brand's colors, fonts, and logos. After that it AUTOMATICALLY brands every business/work
  visual deliverable — presentations, documents, spreadsheets, PDFs, HTML/React artifacts,
  dashboards, charts, and diagrams — so everything shares one consistent, professional
  identity. Trigger whenever the user produces work-related visual output, even if they
  don't mention "branding", "design", or a company name. Also trigger when the user wants
  to set up, configure, change, or reset their company brand. Use ONLY for business/work
  output — fall back to neutral design for personal projects (family, hobbies, school,
  travel, fiction), and skip when the user asks for plain / unbranded / "different design".
cowork:
  category: writing
  icon: Sparkle
---

# Company Design System

This skill gives every business deliverable the user produces a single, consistent visual
identity — their company's real colors, fonts, and logos — without them having to restate
the brand every time.

It works in two phases:

1. **First use — onboarding.** The brand is not known yet. The skill learns it once from
   sources the user provides (a website, uploaded logos, a brand manual), validates what it
   found, gets the user's sign-off, and saves the result.
2. **Every use after that — applying.** The saved brand is loaded and applied automatically
   to whatever the user is building.

The whole point is that onboarding happens **once**. After that the skill should feel
invisible: the user asks for a deck or a report, and it simply comes out on-brand.

---

## Step 0 — Always check the brand profile first

Before doing anything else, read `references/brand-profile.md` in this skill's directory and
look at the `status:` field in its YAML frontmatter.

- `status: unconfigured` → the brand has never been set up. **Go to "First use — onboarding"
  below.**
- `status: configured` → the brand is known. **Go to "Applying the brand" below.**

This check is cheap and must happen every time the skill triggers, because the skill's
behavior is completely different in the two states. Never assume the state — read the file.

---

## First use — onboarding

When the profile is unconfigured, the skill needs a short one-time setup before it can
brand anything. Do **not** silently produce unbranded output and do **not** invent a brand.

How to handle the interruption gracefully:

- If the user's request was itself a setup request ("set up my company design", "configure
  my brand"), just start onboarding — that is exactly what they asked for.
- If the user asked for a deliverable ("make me a deck") and the brand isn't set up yet,
  tell them briefly: this skill can brand the output, but it needs a one-time setup of
  about two minutes. Offer to do the setup now and then build their deliverable on-brand,
  or to proceed unbranded if they'd rather not. Respect their choice.

When the user agrees to set up, **read `references/onboarding.md`** and follow it. That file
covers the full flow: collecting brand sources, extracting colors/fonts/logos, validating
them, proposing the result for the user to confirm, and writing the finished profile back to
`references/brand-profile.md`.

Once onboarding finishes and the profile is saved, continue straight into the user's
original request — now on-brand.

---

## Applying the brand

When the profile is configured, the brand is already decided. Two things to load:

1. **`references/brand-profile.md`** — the specific values for this company: its colors (with
   hex codes and roles), typography, logo files, and any layout or voice notes captured
   during onboarding. This is the source of truth for *what* the brand is.
2. **`references/applying-brand.md`** — format-specific guidance for *how* to apply a brand
   profile to slides, documents, spreadsheets, web artifacts, charts, and diagrams. This is
   written generically and reads its values from the profile.

Apply the profile's values through the guidance in `applying-brand.md`. The profile says
"the primary color is `#xxxxxx`"; `applying-brand.md` says "the primary color goes in slide
titles, the logo, and small accent rules — not stretched across every slide as a colored
bar". You need both.

If the profile's logo files are referenced, embed the actual files from `assets/logos/` —
never redraw a logo from scratch or approximate it with shapes.

---

## When to apply this skill — and when NOT to

Company branding is for **business / work output only**. Before applying any colors, logos,
fonts, or layouts, decide whether the current request is business or personal.

**Apply company branding when** the output is for work: internal documents, reports,
dashboards, or apps; customer- or partner-facing material; team meetings, stakeholder
updates, sales or exec decks; anything where the user is acting in their professional role.

**Do NOT apply company branding when** the context is personal or non-business: personal
projects, hobby code, side experiments; family planning, school work, travel itineraries,
gifts, personal events; fiction, creative writing, art for personal use; personal blogs,
personal finance, learning exercises. For personal output, fall back to a neutral default
design — no company colors, logos, or fonts.

**Always skip company branding when the user explicitly opts out** — "plain", "unbranded",
"generic", "no branding", "use a different design". Honor that immediately, and don't
re-apply the brand later in the same conversation unless the user asks.

**When it's genuinely ambiguous**, ask once: "Is this for work, or a personal project?" Do
not assume.

---

## Reconfiguring the brand later

If the user wants to change the brand after it's been set up — a rebrand, a correction, a
new logo, or "this should be a different company" — treat it as a re-run of onboarding. Read
`references/onboarding.md` and follow the same flow; it overwrites the existing profile. The
user can also ask to see the current profile, in which case just summarize what's in
`references/brand-profile.md`.

---

## A note on persistence

The configured brand is saved inside this skill, at `references/brand-profile.md`, so it
travels with the skill. Onboarding writes to that file directly. If a write ever fails
because the skill is installed in a read-only location, tell the user plainly and ask where
they'd like the profile saved instead — don't lose the values they just confirmed.

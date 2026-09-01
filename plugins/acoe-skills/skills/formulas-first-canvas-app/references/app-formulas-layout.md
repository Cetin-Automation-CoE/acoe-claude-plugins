# Canonical App.Formulas layout

Declaration order is load-bearing. The studio's **document-server binder** — a
different engine from the compile service — cannot resolve a forward reference from one
named formula to another. When it fails on one, it drops the **entire `Formulas` blob**,
and every screen that reads any named formula reports "unknown name". A single
misplaced declaration therefore produces dozens of unrelated-looking errors on screens
you never touched.

So: **nothing may reference a name declared below it.**

## Section order

```
 1. Colour tokens            constPrimaryColor, constInkColor, constBrandTint …
 2. Style object             constStyle  (depends on 1)
 3. Vocabularies             constXChoices tables, enumEntity, enumScreenType
 4. Scalar constants         constLocalValueLimitEur, constBorderRadius
 5. Pure helper UDFs         funcToEur, funcSavings, funcSemaforColor  (depend on 1–4)
 6. Derived values           constActivitiesView, constRegionalSavings (depend on 5)
 7. ===== DATA ACCESS LAYER — BEGIN =====
      funcLoadX / funcSaveX / funcDeleteX, scope formulas, seeds
    ===== DATA ACCESS LAYER — END =====
 8. Registries & navigation  constScreens, constNavigation, colBack helpers
                             — MUST be last: they read globals and layer-7 formulas
 9. UI utility UDFs          funcEllipsis, funcAsCurrency, funcOpenItem
```

Registries go **after** the data-access region, not with the other tables, precisely
because they read from it (`Count: CountRows(constActivitiesInScope)`) and because they
reference globals like `glSelectedActivityKey`.

## Banner style

Section banners are how a human and a script both find the regions. Keep them exact —
`check_data_layer.py` matches on the data-access pair and reports a vacuous pass if
either banner is missing.

```
// ============================================================
// Section name — one line on why this section exists
// ============================================================
```

```
// ============================================================
// ===== DATA ACCESS LAYER — BEGIN ============================
// ============================================================
```

## YAML mechanics

`Formulas` is a block scalar. `//` comments are **Power Fx** syntax and are legal only
*inside* the `|-` block. A `//` line at YAML mapping level is a parse error.

```yaml
App:
  Properties:
    Formulas: |
      =// this comment is fine — it is inside the block scalar
      constBorderRadius = 10;
```

Every named formula and UDF declaration ends with `;`.

## Comment discipline

Comment the **why**, never the what. `constReactGray = …; // the canvas colour` is
noise. These are the comments that earn their line:

- A decision and its date — *"shifted from #F5F5F5 in the 2026-08-27 refresh; name kept
  because of 10 call sites"*
- A verified invariant — *"direction fixed as baseline − award, verified against
  production row 236"*
- A deliberate omission — *"CZ intentionally absent: it runs in its own app and has no
  list in the model"*
- A constraint on placement — *"must stay below the data-access layer; the binder cannot
  forward-reference"*

Studio Save **strips every comment** on round-trip. Treat git as the durable copy: after
the user saves in studio, re-pull, and restore the comment block as its own commit if it
was lost.

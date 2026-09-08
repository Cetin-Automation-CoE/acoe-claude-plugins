# Drift reconciliation: repo vs installed skill copy

Date: 2026-09-07. Repo declared canonical. Verified against the compiled app at
`/Users/krystofpe/powerapps-work/canvas-src` where the two disagreed.

18 files differed. Neither copy was a superset.

## Repo wins (kept as-is)

| File | Hunk | Why repo wins |
|---|---|---|
| `cmp_CommandBar`, `cmp_Dialog`, `cmp_Header`, `cmp_Navigation`, `cmp_Notification` | `Default: =` → `Default: =false` | `Default: =` is an empty value on a Boolean input |
| `cmp_FilterButton` | `Default: =Align.Center` → `="Center"` + `Switch` mapping | The input is `DataType: Text`; installed passed an enum into a text input. The inner control is a `Button`, so the Switch correctly maps to `Align.*` |
| `cmp_Navigation` | `ThisItem.LogicalName` → `ThisItem.Screen.Name` | The repo registry `constScreens` uses `Screen:` references, not `LogicalName:` strings. Installed's form would not resolve against this schema. (Ground truth uses a `LogicalName` string registry — a different, also-valid design; it does not arbitrate here.) |
| `cmp_Spinner` | Requires-comment drops `constPrimaryColor` | The component only references `constScrimColor` |
| `check_tokens.py` | `Radius\w*` → `\w*Radius\w*` | Strictly broader; now catches `BorderRadius` |
| `component-library.md` | `check_references.py` invocation examples | Repo documents both the inlined-token and separate-fragment cases |
| `FormScreen.pa.yaml` | `Weight:` → `FontWeight:` (×3) | Correct for `ModernText` |
| `FormScreen.pa.yaml` | `Value: ="Value"` removed | No `Value` property on `ModernCombobox` |
| `ListScreen.pa.yaml` | `Value: ="Value"` removed; `FontColor:` → `Color:` (×3) | Correct for `ModernCombobox` / `ModernText` |
| `ListScreen.pa.yaml` | `Align: =Align.Right` → `="Right"` | Passing to `cmp_FilterButton`, whose input is `DataType: Text` |
| `design-system.md` | `funcStatusColor` → `funcStatusTextColor` | Matches the actual function name in templates |
| `README.md` | 74 → 224 lines | Repo is a substantial expansion |

## Installed wins (ported to repo)

| File | Hunk | Why installed wins |
|---|---|---|
| `cmp_Header.pa.yaml:216` | `Align: =Align.Center` → `='TextCanvas.Align'.Center` | `lbl_Header_Badge` is a `ModernText`. Ground truth uses `'TextCanvas.Align'.*` on all text controls. The repo regressed this by applying the false SKILL.md rule corrected in Task 1. |

## Both wrong (rewritten in Task 1)

| File | Why |
|---|---|
| `SKILL.md` | Repo added a false rule (`ModernText` takes `Align.Left`); installed's older text was also imprecise |
| `references/powerfx-limits.md` | Same false rule |

## Note

`Align.Center` on a `ModernText` compiles — `Center` is the one member shared by both
namespaces — so the repo's regression was latent, not fatal. `Align.Right` on a text
control (see `design-tokens.pa.yaml`, fixed in Task 3) is a hard error, because
`'TextCanvas.Align'` has no `Right`.

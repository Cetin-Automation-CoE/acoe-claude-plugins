---
name: gantt
description: |
  Generuje Gantt harmonogram projektu z exportu úkolů z Microsoft
  Planneru (.xlsx) jako PowerPoint prezentaci ve stylu „roadmap".
  Vytvoří celkový přehledový Gantt (kvartální/roční osa, oranžové roky,
  milníky, čára „Dnes", plavecká dráha, % / dny / data, barva pruhu podle
  stavu plnění), popisné slidy fází (s kontextem dohledaným z M365) a
  detailní Gantty fází až do 3. úrovně (kroky BRQ→TC→HLD→DEV→TEST→GoLive),
  rozdělené po dvou slidech na fázi.
  Use when user says "udělej gantt", "vytvoř gantt", "gantt z Planneru",
  "gantt chart", "harmonogram projektu", "převeď export z Planneru na
  gantt", "přegeneruj gantt podle plnění", nebo nahraje export úkolů z
  Planneru a chce z něj časovou osu / roadmapu.
  Do NOT use for: data, která nepocházejí z Planner exportu; jednoduché
  sloupcové grafy bez časové osy; Excel-only požadavky (lze, ale primárně
  je výstupem PowerPoint).
cowork:
  category: productivity
  icon: ChartMultiple
---

# Gantt z Planner exportu (styl „roadmap")

Převede export úkolů z Microsoft Planneru (.xlsx) na PowerPoint prezentaci
s celkovým Gantt harmonogramem, popisem fází a detailními Gantty fází.

## Vstup — formát Planner exportu

List „Project tasks" (nebo první list):
- **Řádky 1–7**: metadata (B1 název projektu, B2 vlastník, B3 začátek
  projektu, B4 konec projektu, B7 datum exportu)
- **Řádek 9**: hlavička
- **Řádek 10+**: data úkolů

Klíčové sloupce:
| Sloupec | Význam |
|---|---|
| B | Outline number = hierarchie (počet teček + 1 = úroveň; „1" = fáze, „1.1" = etapa, „1.1.1" = krok) |
| C | Název úkolu |
| E | Začátek |
| F | Konec |
| G | Trvání (dny) |
| I | % plnění (zlomek 0–1) |
| J | Priorita (High / Medium / Low) |
| R | Poznámky (kontext k fázi) |

**POZOR na data (E, F):** zobrazují se v US formátu MM.DD.YYYY, ale
openpyxl je s `data_only=True` čte jako `datetime` objekty — použij je
přímo, NEparsuj ze stringu. Ve výstupu zobrazuj EU formát DD.MM.YYYY.

Export může mít **2 nebo 3 úrovně**. Skill funguje pro obě; 3. úroveň
(realizační kroky) se zobrazí jen v detailních slidech fází.

## Postup

1. **Najdi zdrojový export.** Výchozí zdroj je **OneDrive složka `Documents/PlannerExports`**
   (drive `@user-onedrive`): přes `GetDriveChildren`/`SearchDrive` vezmi **nejnovější `.xlsx`**
   (podle `lastModifiedDateTime`) a načti ho přes `ReadFileContent`. Pokud je složka prázdná
   nebo nedostupná, zkus nahraný soubor v `input/` (Glob `input/**/*.xlsx`). Když je kandidátů
   víc a nejde určit nejnovější, zeptej se který.
2. **Načti a naparsuj** úkoly (openpyxl, `data_only=True`) do `working/gantt_data.json`
   — viz [references/gantt-generator.md](references/gantt-generator.md), krok 1.
   Úroveň = `str(outline).count(".") + 1`.
3. **Dohledej kontext k fázím** z M365 — `SearchM365` (sources files+email+teams)
   na název projektu; přečti klíčové dokumenty (analýza/HLD) přes `ReadFileContent`.
   Popisy etap GROUNDUJ v reálných datech (názvy z exportu + dokumenty + poznámky,
   sloupec R). Co nelze dohledat, popiš střídmě z názvu; NEvymýšlej fakta.
4. **Vygeneruj PowerPoint** (pptxgenjs, 16:9) — kompletní generátor je v
   [references/gantt-generator.md](references/gantt-generator.md). Struktura decku:
   - **Slide 1 — celkový roadmap** (úrovně 1–2): kvartální/roční záhlaví,
     oranžové roky po stranách, milníky (zahájení + konec projektu), červená
     „Dnes" závorka+čára, plavecká dráha „CyberArk", vodicí linky, **% před
     pruhem · dny v pruhu · data za pruhem**, **barva pruhu podle stavu plnění**
     (zelená = hotovo, žlutá = rozpracováno, modrá = nezahájeno).
   - **Slide 2 — logika fází**: úvodní text + přehledové karty fází.
   - **Pro každou fázi**: 1 **popisný slide** (karty etap) + **2 detailní slidy**
     (etapy rozdělené na dvě poloviny, obě sdílí časovou osu fáze). Detailní
     slidy mají STEJNÝ roadmap styl, ale **barvy pruhů podle typu kroku**
     (BRQ→GoLive) s **plnou = dokončeno / světlou = zbývá** výplní.
5. **QA** přes subagenta: render do obrázků (`soffice` → `pdftoppm`),
   zkontroluj přetečení, překryvy, ořezy, oranžové roky mimo pás, „Dnes"
   v mezeře nad řádky. Oprav max 2–3 cykly.
6. **Doruč** do `output/`. Ověř `Glob output/**/*.pptx` před oznámením hotovo.
   Nabídni náhled (render slidu 1 do obrázku).

### Konkrétní spuštění (OUTSIDE/INSIDE)
- Parsovací krok i generační JS skript napiš do `working/` (OUTSIDE Tasku).
- Spuštění generátoru + QA render zabal do `Task` subagenta s user-facing
  popisy Bash kroků („Building your slides", „Checking the slides for errors",
  „Saving your slides"). Prostředí: node + pptxgenjs globálně
  (NODE_PATH=/usr/lib/node_modules), soffice + pdftoppm na PATH, bez internetu.
- soffice helper: `/opt/workspace-config/.claude/skills/pptx/scripts/office/soffice.py`.

## Konvence stylu

- Font Calibri; firemní modrá `0B3D91` pro titulky; oranžová roků `E8730C`.
- **Stav plnění (celkový Gantt)**: hotovo `3FA45B` · rozpracováno `F0A92E` · nezahájeno `3E7CB1`.
- **Typy kroků (detail)**: BRQ `1AA39A` · TC `2E74B5` · HLD `7E5AA8` · DEV `5B6B7B`
  · TEST `E8A33D` · GoLive `3FA45B` · ostatní `8696A7`. Stálá barva na typ; výplň
  plná = dokončeno, světlá (lighten 0.62) = zbývá. Souhrnný pruh etapy = šedý
  track `B7C0CC` + zelený podíl `2E7D32`.
- Semafor priority (na kartách/přehledu): Vysoká `C00000` · Střední `FFC000` · Nízká `548235`.
- Datum EU (DD.MM.YYYY). Texty česky. Bez dekorativních podtržení titulků.
- Granularita osy: měsíční pozicování, kvartální záhlaví. Detaily scopuj na fázi.
- Rozdělení etap na 2 detailní slidy: `[floor(n/2), ceil(n/2)]` (u F4 7 etap → 3+4).

## Výstup a doručení

- Primárně **PowerPoint** do `output/`.
- **Pojmenování souboru (POVINNÉ):** `<nazev-vstupniho-souboru>_YYYYMMDD_vX.pptx`, kde
  `nazev-vstupniho-souboru` = název zdrojového exportu **bez přípony** (verbatim, vč. mezer),
  `YYYYMMDD` = datum, `vX` = verze v rámci dne (v1, v2, …).
  - **Datum NEDUPLIKUJ:** pokud název vstupu už obsahuje datum (vzor `YYYYMMDD`), použij jen
    název vstupu bez přípony a doplň `_vX` (datum už je v něm). Příklad: vstup
    `CyberArk roadmap_20260623.xlsx` → `CyberArk roadmap_20260623_v1.pptx`.
  - Pokud datum v názvu vstupu **není**, doplň datum generování (dnešní):
    `<nazev>_YYYYMMDD_vX.pptx`.
  - **Verze `vX`:** zvyš, pokud v `output/` už existuje soubor se stejným základem názvu
    (spočti max `vN` a použij `v(N+1)`). Stejný vzor i pro Excel výstup (`...vX.xlsx`).
- **Pozor:** soubory v `output/` se synchronizují — generuj rovnou pod cílovým názvem
  (nastav `writeFile` na finální jméno); NE `mv`/přejmenování už hotového souboru (hrozí I/O chyba).
- Při „přegeneruj podle plnění/priorit" jen znovu naparsuj nový export a spusť
  generátor — plnění/priority se promítnou automaticky (přehled i detaily).
- Po dokončení uveď, které popisy fází jsou shrnutím vs. doložené z dokumentů.

## When NOT to Use

- Vstup není export z Planneru (jiná struktura) — nejdřív se domluv na mapování sloupců.
- Uživatel chce čistě Excel Gantt — možné, ale řekni, že primární výstup je PowerPoint.
- Jednorázový jednoduchý graf bez projektové časové osy — použij běžný graf.

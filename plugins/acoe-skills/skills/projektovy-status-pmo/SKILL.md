---
name: projektovy-status-pmo
description: >-
  Připraví aktualizovaný R/A/G projektový status pro LIBOVOLNÝ projekt k aktuálnímu
  dni — všeobecný, projektově nezávislý nástroj sdílitelný s kolegy z PMO. Uživatel
  zadá název projektu (a volitelně klíčová slova / lidi / pracovní balíčky); skill
  projde e-maily, schůzky, přepisy a Teams za uplynulé ~2 týdny (resp. od minulého
  statusu), zachytí změny oproti předchozímu statusu a vygeneruje status ve formátu
  R/A/G s odrážkami (puntíky).
  Use when the user asks to "připrav projektový status", "udělej status k projektu
  <název>", "aktualizuj status projektu", "status pro PMO", "R/A/G status k projektu",
  "projektový status pro kolegy z PMO", or "prepare a project status report".
  Do NOT use for konkrétní projektové skilly, které už existují (např. Digitální
  cesta → digitalni-cesta-status, ESP → esp-status), pro obecné kalendářní/inboxové
  přehledy (use daily-briefing), ani pro tvorbu prezentací nebo BC dokumentů
  (use pptx / docx).
cowork:
  category: productivity
  icon: DocumentBulletList
---

# Projektový status pro PMO

Generuje opakovaně použitelný **R/A/G status** pro jakýkoli projekt. Sebere aktuální data z M365,
porovná je s předchozím statusem a vypíše strukturovaný status k dnešnímu dni se zvýrazněním změn.
Navržen tak, aby byl sdílitelný napříč PMO — projekt i kontext si volí uživatel, žádná tvrdá
specifika jednoho projektu nejsou v šabloně natvrdo.

## When to Use

- "připrav / udělej / aktualizuj **projektový status k projektu <název>**" k aktuálnímu dni
- "**R/A/G status** pro PMO / pro kolegy / pro vedení"
- pravidelný (např. čtrnáctidenní) projektový status libovolného projektu

## When NOT to Use

- Projekt, který už má vlastní dedikovaný skill (Digitální cesta → **digitalni-cesta-status**,
  ESP → **esp-status**) → použij ten konkrétní skill
- Obecný přehled inboxu / kalendáře / "co mě dnes čeká" → use **daily-briefing**
- Tvorba prezentace, Business Case dokumentu nebo Excelu → use **pptx / docx / xlsx**

## Vstup od uživatele (parametry projektu)

Na začátku zjisti (z promptu, nebo se krátce zeptej, pokud chybí to první):

- **Název projektu** — povinné; řídí vyhledávání i nadpis statusu.
- **Klíčová slova / zkratky** — volitelné (témata, produkty, pracovní balíčky/WP, čísla CHR/release,
  partneři). Když je uživatel nedodá, odvoď je z názvu projektu a z nalezeného minulého statusu.
- **Klíčoví lidé / role** — volitelné (PM, dodavatel, byznys, partner). Nehádej e-maily — jména/ID
  dohledej přes lookup nástroje.
- **Příjemci / publikum** — volitelné (komu je status určen). Ovlivní tón, ne fakta.

Pokud uživatel zadá jen název projektu, to stačí — zbytek si dohledej z M365.

## Workflow

1. **Urči časové okno.** Vezmi dnešní datum a zpracuj s posledními ~14 dny (resp. od posledního
   statusu). Relativní data převeď na konkrétní.
2. **Sbírej data paralelně** (`TaskCreate` pro průběh; nezdržuj se a hledej, místo abys odhadoval).
   Vyhledávací dotazy stav z **názvu projektu + klíčových slov** uživatele:
   - **E-maily** — `SearchM365` (sources `email`) + `ListMessages`: dotazy "<název projektu>",
     "<projekt> status", "<klíčové slovo 1>", "<klíčové slovo 2>", "<partner / dodavatel>".
     Detail čti přes `GetMessage`. Najdi i **minulý status** (předmět obsahuje "status" + projekt).
   - **Schůzky** — `ListCalendarView` na okno (subject = klíčové slovo z názvu projektu);
     identifikuj pravidelné synky, workshopy a schůzky k milníkům/dodávce.
   - **Přepisy** — u relevantních schůzek `ListMeetingTranscripts(join_url=…)` →
     `GetMeetingTranscript(...)`. U opakované série vyber `transcript_id` nejbližší startu instance.
   - **Teams** — `SearchM365` (sources `teams`) na název projektu a klíčová slova.
3. **Vytěž změny.** Pro každý milník a scope položku zjisti aktuální stav (hotovo / probíhá /
   posun / nové riziko). Zachyť nové termíny, nová rizika a uzavřené body.
4. **Porovnej s předchozím statusem** (pokud ho uživatel vložil nebo je v historii) a sestav
   **přehled změn** (co + proč + zdroj: schůzka/e-mail).
5. **Vygeneruj status** přesně podle šablony níže. Změněné termíny zobraz přeškrtnutím starého a
   doplněním nového (`~~30.4.~~ → 5.6.`). Nové položky označ **NOVÉ**.
6. **Označ body k ověření**, které se nepodařilo z podkladů potvrdit (nehádej — radši vypiš jako
   "ověřit").
7. **Výstup napiš inline jako markdown.** Soubor (docx) nebo koncept e-mailu vytvoř jen na výslovné
   přání uživatele. Pokud uživatel chce sdílet s PMO e-mailem, převezmi příjemce/předmět z minulého
   statusu (e-maily si **nevymýšlej**; když nejsou, založ draft bez příjemců a upozorni na to).

## Šablona výstupu

```
🗓️ STATUS – {NÁZEV PROJEKTU} – k {DD.MM.RRRR}

LEGENDA: 🔴🟡🟢 R/A/G | ✅ hotovo | ➡️ probíhá | ⏸️ pozastaveno | ⚠️ riziko | 🔥 issue

👁️ Executive Summary
- 🎯 Cíl projektu …
- ✅/🟡/🔴 Celkový stav a hlavní důvod barvy …
- 🚀 Klíčový milník / launch — stav, hlavní issues a rizika …
- 🔝 Potřeba eskalace C-level? …

Business Scope
- (stabilní popis rozsahu projektu)

🟡 Delivery Status
Scope:
- položky se stavovou ikonou …
Schedule / Milníky:
- milníky s termíny (změny přeškrtnutím starého → nový) …

Key Issues & Risks
- …

Nejbližší Com / SteerCo
- ComStream: …
- SteerCo: …
```

Před šablonu vždy vlož sekci **"🔄 Hlavní změny od minula"** (tabulka: Oblast | Změna | Zdroj) a za
status sekci **"K ověření"**.

**Odrážky:** všechny seznamy v těle statusu uvádějte jako puntíky (`-`), **nikdy ne číslované**.

## Output Format

- **Primárně inline markdown** (přehled změn → kompletní status → body k ověření).
- Tón: věcný, projektový, česky. Žádné dramatizování; drž se faktů z nástrojů.
- **Nikdy si nevymýšlej** termíny, jména, čísla ani stavy — co nelze doložit, uveď jako "ověřit".
- Soubor (docx/pptx) nebo koncept e-mailu jen na vyžádání; soubor pak ulož do `output/`.

## Edge Cases & Robustness

- **Chybí název projektu:** zeptej se jednou, krátce, na který projekt status připravit — bez něj
  nelze cílit vyhledávání.
- **Žádná nová data za období:** rozšiř okno na ~4 týdny a zkus znovu; když i tak nic, řekni to
  uživateli a vypiš poslední známý stav místo vymýšlení obsahu.
- **Nenajde se minulý status:** sestav status jako první ("baseline") a sekci "Hlavní změny od
  minula" vynech nebo označ jako N/A.
- **Nedostupný přepis schůzky:** schůzka mohla proběhnout bez nahrávání. Použij pozvánku/poznámky a
  navazující e-maily; v "K ověření" uveď, že přepis chyběl.
- **Více kandidátů na schůzku/sérii:** u opakovaného syncu vyber instanci s `transcript_id` nejblíže
  startu dané instance; nepleť dohromady více termínů.
- **Selhání nástroje:** zopakuj jednou; pokud se nepodaří, pokračuj s tím, co máš, a transparentně
  uveď, co se nepodařilo načíst.
- **Stránkování:** u rozsáhlejších výsledků (e-maily, přepisy) projdi `next_link`, ať status nestojí
  jen na první stránce.
- **Nejednoznačná jména:** lidi/ID dohledej přes lookup nástroje, nehádej e-maily ani stavy.
- **Časové okno a zóna:** počítej v lokální zóně uživatele; relativní data ("příští týden") převeď na
  konkrétní datum.

## Guardrails

- Stav a tvrzení opírej výhradně o výsledky nástrojů (e-maily, přepisy, kalendář). Při mezerách to
  napiš, nedoplňuj domněnkami.
- Privátní/osobní události v kalendáři neřeš a nerozváděj — status se týká pracovních schůzek.
- Pokud se nenajdou žádná nová data za období, řekni to a nabídni delší okno — negeneruj prázdný
  status s vymyšleným obsahem.
- Žádné hodnocení výkonu jednotlivců; popisuj výstupy a stav projektu, ne lidi.

# Writing the Summary, the Description and the Business Case

These carry the whole Idea. Everything else is metadata. Read this before drafting any of them.

## Who is reading

Two audiences, and the Idea has to serve both.

A **manager** scanning a backlog list sees only the Summary, and then at most the first
paragraph of the Description. They need to know what this is about in about ten seconds,
without opening anything.

A **CoE analyst** who was not in the meeting is triaging twenty Ideas in an afternoon and
deciding which three get scoped this quarter. They need, within about a minute: what happens
today, what should happen instead, and why it deserves a slot. They do **not** need the
click-by-click sequence, which belongs in the analysis phase after the Idea is picked up.

---

## Summary

**3–8 words. Name the subject, plainly. Nothing else.**

The whole company already knows the ACOE project delivers automation and digitalisation, so
saying it again in every title is redundant and it makes thirty backlog rows look identical.
Name the process, the document, the report or the agenda that the Idea is about, and stop.

**Banned vocabulary in the Summary**, in any language: *automatizace, automatický,
automatizovaný, digitalizace, digitalizovaný, robotizace, robot, bot, RPA, automation,
automated, digitalisation*. Also drop the delivery technology (*Power BI dashboard*, *Power
App pro…*, *Copilot agent*) unless the artefact genuinely is the subject of the request.

Keep it simple and self-explanatory. Prefer the noun the business itself uses.

| Weak | Strong |
|---|---|
| Automatizované generování faktur | Generování faktur |
| Automatické směrování datových zpráv z podatelny | Směrování datových zpráv z podatelny |
| RPA pro Výstavbu | Kontrola stavebních deníků |
| Digitalizace procesu v P8 | Evidence příchozí pošty v P8 |
| Power BI report vytížení techniků FLM | Vytížení techniků FLM po regionech |
| Automatizace | anything at all |

A domain noun that names the artefact is fine: *report*, *přehled*, *evidence*, *výkaz*. What
is banned is the word describing what our team does to it.

The test: read the Summary next to thirty siblings. Can a manager tell them apart, and does
each one say what it is about without opening it?

---

## Description — structure

The Description opens with a short block for management and only then goes into the process
detail. Aim for **8–15 bullets total** across the detail sections. If a reader could reproduce
the process step by step from your text you have gone too deep. If they cannot tell which
system the work happens in, not deep enough.

Concretely: name the systems, the volumes, the hand-offs and the decision points. Skip menu
paths, field names, button labels and screen-by-screen narration.

- Too deep: *"Operátor otevře P8, klikne na záložku Doručené, vybere zprávu, zkopíruje IČO do
  schránky, přepne do ODOS…"*
- Right: *"Operátor v P8 ručně určí příjemce podle adresy a předmětu dokumentu, k čemuž musí
  dohledat rajonizaci v ODOS."*
- Too shallow: *"Zprávy se routují ručně, chceme to automatizovat."*

```markdown
## Shrnutí
2–4 věty souvislého textu. Čeho se to týká, kdo to dnes dělá, co se má změnit.
Žádné odrážky, žádná čísla navíc, žádné systémové detaily.
Vedení musí po přečtení tohoto odstavce vědět, o čem idea je, a nemuset číst dál.

## Aktuální proces
- 4–8 odrážek: co se dnes děje, kde, jak často, kdo to dělá, kde to bolí
- objem a čas patří sem (kolik kusů, kolik minut na kus, kolik lidí to dělá)
- rozlišuj, co je ověřené číslo a co odhad z jednání

## Cílový stav
- 3–6 odrážek: co má řešení umět, v jakém rozsahu
- co se má stát ve výjimkách a při chybě (fallback na člověka)

```

Those three sections are the whole Description. Do not add others. In particular there is no
scope section and no open-questions section, both of which used to exist and are now gone.

### The Shrnutí block

This is the one section written for someone who will read nothing else. Rules:

- **Prose, not bullets.** Two to four sentences.
- Answer three things: **what is the subject**, **who does it today**, **what should change**.
- No system names unless the system *is* the subject. No volumes, no minutes, no ROI. Those
  are two sections further down and repeating them here makes the block long enough to skip.
- Do not restate the Summary as a sentence. The Summary says *Generování faktur*; the Shrnutí
  says what generating them involves today and why anyone cares.
- Never open with "Cílem této idey je automatizovat…". Start with the subject itself.

Good: *"Fakturace subdodavatelům se dnes připravuje ručně v Excelu na základě výkazů z SAP.
Účtárna to dělá jednou měsíčně pro zhruba dvě stě dodavatelů a vzniká při tom největší část
reklamací. Idea má fakturační podklad sestavit přímo z dat v SAP."*

Bad: *"Tato idea se zabývá automatizací a digitalizací procesu generování faktur pomocí RPA
robota, což přinese významné úspory."*

### Uncertainty and scope

There is no section for either, so both are handled inline.

**Mark uncertainty on the number it belongs to**, in brackets, right where the number appears:
*"cca 750 zpráv denně (číslo pouze za Výstavbu, nutné doplnit podatelnu)"*. An Idea that says
this is more useful than one quietly presenting a partial number as a total. Never drop the
caveat just because there is no longer a section inviting it.

**Scope limits belong in *Cílový stav*.** What the solution will not cover is part of
describing what it will cover, so write it as a bullet there, for example *"cílové pokrytí cca
80 % objemu, zbytek zůstává manuální"* or *"schvalovací krok zůstává manuální"*. A known
blocker or a related project goes in the same section as one bullet.

**Assumptions you made rather than read** do not go in the Description at all. They go in the
Step 4 presentation under *Předpoklady k ověření*, where the user can correct them before
anything reaches Jira.

---

## Business Case — structure

Time saved is the default currency and it must be reproducible, so show the arithmetic. Since
the scoring multiplies **Affected People × Monthly Runs per Person × Minutes per Run**, the
Business Case has to make all three visible and defensible.

**Formatting constraint:** this field renders as plain text, so no Markdown, no `h3.`, no `*`
bullets, they all appear on screen literally. Section titles sit on their own line in normal
sentence case, never in capitals, and bullets use a `•` character. See `references/fields.md` §6 for how to encode that.

```

▚ Proč to řešit:
• 2–4 odrážky: co dnešní stav způsobuje (zátěž, chybovost, riziko, prodlevy)

▚ Přínosy:
• Časová úspora: <počet lidí> × <běhů na osobu>/měsíc × <minuty> min
  = <hodin> h/měsíc ≈ <MD> MD/měsíc
• Provozní náklad řešení: <částka> CZK/měsíc — <z čeho se skládá>
• Finanční přínos jinde: <částka> CZK/měsíc — <z čeho> (pokuty, SLA, sankce)
• Kvalitativní: nižší chybovost, lepší plnění SLA, snížení rizika, compliance

▚ Dopad při nerealizaci:
• 1–2 odrážky: co se stane, když se to neudělá
```

Rules that keep this field trustworthy:

- **Write the saving as a product of the three fields**, in the same order and with the same
  numbers you put in Jira. A reviewer must be able to reconstruct Saved FTEs from the text.
  If the text and the fields disagree, the Idea loses credibility even when the fields are
  right.
- **State the headcount in the text as well as the field.** The field carries the number, the
  text carries where it came from. "60 techniků FLM" is checkable; a bare 60 is not.
- **Monthly Run Cost belongs in the text too**, with its components. It counts 36 times in the
  three-year calculation, so an unexplained 0 or an unexplained 25,000 both invite a challenge.
- **Labour saving and money saved elsewhere are different things.** Hours freed up go in the
  time line; fines avoided go in Other Cash Saved / Month. Do not add them together into one
  headline number. Double counting is the most common way an Idea loses credibility.
- **Not every risk is a monthly number.** "We might lose a subsidy" or "we would have to pick
  a more expensive supplier" are real and belong in *Dopad při nerealizaci* as prose. Do not
  invent a CZK/month figure to force them into the financial field.
- **Wave-driven work needs both rates.** State the annual volume, the per-wave volume, and
  which one you put in Monthly Runs per Person.
- **Do not convert hours to CZK unless the user gives you a rate.** If they want monetisation,
  ask which internal MD rate to use and state it in the text.
- **1 MD = 8 hours. One person-month is roughly 168 hours.** See the impossibility check below.
- **Compare the saving against the build cost** when the user has given an Effort estimate. A
  one-line payback ("při 10 MD realizace se vrátí během prvního měsíce") does more for
  prioritisation than another benefit bullet.
- **Enabler value counts.** Some Ideas save little time but unblock something larger or close
  a regulatory gap. Say that explicitly, it is a legitimate reason to prioritise.

### Saturation — the check that catches most bad business cases

Because Monthly Runs per Person and Minutes per Run are both **per person**, their product is
how long one person spends on this every month. Compare it against a working month:

```
saturation = (Monthly Runs per Person × Minutes per Run) ÷ 10 080     (168 h = one person-month)
```

- **Above 1.0 is impossible.** Nobody works more than a full month in a month. One of the two
  numbers is a team total or an elapsed duration rather than hands-on time.
- **Above 0.5 is implausible and must be raised.** It is very unusual for a single automation
  to take over more than half of somebody's working month. One affected person at 168 h means
  the automation replaces that entire person, which almost never survives contact with the
  requestor. Ask what else that person does with their time.
- Around 0.1 to 0.3 is the normal range for a healthy Idea.

The same ratio read from the other end is `Saved FTEs ÷ Affected People`, which is why an Idea
claiming 1.0 Saved FTEs from one person is the same red flag as a saturation of 1.0.

Run this before presenting, and raise it as a question rather than quietly adjusting a number
the requestor gave you. The full list of checks is in `references/fields.md` §2.

## Worked example 1 — routing of data messages

Raw material: meeting notes with volumes, a 75 % concentration on one department, rework
complaints, and a stated 10 minutes per message.

**Summary:** `Směrování datových zpráv z podatelny`

*(Not "Automatické směrování datových zpráv z podatelny (P8/ODOS)". The word "automatické" is
what our project does to everything, and the system names belong in Used Applications.)*

**What the consistency check caught.** The notes give a team total of 750 messages a day and
10 minutes per message. The old field took the team total directly. The new one does not, so
the extraction has to split it: podatelna has 3 people, giving 250 messages per person per day
and 5 250 per month. At 10 minutes that is 875 hours per person per month, against a ceiling of
168. Impossible, so the skill asks rather than submits. The user confirms the 10 minutes was
aggregated elapsed time including waiting, and that hands-on routing is about 1.5 minutes.

**Description:**

```markdown
## Shrnutí
Příchozí datové zprávy dnes ručně třídí a směruje podatelna, denně jich je zhruba 750.
Tři pracovnice u nich každé ráno určují správné oddělení a příjemce podle adresy a předmětu
dokumentu. Idea má toto rozhodnutí převzít a zprávy směrovat rovnou na odpovědný tým.

## Aktuální proces
- Denně přichází cca 750 datových zpráv (číslo zatím pouze za Výstavbu, podatelnu a další
  oddělení je nutné doplnit), které podatelna každé ráno ručně reviduje a směruje na správné
  oddělení nebo regionální bod (Routing Level 1).
- Zpracovávají to 3 pracovnice podatelny, tj. cca 250 zpráv na osobu a den.
- Odtud se zprávy dále směrují na konkrétní týmy (RL2) a jednotlivé pracovníky (RL3).
- Zpráva přistane v systému P8, kde operátor rozhoduje podle rajonizace (adresy) a předmětu
  dokumentu, k čemuž využívá systém ODOS.
- Cca v 80 % případů je pro správné nasměrování nutné vyčíst údaje přímo z obsahu dokumentu.
- 75 % objemu míří na oddělení Ochrana sítě.
- Denně se jednotky zpráv vracejí k přeřazení kvůli chybnému nasměrování.
- Vlastní rozhodnutí o směrování zabere cca 1,5 minuty na zprávu. Původně uváděných
  10 minut byl agregovaný průběžný čas včetně čekání, ne čistá práce.

## Cílový stav
- Vyčíst z dokumentu potřebné atributy a nasměrovat zprávu na odpovědný tým (RL2), případně
  přímo na koncového příjemce (RL3).
- Pokud automat nedokáže rozhodnout nebo nastane chyba, vrátit zprávu podatelně k manuálnímu
  zpracování.
- Cílové pokrytí cca 80 % objemu, zbytek zůstává manuální.
- Pro čtení atributů lze pravděpodobně využít nevyužívané pole v P8, nutná konzultace
  se správcem systému.
```

Note where the caveats went. The volume bullet carries its own limitation in brackets, the
partial coverage sits in *Cílový stav* as a scope bullet, and the P8 field question became a
plain constraint bullet in the same section. Nothing was lost by dropping the two extra
sections, it just moved next to the thing it qualifies.

**Business Case:**

```

▚ Proč to řešit:
• Ranní ruční třídění stovek zpráv je trvalá administrativní zátěž podatelny.
• Chybné nasměrování generuje přeřazování a zdržení.
• Roste riziko pozdní reakce na zprávu s právními či smluvními dopady.

▚ Přínosy:
• Časová úspora: 3 osoby × 5 250 zpráv/měsíc × 1,5 min = 394 h/měsíc ≈ 49 MD/měsíc.
  Při cílovém pokrytí 80 % jde o cca 315 h/měsíc ≈ 39 MD/měsíc.
• Provozní náklad řešení: cca 1 500 CZK/měsíc (podíl na licenci unattended robota
  a Orchestratoru, očekávaná údržba).
• Kvalitativní: nižší chybovost a méně přeřazování, rychlejší doručení na správné místo,
  lepší plnění lhůt.

▚ Dopad při nerealizaci:
• Zátěž poroste s objemem zpráv a bude nutné ji řešit navýšením kapacity podatelny.
```

**Structured fields:** Components `RPA` · Affected People `3` · Monthly Runs per Person
`5250` · Minutes per Run `1.5` · Monthly Run Cost `1500` · Other Cash Saved / Month `0` ·
Effort Estimation `L (10-20 MD)` · PR Potential `Medium` · Used Applications `DMSP8`, `ODOS`.

Note what changed against the raw notes. The "~12 FTE" claim from the meeting was not copied
over, and neither was the 10 minutes, because the per-person split made both impossible. The
calculation is now shown rather than asserted. Where such a claim does not reconcile, raise it
with the user instead of publishing either version.

---

## Worked example 2 — TSM ↔ CRM/ZIS rewriting

Raw material: a list of eight scenarios, two time measurements, and a quarterly penalty figure.

**Summary:** `Přepis poptávek a objednávek mezi TSM a CRM/ZIS`

**Description:**

```markdown
## Shrnutí
Poptávky, nabídky a objednávky pro O2 se dnes ručně přepisují mezi systémem TSM a systémy
CRM a ZIS, protože spolu systémy nekomunikují. Dělá to oddělení Implementace služeb při každé
změně na obou stranách a zpoždění z přepisu je hlavní důvod propadlých nabídek. Idea má
přenos dat mezi systémy převzít.

## Aktuální proces
- Poptávky, nabídky a objednávky se ručně přepisují mezi TSM a systémy CRM a ZIS.
- Přepis provádějí 4 pracovníci oddělení Implementace služeb při každé nové poptávce,
  vystavení nabídky, dotazu z obou stran i při pozastavení či stornu.
- Celkem jde o cca 180 přepisů měsíčně, tj. cca 45 na osobu.
- Hlavní scénáře: nová poptávka TSM → CRM, nabídka CRM → TSM, dotazy oběma směry,
  nová objednávka TSM → ZIS, notifikace o stavu přes TSM.
- Veškerá komunikace s O2 probíhá přes TSM, takže se ručnímu přepisu nelze vyhnout.

## Cílový stav
- Přenášet poptávky, nabídky, objednávky a související komunikaci mezi TSM a CRM/ZIS
  bez ručního přepisu.
- Pokrýt uvedené scénáře včetně pozastavení a storna.
- Připravuje se technické zadání integrace těchto systémů (Clooney WP3560), je nutné sladit
  rozsah, aby se práce nedublovala.
```

**Business Case:**

```

▚ Proč to řešit:
• Ruční přepis prodlužuje zpracování nabídky v průměru o cca 2 dny.
• Lhůta na odeslání nabídky je 20 dní. Propadlé nabídky se typicky vejdou do 21–22 dní,
  tedy propadají právě o zpoždění způsobené přepisem.

▚ Přínosy:
• Časová úspora: 4 osoby × 45 přepisů/měsíc × 12 min = 36 h/měsíc ≈ 4,5 MD/měsíc.
  12 min je vážený průměr (80 poptávek po 15 min a 100 nabídek po 10 min).
• Provozní náklad řešení: cca 1 000 CZK/měsíc (podíl na licenci robota a údržba).
• Finanční přínos jinde: v Q4/2023 činily sankce cca 190 tis. CZK. Po odečtení nabídek
  propadlých o 1–2 dny by šlo o cca 60 tis. CZK, tedy úspora cca 130 tis. CZK/kvartál,
  což je cca 43 tis. CZK/měsíc.

▚ Dopad při nerealizaci:
• Sankce za propadlé nabídky pokračují v obdobné výši.
```

**Structured fields:** Components `RPA` · Affected People `3` · Monthly Runs per Person
`45` · Minutes per Run `12` · Monthly Run Cost `1000` · Other Cash Saved / Month `43000` ·
Effort Estimation `L (10-20 MD)` · PR Potential `Medium` · Used Applications `TSM-Core`,
`CRM`, `ZIS`.

Note the three fixes against the raw notes. The source said "36,6 hodin = cca 0,25 MD měsíčně",
which is off by an order of magnitude (36,6 h ÷ 8 = 4,6 MD). The penalty figure was quarterly
while the Jira field wants a monthly number. And the 180 rewrites were a team total, which had
to be divided by the four people before it could go into Monthly Runs per Person. All three are
worth catching and flagging to the user, but flag them as questions. Do not silently overwrite
what the requestor wrote.

`WP3560` goes in the **External ID** field (`customfield_10062`), and the sentence explaining
what that work package is stays in the Description as a bullet under *Cílový stav*. The field
makes it findable, the prose makes it understandable.

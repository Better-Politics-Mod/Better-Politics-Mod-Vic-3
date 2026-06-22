# Taxonomy of `add_ideology` / `remove_ideology` Usage (Dimensional Ideologies)

This document covers all usages of `add_ideology` and `remove_ideology` where the ideology follows the `ideology_{three_letter_code}_*` naming convention — i.e. the BPM dimensional ideology system (eco, gov, dop, rel, mil, fem, cit, wel, sta, exe, ban). This is distinct from character-level ideologies (ideology_fascist, ideology_moderate, etc.) covered in the separate document.

Each IG holds exactly one ideology per dimension at any given time. The system enforces this by calling `bpm_remove_all_{dim}_ideologies` before adding the replacement.

---

## 1. Plumbing Infrastructure

The `bpm_remove_all_*` functions in [bpm_ideology_utils.txt](better-politics-mod/common/scripted_effects/bpm_ideology_utils.txt) are the foundational layer. They exist purely to be called by every other system before adding a replacement ideology, ensuring no dimension ever accumulates two simultaneous ideologies. They are not a semantic category — they're a tool.

---

## 2. IG Civilizational / Cultural Archetype Assignment

**File:** [bpm_ig_effects.txt](better-politics-mod/common/scripted_effects/bpm_ig_effects.txt)

The most architecturally significant category. BPM defines named "archetype" functions that express a coherent civilizational or political model as a cluster of dimensional ideologies. Each archetype is a named scripted effect called during country initialization (and sometimes during game events) to stamp an IG with the ideology package appropriate to that society.

### 2.1 Religious / Doctrinal Archetypes

These archetypes encode how a specific religious tradition shapes an IG's political outlook across several dimensions simultaneously.

| Archetype | gov | dop | eco | fem | cit | rel | mil | Notes |
|---|---|---|---|---|---|---|---|---|
| `bpm_ig_make_buddhist_moralist` | theocrat | — | — | — | nationalist | — | — | Theocratic Buddhist polity |
| `bpm_ig_make_confucian` | radical_monarchist | state_power | — | patriarchal | — | — | — | Confucian scholar-bureaucracy |
| `bpm_ig_make_shinto_moralist` | radical_monarchist | autocrat | — | patriarchal | — | — | — | Imperial Japan (pre-Meiji) |
| `bpm_ig_make_russian_patriarch` | radical_monarchist | autocrat | serf_economy | patriarchal | — | — | — | Russian Orthodox tsarist model |
| `bpm_ig_make_orthodox_patriarch` | *(= shinto_moralist)* | autocrat | — | patriarchal | — | — | — | General Eastern Orthodox model |
| `bpm_ig_make_oriental_orthodox_patriarch` | *(= orthodox_patriarch)* | | | | | | | Coptic/Armenian/Ethiopian |
| `bpm_ig_make_hindu_moralist` | radical_monarchist | autocrat | — | patriarchal | traditional_culture | — | — | Hindu princely states |
| `bpm_ig_make_hindu_moralist_british_india` | radical_monarchist | autocrat | — | patriarchal | traditional_culture | pragmatic_moralist | — | India under British suzerainty |
| `bpm_ig_make_sikh_moralist` | radical_monarchist | — | — | — | nationalist | — | mass_army | Sikh martial tradition |
| `bpm_ig_make_papal_paternalistic` | theocrat | — | — | — | — | — | — | Papal / ultramontane Catholics |

### 2.2 Feudal & Pre-Modern Political Archetypes

These encode a specific pre-modern political-economic structure, not a religion.

| Archetype | gov | dop | eco | Notes |
|---|---|---|---|---|
| `bpm_ig_make_bakufu` | radical_monarchist | oligarch | serf_economy | Tokugawa shogunate feudal structure |
| `bpm_ig_make_samurai` | radical_monarchist | oligarch | trad_isolationist | Pre-Meiji samurai caste; replaced at Meiji |
| `bpm_ig_make_scholar_paternalistic` | radical_monarchist | meritocratic_autocrat | — | Confucian examination-based governance; also sets exe_traditional |
| `bpm_ig_make_junker_paternalistic` | radical_monarchist | — | — | Prussian military-aristocratic model; also sets mil_patriotic |

### 2.3 Latin American Political Archetypes

| Archetype | gov | dop | Notes |
|---|---|---|---|
| `bpm_ig_make_caudillismo` | liberal_republican | oligarch | Strongman republic: formally republican, factionally oligarchic |
| `bpm_ig_make_republican_paternalistic` | liberal_republican | authoritarian_democrat | Paternalistic republic with centralized power |

### 2.4 European Moderate Archetypes

| Archetype | gov | Notes |
|---|---|---|
| `bpm_ig_make_paternalistic` | moderate_monarchist | Generic conservative-monarchist baseline |
| `bpm_ig_make_austrian_hegemony` | — | Sets cit_nationalist only; Habsburg multi-ethnic hegemony model |

### 2.5 Government Conversion: Monarchist → Republican

`bpm_ig_make_republican` converts every IG holding `ideology_gov_moderate_monarchist` to `ideology_gov_liberal_republican`. The Radicals IG specifically gets `ideology_gov_radical_republican` instead.

---

## 3. Economic Labor Status Archetypes

**File:** [bpm_ig_effects.txt](better-politics-mod/common/scripted_effects/bpm_ig_effects.txt)

A parallel set of archetype functions focused exclusively on the **eco** dimension, expressing an IG's position on the country's labor system. Applied to traditionalist IGs and landowners when a country's starting economic configuration is set.

### 3.1 Coercive Labor Systems (eco dimension — applied to traditionalist IGs / landowners)

| Function | Eco ideology assigned | Who gets it |
|---|---|---|
| `bpm_make_igs_pro_slavery` | `eco_slave_economy` | Traditionalist IGs + landowners with agrarian/interventionist eco |
| `bpm_make_igs_pro_colonial_slavery` | `eco_colonial_slavery_supporter` | Same, colonial context |
| `bpm_make_igs_pro_serfdom` | `eco_serf_economy` | Traditionalist IGs; conservatives separately get `eco_conservative_agrarian` |
| `bpm_make_igs_pro_isolationist_serfdom` | `eco_trad_isolationist` | Same, for isolated serf economies |
| `bpm_make_igs_pro_debt_serfdom` | `eco_debt_serf_economy` | Debt-peonage economies |

### 3.2 Transitional / Modernizing

| Function | What it does |
|---|---|
| `bpm_make_igs_not_pro_slavery_serfdom` | Converts all coercive-labor eco ideologies back to `eco_traditional_agrarian`, then calls `bpm_make_igs_modern_agrarian` |
| `bpm_make_igs_modern_agrarian` | Progressive/left IGs with traditional_agrarian → `eco_modern_agrarian`; right/institutional IGs → `eco_conservative_agrarian` |
| `bpm_make_igs_conservative_agrarian` | Traditionalist IGs with traditional/interventionist eco → `eco_conservative_agrarian` |

---

## 4. Game Initialization — Country-Specific Baselines

**Files:** [zzz_bpm_country_specific_global.txt](better-politics-mod/common/history/global/zzz_bpm_country_specific_global.txt), [bpm_country_setup_effects.txt](better-politics-mod/common/scripted_effects/bpm_country_setup_effects.txt)

One-time calls at game start that set the dimensional ideology baseline for specific countries. These use the archetype functions above plus direct add/remove calls for country-specific nuance.

### 4.1 Economic Starting Position
Countries are given a distinctive economic ideology to establish their 1836 character:
- **USA:** Conservatives and intelligentsia get `eco_american_system` (Whig protectionism)
- **Russia:** Relevant IGs get the serfdom archetype package
- Country-specific global file also does direct one-line swaps, e.g. removing a vanilla dimensional ideology and replacing with the BPM equivalent

### 4.2 Vanilla Dimensional Ideology Replacement
Direct 1:1 swaps to replace Paradox-vanilla dimensional ideologies with BPM's equivalents across the country's IGs:
- `ideology_gov_radical_monarchist` → `ideology_gov_liberal_republican`
- `ideology_dop_authoritarian_democrat` → `ideology_dop_moderate_democrat`
- `ideology_dop_autocrat` → `ideology_dop_authoritarian_democrat`
- `ideology_rel_radical_moralist` → `ideology_rel_moralist`
- `ideology_sta_powerful_state` / `ideology_sta_weak_state` → `ideology_sta_federated_state`

---

## 5. Government Type Assignment

**File:** [bpm_country_setup_effects.txt](better-politics-mod/common/scripted_effects/bpm_country_setup_effects.txt)

When a country is initialized (or a regime change is processed), every IG in the country is given a government-form ideology appropriate to the new regime. This sweeps across all IGs using `every_interest_group` with `limit` clauses.

| Regime | Gov ideology assigned | Notes |
|---|---|---|
| Republic | `gov_liberal_republican` | IGs holding radical_monarchist → liberal_republican |
| Constitutional monarchy | `gov_moderate_monarchist` | IGs holding liberal_republican → moderate_monarchist |
| Absolutist monarchy | `gov_radical_monarchist` | — |
| Theocracy | `gov_theocrat` | Triple removal (moderate/radical monarchist + liberal_republican) then theocrat |
| Bourgeois republic | `gov_liberal_republican` | Wipes all gov ideologies first via `bpm_remove_all_gov_ideologies` |

---

## 6. Law Enactment / Repeal

### 6.1 Labour Association Laws
**File:** [BPM_labor_unions.txt](better-politics-mod/common/laws/BPM_labor_unions.txt)

When a labour association law is enacted, the **trade unions IG's dop ideology** is updated to reflect the legal form of collective action available to them. All wipe the dop dimension first via `bpm_remove_all_dop_ideologies`.

| Law | dop ideology assigned to ig_trade_unions |
|---|---|
| `law_right_to_associate` | `dop_unionist` |
| `law_guild_system` | `dop_unionist` |
| `law_state_unionism` | `dop_state_unionist` |
| `law_syndicalism` | `dop_syndical_unionist` (or `dop_anarcho_syndicalist` for the more radical split) |
| Reverting from syndicalism | `dop_unionist` |

### 6.2 Governance Principles Laws
**File:** [BPM_governance_principles.txt](better-politics-mod/common/laws/BPM_governance_principles.txt)

- **Radical Leftist Government** enacted: `ig:ig_agrarian_populists` gets `gov_radical_proletarian` + `eco_agrarian_socialist` — the agrarian populists shift to a vanguard peasant-socialist position.

### 6.3 Slavery Abolition
**File:** [BPM_slavery.txt](better-politics-mod/common/laws/BPM_slavery.txt)

When slavery is abolished in the **USA**, IGs that held `eco_slave_economy` or `eco_american_system` have their eco ideology updated to reflect the post-abolition political economy:
- Conservatives / upper IGs → `eco_modern_agrarian`
- Liberal / intelligentsia IGs → `eco_interventionist`

---

## 7. Dynamic Ban Ideology Recalculation

**File:** [bpm_ig_effects.txt](better-politics-mod/common/scripted_effects/bpm_ig_effects.txt) — `bpm_ig_update_ig_ban_support`

The **ban** dimension (`ban_*`) is recalculated dynamically rather than set once. This function runs periodically to keep each IG's ban ideology consistent with current political conditions.

### 7.1 Country-Specific Overrides (applied first)
Certain country+IG combinations get a fixed ban ideology that overrides the general logic:

| Country | IG | Condition | Ban ideology |
|---|---|---|---|
| Brazil | ig_national_liberals | `brz_estado_novo` variable | `ban_anti_radical` |
| Brazil | ig_national_liberals | `brz_integralist_estado_novo` variable | `ban_conservative_supremacist` |
| Paraguay | ig_radicals | `patino_paraguay_var` variable | `ban_socialist_antifascist` |

### 7.2 General Political Logic
For all other IGs, the ban ideology is assigned based on the IG's political character (liberal, moderate-conservative, radical-right, socialist, etc.) combined with active journal entries tracking communist or fascist movements:

- Liberal and moderate-conservative IGs → anti-communist or antifascist ban ideologies, depending on which threat is more salient (controlled by `je_bpm_ban_communists` and `je_bpm_ban_fascists` journal entries)
- Radical-right IGs → anti-socialist / supremacist ban ideologies
- Socialist IGs → antifascist ban ideologies

---

## 8. Adapting to Regime Change (Events)

### 8.1 American Civil War — Political Realignment
**File:** [bpm_acw_events.txt](better-politics-mod/events/_american_civil_war/bpm_acw_events.txt)

The ACW event chain triggers a sweeping multi-IG ideology realignment that fires across multiple ACW phase events (at least four separate instances). Each instance replaces extreme or antebellum dimensional ideologies with more moderate post-war equivalents, across the whole country's IG pool using conditional loops:

| Old ideology | New ideology | Dimension | What it represents |
|---|---|---|---|
| `gov_radical_monarchist` | `gov_liberal_republican` | gov | Authoritarian holdovers accept republican norms |
| `dop_authoritarian_democrat` | `dop_moderate_democrat` | dop | Moderate democratization of political culture |
| `dop_autocrat` | `dop_authoritarian_democrat` | dop | Hard autocrats shift toward limited democracy |
| `rel_radical_moralist` | `rel_moralist` | rel | Religious extremism moderated |
| `sta_powerful_state` | `sta_federated_state` | sta | Centralism breaks down into federalism |
| `sta_weak_state` | `sta_federated_state` | sta | Fragmented states also consolidate federally |

Additionally, specific IGs (Radicals, Intelligentsia, Anarchists) get targeted positive ideology additions:
- `rel_secularist`, `sta_decentralized_state`, `ban_averse` (Radicals / Anarchists)
- `eco_interventionist`, `cit_liberal_nationalist` (Intelligentsia)
- `eco_modern_agrarian`, `cit_immigrant_nationalist`, `rel_radical_secularist` (Radical intelligentsia)
- `eco_american_system`, `cit_immigrant_nationalist` (post-war Union alignment)

### 8.2 Meiji Restoration — Samurai Modernization
**File:** [_meiji_restoration.txt](better-politics-mod/events/_meiji_restoration.txt)

When the Meiji Restoration events fire, the samurai IG's feudal ideology package is replaced:

- Removes `dop_oligarch` — feudal oligarchic power structure dissolved
- Removes `eco_trad_isolationist` — sakoku (isolation policy) abandoned
- Adds `dop_autocrat` — power consolidated under imperial autocracy

This fires on two alternate event paths.

### 8.3 Portuguese Regeneration — Economic Modernization
**File:** [_ip4_portuguese_political_events.txt](better-politics-mod/events/iberia_events/_ip4_portuguese_political_events.txt)

The Regeneration event chain (Portugal's 1851 stabilization) updates economic ideologies for the modernizing IGs:

- **Industrialists** → `eco_modernizer` (Regeneration beginning) → then `eco_interventionist` (Regeneration completed)
- **Petty bourgeoisie** → `eco_interventionist`

---

## 9. Colonial Administration — Metropole Loyalism

**File:** [BPM_code_on_actions.txt](better-politics-mod/common/on_actions/BPM_code_on_actions.txt)

When the **colonial administration law** is repealed (tracked via `bpm_on_col_adm` variable), the following IGs lose `ideology_dop_metropole_loyalist`:

- ig_landowners, ig_industrialists, ig_armed_forces, ig_conservatives

This represents those IGs no longer having a political stake in maintaining the colonial relationship. The removal happens through `on_actions` rather than a law `on_repeal` block, with a 6-month cooldown enforced by a counter variable.

---

## 10. Technology Research

**File:** [zzzz_bpm_technologies_important.txt](better-politics-mod/common/technology/technologies/zzzz_bpm_technologies_important.txt)

Currently **commented out**:
- A technology unlock that would remove `fem_benevolent_sexism` and add `fem_gender_egalitarian`

This pathway exists in the code but is not currently active.

---

## Summary

| Category | Trigger | Scope | Key dimensions |
|---|---|---|---|
| Civilizational archetypes | Country init / game start | Specific IGs | gov, dop, eco, fem, cit, rel, mil |
| Economic labor archetypes | Country init / game start | Traditionalist IGs + landowners | eco |
| Game initialization baselines | Once at game start | Per-country IG pool | eco, gov, dop, rel, sta |
| Government type assignment | Regime initialization | All IGs in country | gov |
| Labour association laws | Law enacted / repealed | ig_trade_unions | dop |
| Governance laws | Law enacted | ig_agrarian_populists | gov, eco |
| Slavery abolition | Law enacted | Coercive-labor IGs (USA) | eco |
| Dynamic ban recalculation | Periodic / ongoing | All IGs | ban |
| ACW realignment | Event fires (multiple phases) | All IGs in USA | gov, dop, rel, sta, cit, eco |
| Meiji Restoration | Event fires | Samurai IG | dop, eco |
| Portuguese Regeneration | Event fires | Industrialists, petty bourgeoisie | eco |
| Colonial admin repeal | on_actions | Landowners, industrialists, armed forces, conservatives | dop |
| Technology (disabled) | Tech research | — | fem |

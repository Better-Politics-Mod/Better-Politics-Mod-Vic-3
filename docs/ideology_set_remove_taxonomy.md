# Taxonomy of `set_ideology` / `remove_ideology` Usage

This document classifies all usages of `set_ideology` and `remove_ideology` in the BPM codebase by conceptual purpose.

---

## 1. Plumbing Infrastructure

The foundational layer that all other systems build on. These are not standalone calls but utilities invoked by higher-level effects.

### 1.1 Bulk "Remove All" Utility Functions
**File:** [bpm_ideology_utils.txt](better-politics-mod/common/scripted_effects/bpm_ideology_utils.txt)

Eleven category-scoped removal functions, each individually `remove_ideology`-ing every ideology in that dimension. Used as a "wipe the slate" before selectively re-adding.

| Function | Ideologies removed |
|---|---|
| `bpm_remove_all_eco_ideologies` | 24 economic ideologies (laissez_faire → colonial_slavery_supporter) |
| `bpm_remove_all_gov_ideologies` | 8 government-form ideologies (liberal_republican, monarchist variants, proletarian variants, theocrat…) |
| `bpm_remove_all_dop_ideologies` | 21 distribution-of-power ideologies (anarchist → organic_power) |
| `bpm_remove_all_rel_ideologies` | 7 religious ideologies (atheist, secularist variants, moralist variants) |
| `bpm_remove_all_mil_ideologies` | 13 militarism ideologies (ultramilitarist → antimilitarist, mass_army variants) |
| `bpm_remove_all_fem_ideologies` | 4 feminist ideologies (gender_egalitarian, benevolent_sexism, patriarchal variants) |
| `bpm_remove_all_cit_ideologies` | 11 citizenship ideologies (internationalist → segregationist) |
| `bpm_remove_all_wel_ideologies` | 10 welfare ideologies (expanded_public_welfare → no_welfare variants) |
| `bpm_remove_all_sta_ideologies` | 15 state-structure ideologies (minimal_state → organic_state) |
| `bpm_remove_all_exe_ideologies` | 7 executive ideologies (strong/weak dynamic/rigid, traditional, ceremonial) |
| `bpm_remove_all_ban_ideologies` | 9 ban/prohibition ideologies (antifascist, supremacist, anticommunist…) |

Each has a matching `bpm_re_add_*_ideology` mirror function.

### 1.2 Ideology Stashing / Unstashing

Temporary ideology preservation system. Used when an effect must briefly remove ideologies (e.g. to reorder them) without losing the original state.

- `bpm_stash_ideology` — stores a single ideology in a variable
- `bpm_stash_rel_ideology`, `bpm_stash_sta_ideology`, `bpm_stash_dop_ideology` — bulk stash by category

---

## 2. Mod Initialization & Vanilla Cleanup

One-time calls at game start to remove vanilla ideologies that conflict with BPM's ideology system or that the mod replaces with its own variants.

### 2.1 Global Vanilla Ideology Removal
**File:** [zzz_bpm_country_specific_global.txt](better-politics-mod/common/history/global/zzz_bpm_country_specific_global.txt)

Runs at game start to strip out Paradox-vanilla ideologies that BPM supersedes:

- Removes `ideology_agrarian_jeffersonian` from USA
- Removes `ideology_gov_radical_monarchist`
- Removes `ideology_dop_authoritarian_democrat`
- Removes `ideology_dop_autocrat`
- Removes `ideology_rel_radical_moralist`
- Removes `ideology_sta_powerful_state` and `ideology_sta_weak_state`

### 2.2 Country-Specific Ideology Cleanup
**File:** [bpm_country_setup_effects.txt](better-politics-mod/common/scripted_effects/bpm_country_setup_effects.txt)

Each major playable country gets a setup pass that removes ideologies incompatible with that country's starting configuration:

- **USA:** removes `ideology_paternalistic`, `ideology_gov_liberal_republican`
- **Russia:** removes `ideology_gov_moderate_monarchist`, `ideology_gov_radical_monarchist`, `ideology_gov_liberal_republican`; removes `ideology_wel_no_welfare`
- **Belgium / Nordic:** removes `ideology_cit_nationalist`, `ideology_cit_ethnonationalist`, `ideology_cit_liberal_nationalist`
- **Military adjustments (various):** removes `ideology_mil_antimilitarist` or `ideology_mil_patriotic` depending on country culture

### 2.3 Brazil / Latin America Positivist Initialization
**File:** [zzzz_bpm_brazil_la_specific_global.txt](better-politics-mod/common/history/global/zzzz_bpm_brazil_la_specific_global.txt)

Assigns `ideology_despotic_utopian` to three specific Brazilian positivist characters at game start.

---

## 3. IG Initialization

Default ideologies applied to all interest groups at the start of any game, before country-specific or event-driven changes.

### 3.1 Default Center Leader Assignment
**File:** [bpm_ig_init_effects.txt](better-politics-mod/common/scripted_effects/bpm_ig_init_effects.txt)

Sets `ideology_center_leader` as the baseline for most IG leaders. Also initializes `ideology_social_democrat` for specific IGs. Uses a `remove_ideology = ideology_nonexistent` trick for initialization ordering.

---

## 4. Historical Character Templates

Static ideology assignments for specific named historical figures, set in character template files. These are baked into characters' definitions rather than triggered by gameplay.

### 4.1 Portuguese Miguelists
**File:** [zz_bpm_country_por.txt](better-politics-mod/common/character_templates/zz_bpm_country_por.txt)

Six Portuguese noble and military characters (c. 1836–1850s) receive `ideology_miguelist_2`.

### 4.2 Spanish Carlists
**File:** [zz_bpm_country_spa.txt](better-politics-mod/common/character_templates/zz_bpm_country_spa.txt)

Nine Spanish Carlist faction members receive `ideology_carlist_2`. One Don Carlos variant receives `ideology_humanitarian_royalist`.

### 4.3 Brazilian Historical Figures
**File:** [zz_bpm_country_brz.txt](better-politics-mod/common/character_templates/zz_bpm_country_brz.txt)

A range of ideologies assigned to named Brazilian figures:

- Pedro II and several royalist officers → `ideology_humanitarian_royalist`
- Republican social democrat character → `ideology_social_democrat`
- Positivist vanguardist character → `ideology_vanguardist`
- One character → `ideology_humanitarian`

### 4.4 Russian Serfdom Reformer
**File:** [zzz_bpm_country_specific_global.txt](better-politics-mod/common/history/global/zzz_bpm_country_specific_global.txt)

The Russian Conservative IG leader is assigned `ideology_serfdom_reformer` at game start, reflecting the reformist faction of Russian conservatism in 1836.

### 4.5 Historical Agitators
**File:** [zz_bpm_historical_agitators.txt](better-politics-mod/common/character_templates/zz_bpm_historical_agitators.txt)

A historical agitator character receives `ideology_liberal_leader`.

### 4.6 Cuba
**File:** [zz_bpm_country_cub.txt](better-politics-mod/common/character_templates/zz_bpm_country_cub.txt)

One Cuban character (*Dios, la Razón y la Virtud* context) receives `ideology_radical`.

---

## 5. Character Interactions (Player-Triggered Sways)

Player-initiated actions that shift a character's ideology. These require specific governmental and factional preconditions.

### 5.1 French Second Republic Factional Sways
**File:** [bpm_french_interactions.txt](better-politics-mod/common/character_interactions/bpm_french_interactions.txt)

Three distinct sway interactions available during the French Second Republic, each requiring different supporting IGs to be in government:

- **Sway to Bonapartism** — requires rural_folk, petty_bourgeoisie, industrialists, armed_forces, conservatives, national_liberals, agrarian_populists → sets `ideology_bonapartist`
- **Sway to Legitimism** — requires devout, rural_folk, petty_bourgeoisie, landowners, conservatives, reactionaries → sets `ideology_legitimist`
- **Sway to Orleanism** — requires industrialists, petty_bourgeoisie, intelligentsia, armed_forces, liberals, market_liberals, conservatives → sets `ideology_orleanist`

All three block characters who already hold ideologies from competing factions (republican, communist, anarchist, etc.).

---

## 6. Mechanical / Dynamic Systems

Ideologies set automatically and continuously by scripted logic, not by discrete events or player choices.

### 6.1 Movement Variant Traits
**File:** [bpm_variant_effects.txt](better-politics-mod/common/scripted_effects/bpm_variant_effects.txt)

The `bpm_movement_*` ideologies are dynamically added or removed based on which political faction is largest within an interest group. These reflect the IG's current political *character* rather than a fixed identity:

| Ideology | Condition |
|---|---|
| `ideology_bpm_movement_constitutionalist` | Country has monarchy + advisory body |
| `ideology_bpm_movement_restorationist` | Country has no monarchy |
| `ideology_bpm_movement_republican` | Country has monarchy |
| `ideology_bpm_movement_abolitionist` | Slavery law in place |
| `ideology_bpm_movement_slaver` | No slavery law (or slavery abolished) |
| `ideology_bpm_movement_modernizer` | Pre-modern country |
| `ideology_bpm_movement_liberal_nationalist` | Non-socialist IG |
| `ideology_bpm_movement_nationalist` / `_internationalist` / `_paternalist` | Socialist IG variants |
| `ideology_bpm_movement_laissez_faire` | Market-oriented IG |

### 6.2 Single Party System Toggle
**File:** [bpm_single_party_effects.txt](better-politics-mod/common/scripted_effects/bpm_single_party_effects.txt)

When the single-party law is enacted or repealed, IGs are toggled between `ideology_pro_single_party` and `ideology_against_single_party`.

### 6.3 IG Naming / Identity Shift
**File:** [bpm_ig_naming_effects.txt](better-politics-mod/common/scripted_effects/bpm_ig_naming_effects.txt)

When an IG's identity shifts (renaming), `ideology_eco_modern_agrarian` is removed from rural_folk if no longer applicable.

---

## 7. Events

Ideology changes triggered when a specific event fires. These represent discrete historical moments.

### 7.1 Rise of Fascism
**File:** [_fascism_events.txt](better-politics-mod/events/_fascism_events.txt)

As the fascist movement progresses through its event chain, characters and IG leaders receive:

- `ideology_fascist` — core fascist assignment as the movement crystallizes
- `ideology_traditionalist` — for more conservative-authoritarian fascist wing
- `ideology_ethno_nationalist` — for the racial-nationalist faction of fascism

### 7.2 Liberal Movement Milestone Events
**File:** [_liberalism.txt](better-politics-mod/events/_liberalism.txt)

At specific milestones in the liberal movement event chain:

- `ideology_radical` — given to liberal IG leader when the movement radicalizes
- `ideology_reformer` — given to liberal IG leader at a reformist milestone

### 7.3 Suffragist Victory
**File:** [_suffragist_events.txt](better-politics-mod/events/_suffragist_events.txt)

When the suffragist event fires (movement breakthrough):

- `ideology_feminist` — given to the relevant IG leader

### 7.4 Meiji Restoration — Adapting to the New Regime
**File:** [_meiji_restoration.txt](better-politics-mod/events/_meiji_restoration.txt)

During the Japanese modernization events, the old Tokugawa-era ideological constraints are lifted:

- Removes `ideology_dop_oligarch` — the oligarchic power structure dissolves
- Removes `ideology_eco_trad_isolationist` — isolationism abandoned as modernization proceeds

### 7.5 Heavenly Kingdom (Chinese Religious Rebellion)
**File:** [_heavenly_kingdom_events.txt](better-politics-mod/events/_heavenly_kingdom_events.txt)

Two ideological shifts within the Taiping/Heavenly Kingdom event chain:

- `ideology_theocrat` — as the movement takes on its religious-governing character
- `ideology_jingoist` — as the movement's military expansion intensifies

### 7.6 Paris Commune
**File:** [_paris_commune_events.txt](better-politics-mod/events/_paris_commune_events.txt) (lite version)

When the commune is established, prior loyalties are stripped:

- Removes `ideology_loyalist` — commune leaders shed state loyalism
- Removes `ideology_patriotic` — narrow patriotism replaced by internationalist/class politics

### 7.7 French Republican Victory
**File:** [bpm_france.txt](better-politics-mod/events/bpm_france.txt)

When republicanism definitively wins in France, former monarchist leaders are moderated:

- Sets `ideology_moderate` — monarchist IG leaders become moderate republicans rather than staying as monarchists

---

## 8. Journal Entries

Ideologies earned by completing (or progressing through) a journal entry chain. These represent ideological maturation through sustained political development.

### 8.1 Agrarian Socialism Progression
**File:** [BPM_je_socialists.txt](better-politics-mod/common/journal_entries/BPM_je_socialists.txt)

When the agrarian socialism journal variable reaches 33.1+:

- `ideology_agrarian_socialist_leader` — given to the agrarian_populists IG leader
- Accompanied by a bulk eco/gov ideology reset via `bpm_remove_all_*` + selective re-add

### 8.2 Syndicalism Progression
**File:** [BPM_je_socialists.txt](better-politics-mod/common/journal_entries/BPM_je_socialists.txt)

When the syndicalism journal variable exceeds 33.1:

- `ideology_anarchist_syndicalist` — given to the anarchist IG leader (if IG is ig_anarchists)
- `ideology_syndicalist` — given to the trade unions IG leader (if IG is ig_trade_unions and not corporatized)

---

## 9. Law Changes

Ideology shifts that occur when a specific governance law is enacted or repealed.

### 9.1 Constitutionalism Law Change
**File:** [BPM_governance_principles.txt](better-politics-mod/common/laws/BPM_governance_principles.txt)

When the constitutionalism governance principle is changed, the movement ideology `ideology_constitutionalist` is removed from affected interest groups — the political demand has been either won or made irrelevant.

---

## Summary Table

| Category | Trigger | Scope | Examples |
|---|---|---|---|
| Plumbing | Called by other effects | Per-character | bulk remove_all_* functions |
| Mod Init / Vanilla Cleanup | Game start, once | Per-country | Remove vanilla DOP/ECO ideologies |
| IG Initialization | Game start, once | All IGs | Set center_leader as default |
| Historical Templates | Baked into character definition | Named historical figures | Carlists, Miguelists, Pedro II |
| Character Interactions | Player action | Individual character | French Second Republic sways |
| Dynamic Movement Traits | Continuous, condition-based | IG leaders | movement_constitutionalist, movement_slaver |
| Single Party Toggle | Law enacted/repealed | All IGs | pro/against_single_party |
| Events | Event fires | IG leader or character | Fascism, Meiji, Paris Commune |
| Journal Entries | JE variable threshold | IG leader | agrarian_socialist_leader, syndicalist |
| Law Changes | Law enacted/repealed | Affected IGs | Remove constitutionalist |

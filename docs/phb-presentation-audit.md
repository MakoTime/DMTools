# Player's Handbook Presentation Audit

Version: 2
Reference: `PlayersHandbook.pdf` (presentation reference only)
Runtime source: canonical SQLite entity payloads

## Scope

This audit covers generated entity Markdown and HTML inspections. The renderer is
versioned independently from imported data. Unknown fields remain visible after
known fields, so an import cannot silently lose information while the presentation
contract evolves.

## Ordered sections

| Entity | Reader-facing order | Current status |
| --- | --- | --- |
| Creature/monster | identity, defenses, movement, abilities, saves/skills, senses, languages, resistances, traits, actions, reactions, legendary actions, spellcasting | Implemented in renderer contract v2 |
| Spell | level/school, casting time, target, components, material, duration, effects, description, higher-level effect, class lists | Implemented in renderer contract v2 |
| Item | category, weapon/armor/magic properties, weight, cost, features, description, source | Implemented in renderer contract v2 |
| Class/subclass | class table and feature order; source-backed subclass tables when present; subclass features and description | Contract corrected; table rendering remains source-data dependent |
| Race | size, speed, ability increases, traits, languages, description | Implemented in renderer contract v2 |
| Feat/background/ability | prerequisites or proficiencies, features/effects, description, source | Implemented in renderer contract v2 |

## Corrected structured fields

- Sense records render as `Darkvision: 60 ft`; typed keys such as
  `distance_type` are not exposed for recognized sense records.
- Movement records render as `Walk: 30 ft` and preserve zero distances.
- Missing recognized measurements render as `Unavailable` instead of an empty
  or misleading value.
- Markdown and HTML use the same normalized Markdown-derived values.

## Prioritized discrepancies and follow-up

1. Spell-slot progression is not present in the imported class definition schema;
   the presentation layer supplies the standard full/half/third-caster slot
   shape from the imported spellcasting progression type. Explicit presentation
   metadata takes precedence when imported data supplies exact slot values.
   Non-spellcasting classes omit slot columns rather than displaying empty ones.
2. Class and subclass features are rendered at their imported levels. Missing
   feature levels remain outside the derived class progression table until
   source data supplies them. A subclass table is rendered only when the source
   provides one; Eldritch Knight has a source-backed Spellcasting table, while
   College of Lore does not have a separate PHB progression table.
3. Proficiencies, damage, ranges, durations, and costs need additional typed
   fixtures as those source records become available. Unknown shapes currently
   use the safe generic renderer and remain visible.
4. Compact object views should be compared with the same contract before adding
   view-specific labels or abbreviations.
5. Named feature objects render their name as a bold display label followed by
   the description; redundant same-entity feature sources are omitted while
   differing provenance remains available.

## Test fixtures

The representative fixtures are in `tests/test_entity_rendering.py`. They cover
stat-block and spell-block ordering, class/subclass progression, sense and
movement normalization, zero/missing values, nested data, long text, and HTML
conversion safety. No Player's Handbook prose is stored as runtime data.

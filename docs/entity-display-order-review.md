# Entity Display Order Review

Status: Proposed for review
Reference: `PlayersHandbook.pdf` (layout and terminology reference only)
Scope: derived Markdown, HTML, compact inspection objects, and linked display data

## Findings

The current renderer uses one field-order contract, but it mixes three different
levels of information: identity, compact combat/reference metadata, and long
feature prose. The class progression table is now derived separately, while
other entity types still fall back to payload insertion order for nested records.
That makes the visible order sensitive to parser/adaptor changes and causes the
output to drift from the reference layout.

The proposed order below is a presentation contract, not an import schema. It
must preserve canonical payloads and omit optional sections only when their data
is absent.

## Proposed Orders

| Entity | Proposed reader-facing order |
| --- | --- |
| Monster | Name and identity; size/type/alignment; armor class and hit points; movement; ability scores; saving throws and skills; senses and passive Perception; languages; resistances, immunities, and vulnerabilities; challenge rating and proficiency bonus; spellcasting; traits; actions; reactions; legendary actions; description; source and image metadata |
| Spell | Name; level and school; casting time; range/target; components and material; duration; ritual/concentration; effects and roll tables; description; higher-level effects; class lists; grants/tags; source |
| Item | Name; category and rarity; armor/weapon profile; magic properties and attunement; weight and cost; granted spells/effects; features; description; source and image metadata |
| Class | Name and class identity; hit die and proficiencies; primary abilities and saving throws; level progression table; spellcasting summary and cantrip/spell progression; feature details grouped by level; subclass availability; description; source and tags |
| Subclass | Name and parent class; subclass identity/proficiencies; subclass feature progression table; feature details grouped by level; spell grants; description; source |
| Race | Name; size and movement; ability score increases; senses; languages; proficiencies; spell/feat grants; traits grouped by feature; description; source |
| Feat | Name; prerequisites; ability score increases; benefits/features; granted spells/effects; description; source |
| Background | Name; skill/tool proficiencies; languages; starting equipment; background features; grants/effects; description; source |
| Ability | Name and category; effects; prerequisites/targets if present; description; source |

## Shared Rules

- The entity name is the display heading, not a repeated `name` field.
- A named feature or action renders as a bold name followed by its description on
  the next line. `name` and `description` are not shown as generic child fields.
- Level-based content is grouped by level and sorted numerically, preserving
  source order for entries with the same level.
- Tables appear before long-form feature descriptions when they summarize the
  entity, especially class and subclass progression tables.
- Source is displayed once at the entity level. A nested source is visible only
  when it differs from the containing entity or provides a distinct provenance
  action.
- Canonical links use entity UIDs and remain selectable in Markdown, HTML, and
  compact views. Display labels never become alternate entity identities.
- Missing optional data leaves the surrounding order unchanged. It does not
  create empty headings or placeholder rows unless the absence itself is useful
  to explain a supported rule table.
- Unknown fields remain visible in a deterministic fallback section after the
  known contract fields.

## Required Validation

1. Compare generated Markdown and HTML against this order for every entity type.
2. Compare compact inspection objects against the same semantic order rather than
   accepting dictionary insertion order.
3. Use fixtures containing missing fields, repeated levels, nested names and
   descriptions, source overrides, spell links, and long text.
4. Verify table headers, feature grouping, links, and source placement separately
   from typography and CSS.
5. Record intentional differences from `PlayersHandbook.pdf` in the audit rather
   than copying protected rules prose into runtime data.

## Open Review Questions

- Should monster spellcasting appear before traits, as in a spellcasting block,
  or remain immediately before actions for compact stat-block density?
- Should class feature details be collapsed by level in compact views while the
  full Markdown/HTML view keeps the complete descriptions?
- Should item rarity be shown alongside category or alongside magic-item
  properties when one of those fields is absent?
- Which compact views are user-facing enough to require exact table placement,
  rather than only semantic ordering?

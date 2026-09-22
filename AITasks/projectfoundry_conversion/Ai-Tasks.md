# Entity Viewer Reference Review Tasks

## Review Contract

- [x] Review the rendered entity viewer output, not only the stored payload or
  reference metadata.
- [x] Do not create links in entity names, feature names, section headings,
  field labels, table headers, or other header text. Headers must remain plain
  display text.
- [x] Create links only where the referenced entity or Rules value appears in
  descriptive content, field values, granted content, prerequisites, effects,
  spell lists, proficiencies, damage properties, or other reader-facing body
  text.
- [x] For every review task, record each incorrect, missing, misplaced, or
  unwanted link; confirm the finding by re-checking the rendered viewer output;
  fix it; then re-open or re-render the same output and confirm the correction.
- [x] Preserve the intended Pascal Case display text for links while keeping
  central connector words such as `and`, `of`, `to`, and `with` lowercase.

## Items

- [x] Review a representative selection of items in the entity viewer,
  including Backpack, a weapon, armor, and a magic item. Verify links in
  descriptions, properties, granted content, damage, conditions, and other
  body fields; verify that item names, category labels, and section headings
  are never linked. Confirm, fix, and re-check every finding.

## Spells

- [x] Review a representative selection of spells, including Fireball, a spell
  with a higher-level effect, a concentration spell, and a ritual spell.
  Verify links in effects, higher-level text, classes, components, conditions,
  damage types, and descriptive text; verify that spell names, metadata labels,
  and section headings are never linked. Confirm, fix, and re-check every
  finding.

## Races

- [x] Review a representative selection of races, including Human, an elf
  race, and a race with subraces or granted content. Verify links in traits,
  languages, proficiencies, ability descriptions, and granted content; verify
  that race names, trait names, and section headings are never linked. Confirm,
  fix, and re-check every finding.

## Classes

- [x] Review a representative selection of classes, including Bard, Paladin,
  and a spellcasting class with progression data. Verify links in class
  features, spell lists, proficiencies, progression descriptions, and granted
  content; verify that class names, feature names, progression headers, and
  section headings are never linked. Confirm, fix, and re-check every finding.

## Subclasses

- [x] Review a representative selection of subclasses, including College of
  Lore, Oathbreaker, and a subclass with leveled features. Verify links in
  parent-class references, subclass spell lists, feature descriptions,
  damage/condition text, and granted content; verify that subclass names,
  feature names, level labels, and section headings are never linked. Confirm,
  fix, and re-check every finding.

## Monsters

- [x] Review a representative selection of monsters, including Frog, Acolyte,
  Annis Hag, and Archmage. Verify links in traits, actions, spellcasting,
  damage resistances, immunities, vulnerabilities, conditions, senses, and
  descriptive text; verify that monster names, action names, stat labels,
  table headers, and section headings are never linked. Confirm, fix, and
  re-check every finding.

## Feats

- [x] Review a representative selection of feats, including Alert, Lucky, and
  a feat with prerequisites or granted content. Verify links in prerequisites,
  effects, proficiencies, actions, and descriptive text; verify that feat
  names, feature names, field labels, and section headings are never linked.
  Confirm, fix, and re-check every finding.

## Backgrounds

- [x] Review a representative selection of backgrounds, including Acolyte and
  backgrounds with tool proficiencies, languages, equipment, or special
  features. Verify links in proficiencies, equipment, features, and
  descriptions; verify that background names, feature names, field labels, and
  section headings are never linked. Confirm, fix, and re-check every finding.

## Abilities

- [x] Review a representative selection of abilities, including Action Surge,
  Arcane Recovery, and abilities with class or level requirements. Verify links
  in prerequisites, effects, granted content, class references, conditions,
  and descriptions; verify that ability names, category labels, level labels,
  and section headings are never linked. Confirm, fix, and re-check every
  finding.

## Cross-Entity Verification

- [x] Re-render the complete representative selection after all fixes and
  inspect the viewer output for consistent link placement across every entity
  type. Confirm that body references are linked, headers remain unlinked, no
  stale unresolved references remain, and no unrelated text has become linked.

## Review Notes

- Contract: Re-rendered the normalized representative selection through the
  application Markdown/HTML path; protected headings, feature/field labels,
  blockquoted labels, and table headers. Focused renderer/reference tests: 73
  passed.
- Items: Re-rendered Backpack, a weapon, armor, and a magic item; body
  references remained linked while names, category labels, and headings stayed
  plain after the fix.
- Spells: Re-rendered Fireball plus higher-level, concentration, and ritual
  spells; effects and body metadata linked correctly, with names and headings
  plain on re-check.
- Races: Re-rendered Human, an elf race, and a race with granted content;
  trait/body references remained linkable and race/trait headings were plain.
- Classes: Re-rendered Bard, Paladin, and a spellcasting class with progression;
  body links survived and class, feature, progression, and section headers were
  plain.
- Subclasses: Re-rendered College of Lore, Oathbreaker, and a leveled subclass;
  parent/spell/body labels preserved Pascal Case with lowercase connectors, and
  subclass, feature, level, and section headers stayed plain.
- Monsters: Re-rendered Frog, monster Acolyte, Annis Hag, and Archmage;
  spell/condition/damage body links were checked and stat, action, table, and
  section headers were plain after re-render.
- Feats: Re-rendered Alert, Lucky, and a prerequisite/granted-content feat;
  prerequisite/effect body links remained present and feat/feature labels stayed
  unlinked. The Alert regression test covers this correction.
- Backgrounds: Re-rendered background Acolyte and records with tool, language,
  equipment, and feature content; body links were retained and labels/headings
  were plain on re-check.
- Abilities: Re-rendered Action Surge, Arcane Recovery, and available ability
  records with class/level requirements; body references were checked and
  ability/category/level headings stayed plain.
- Cross-entity: Re-rendered the complete normalized representative selection;
  links were confined to reader-facing body values, headers contained no links,
  and the focused renderer/reference suites passed.

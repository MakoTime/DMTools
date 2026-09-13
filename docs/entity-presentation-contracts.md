# Entity Presentation Contracts

These contracts define reader-facing Markdown layouts derived from canonical entity payloads. They do not change or persist canonical data. Missing fields are omitted unless a contract explicitly requires a placeholder.

## Monster

Reference records: Frog and Acolyte.

Order:

1. Name.
2. Italic identity line: size, creature type, and alignment.
3. Armor Class.
4. Hit Points, combining maximum and hit dice where available.
5. Speed, grouped by movement type.
6. Ability-score table with scores and calculated modifiers.
7. Saving Throws, when present.
8. Skills, with modifiers.
9. Damage Vulnerabilities, Resistances, and Immunities, when present.
10. Condition Immunities, when present.
11. Senses and passive Perception.
12. Languages, when present.
13. Challenge and experience value, when available.
14. Proficiency Bonus, when available or derivable.
15. Traits.
16. Actions.
17. Reactions.
18. Legendary Actions.

Storage-only fields such as current hit points, temporary hit points, maximum changes, raw hit-dice count, and internal movement flags are not displayed independently.

## Spell

Reference record: Fireball.

Order:

1. Name and spell level/school.
2. Casting Time.
3. Range or target.
4. Components and material requirements.
5. Duration, including concentration.
6. Classes.
7. Description/effects.
8. At Higher Levels.
9. Ritual and concentration indicators where not already represented.
10. Source.

## Item

Reference records: Backpack, a weapon, and a magic item.

Order:

1. Name and item category.
2. Armor or weapon statistics when applicable.
3. Weight.
4. Cost.
5. Properties, damage, range, and mastery information when applicable.
6. Magic-item properties, charges, effects, and granted content when applicable.
7. Features and description.
8. Source.

Irrelevant weapon, armor, or magic sections are omitted.

## Class

Reference record: Bard.

Order:

1. Name and class identity/introduction.
2. Class overview or quick-build material when present.
3. The class's primary level progression table, such as the Bard table.
4. Class Features in the source's reader-facing order: Hit Points,
	Proficiencies, Equipment, Spellcasting, then the named class features in
	their source order.
5. Optional or supplementary features.
6. Description material that is not already represented by the overview or
	feature sections.
7. Source.

The progression table is a reader-facing summary, not a replacement for the
detailed feature sequence. Spellcasting is rendered in its source position
within Class Features rather than as a generic summary placed before the
table.

## Subclass

Reference records: College of Lore and Eldritch Knight.

Order:

1. Name and parent class.
2. Subclass overview or identity prose.
3. A source-backed subclass progression or spellcasting table when the source
	provides one. For example, Eldritch Knight includes an Eldritch Knight
	Spellcasting table within its Spellcasting feature.
4. Subclass features in source order, including the table-bearing feature at
	its source position.
5. Granted spells, proficiencies, or other content.
6. Description material that is not already represented by the overview or
	feature sections.
7. Source.

College of Lore has no separate PHB progression table, so its presentation is
the overview followed by Bonus Proficiencies, Cutting Words, Additional
Magical Secrets, and Peerless Skill. A derived table must not be presented as
if it were part of the PHB layout.

Class-owned content is not repeated in a subclass view.

## Race

Reference record: Human.

Order:

1. Name and size.
2. Speed.
3. Ability score increases.
4. Skill, weapon, armor, and tool proficiencies.
5. Languages.
6. Traits.
7. Granted spells or feats.
8. Description.
9. Source.

## Feat

Reference record: Alert or Lucky.

Order:

1. Name.
2. Prerequisites.
3. Ability score increases.
4. Proficiencies.
5. Features and actions.
6. Granted spells or other content.
7. Description.
8. Source.

## Background

Reference record: Acolyte.

Order:

1. Name.
2. Skill proficiencies.
3. Tool proficiencies.
4. Languages.
5. Equipment.
6. Features.
7. Description.
8. Source.

## Ability

Reference records: Action Surge or Arcane Recovery.

Order:

1. Name and category.
2. Class and level.
3. Prerequisites.
4. Effects.
5. Granted spells, proficiencies, or other content.
6. Description.
7. Source.

## Shared conventions

- Use reader-facing labels and units; never expose canonical snake_case keys.
- Preserve imported prose and do not fabricate missing data.
- Omit empty, null, and irrelevant sections.
- Render named features as distinct blocks with separated descriptions and metadata.
- Render source mappings through their readable text value.
- Preserve canonical payloads and source metadata unchanged.
- Generate Markdown first; derive HTML from the generated Markdown.
- Keep unknown fields visible through the generic fallback renderer until a dedicated contract is added.

# Phase 1F Confirmed Transition Boundary

canonical_rule_id: RULE_CONFIRMED_TRANSITION_VALIDATED_BOUNDARY
source_section_id: 19::CONFIRMED_TRANSITION_VALIDATED_BOUNDARY

A confirmed-semantic transition has one formal validation boundary. That boundary consumes the exact source set, Brain mapping, Brain mapping seal, disposition decision set, disposition seal and capability registry, validates their exact IDs and digests, and only then returns a short-lived validated input object for mechanical migration derivation. The validated object is temporary process state, not a new durable authority or truth source.

canonical_rule_id: RULE_CONFIRMED_TRANSITION_SEAL_CONSUMPTION
source_section_id: 19::CONFIRMED_TRANSITION_SEAL_CONSUMPTION

The public confirmed-transition path must verify both the separately sealed Web Brain semantic mapping and the separately sealed disposition decision set. Internal migration derivation may assume a validated input object, but raw or independently re-digested mapping or disposition objects may not enter the renderer directly.

canonical_rule_id: RULE_PACKAGE_RELATIVE_EXACT_SOURCE_BINDING
source_section_id: 19::PACKAGE_RELATIVE_EXACT_SOURCE_BINDING

When a source set declares that exact legacy bytes are bundled in the current package, its source root is a package-relative path included in the source-set digest and Brain mapping seal. The resolved root must remain inside the current package and every exact source file must match the bound byte count and SHA-256. Unbundled current legacy sources declare no package-relative source root.

canonical_rule_id: RULE_ORDERED_SECTION_BOUNDARY
source_section_id: 19::ORDERED_SECTION_BOUNDARY

Exact legacy and Brain semantic-evidence sections require one start marker followed by one end marker and non-empty content between them. Missing, duplicated, reversed or empty section boundaries block before semantic or disposition effects.

canonical_rule_id: RULE_DERIVED_MAPPING_STATUS
source_section_id: 19::DERIVED_MAPPING_STATUS

The top-level Brain mapping status is mechanically derived from the row-level Brain mapping statuses and is not independently authored. A value inconsistent with the rows blocks before the mapping or disposition is consumed.

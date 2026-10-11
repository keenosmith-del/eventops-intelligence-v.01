# Architecture decisions

## Initial isolation (superseded by owner correction)

Problem: maintain the submitted demonstration while changing behavior. Options: edit main, copy a repository, or Git worktree. Selected: dedicated worktree on the explicitly requested branch, independent Compose project/volume/ports and new credentials. This preserves comparison and avoids production data coupling. Consequence: separate dependency installations and local setup.

## Floating UUID lookup

Problem: inline disclosure expands into sidebar controls. Options: expanding form, modal, or anchored popover. Selected: controlled absolutely positioned upward popover. It fits the narrow sidebar and preserves navigation geometry. Trade-off: dismissal and focus must be managed explicitly; browser regressions cover them.

## Reader-controlled chat scrolling

Problem: unconditional scroll-to-end removes the question from view on answer completion. Options: keep automatic scrolling, use an inner scroll area, or anchor turns in the document. Selected: one-time question anchors and explicit latest navigation using the existing document scroll. No extra scroll container or dependency. Spacing keeps the turn reachable above the sticky composer; ResizeObserver and passive scroll listeners track end visibility. Trade-off: short final turns retain some negative space.

## Frosted composer and accessible focus

Problem: opaque composer creates a hard edge; native focus outlines look too dark. Selected: pointer-transparent masked backdrop blur plus gradient; rounded surface focus and one-pixel muted form outlines. Text remains opaque/readable. CSS fallbacks retain the translucent gradient where blur is unsupported. Trade-off: blur support varies by browser and focus must remain visible.

## Context in navigation URLs

Problem: moving from an answered event to verification loses its context. Selected: validated event and conversation query parameters carried through agent/result/history links. URLs survive refresh, and existing backend object ownership still controls access. No server schema change. Trade-off: the UI context is navigation metadata and not an operational verification claim; seeded supported events remain bounded.

## Preserve export timing semantics

Problem: an old live test assumed downloading CSV completes a stored graph stage. Selected: assert unchanged saved stage timestamps and result records after downloads/history restoration, matching the existing API and iteration requirements. No fabricated execution stage or replay timing is introduced.

## Consolidate into the existing repository

Problem: the temporary external directory was based on an incorrect structure requirement. Options: cherry-pick, copy files, or fast-forward the original main. Selected: fast-forward because both working trees were clean and main was an ancestor of the two Phase 1 commits. This preserves exact commit identities and newer submission assets without duplicated commits.

Restore original local runtime configuration while retaining credentials/volumes. Preserve comparisons with annotated historical tags, not duplicate application directories. The recorded assessment release and later repository baseline are distinguished explicitly. Trade-off: main is now the development branch; every production-triggering push requires owner confirmation. The obsolete worktree is removed only after full verification; its branch and local database volume remain.

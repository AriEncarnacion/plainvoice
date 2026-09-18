# Data conventions

The documentation files in this directory are tracked in Git; `local/` holds the complete local data package and is excluded as a whole directory by `.gitignore`. All examples in the annotation protocol are original demos; automatically generated candidates are not equivalent to gold confirmed by human evaluation.

On 2026-09-12, six public datasets, a small agentic sample, and six sets of real-source rewrite candidates were saved to the desktop at the location the user specified; on 2026-09-15 they were moved into this directory's `local/`, without being imported into Git. See the [actual collection record](../09-12-local-data-and-rewrite-pilot.md). These candidates have not yet been through independent human evaluation.

In future, every individual task records at least the following fields:

| Field | Meaning |
|---|---|
| task_id / source_family_id / split | Task, source family, train/dev/test; split by source family first, then derive |
| language / locale / genre / subgenre | Chinese or English, region, technical or marketing and subgenre |
| audience / purpose / channel | Audience, task objective, and channel |
| source_url / source_version / original_date / date_evidence | Origin, commit/archive version, original date and evidence |
| provenance / provenance_evidence | Human / model / hybrid / unknown, independent of quality |
| rights_status / permitted_uses / consent_reference | Rights verification status, and scope for training / internal evaluation / redistribution |
| draft / source_pack / protected_claims / protected_spans | Source draft, evidence, information that must be preserved, code and identifiers, and so on |
| voice_reference / editable_scope / length_requirement | Voice, the scope permitted for modification, length requirement |
| candidates[] | Text of each draft, full model ID/revision, prompt version, decoding/thinking settings, seed, and all costs and latencies |
| annotations[] | Anonymized reviewer ID, language/domain seniority, per-draft constraint results, issue score, evidence, the two preferences, and disagreement |
| derivation / parent_ids | Relationships for translations, synthetic contamination, revisions of older drafts, or multi-model variants |
| adjudication / annotation_version | Adjudication and version; it does not overwrite the original evaluations |

The actual JSON Schema, collection scripts, and model adapters will be implemented once the pilot conventions are stable; for now the field draft is not presented as a working benchmark tool.

Pre-existing errors in the source text and errors introduced by the rewrite must be recorded separately. Without an external factual basis, the only claim available is fidelity relative to the input, not correctness against real-world fact.

Verify usage conditions separately for each source. `.gitignore` only guards against accidental commits; it cannot guarantee the confidentiality of data in local or cloud backups. A personal repository should not automatically import internal company material.

## The local cleaning layer as implemented

For the repo-wide unified body-text layer, auditing, and minimal text export, see the [body-text cleaning notes](../09-12-text-cleaning.md). The data lives in `~/Desktop/plainvoice/data/local/`. The cleaned export preserves each original task's roles, its null versus empty-string distinction, and its multi-reference distinctions, and does not automatically produce human preference labels.

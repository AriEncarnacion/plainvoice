#!/usr/bin/env python3
"""Lossless, stdlib-only exporter for Plainvoice's rewrite and agentic samples.

Only reads the supplied data root. Nothing is sent to a network or executed from
the source corpus. Call export(root, emit), or use --root --output --report.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re


def js(value):
    return json.dumps(value, ensure_ascii=False, indent=2)


def side(label, text, role):
    return {"label": label, "text": text, "role": role}


def language(text):
    han = len(re.findall(r"[\u3400-\u9fff]", text))
    latin = len(re.findall(r"[A-Za-z]", text))
    if not han and not latin:
        return "unknown"
    if han > max(20, latin * .2):
        return "zh"
    if han > max(20, latin * .03):
        return "mixed"
    return "en"


def message_text(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(v.get("text", js(v)) if isinstance(v, dict) else str(v) for v in value)
    return "" if value is None else js(value)


def export(root: Path, emit):
    root = Path(root).resolve()
    touched = {}
    summaries = {}
    record_ids = []
    public_candidates = []
    duplicate_checks = []

    def read(rel):
        rel = str(rel)
        touched[rel] = "incorporated_text_or_metadata"
        return (root / rel).read_text(encoding="utf-8")

    def load(rel):
        return json.loads(read(rel))

    def rows(rel):
        return [json.loads(line) for line in read(rel).splitlines() if line.strip()]

    def paths(value):
        if isinstance(value, str):
            return value.replace(str(root) + "/", "")
        if isinstance(value, list):
            return [paths(v) for v in value]
        if isinstance(value, dict):
            return {k: paths(v) for k, v in value.items()}
        return value

    def attach(rel, note="raw source retained locally"):
        p = root / rel
        touched[str(rel)] = "linked_original_artifact"
        return {"local_path": str(rel), "bytes": p.stat().st_size,
                "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "note": note}

    def add(collection, title, family, key, pair_type, heading, left, right=None,
            context="", source_url="", local_path="", split="", locator="",
            license="unknown", notes="", extra=None, lang=None, public_status="local-only"):
        identifier = collection + ":" + str(key)
        if identifier in record_ids:
            raise ValueError("Duplicate ID " + identifier)
        record_ids.append(identifier)
        lang = lang or language(left["text"])
        obj = {"id": identifier, "collection": collection, "collection_title": title,
               "family": family, "language": lang, "pair_type": pair_type,
               "title": heading, "left": left, "right": right, "alternatives": [],
               "context": context, "provenance": {
                   "source_url": source_url, "local_path": local_path, "split": split,
                   "record_locator": locator, "license": license, "notes": notes},
               "extra": {"publication_status": public_status, **(extra or {})}}
        obj = paths(obj)
        emit(obj)
        summary = summaries.setdefault(collection, {"slug": collection, "collection": collection,
            "title": title, "collection_title": title, "family": family, "count": 0,
            "languages": Counter(), "pair_types": Counter(), "rights": Counter()})
        summary["count"] += 1
        summary["languages"][lang] += 1
        summary["pair_types"][pair_type] += 1
        summary["rights"][public_status] += 1
        return identifier

    # Both experiments are preserved as separate collection versions.
    base = "human-rewrite-pairs"
    pairs = load(base + "/pairs.json")
    source_metadata = {p["id"]: load(base + "/sources/" + p["id"] + "/metadata.json") for p in pairs}
    paragraph_qa = {p["id"]: p for p in load(base + "/generation/mechanical-qa.json")}
    paragraph_run = load(base + "/generation/run.json")
    paragraph_prompt = read(base + "/generation/prompt.txt")
    paragraph_inputs = load(base + "/generation/inputs.json")
    for p in pairs:
        k = p["id"]
        meta = source_metadata[k]
        add("rewrite-paragraph-v1", "Paragraph rewrite experiment · v1", "rewrite-experiment", k,
            "rewrite", p["title"],
            side("Source excerpt" if "current" in k else "Historically attributed source excerpt",
                 read(base + "/" + p["excerpt_local"]), "source-authorship-unknown" if "current" in k else "human-attributed-source"),
            side("AI rewrite candidate · paragraph v1", p["rewrite"], "ai-rewrite"),
            context="Source excerpt location: " + p["locator"] + "\n" + p["provenance_note"],
            source_url=p["source_url"], local_path=base + "/pairs.json", split="paragraph-v1",
            locator="id=" + k, license=p["rights_status"],
            notes="Unreviewed candidate. Authorship is not a quality label. Source is not a predefined winner.",
            extra={"source_metadata": meta, "pair_metadata": p, "prompt": paragraph_prompt,
                   "generation_run": paragraph_run, "generation_inputs": paragraph_inputs,
                   "mechanical_qa": paragraph_qa[k], "rewrite_metadata": load(base + "/pairs/" + k + "/metadata.json"),
                   "original_artifact": attach(base + "/" + p["source_local"]),
                   "full_article_record": "rewrite-article-v2:" + k}, lang=p["language"])

    v2 = base + "/article-v2"
    generation = load(v2 + "/generation-runs.json")
    runs = {r["article_id"]: r for r in generation["runs"]}
    mechanical = {r["article_id"]: r for r in load(v2 + "/qa/mechanical-audit.json")}
    semantic_review = load(v2 + "/qa/independent-model-review.json")
    coordinator = load(v2 + "/qa/coordinator-checks.json")
    extraction_prompt = read(v2 + "/prompts/article-content-extraction.md")
    writing_prompt = read(v2 + "/prompts/article-from-content.md")
    for r in load(v2 + "/article-results.json"):
        k, packet_id = r["id"], r["packet_id"]
        source = read(v2 + "/" + r["source_path"])
        rewrite = read(v2 + "/" + r["rewrite_path"])
        raw_rewrite = read(v2 + "/generated/" + packet_id + ".md")
        if raw_rewrite != rewrite:
            raise ValueError("Generated and friendly rewrite copies differ: " + k)
        duplicate_checks.append({"path": v2 + "/generated/" + packet_id + ".md",
                                 "same_text_as": v2 + "/" + r["rewrite_path"], "verified": True})
        add("rewrite-article-v2", "Full article rewrite experiment · v2", "rewrite-experiment", k,
            "rewrite", r["title"],
            side("Complete cleaned source article", source, "source-authorship-unknown" if "current" in k else "human-attributed-source"),
            side("AI article · " + r["generated_title"], rewrite, "ai-rewrite"),
            context="\n".join(r["notes"]), source_url=r["source_url"],
            local_path=v2 + "/article-results.json", split="article-v2", locator="id=" + k,
            license=source_metadata[k]["rights_status"],
            notes="Full source and rewrite preserved. Generator coverage is self-report; mechanical QA is not human preference. The independent model review covers only two articles.",
            extra={"source_metadata": source_metadata[k], "result_metadata": r,
                   "source_audit": load(v2 + "/source-audit/" + k + "/coverage.json"),
                   "original_full_extracted_text": read(base + "/sources/" + k + "/extracted.txt"),
                   "content_extraction": load(v2 + "/" + r["content_path"]),
                   "writer_packet": load(v2 + "/" + r["shuffled_packet_path"]),
                   "packet_audit": load(v2 + "/packet-audit/" + packet_id + ".audit.json"),
                   "generator_coverage": load(v2 + "/" + r["coverage_path"]),
                   "generation_run": runs[k], "generation_parameters": {q:v for q,v in generation.items() if q != "runs"},
                   "prompts": {"content_extraction": extraction_prompt, "writing": writing_prompt},
                   "qa": {"mechanical": mechanical[k], "coordinator": coordinator,
                          "independent_model_review": semantic_review},
                   "original_artifact": attach(base + "/sources/" + k + "/" + Path(source_metadata[k]["local_path"]).name),
                   "paragraph_record": "rewrite-paragraph-v1:" + k}, lang=r["language"])

    a = "agentic-technical"
    manifest = load(a + "/source-manifest.json")
    sources = {s["source"]: s for s in manifest["sources"]}
    downloads = {d["path"]: d for d in manifest["direct_downloads"]}
    public = "public-license-candidate-with-attribution"

    # Final summaries and actual observations stay attached, never made into human pairs.
    hero = a + "/traces/swe-hero-openhands/samples"
    hero_traces = rows(hero + "/trajectories.3.jsonl")
    finals = rows(hero + "/final-text-for-editing.jsonl")
    hero_inspection = load(hero + "/inspection.json")
    for i, (trace, f) in enumerate(zip(hero_traces, finals, strict=True)):
        assert trace["trajectory_id"] == f["trajectory_id"]
        ident = add("swe-hero-openhands", "SWE-Hero · agent engineering summaries and traces", "agentic-technical",
            f["trajectory_id"], "trace", f["instance_id"], side("Agent final summary · unedited", f["final_text"], "ai-final"),
            context=f["task_statement"], source_url="https://huggingface.co/datasets/nvidia/SWE-Hero-openhands-trajectories",
            local_path=hero + "/trajectories.3.jsonl", split=f["source_split"], locator="row=" + str(i) + "; trajectory_id=" + f["trajectory_id"],
            license="CC BY 4.0 (dataset); " + trace["license"] + " (repository)",
            notes="No human rewrite; no test replay or claim verification. Empty API truncated_cells does not establish complete environment history.",
            extra={"trace": trace, "editing_entry": f, "inspection": hero_inspection[i],
                   "raw_trace_artifact": attach(hero + "/trajectories.3.jsonl", "Full local NDJSON; select source_row_idx"),
                   "source_manifest": sources["swe-hero-openhands"]}, public_status=public)
        if i == 0:
            public_candidates.append({"id": ident, "scope": "final summary or a short attributed excerpt; repository BSD-3-Clause attribution also required", "trace": "Keep large full trace local in a small public demo."})

    smith = a + "/traces/swe-smith/samples"
    smith_traces = rows(smith + "/trajectories.3.jsonl")
    smith_inspection = load(smith + "/inspection.json")
    for i, trace in enumerate(smith_traces):
        task = next((message_text(m.get("content")) for m in trace["messages"] if m["role"] == "user"), "")
        terminal = trace["messages"][-1]
        add("swe-smith", "SWE-smith · tool traces and QA counterexamples", "agentic-technical",
            trace["traj_id"], "trace", trace["instance_id"],
            side("Terminal submission event · no final prose", js(terminal), "ai-tool-action"),
            context=task, source_url="https://huggingface.co/datasets/SWE-bench/SWE-smith-trajectories",
            local_path=smith + "/trajectories.3.jsonl", split="tool", locator="row=" + str(i) + "; traj_id=" + trace["traj_id"],
            license=sources["swe-smith"]["license"], notes=sources["swe-smith"]["quality_warning"],
            extra={"trace": trace, "inspection": smith_inspection[i], "final_prose_available": False,
                   "human_rewrite": None, "source_manifest": sources["swe-smith"],
                   "raw_trace_artifact": attach(smith + "/trajectories.3.jsonl", "Full local NDJSON; select row")},
            public_status="local-demo-default; repository-license-attribution-review-needed", lang=language(task))

    # A report accompanied by rubric/source URLs is still unpaired writing.
    drb_path = a + "/deepresearch-bench-ii/samples/tasks-and-rubrics.10.jsonl"
    for i, task in enumerate(rows(drb_path)):
        report_rel = "drb2-model-reports/samples/Doubao-DeepResearch/idx-" + str(task["idx"]) + ".md"
        report = read(a + "/" + report_rel)
        ident = add("deepresearch-bench-ii", "DeepResearch Bench II · bilingual technical reports", "agentic-technical",
            task["idx"], "unpaired", task["description"], side("Doubao DeepResearch final report", report, "ai-final"),
            context=task["prompt"] + "\n\nExpert evaluation rubric:\n" + js(task["content"]["rubric"]),
            source_url=downloads[report_rel]["url"], local_path=a + "/" + report_rel, split="idx-41-50",
            locator="idx=" + str(task["idx"]) + "; task row=" + str(i),
            license=task["license"] + " task/rubric; Apache-2.0 model report",
            notes="Human source article is a URL/reference only; its body is not in the downloaded package. No trace or human rewrite.",
            extra={"task_and_rubric": task, "human_source_article": task["content"]["blocked"],
                   "human_reference_body_available": False, "complete_action_trace_available": False,
                   "source_manifest": sources["deepresearch-bench-ii"], "report_download": downloads[report_rel]},
            lang=task["language"], public_status=public)
        if i == 0:
            public_candidates.append({"id": ident, "scope": "Task and a short model-report sample with both task attribution and model-report Apache-2.0 notice; source article body is absent."})

    cog_path = a + "/coggen/samples/owid-task-human-reference.20.jsonl"
    cog_rows = rows(cog_path)
    cog_pair_path = a + "/coggen/samples/deforestation.same-task-pair.json"
    cog_pair = load(cog_pair_path)
    pair_task = cog_pair["task"]["id"]
    seen_pair = False
    for i, item in enumerate(cog_rows):
        task, human = item["task"], item["human_reference"]
        paired = task["id"] == pair_task
        right = None
        generated = None
        if paired:
            assert task["query"] == cog_pair["ai_report"]["config"]["query"]
            assert human["content"]["markdown"] == cog_pair["human_reference"]["content"]["markdown"]
            generated = cog_pair["ai_report"]
            right = side("CogGen AI report · same task", generated["markdown"], "ai-final")
            seen_pair = True
        ident = add("coggen-owid", "CogGen · OWID references and released AI reports", "agentic-technical", task["id"],
            "same-task" if paired else "unpaired", human["metadata"]["title"],
            side("OWID human reference", human["content"]["markdown"], "human-reference"), right,
            context=task["query"], source_url=human["metadata"]["url"], local_path=cog_pair_path if paired else cog_path,
            split="OWID", locator="task.id=" + task["id"] + "; source row=" + str(i),
            license="OWID text CC BY 4.0; third-party media/data have separate terms" + ("; CogGen repository MIT (AI example rights not separately specified)" if paired else ""),
            notes="Same task does not establish equivalent content or human editing of AI output." if paired else "Human reference only; no matched AI output in the downloaded sample.",
            extra={"task": task, "human_source": {k:v for k,v in human.items() if k != "content"},
                   "human_content_structure": {k:v for k,v in human["content"].items() if k != "markdown"},
                   "source_manifest": sources["coggen-owid"], "ai_report": generated,
                   "verification": cog_pair["verification"] if paired else {"matched_ai_report": False}},
            lang="en", public_status="local-demo-default; AI-example-license-scope-review-needed" if paired else public)
        if i == 0:
            public_candidates.append({"id": ident, "scope": "OWID prose only, author/date/source and CC BY 4.0 attribution; do not embed unreviewed third-party chart assets."})
    assert seen_pair
    gen = "coggen/samples/generated/"
    for p in sorted((root / a / gen).glob("*/report_final.md")):
        rel = str(p.relative_to(root))
        config = load(str(p.with_name("config.json").relative_to(root)))
        body = read(rel)
        if config["query"] == cog_pair["task"]["query"]:
            assert body == cog_pair["ai_report"]["markdown"]
            duplicate_checks.append({"path": rel, "same_text_as": cog_pair_path + "#ai_report.markdown", "verified": True})
            continue
        add("coggen-owid", "CogGen · OWID references and released AI reports", "agentic-technical",
            p.parent.name, "unpaired", config["title"], side("CogGen AI report · no human match", body, "ai-final"),
            context=config["query"], source_url=downloads[str(p.relative_to(root / a))]["url"], local_path=rel,
            split="released-example", locator=p.parent.name,
            license="CogGen repository MIT; AI example report rights not separately specified",
            notes="No human reference or action trace for this sample was downloaded.", extra={"config": config},
            lang="en", public_status="local-demo-default; AI-example-license-scope-review-needed")

    def wiki_section(section, depth=2):
        out = []
        if section.get("section_title"):
            out.append("#" * depth + " " + section["section_title"])
        for sentence in section.get("section_content", []):
            out.append(sentence["sentence"])
        for sub in section.get("subsections", []):
            out.append(wiki_section(sub, min(depth + 1, 6)))
        return "\n\n".join(out)

    for p in sorted((root / a / "freshwiki/samples").glob("*.json")):
        rel = str(p.relative_to(root))
        doc = load(rel)
        full = "# " + doc["title"] + "\n\n" + doc["summary"] + "\n\n" + "\n\n".join(wiki_section(s) for s in doc["content"])
        ident = add("freshwiki", "FreshWiki · reference articles", "agentic-technical", p.stem,
            "unpaired", doc["title"], side("Wikipedia reference article", full, "community-reference"),
            context="Full downloaded summary and section text; sentence references and original structure are in metadata.",
            source_url=doc["url"], local_path=rel, split="selected-10", locator=p.stem,
            license="CC BY-SA 4.0; preserve Wikipedia contributor attribution and indicate formatting changes",
            notes="No matched AI output. Wikipedia authorship is not proof of no machine assistance. Formatting assembled from downloaded section/sentence records without omitting prose.",
            extra={"original_record": doc, "download": downloads[str(p.relative_to(root / a))],
                   "source_manifest": sources["freshwiki"]}, lang="en", public_status=public)
        if p.stem == "Eukaryote":
            public_candidates.append({"id": ident, "scope": "Small CC BY-SA 4.0 text sample with Wikipedia attribution and a note that source sections were formatted as Markdown."})

    code_path = a + "/code2doc/samples/test.rows-0-19.jsonl"
    code_rows = rows(code_path)
    for i, c in enumerate(code_rows):
        add("code2doc", "Code2Doc · existing technical documentation", "agentic-technical", "test-" + str(i),
            "unpaired", c["repo_name"] + " · " + c["function_name"],
            side("Existing repository documentation", c["documentation"], "source-documentation-authorship-unverified"),
            context="Source code (" + c["language"] + "):\n\n" + c["function_code"],
            source_url="https://huggingface.co/datasets/kaanrkaraman/code2doc", local_path=code_path, split="test",
            locator="row=" + str(i) + "; " + c["repo_name"] + "/" + c["file_path"] + ":" + str(c["line_number"]),
            license=sources["code2doc"]["license"],
            notes="Code/documentation relationship, not a human/AI rewrite pair. Heuristic quality score and source attribution are not human-gold labels. Source revision not included.",
            extra={"source_record": c, "programming_language": c["language"], "source_manifest": sources["code2doc"]},
            lang=language(c["documentation"]), public_status="local-demo-default; repository-license-attribution-review-needed")

    researcher_path = a + "/researcherbench/samples/questions-rubrics-claude.10.jsonl"
    for i, r in enumerate(rows(researcher_path)):
        q = r["question"]
        add("researcherbench", "ResearcherBench · answers with expert rubrics", "agentic-technical", q["id"],
            "unpaired", str(q["id"]) + " · " + q["Subject"],
            side("Claude research answer", r["ai_response_record"]["response"], "ai-final"),
            context=q["question"] + "\n\nExpert rubric:\n" + js(r["rubric_record"]["rubric"]),
            source_url=sources["researcherbench"]["original_urls"][2], local_path=researcher_path,
            split="first-10-official-order", locator="question.id=" + str(q["id"]) + "; row=" + str(i),
            license=sources["researcherbench"]["license"], notes="No human reference article or complete action trace. Expert rubric is not a human answer.",
            extra={"source_record": r, "source_manifest": sources["researcherbench"]}, lang="en")

    # Verify that retained API transports contain no extra records beyond exports.
    transports = [("code2docrows.json", code_rows), ("swehero-rows.json", hero_traces), ("swe-rows.json", smith_traces)]
    for filename, normalized in transports:
        rel = a + "/discovery/" + filename
        raw = load(rel)
        raw_rows = [r["row"] for r in raw["rows"]]
        for row in raw_rows:
            if isinstance(row.get("messages"), str):
                row["messages"] = json.loads(row["messages"])
        equal = raw_rows == normalized
        if not equal:
            raise ValueError("Unaccounted discovery rows in " + rel)
        duplicate_checks.append({"path": rel, "rows": len(raw_rows), "all_rows_in_normalized_samples": True,
                                 "api_truncated_cells": [r.get("truncated_cells", []) for r in raw["rows"]]})
        touched[rel] = "verified_duplicate_raw_api_transport"

    inventory = []
    for folder in ["human-rewrite-pairs", "agentic-technical"]:
        for p in sorted((root / folder).rglob("*")):
            if not p.is_file():
                continue
            rel = str(p.relative_to(root))
            status = touched.get(rel)
            if not status:
                if "/documentation/" in rel or p.name.startswith("README") or p.name == "RESEARCH-NOTE.md":
                    status = "reference_documentation_not_sample"
                elif "/discovery/" in rel:
                    status = "discovery_file_listing_or_dataset_metadata_not_sample"
                elif "generation-cli-failed" in rel:
                    status = "failed_generation_attempt_no_candidate"
                elif p.suffix == ".html":
                    status = "previous_viewer_or_redirect_duplicates_source_records"
                elif "/pairs/" in rel and p.name == "rewrite.md":
                    status = "duplicate_rewrite_copy_in_pairs_json"
                elif re.search(r"row-\d+\.final\.json$", rel):
                    status = "duplicate_final_event_in_full_trace"
                elif p.suffix == ".py":
                    status = "qa_or_export_program_not_executed"
                elif p.name in {"response.json", "manifest.json", "SHA256SUMS", "verification.json", "download-documentation-manifest.json", "packet-report.json"}:
                    status = "supporting_manifest_or_duplicate_generation_metadata"
                else:
                    status = "unclassified_requires_review"
            inventory.append({"local_path": rel, "bytes": p.stat().st_size, "status": status})
    report = {
        "schema_version": "plainvoice-normalized-1", "input_root": str(root),
        "record_count": len(record_ids), "collections": list(summaries.values()),
        "inventory": inventory, "inventory_status_counts": dict(Counter(x["status"] for x in inventory)),
        "duplicate_checks": duplicate_checks, "public_sample_candidates": public_candidates,
        "publication_policy": {
            "default": "Exporter emits a complete LOCAL review corpus, not an approval or license to publish it.",
            "local_only": ["All 12 rewrite-experiment records: Oaktree reserved rights, Stripe no permissive prose license established, Ruan Yifeng CC BY-NC-ND 3.0 derivatives not cleared.",
                           "ResearcherBench: no LICENSE in inspected official revision."],
            "conditional": "Source rights evidence comes from downloaded official READMEs/manifests. Preserve licenses, source URLs and author attribution. Public sample candidates are scoped text suggestions, not full-corpus redistribution.",
            "privacy": "Public-download provenance; no private user communications requested or imported. Third-party trace contents were not executed. No comprehensive PII or secret audit is claimed; full trace metadata remains for local review.",
            "external_media": "URLs are metadata only; do not automatically load or embed third-party images."},
        "coverage_notes": ["No arbitrary cap applied: all records actually present in downloaded samples exported.",
                           "Upstream datasets are larger; this scope is the complete downloaded local sample, not their full upstream corpora.",
                           "Full trace messages and patches included in extra.trace, with local artifact metadata. System prompts and commands are inert research data.",
                           "All six source-only full articles are included in article pairs; no extra unpaired source duplicates.",
                           "Only the existing CogGen exact-query match is a same-task human/AI pair; no semantic equivalence assumed.",
                           "Code2Doc is unpaired existing documentation with full code context; ResearcherBench/DRB II rubrics are context, not human prose alternatives."]}
    export.last_report = paths(report)
    return paths(list(summaries.values()))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    with args.output.open("w", encoding="utf-8") as f:
        summaries = export(args.root, lambda row: f.write(json.dumps(row, ensure_ascii=False) + "\n"))
    args.report.write_text(js(export.last_report) + "\n", encoding="utf-8")
    print(js({"records": sum(s["count"] for s in summaries), "collections": summaries,
              "output": str(args.output), "report": str(args.report)}))


if __name__ == "__main__":
    main()

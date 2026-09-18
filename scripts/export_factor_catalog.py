"""Export a metadata-only factor catalogue. Never loads market panels or scores.

Uses the Python standard library. Source research files are read-only inputs.
"""
from __future__ import annotations

import argparse
import ast
import collections
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import re


SOURCES = {
    "classic": "经典量价", "alpha158": "Alpha158 简化集", "alpha101": "Alpha101 插件",
    "alpha191": "Alpha191 插件", "calendar": "因子日历插件", "legacy": "旧框架因子",
    "gp": "遗传规划", "llm": "模型提案", "expand": "程序改造", "crossover": "交叉复合",
    "minute": "分钟聚合", "pv2_item2": "A15 动量探索", "pv2_item3": "A15 条件反转探索",
    "pv2_item4": "A15 隔夜日内探索", "pv2_item5": "A15 成交量结构探索",
}
RESULT_KEYS = (
    "status", "direction", "train_t", "train_mean_rank_ic", "target_mean_rank_ic",
    "target_worst_rank_ic", "annual_rank_ic", "coverage", "max_pool_corr", "redundant_with",
    "failure_class", "in_pool", "approx_indneutralize", "plugin", "style_exposure", "saved",
)
DEFINITION_KEYS = (
    "id", "name", "source", "mechanism_id", "expression", "canonical", "plugin", "transform",
    "parents", "composite", "hypothesis", "expected_sign", "why_different", "falsifier", "batch", "created",
)


def digest(b):
    return hashlib.sha256(b).hexdigest()


def clean(x):
    if isinstance(x, float) and not math.isfinite(x):
        return None
    if isinstance(x, dict):
        return {k: clean(v) for k, v in x.items()}
    if isinstance(x, list):
        return [clean(v) for v in x]
    return x


def md(x):
    return str(x if x is not None else "—").replace("|", "&#124;").replace("\n", " ").replace("<", "&lt;").replace(">", "&gt;")


def num(x):
    return f"{x:.4f}" if isinstance(x, (int, float)) and math.isfinite(x) else "—"


def literal(path, name):
    for node in ast.parse(path.read_text(encoding="utf-8-sig")).body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise ValueError(f"missing literal {name}")


def export(args):
    root, repo, out = Path(args.research_root), Path(args.source_repo), Path(args.output_repo)
    evidence = {}

    def read(path, label):
        data = path.read_bytes()
        evidence[label] = {"sha256": digest(data), "bytes": len(data)}
        return json.loads(data.decode("utf-8-sig"))

    raw = (root / "candidates.jsonl").read_bytes()
    evidence["research/candidates.jsonl"] = {"sha256": digest(raw), "bytes": len(raw)}
    candidates = [json.loads(s) for s in raw.decode("utf-8-sig").splitlines() if s.strip()]
    by = {c["id"]: c for c in candidates}
    if len(by) != len(candidates):
        raise ValueError("duplicate candidate IDs")
    state = read(root / "state.json", "research/state.json")
    protocol = read(root / "protocol.json", "research/protocol.json")
    for filename in ("dsl.py", "expand.py", "external.py", "crossover.py", "cli.py", "panel.py", "minute_features.py"):
        relative = Path("src/quanta_agents/factor_lab_a") / filename
        payload = (repo / relative).read_bytes()
        evidence[f"source/{relative.as_posix()}"] = {"sha256": digest(payload), "bytes": len(payload)}
        if (out / relative).exists() and digest((out / relative).read_bytes()) != digest(payload):
            raise ValueError(f"published factor implementation differs from source: {filename}")
    sets = {}
    for name, filename in [("active_396", "combinations_v11_396_blend51020.json"),
                           ("research_597", "combinations_pool_all_597_blend51020.json")]:
        rows = read(root / "batches" / filename, f"research/batches/{filename}")
        row = rows[0] if isinstance(rows, list) else rows
        ids = row["features"]
        if len(ids) != len(set(ids)) or len(ids) != row["n_features"] or set(ids) - by.keys():
            raise ValueError(f"invalid membership {name}")
        sets[name] = {"members": ids, "source": f"research/batches/{filename}",
                      "model": {k: row.get(k) for k in ("model", "target", "update", "label_blend", "day_step")}}
    pool = sorted({p.stem for p in (root / "pool_ranks").glob("*.npy")} |
                  {p.stem for p in (root / "pool").glob("*.parquet")})
    if set(pool) - by.keys():
        raise ValueError("pool contains unknown candidate IDs")
    sets["pool_current"] = {"members": pool, "source": "Store.pool_ids: pool/*.parquet union pool_ranks/*.npy"}
    active, research = set(sets["active_396"]["members"]), set(sets["research_597"]["members"])
    sets["pool_not_active"] = {"members": sorted(set(pool) - active), "source": "pool_current minus active_396"}
    sets["research_extra"] = {"members": sorted(research - active), "source": "research_597 minus active_396"}
    verified_models = []
    if args.live_root:
        for path in sorted((Path(args.live_root) / "models").glob("*/model_meta.json")):
            m = read(path, f"live/models/{path.parent.name}/model_meta.json")
            if m.get("features") != sets["active_396"]["members"]:
                raise ValueError(f"live model feature order differs: {path.parent.name}")
            verified_models.append(path.parent.name)
    print(f"Read {len(by)} definitions; checking saved result metadata...", flush=True)

    def result(cid):
        p = root / "results" / f"{cid}.json"
        if not p.exists():
            return cid, {}, None
        b = p.read_bytes()
        return cid, json.loads(b.decode("utf-8-sig")), {"sha256": digest(b), "bytes": len(b)}

    with ThreadPoolExecutor(max_workers=8) as executor:
        results = {}
        for index, (cid, res, proof) in enumerate(executor.map(result, by), 1):
            results[cid] = res
            if proof:
                evidence[f"research/results/{cid}.json"] = proof
            if index % 300 == 0:
                print(f"Read result metadata {index}/{len(by)}", flush=True)
    missing_parents = [(c["id"], p) for c in candidates for p in c.get("parents", []) if p not in by]
    if missing_parents:
        raise ValueError(f"unresolved parents: {missing_parents}")
    visiting, visited = set(), set()

    def visit(cid):
        if cid in visiting:
            raise ValueError("cyclic parent relationship")
        if cid in visited:
            return
        visiting.add(cid)
        for p in by[cid].get("parents", []):
            visit(p)
        visiting.remove(cid)
        visited.add(cid)

    for cid in by:
        visit(cid)
    selected = active | research | set(pool)
    for cid in selected:
        if results[cid].get("direction") not in (-1, 1):
            raise ValueError(f"selected factor has no frozen direction: {cid}")
    mechanisms = read(repo / "src/quanta_agents/factor_lab_a/mechanisms.json", "source/mechanisms.json")["mechanisms"]
    new_path = root / "new_mechanisms.jsonl"
    if new_path.exists():
        b = new_path.read_bytes()
        evidence["research/new_mechanisms.jsonl"] = {"sha256": digest(b), "bytes": len(b)}
        mechanisms += [json.loads(s) for s in b.decode("utf-8-sig").splitlines() if s.strip()]
    mechanisms_by_id = {m["id"]: m for m in mechanisms}
    records = []
    for cid, c in by.items():
        res = results[cid]
        kind = "composite" if c.get("composite") else "plugin" if c.get("plugin") else "dsl"
        definition = {k: c[k] for k in DEFINITION_KEYS if k in c}
        definition["kind"] = kind
        definition["formula_note"] = ("外部插件登记公式或说明；实际实现以适配器和对应外部库为准。" if kind == "plugin" else
                                      "父因子先乘各自冻结方向并作当日截面排名，再按 composite 算子组合。" if kind == "composite" else
                                      "canonical 是实际求值表达式，expression 是登记原式。")
        record = {"id": cid, "definition": definition,
                  "mechanism_name": mechanisms_by_id.get(c.get("mechanism_id"), {}).get("name", c.get("mechanism_id")),
                  "membership": {s: cid in v["members"] for s, v in sets.items()},
                  "evaluation": {k: res[k] for k in RESULT_KEYS if k in res},
                  "evaluation_available": bool(res)}
        records.append(clean(record))
    record_by = {r["id"]: r for r in records}
    docs, data = out / "docs/factors", out / "research/factors"
    docs.mkdir(parents=True, exist_ok=True)
    (docs / "details").mkdir(exist_ok=True)
    (data / "sets").mkdir(parents=True, exist_ok=True)
    outputs = []

    def write(path, value):
        text = json.dumps(clean(value), ensure_ascii=False, indent=2, allow_nan=False) + "\n" if path.suffix == ".json" else value.rstrip() + "\n"
        path.write_text(text, encoding="utf-8", newline="\n")
        outputs.append(path.relative_to(out).as_posix())

    write(data / "catalog.json", {"schema_version": 1, "records": records})
    for name, values in sets.items():
        write(data / "sets" / f"{name}.json", values)
    counts = {name: len(v["members"]) for name, v in sets.items()}
    sources = sorted({c["source"] for c in candidates})

    def link(cid, prefix="details/"):
        c = by[cid]
        return f"[{cid}]({prefix}{c['source']}.md#f-{cid})"

    def listing(ids, heading, explanation):
        lines = [f"# {heading}", "", explanation, "", "按来源、名称排列；模型输入顺序见对应 JSON 成员清单。IC 是已曝光历史单因子统计，不是因子重要性或组合增量。", "",
                 "| ID / 详情 | 名称 | 来源 | 机制标签 | 方向 | 历史均值 RankIC | 最差年 RankIC |", "|---|---|---|---|---:|---:|---:|"]
        for cid in sorted(ids, key=lambda i: (by[i]["source"], by[i]["name"], i)):
            r, c = record_by[cid], by[cid]
            e = r["evaluation"]
            lines.append(f"| {link(cid)} | {md(c['name'])} | {SOURCES[c['source']]} | {md(r['mechanism_name'])} | {e.get('direction', '—')} | {num(e.get('target_mean_rank_ic'))} | {num(e.get('target_worst_rank_ic'))} |")
        return "\n".join(lines) + "\n"

    model_note = (f"与本地 {len(verified_models)} 个最终模型的 features 顺序核对一致。" if verified_models else "本次未提供可核对的最终模型元数据。")
    write(docs / "ACTIVE_396.md", listing(sets["active_396"]["members"], "当前日频模型：396 个因子", "来自实际组合 features 清单；" + model_note))
    write(docs / "RESEARCH_597.md", listing(sets["research_597"]["members"], "研究扩展版：597 个因子", "全 A 研究扩展模型，包含分钟聚合及其衍生表达；与日频 396 版分开标识。"))
    write(docs / "POOL_NOT_ACTIVE.md", listing(sets["pool_not_active"]["members"], "已入池但不在日频 396 版中的因子", "这些成员可能属于研究 597 版，或属于后续探索；不在主模型不等于无效，入池也不等于有组合增量。"))
    for source in sources:
        lines = [f"# {SOURCES[source]}", "", "[目录总览](../README.md) · [定义与口径](../DEFINITIONS.md)", "",
                 "原假设是提案时的研究解释，可能尚未验证；原判定只表示当时实验结果。完整结构化记录见 catalog.json。", ""]
        for r in sorted((r for r in records if r["definition"]["source"] == source), key=lambda r: (r["definition"]["name"], r["id"])):
            c, e, cid = r["definition"], r["evaluation"], r["id"]
            tags = [s for s in ("active_396", "research_597", "pool_current") if r["membership"][s]]
            lines += [f'<a id="f-{cid}"></a>', "", f"## {md(c['name'])}", "",
                      f"- ID：`{cid}`；归属：{', '.join(tags) or '历史候选，未列入上述集合'}。",
                      f"- 机制：{md(r['mechanism_name'])}（登记标签，不是独立信息量判定）。",
                      f"- 类型：`{c['kind']}`；冻结方向：`{e.get('direction', '未知')}`；评价状态：`{e.get('status', '未找到结果')}`。",
                      f"- 原假设：{md(c.get('hypothesis', '未记录'))}",
                      f"- 原判定：{md(e.get('failure_class', '未记录'))}；历史均值 / 最差年 RankIC：{num(e.get('target_mean_rank_ic'))} / {num(e.get('target_worst_rank_ic'))}。",
                      "", "登记表达式或插件说明：", "", "```text", c.get("expression", ""), "```", ""]
            if c.get("canonical") != c.get("expression"):
                lines += ["规范式 / 计算标识：", "", "```text", c.get("canonical", ""), "```", ""]
            if c.get("plugin"):
                lines += [f"- 插件：`{c['plugin']}`；变换链：`{json.dumps(c.get('transform', []), ensure_ascii=False)}`。"]
            if c.get("parents"):
                lines += ["- 父因子：" + "、".join(link(p, "") for p in c["parents"]) + "。"]
            if c.get("composite"):
                lines += [f"- 复合算子：`{c['composite']['op']}`，准确语义见定义说明。"]
            if e.get("approx_indneutralize"):
                lines += ["- 实现差异：行业中性化被适配器近似为截面去均值。"]
            lines += [""]
        write(docs / "details" / f"{source}.md", "\n".join(lines))
    source_rows = []
    for source in sources:
        ids = {c["id"] for c in candidates if c["source"] == source}
        source_rows.append(f"| [{SOURCES[source]}](details/{source}.md) | {len(ids & active)} | {len(ids & research)} | {len(ids & set(pool))} | {len(ids)} |")
    plugin_counts = {s: sum(bool(by[i].get("plugin")) for i in sets[s]["members"]) for s in ("active_396", "research_597")}
    summary = f"""# QuantAgent 因子目录

整理日期：{args.snapshot_date}。依据研究目录中的实际成员清单、候选登记和已保存评价整理，本次没有重算因子或收益。

## 阅读入口

- [当前日频模型：396 个因子](ACTIVE_396.md)
- [研究扩展版：597 个因子](RESEARCH_597.md)
- [已入池但不在日频模型：{counts['pool_not_active']} 个](POOL_NOT_ACTIVE.md)
- [公式、方向、复合算子与数据口径](DEFINITIONS.md)
- [全部 {len(records)} 个登记候选的结构化目录](../../research/factors/catalog.json)
- [有序成员清单](../../research/factors/sets/) · [来源哈希与核验清单](../../research/factors/manifest.json)

## 哪些是实际使用的因子

日频模型成员数为 **{counts['active_396']}**，研究扩展版为 **{counts['research_597']}**，当前物理因子池为 **{counts['pool_current']}**。
研究版比日频版多 {counts['research_extra']} 个；因子池中另有 {counts['pool_not_active']} 个不属于日频版。
这些集合有重叠，不能相加当作独立因子总数。{model_note}

这里的“实际使用”指模型输入成员身份，不表示每棵树都使用该成员，也不表示它有正的边际 alpha；本目录没有伪造特征重要性或收益贡献。
396 与 597 是特征表达式数量，并非独立经济机制数量。标签中性化、种子融合、指数权重和组合规则也不计作新因子。

## 按生成来源分类

| 来源 | 日频396 | 研究597 | 当前池 | 全部登记候选 |
|---|---:|---:|---:|---:|
{chr(10).join(source_rows)}

“来源”回答因子从哪里生成；“机制”保留原登记标签。遗传规划、外部库和交叉复合常包含多种机制，本次不凭名称强行赋予唯一经济解释。

## 用直白的话理解当前因子

以下是日频396中的实际成员例子，用于解释研究内容；不是对全部成员的互斥分类，也不是推荐或重要性排名。

| 研究内容 | 实际成员例子 | 想测量什么 |
|---|---|---|
| 短期反转 | [rev20](details/classic.md#f-0a59417e689c8096) | 近期涨跌幅与之后收益的关系 |
| 波动与风险 | [vol20_low](details/classic.md#f-2102e7b0aa51c223) | 最近20日收益波动水平 |
| 换手与交易活跃度 | [turn20_low](details/classic.md#f-0a38584bd0558cdb) | 最近20日平均换手率 |
| 量价共同变化 | [mw_reversal_vwap20](details/llm.md#f-ba970f639369393e) | 用换手率加权的均价涨跌 |
| 持仓成本代理 | [cost_basis_dev60](details/llm.md#f-df081b65f2e74a4b) | 价格相对量价累计成本代理的偏离，并剥离市值影响 |
| 条件组合 | [size_cond_reversal20](details/llm.md#f-77d726db8cf4dc36) | 反转与市值条件的交互 |

这些是机制假设；记录中存在表现不稳、冗余和没有组合增量的情况，不能把名称当作已验证的因果解释。

## 如何理解表现

目录中的 IC 来自已保存的全 A 单因子评价：训练年 2016—2018 决定方向，2019—2024 为反复用于研究的已曝光历史。
它们不是中证500专属 IC，不是独立样本外证据，也不是固定组合中的删减增量。缺失结果保留为空，不按零处理。
候选登记的原始 status 经常一直为 pending，本目录采用 results 中的评价状态；当前池身份采用 Store.pool_ids 的文件集合，另保留历史 in_pool 标记用于核对。
旧 protocol 的日期限制是当时协议记录，不能覆盖后来研究版本；本次只读取元数据，不加载任何年份的行情和预测矩阵。

## 复现边界

日频396中有 {plugin_counts['active_396']} 个、研究597中有 {plugin_counts['research_597']} 个成员直接调用外部插件（含带变换链的插件）。
目录保留 Alpha101/191 登记公式、因子日历原说明、插件标识及变换链；登记说明不能替代插件实际实现。
外部库和行情数据仍需按[仓库依赖说明](../REPOSITORY_CONTENTS.md)准备。这里不包含行情、模型权重、逐日分数、持仓、Choice 返回数据或账户凭证。

生成命令：`python scripts/export_factor_catalog.py --research-root <研究目录> --source-repo <源代码目录> --live-root <最终模型目录的上级> --output-repo . --snapshot-date {args.snapshot_date}`。
生成器只用标准库读取定义和统计元数据；成员顺序、父代引用、父代无环、冻结方向及最终模型一致性会自动检查。
"""
    write(docs / "README.md", summary)
    transforms = literal(repo / "src/quanta_agents/factor_lab_a/expand.py", "TRANSFORMS")
    write(data / "transforms.json", transforms)
    # Detect mutation of inputs that define identity during the snapshot.
    if digest((root / "candidates.jsonl").read_bytes()) != evidence["research/candidates.jsonl"]["sha256"]:
        raise ValueError("candidate ledger changed during export")
    for name in ("active_396", "research_597"):
        relative = sets[name]["source"].removeprefix("research/")
        if digest((root / relative).read_bytes()) != evidence[sets[name]["source"]]["sha256"]:
            raise ValueError("membership changed during export")
    manifest = {"schema_version": 1, "snapshot_date": args.snapshot_date,
                "generated_utc": datetime.now(timezone.utc).isoformat(), "counts": counts,
                "registered_candidates": len(records), "saved_results": sum(bool(r) for r in results.values()),
                "state_pool_size": state.get("pool_size"), "historical_result_in_pool": sum(bool(r.get("in_pool")) for r in results.values()),
                "active_subset_of_research": active <= research, "verified_final_models": verified_models,
                "unresolved_parents": missing_parents, "parent_cycles": False,
                "metric_scope": {k: protocol.get(k) for k in ("label", "train_years", "target_years", "metric", "exposed_history")},
                "input_evidence": dict(sorted(evidence.items())),
                "generated_files": {p: {"sha256": digest((out / p).read_bytes()), "bytes": (out / p).stat().st_size} for p in sorted(outputs)}}
    write(data / "manifest.json", manifest)
    print(json.dumps({"counts": counts, "candidates": len(records), "models_verified": verified_models,
                      "files": len(outputs), "historical_in_pool": manifest["historical_result_in_pool"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--research-root", required=True)
    p.add_argument("--source-repo", required=True)
    p.add_argument("--live-root")
    p.add_argument("--output-repo", default=".")
    p.add_argument("--snapshot-date", required=True)
    export(p.parse_args())

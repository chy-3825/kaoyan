#!/usr/bin/env python3
"""Build the local 1,500-question multiple-choice study bank.

Requires pdftotext and pyarrow. The 2009 HTML source is fetched once per run;
all other source files are already under sources/raw/.
"""

from __future__ import annotations

import json
import csv
import re
import subprocess
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

import pyarrow.parquet as pq
import requests


ROOT = Path(__file__).resolve().parents[1]
PAPERS = ROOT / "sources/raw/papers"
CEVAL = ROOT / "sources/raw/ceval"
OUTPUT = ROOT / "data/questions.jsonl"

HQQT_2010_2023 = "https://m.hqqt.com/kaoyan-kaoshi/ziliaolm/1384856.html"
HQQT_2020_2026 = "https://m.hqqt.com/kaoyan-kaoshi/ziliaolm/1297044.html"
WENDU_2009_PAPER = "https://www.wendu.com/uploadfile/2017/0823/20170823032317149.pdf"
EOL_2009 = "https://kaoyan.eol.cn/shiti/zhengzhi/201605/t20160516_1398236"
CEVAL_URL = "https://huggingface.co/datasets/ceval/ceval-exam"
CMMLU_URL = "https://github.com/haonan-li/CMMLU"
CMMLU = ROOT / "sources/raw/cmmlu"

Q_START = re.compile(r"^\s*(\d{1,2})\s*[.．、]\s*(.*)$")
OPTION_START = re.compile(
    r"(?<!\S)([A-Da-d])(?:\s*[.．、:：)）]\s*|\s+(?=[\u4e00-\u9fff（(]))"
)
ANSWER_LINE = re.compile(
    r"^\s*(\d{1,2})\s*[.．、]\s*(?:([A-D]{1,4})\s*【解析】|【(?:参考)?答案】\s*([A-D]{1,4}))"
)


class ArticleText(HTMLParser):
    """Collect only the article body from the EOL 2009 article."""

    def __init__(self) -> None:
        super().__init__()
        self.depth = 0
        self.active = False
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attrs_dict = dict(attrs)
        is_article = tag == "div" and "article" in (attrs_dict.get("class") or "").split()
        if is_article:
            self.depth += 1
            self.active = True
        elif self.active and tag == "div":
            self.depth += 1
        if self.active and tag in {"p", "br", "div", "li"}:
            self.parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if self.active and tag in {"p", "div", "li"}:
            self.parts.append("\n")
        if self.active and tag == "div":
            self.depth -= 1
            if self.depth <= 0:
                self.active = False

    def handle_data(self, data: str) -> None:
        if self.active:
            self.parts.append(data)


def norm_text(text: str) -> str:
    text = text.replace("\f", "\n").replace("\u3000", " ")
    text = re.sub(r"(?m)^\s*学员专用请勿外泄\s*$", "", text)
    text = re.sub(r"(?m)^\s*第\s*\d+\s*页\s*共\s*\d+\s*页\s*$", "", text)
    text = re.sub(r"(?m)^\s*[-—]?\s*\d+\s*[-—]?\s*$", "", text)
    # Join Chinese words split across PDF line wraps while retaining spacing around Latin text.
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[\u4e00-\u9fff])", "", text)
    text = re.sub(r"(?<=[\u4e00-\u9fff])\s+(?=[，。；：！？、）》】])", "", text)
    text = re.sub(r"(?<=[，。；：！？、）》】])\s+(?=[\u4e00-\u9fff])", "", text)
    return re.sub(r"[ \t]+", " ", text).strip()


def pdf_text(path: Path) -> str:
    result = subprocess.run(
        ["pdftotext", "-layout", str(path), "-"],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


def section_bounds(text: str) -> tuple[str, str]:
    text = re.sub(r"(?m)^(\s*)2\s+5\s*([.．、])", r"\g<1>25\2", text)
    single = re.search(r"单项选择题", text)
    multi = re.search(r"(?m)^\s*二\s*[、．.]\s*多项选择题", text)
    if not multi:
        multi = re.search(r"多项选择题", text)
    if not single or not multi or multi.start() <= single.start():
        raise ValueError("could not locate the single and multiple choice sections")
    end_candidates = [
        m.start()
        for m in re.finditer(r"(?m)^\s*三\s*[、．.]\s*(?:材料)?分析题", text)
        if m.start() > multi.start()
    ]
    end_candidates.extend(
        m.start()
        for m in re.finditer(r"(?m)^\s*34\s*[.．、]", text)
        if m.start() > multi.start()
    )
    end = min(end_candidates) if end_candidates else len(text)
    return text[single.end() : multi.start()], text[multi.end() : end]


def split_question_blocks(section: str, low: int, high: int, *, trim_answer: bool = True) -> dict[int, str]:
    section = re.sub(r"(?m)^(\s*)2\s+5\s*([.．、])", r"\g<1>25\2", section)
    starts: list[tuple[int, int]] = []
    offset = 0
    for line in section.splitlines(keepends=True):
        m = Q_START.match(line)
        if m:
            number = int(m.group(1))
            tail = m.group(2)
            # In solved papers the answer heading repeats the question number.
            if low <= number <= high and "【答案】" not in tail and "【参考答案】" not in tail:
                starts.append((offset, number))
        offset += len(line)
    blocks: dict[int, str] = {}
    for i, (pos, number) in enumerate(starts):
        if number in blocks:
            continue
        end = starts[i + 1][0] if i + 1 < len(starts) else len(section)
        block = section[pos:end]
        if trim_answer:
            block = re.sub(r"【(?:参考)?答案】.*", "", block, flags=re.S)
        blocks[number] = block
    return blocks


def parse_options(block: str, number: int) -> tuple[str, dict[str, str]]:
    block = re.sub(r"(?ms)^\s*\d{1,2}\s*[.．、]\s*【(?:参考)?答案】.*$", "", block)
    block = re.sub(r"【(?:参考)?答案】.*", "", block, flags=re.S)
    lines = []
    for line in block.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.fullmatch(r"\d+", line) or "学员专用请勿外泄" in line:
            continue
        lines.append(line)
    joined = "\n".join(lines)
    joined = re.sub(r"^\s*\d{1,2}\s*[.．、]\s*", "", joined, count=1)
    matches = list(OPTION_START.finditer(joined))
    # Keep a clean stem plus A-D choices; inline and one-option-per-line layouts both work.
    expected = [m for m in matches if m.group(1).upper() in "ABCD"]
    sequence: list[re.Match[str]] = []
    for m in expected:
        if len(sequence) < 4 and (not sequence or m.group(1).upper() == "ABCD"[len(sequence)]):
            sequence.append(m)
    if len(sequence) < 4 or "".join(m.group(1).upper() for m in sequence[:4]) != "ABCD":
        raise ValueError(f"question {number}: did not find four ordered options")
    sequence = sequence[:4]
    stem = norm_text(joined[: sequence[0].start()])
    options: dict[str, str] = {}
    for idx, m in enumerate(sequence):
        end = sequence[idx + 1].start() if idx < 3 else len(joined)
        value = norm_text(joined[m.end() : end])
        if not value:
            raise ValueError(f"question {number}: empty option {m.group(1)}")
        options[m.group(1).upper()] = value
    if not stem:
        raise ValueError(f"question {number}: empty stem")
    return stem, options


def parse_answers(text: str, year: int) -> tuple[dict[int, str], dict[int, str]]:
    if year in (2024,):
        answer_pdf_keys = re.findall(r"【答案】\s*([A-D]{1,4})", text)
        single_answers = [a for a in answer_pdf_keys if len(a) == 1]
        if len(single_answers) < 16:
            raise ValueError(f"{year}: expected 16 single-choice answers, got {len(single_answers)}")
        # The available solution PDF stops after a partial multiple-choice section.
        # Cross-check and complete its key against New Oriental's published answer list.
        response = requests.get("https://kaoyan.xdf.cn/202312/13554744.html", timeout=40)
        response.raise_for_status()
        # Generic HTML text extraction for this answer-list page.
        class PlainText(HTMLParser):
            def __init__(self):
                super().__init__()
                self.parts: list[str] = []
            def handle_data(self, data: str) -> None:
                self.parts.append(data)
        plain = PlainText()
        plain.feed(response.content.decode(response.apparent_encoding or "utf-8", "replace"))
        page_text = " ".join(" ".join(plain.parts).split())
        multiple: dict[int, str] = {}
        for m in re.finditer(r"(?<!\d)(1[7-9]|2\d|3[0-3])\s*[.．、]\s*([A-D]{2,4})(?=\s|$)", page_text):
            multiple[int(m.group(1))] = m.group(2)
        if set(multiple) != set(range(17, 34)):
            raise ValueError(f"2024: incomplete independent multi-choice key: {sorted(multiple)}")
        # The answer PDF and New Oriental agree on 17-22. The PDF diverges later,
        # so use the complete answer list cross-checked against ChinaKaoyan for 17-33.
        for number in range(17, 23):
            if len(answer_pdf_keys) >= number and answer_pdf_keys[number - 1] != multiple[number]:
                raise ValueError(f"2024 Q{number}: independent answer keys disagree")
        return ({i + 1: a for i, a in enumerate(single_answers[:16])} | multiple), {}

    answer_start = 0
    if year <= 2023:
        marker = re.search(r"试题答案|试题解析", text)
        if not marker:
            raise ValueError(f"{year}: answer section not found")
        answer_start = marker.start()
    elif year == 2025:
        answer_start = 0
    else:
        marker = re.search(r"真题答案", text)
        if not marker:
            raise ValueError(f"{year}: answer section not found")
        answer_start = marker.start()

    segment = text[answer_start:]
    if year <= 2023:
        next_answer_section = re.search(r"试题答案|试题解析", segment[1:])
        if next_answer_section:
            segment = segment[: next_answer_section.start() + 1]
    analysis_heading = re.search(r"(?m)^\s*三\s*[、．.]\s*材料分析题", segment)
    if analysis_heading:
        segment = segment[: analysis_heading.start()]
    matches: list[tuple[int, str, int, int, str]] = []
    for line_match in re.finditer(r"(?m)^([^\n]+)", segment):
        line = line_match.group(1)
        m = ANSWER_LINE.match(line)
        if m and 1 <= int(m.group(1)) <= 33:
            answer = m.group(2) or m.group(3)
            if answer:
                matches.append((int(m.group(1)), answer, line_match.start(), line_match.end(), line))
    answers: dict[int, str] = {}
    explanations: dict[int, str] = {}
    for i, (number, answer, line_start, line_end, line) in enumerate(matches):
        if number in answers:
            continue
        answers[number] = answer
        if "【解析】" in line:
            marker_end = line.index("【解析】") + len("【解析】")
            explanation = line[marker_end:] + segment[line_end : matches[i + 1][2] if i + 1 < len(matches) else len(segment)]
            explanations[number] = norm_text(explanation)
    return answers, explanations


def record(
    *,
    qid: str,
    stem: str,
    options: dict[str, str],
    answer: str,
    year: int | None,
    number: int | None,
    question_type: str,
    source_type: str,
    source_name: str,
    source_url: str,
    source_license: str,
    explanation: str = "",
    topic: str = "",
    source_id: str = "",
) -> dict:
    return {
        "id": qid,
        "stem": stem,
        "options": options,
        "answer": answer,
        "explanation": explanation,
        "questionType": question_type,
        "sourceType": source_type,
        "examYear": year,
        "questionNo": number,
        "sourceName": source_name,
        "sourceUrl": source_url,
        "sourceLicense": source_license,
        "sourceTopic": topic,
        "sourceId": source_id,
    }


def ingest_exams() -> list[dict]:
    result: list[dict] = []
    for year in range(2010, 2027):
        source_pdf = PAPERS / ("2024-official.pdf" if year == 2024 else f"{year}.pdf")
        exam_text = pdf_text(source_pdf)
        single_section, multi_section = section_bounds(exam_text)
        questions = {}
        questions.update(split_question_blocks(single_section, 1, 16, trim_answer=(year != 2025)))
        questions.update(split_question_blocks(multi_section, 17, 33, trim_answer=(year != 2025)))
        if set(questions) != set(range(1, 34)):
            missing = sorted(set(range(1, 34)) - set(questions))
            raise ValueError(f"{year}: missing question numbers {missing}")

        if year == 2024:
            answer_text = pdf_text(PAPERS / "2024-iqihang-partial-answer-key.pdf")
        else:
            answer_text = exam_text
        answers, explanations = parse_answers(answer_text, year)
        if set(answers) != set(range(1, 34)):
            missing = sorted(set(range(1, 34)) - set(answers))
            raise ValueError(f"{year}: missing answer numbers {missing}; found {len(answers)}")

        source_url = HQQT_2010_2023 if year <= 2023 else HQQT_2020_2026
        if year == 2024:
            source_url = "https://xxgcxy.ztbu.edu.cn/attachment/sites/item/2024_11/05_17/caddfaec310365de.pdf"
        answer_url = (
            "https://kaoyan.xdf.cn/202312/13554744.html"
            if year == 2024
            else source_url
        )
        for number in range(1, 34):
            stem, options = parse_options(questions[number], number)
            explanation = explanations.get(number, "")
            if year == 2025:
                inline = questions[number]
                marker = inline.find("【解析】")
                if marker >= 0:
                    explanation = norm_text(inline[marker + len("【解析】") :])
                    explanation = re.split(r"三\s*[、．.]\s*(?:分析|材料)", explanation, maxsplit=1)[0].strip()
            if year == 2024 and number == 27:
                stem = stem.replace("大茧命", "大革命")
            if year == 2024 and number == 33:
                stem = stem.replace("宜布", "宣布")
            if year == 2024 and number == 11:
                stem = stem.replace("植香山", "檀香山")
            if year == 2024 and number == 28:
                stem = stem.replace("1956 年.以", "1956年，以")
            kind = "single" if number <= 16 else "multiple"
            answer = answers[number]
            if (kind == "single" and len(answer) != 1) or any(c not in "ABCD" for c in answer):
                raise ValueError(f"{year} Q{number}: answer {answer!r} does not match {kind}")
            result.append(
                record(
                    qid=f"K政治-{year}-{number:02d}",
                    stem=stem,
                    options=options,
                    answer=answer,
                    explanation=explanation,
                    year=year,
                    number=number,
                    question_type=kind,
                    source_type="past_exam",
                    source_name=f"{year}年全国硕士研究生招生考试思想政治理论真题",
                    source_url=source_url,
                    source_license="原题/解析授权状态未核实；此份数据用于个人本地备考，公开传播前请另行确认授权",
                    source_id=(
                        "single-key:https://aged-jixun-cdn.iqihang.com/2024/0830/20240830060446466.pdf;"
                        "multi-key:https://kaoyan.xdf.cn/202312/13554744.html;"
                        "cross-check:https://www.chinakaoyan.com/info/article/id/527483.shtml"
                        if year == 2024
                        else f"answer:{answer_url}"
                    ),
                )
            )
    return result


def html_article_text(url: str) -> str:
    response = requests.get(url, timeout=40)
    response.raise_for_status()
    parser = ArticleText()
    parser.feed(response.content.decode(response.apparent_encoding or "utf-8", "replace"))
    return "\n".join(parser.parts)


def ingest_2009() -> list[dict]:
    result: list[dict] = []
    page_groups = [("", 1, 8), ("_1", 9, 16), ("_2", 17, 22), ("_3", 23, 28), ("_4", 29, 33)]
    for suffix, low, high in page_groups:
        url = EOL_2009 + suffix + ".shtml"
        text = html_article_text(url)
        starts: list[tuple[int, int]] = []
        for m in re.finditer(r"(?m)^\s*(\d{1,2})\s*[.．、]\s*", text):
            number = int(m.group(1))
            if low <= number <= high:
                starts.append((m.start(), number))
        full_blocks: dict[int, str] = {}
        for i, (pos, number) in enumerate(starts):
            if number in full_blocks:
                continue
            end = starts[i + 1][0] if i + 1 < len(starts) else len(text)
            full_blocks[number] = text[pos:end]
        if set(full_blocks) != set(range(low, high + 1)):
            raise ValueError(f"2009 page {suffix or '0'}: expected {low}-{high}, got {sorted(full_blocks)}")
        for number in range(low, high + 1):
            full_block = full_blocks[number]
            answer_match = re.search(r"【答案】\s*([A-D]{1,4})", full_block)
            answer = answer_match.group(1) if answer_match else ""
            block = re.sub(r"【答案】.*", "", full_block, flags=re.S)
            stem, options = parse_options(block, number)
            if not answer or (number <= 16 and len(answer) != 1):
                raise ValueError(f"2009 Q{number}: answer missing/invalid: {answer!r}")
            result.append(
                record(
                    qid=f"K政治-2009-{number:02d}",
                    stem=stem,
                    options=options,
                    answer=answer,
                    year=2009,
                    number=number,
                    question_type="single" if number <= 16 else "multiple",
                    source_type="past_exam",
                    source_name="2009年全国硕士研究生入学统一考试思想政治理论真题",
                    source_url=url,
                    source_license="原题/解析授权状态未核实；此份数据用于个人本地备考，公开传播前请另行确认授权",
                    source_id=f"original-download:{WENDU_2009_PAPER}",
                )
            )
    return result


SUPPLEMENT_QUOTAS = {
    "ideological_and_moral_cultivation": 102,
    "mao_zedong_thought": 102,
    "marxism": 101,
    "modern_chinese_history": 101,
}
TOPIC_NAMES = {
    "ideological_and_moral_cultivation": "思想道德与法治基础",
    "mao_zedong_thought": "毛泽东思想与中国特色社会主义理论",
    "marxism": "马克思主义基本原理",
    "modern_chinese_history": "中国近现代史纲要",
}


def ingest_ceval() -> list[dict]:
    result: list[dict] = []
    seen: set[str] = set()
    for config, quota in SUPPLEMENT_QUOTAS.items():
        path = CEVAL / f"{config}-test.parquet"
        rows = pq.read_table(path).to_pylist()
        added = 0
        for row in sorted(rows, key=lambda x: x["id"]):
            stem = norm_text(row.get("question") or "")
            options = {letter: norm_text(row.get(letter) or "") for letter in "ABCD"}
            answer = re.sub(r"[^A-D]", "", str(row.get("answer") or "").upper())
            if not stem or any(not value for value in options.values()) or len(answer) != 1:
                continue
            fingerprint = re.sub(r"\s+", "", stem)
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            result.append(
                record(
                    qid=f"CEVAL-{config}-{int(row['id']):04d}",
                    stem=stem,
                    options=options,
                    answer=answer,
                    year=None,
                    number=None,
                    question_type="single",
                    source_type="supplement",
                    source_name="C-Eval 中文考试评测题库",
                    source_url=CEVAL_URL,
                    source_license="CC BY-NC-SA 4.0",
                    explanation=norm_text(row.get("explanation") or ""),
                    topic=TOPIC_NAMES[config],
                    source_id=f"ceval-exam/{config}/test#{row['id']}",
                )
            )
            added += 1
            if added == quota:
                break
        if added != quota:
            raise ValueError(f"C-Eval {config}: wanted {quota}, got {added}")
    return result


CMMLU_QUOTAS = {
    "marxist_theory": 120,
    "legal_and_moral_basis": 120,
    "chinese_history": 100,
    "high_school_politics": 80,
    "chinese_foreign_policy": 80,
}
CMMLU_TOPICS = {
    "marxist_theory": "马克思主义理论",
    "legal_and_moral_basis": "法律与道德基础",
    "chinese_history": "中国历史",
    "high_school_politics": "高中政治",
    "chinese_foreign_policy": "中国外交政策",
}
# Upstream test keys can contain annotation noise. This item defines state-monopoly
# capitalism as the fusion of bourgeois state power and monopoly capital, so the
# source answer is corrected to the matching option; the override is also recorded
# in sources/manifest.json.
CMMLU_ANSWER_OVERRIDES = {("marxist_theory", 0): "A"}
CMMLU_HISTORY = re.compile(
    r"鸦片战争|太平天国|甲午|洋务|戊戌|维新|义和团|辛亥|新文化|五四|中共|中国共产党|国民党|共产党|抗日|解放战争|新中国|中华人民共和国|改革开放|社会主义改造|民主革命|统一战线|近代中国|晚清|民国|辛丑|八国联军|北伐|长征|遵义|南京条约|孙中山|毛泽东|邓小平|新民主主义|抗日战争|延安|土地革命|清政府|光绪|北洋|卢沟桥|七七事变|国共|大革命|中国革命|(?:18|19|20)\d{2}年|1840"
)
CMMLU_HISTORY_BROAD = re.compile(r"(?:18|19|20)\d{2}年|1840|近代|晚清|民国|清末|北洋|新中国|中华人民共和国|中国革命")
CMMLU_POLICY = re.compile(
    r"毛泽东|邓小平|马克思主义|社会主义|共同富裕|中国共产党|改革开放|人民民主|所有制|国家治理|民营经济|高质量发展|公有制|经济体制|人民代表大会|党的领导|新发展|基本经济|以人民为中心|市场经济|法治|宪法|国家主权|外交|全球|和平发展|国际|中国外交|习近平|新时代|人类命运共同体"
)


def cmmlu_topic(config: str, stem: str, options: dict[str, str]) -> str:
    text = stem + " " + " ".join(options.values())
    if config == "marxist_theory":
        return "马克思主义基本原理"
    if config == "legal_and_moral_basis":
        return "思想道德与法治"
    if config == "chinese_history":
        return "中国近现代史纲要"
    if config == "high_school_politics":
        if re.search(r"爱国|道德|法律|宪法|权利|义务|公民|人生价值|诚信", text):
            return "思想道德与法治"
        if re.search(r"新时代|习近平|共同富裕|高质量发展|新发展理念|生态文明|国家治理|人类命运共同体|中国式现代化", text):
            return "习近平新时代中国特色社会主义思想概论"
        return "毛泽东思想和中国特色社会主义理论体系概论"
    # The source subject spans diplomatic history and current diplomatic principles.
    if re.search(r"(?:19|18)\d{2}|周恩来|乔冠华|尼克松|万隆会议|建交高潮|抗美援朝", text):
        return "中国近现代史纲要"
    return "习近平新时代中国特色社会主义思想概论"


def spread_rows(rows: list[tuple[int, dict]], count: int) -> list[tuple[int, dict]]:
    """Put a deterministic, evenly spaced sample first, then all remaining rows."""
    if len(rows) < count:
        raise ValueError(f"CMMLU: requested {count} rows but only {len(rows)} are eligible")
    picked: list[int] = []
    for i in range(count):
        pos = round(i * (len(rows) - 1) / max(1, count - 1))
        if pos not in picked:
            picked.append(pos)
    picked.extend(i for i in range(len(rows)) if i not in set(picked))
    return [rows[i] for i in picked]


def ingest_cmmlu(existing_records: list[dict] | None = None) -> list[dict]:
    """Select a balanced 500-question CMMLU subset and preserve dataset attribution."""
    result: list[dict] = []
    seen: set[str] = set()
    # Existing banks are already partly drawn from open test collections. Avoid exact
    # duplicate stems; if one is found, the deterministic tail of that subject fills it.
    if existing_records is not None:
        for row in existing_records:
            seen.add(re.sub(r"\s+", "", row.get("stem", "")))
    elif OUTPUT.exists():
        for line in OUTPUT.read_text(encoding="utf8").splitlines():
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            if "CMMLU" not in row.get("sourceName", ""):
                seen.add(re.sub(r"\s+", "", row.get("stem", "")))

    total_added = 0
    for config, quota in CMMLU_QUOTAS.items():
        path = CMMLU / f"{config}.csv"
        if not path.exists():
            raise FileNotFoundError(f"missing CMMLU source file: {path}")
        with path.open(encoding="utf-8", newline="") as handle:
            source_rows = list(csv.DictReader(handle))
        eligible: list[tuple[int, dict]] = []
        for row in source_rows:
            stem = norm_text(row.get("Question") or "")
            options = {letter: norm_text(row.get(letter) or "") for letter in "ABCD"}
            answer = re.sub(r"[^A-D]", "", str(row.get("Answer") or "").upper())
            if not stem or any(not value for value in options.values()) or not answer:
                continue
            body = stem + " " + " ".join(options.values())
            if config == "chinese_history" and not (CMMLU_HISTORY.search(body) or CMMLU_HISTORY_BROAD.search(body)):
                continue
            if config in {"high_school_politics", "chinese_foreign_policy"} and not CMMLU_POLICY.search(body):
                continue
            source_number = int(row.get("") or len(eligible))
            answer = CMMLU_ANSWER_OVERRIDES.get((config, source_number), answer)
            eligible.append((source_number, {"stem": stem, "options": options, "answer": answer}))

        if len(eligible) < quota:
            raise ValueError(f"CMMLU {config}: wanted {quota} suitable questions, found {len(eligible)}")
        ordered = spread_rows(eligible, quota)
        added = 0
        for source_number, item in ordered:
            fingerprint = re.sub(r"\s+", "", item["stem"])
            if fingerprint in seen:
                continue
            seen.add(fingerprint)
            topic_tag = cmmlu_topic(config, item["stem"], item["options"])
            new_record = record(
                    qid=f"CMMLU-{config}-{source_number:04d}",
                    stem=item["stem"],
                    options=item["options"],
                    answer=item["answer"],
                    year=None,
                    number=None,
                    question_type="multiple" if len(item["answer"]) > 1 else "single",
                    source_type="supplement",
                    source_name=f"CMMLU 中文多任务理解评测（{CMMLU_TOPICS[config]}）",
                    source_url=CMMLU_URL,
                    source_license="CC BY-NC-SA 4.0",
                    topic=CMMLU_TOPICS[config],
                    source_id=f"CMMLU/{config}/test#{source_number}",
                )
            new_record["topicTag"] = topic_tag
            result.append(new_record)
            added += 1
            total_added += 1
            if added == quota:
                break
        if added != quota:
            raise ValueError(f"CMMLU {config}: wanted {quota} unique questions, got {added}")
    if total_added != 500:
        raise ValueError(f"CMMLU expansion target mismatch: {total_added}")
    return result


def validate(records: list[dict]) -> None:
    ids = [r["id"] for r in records]
    if len(ids) != len(set(ids)):
        raise ValueError("duplicate IDs")
    for r in records:
        if set(r["options"]) != set("ABCD"):
            raise ValueError(f"{r['id']}: missing option")
        if not r["stem"] or not r["answer"]:
            raise ValueError(f"{r['id']}: missing stem or answer")
        if any(c not in "ABCD" for c in r["answer"]):
            raise ValueError(f"{r['id']}: invalid answer")
        if not r.get("explanation", "").strip():
            raise ValueError(f"{r['id']}: missing pre-analysis")
    exams = [r for r in records if r["sourceType"] == "past_exam"]
    expected = {(year, q) for year in range(2009, 2027) for q in range(1, 34)}
    got = {(r["examYear"], r["questionNo"]) for r in exams}
    if got != expected:
        raise ValueError(f"exam corpus mismatch: missing {len(expected - got)}, extra {len(got - expected)}")
    if len(records) != 1500:
        raise ValueError(f"expected 1500 questions, got {len(records)}")
    if sum("CMMLU" in r.get("sourceName", "") for r in records) != 500:
        raise ValueError("expected exactly 500 CMMLU supplement questions")


def main() -> None:
    records = ingest_2009() + ingest_exams() + ingest_ceval()
    records += ingest_cmmlu(records)
    from tag_questions import tag_records, write_outputs
    tag_records(records)
    from preanalysis import annotate_records
    generated_analyses = annotate_records(records)
    validate(records)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    write_outputs(records)
    print(json.dumps({"total": len(records), "generated_preanalyses": generated_analyses, "by_source_type": dict(Counter(r["sourceType"] for r in records)), "by_year": dict(Counter(str(r["examYear"]) for r in records if r["examYear"])), "output": str(OUTPUT)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()

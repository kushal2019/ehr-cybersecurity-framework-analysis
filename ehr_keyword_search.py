import argparse
import glob
import os
import re

import pymupdf
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor


KEYWORD_GROUPS = {
    "Ransomware": [
        "ransomware", "backup", "recovery", "business continuity",
        "encryption", "restore", "incident recovery", "WannaCry",
    ],
    "FHIR API Exploitation": [
        "FHIR", "HL7", "API", "interoperability", "interface",
        "endpoint", "RESTful", "health information exchange",
    ],
    "IoMT Vulnerabilities": [
        "IoT", "medical device", "firmware", "connected device",
        "patch", "operational technology", "embedded",
    ],
    "Insider Threats": [
        "insider", "privileged access", "role-based access", "monitoring",
        "authentication", "least privilege", "workforce", "credential",
    ],
    "Nation-State APT": [
        "APT", "nation", "advanced persistent", "supply chain",
        "threat intelligence", "ATT&CK", "MITRE", "nation-state",
    ],
    "NHS Applicability": [
        "NHS", "clinical", "patient", "EHR", "healthcare", "trust", "hospital",
    ],
    "GDPR Alignment": [
        "GDPR", "data protection", "privacy", "personal data", "UK GDPR",
    ],
    "Threat Modelling Integration": [
        "STRIDE", "LINDDUN", "PASTA", "threat model", "attack tree",
    ],
}

# Control reference formats used by each framework
CONTROL_PATTERNS = [
    r"\b[A-Z]{2}\.[A-Z]{2,3}-\d{2}\b",          # NIST, e.g. PR.DS-11
    r"\bA\.\d{1,2}\.\d{1,2}\b",                  # ISO 27001, e.g. A.8.13
    r"\bStandard\s+\d{1,2}(\.\d{1,2}){0,2}\b",   # DSPT, e.g. Standard 6
    r"\bCategory\s+\d{1,2}(\.[a-z]{2})?\b",      # HITRUST category
    r"\b\d{2}\.[a-z]{1,2}\b",                    # HITRUST control, e.g. 09.l
]

HEALTHCARE_TERMS = [
    "NHS", "clinical", "patient", "EHR", "healthcare", "hospital",
    "trust", "care record", "GP", "FHIR", "HL7",
]

THREAT_ORDER = [
    "Ransomware", "FHIR API Exploitation", "IoMT Vulnerabilities",
    "Insider Threats", "Nation-State APT",
]


def find_control_id(text):
    for pattern in CONTROL_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return None


def find_nearest_heading(page_text, idx):
    # fall back to the closest short line above that looks like a heading
    lines = [l.strip() for l in page_text[:idx].split("\n") if l.strip()]
    for line in reversed(lines[-15:]):
        if 3 < len(line) < 60 and not line.endswith("."):
            if line.isupper() or line.istitle():
                return line
    return None


def get_sentence(page_text, idx, length):
    start = page_text.rfind(".", 0, idx)
    start = start + 1 if start != -1 else max(0, idx - 150)
    end = page_text.find(".", idx + length)
    end = end + 1 if end != -1 else min(len(page_text), idx + 200)

    sentence = re.sub(r"\s+", " ", page_text[start:end].strip())
    return sentence[:350] + "..." if len(sentence) > 350 else sentence


def healthcare_flag(context):
    # only flags nearby terms, the relevance still needs checking by hand
    found = [t for t in HEALTHCARE_TERMS if t.lower() in context.lower()]
    if found:
        return f"Healthcare terms nearby ({', '.join(found[:3])}), check context"
    return "No healthcare terms nearby, likely generic, check context"


def search_pdf(pdf_path, framework):
    doc = pymupdf.open(pdf_path)
    pages = [page.get_text() for page in doc]
    doc.close()

    results = []
    stats = {
        "framework": framework,
        "pdf": os.path.basename(pdf_path),
        "pages": len(pages),
        "keywords_searched": sum(len(k) for k in KEYWORD_GROUPS.values()),
        "keywords_found": 0,
        "keywords_absent": 0,
        "total_matches": 0,
        "by_group": {},
    }

    for group, keywords in KEYWORD_GROUPS.items():
        found_in_group = 0

        for keyword in keywords:
            hits = []
            for page_no, text in enumerate(pages, start=1):
                lower = text.lower()
                idx = lower.find(keyword.lower())
                while idx != -1 and len(hits) < 3:  # keep the first 3 hits per keyword
                    window = text[max(0, idx - 600):idx + 600]
                    control = find_control_id(window) or find_nearest_heading(text, idx)
                    hits.append({
                        "page": page_no,
                        "control": control or "(no control ID nearby)",
                        "text": get_sentence(text, idx, len(keyword)),
                        "flag": healthcare_flag(window),
                    })
                    idx = lower.find(keyword.lower(), idx + len(keyword))

            if hits:
                stats["keywords_found"] += 1
                stats["total_matches"] += len(hits)
                found_in_group += 1
                for h in hits:
                    results.append({"group": group, "keyword": keyword, "found": "Yes", **h})
            else:
                stats["keywords_absent"] += 1
                results.append({
                    "group": group, "keyword": keyword, "found": "No",
                    "page": "-", "control": "-",
                    "text": "Not found in this document",
                    "flag": "Absence supports a Weak rating",
                })

        stats["by_group"][group] = f"{found_in_group}/{len(keywords)} keywords found"

    return results, stats


def write_notebook(results, stats, out_path):
    lines = [
        f"Keyword search record: {stats['framework']}",
        f"Source document: {stats['pdf']}",
        f"Pages searched: {stats['pages']}",
        f"Keywords applied: {stats['keywords_searched']}",
        "",
        "Note: this output locates evidence only. Ratings are assigned by reading each passage.",
        "",
    ]

    current = None
    for r in results:
        if r["group"] != current:
            current = r["group"]
            lines += ["", current]

        lines += [
            "",
            f"Search word:       {r['keyword']}",
            f"Found:             {r['found']}",
            f"Page:              {r['page']}",
            f"Section/control:   {r['control']}",
            f"What it says:      {r['text']}",
            f"EHR/NHS specific:  {r['flag']}",
        ]

    lines += [
        "",
        "Summary",
        f"Keywords found:  {stats['keywords_found']} of {stats['keywords_searched']}",
        f"Keywords absent: {stats['keywords_absent']}",
        f"Total matches:   {stats['total_matches']}",
        "",
    ]
    for group, summary in stats["by_group"].items():
        lines.append(f"  {group:32} {summary}")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def shade(cell, colour):
    tc_pr = cell._tc.get_or_add_tcPr()
    fill = OxmlElement("w:shd")
    fill.set(qn("w:val"), "clear")
    fill.set(qn("w:color"), "auto")
    fill.set(qn("w:fill"), colour)
    tc_pr.append(fill)


def write_cell(cell, text, bold=False, colour=None, size=8):
    cell.text = ""
    para = cell.paragraphs[0]
    para.paragraph_format.line_spacing = 1.0
    para.paragraph_format.space_after = Pt(0)
    para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    run = para.add_run(text)
    run.font.size = Pt(size)
    run.bold = bold
    if colour:
        run.font.color.rgb = RGBColor.from_string(colour)


def write_appendix_docx(all_results, out_path):
    doc = Document()

    # A4 portrait with the handbook margins
    section = doc.sections[0]
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.left_margin = Inches(1.5)
    section.right_margin = Inches(1)
    section.top_margin = Inches(1)
    section.bottom_margin = Inches(1)

    # body text: 12pt, 1.5 spacing, left aligned
    normal = doc.styles["Normal"]
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = 1.5
    normal.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.LEFT

    doc.add_heading("Appendix A: Data Extraction Table", level=1)
    doc.add_paragraph(
        "Keywords, pages, control references and evidence were located by the search tool."
    )

    headers = ["Threat category", "Keywords searched", "Found", "Page(s)",
               "Control reference", "Evidence"]

    for n, (framework, results) in enumerate(all_results, start=1):
        doc.add_heading(f"A.{n} {framework}", level=2)

        table = doc.add_table(rows=1, cols=len(headers))
        table.style = "Table Grid"

        for cell, heading in zip(table.rows[0].cells, headers):
            write_cell(cell, heading, bold=True, colour="000000", size=8)
            shade(cell, "D9D9D9")

        for threat in THREAT_ORDER:
            rows = [r for r in results if r["group"] == threat]
            if not rows:
                continue

            keywords = sorted({r["keyword"] for r in rows})
            hits = [r for r in rows if r["found"] == "Yes"]
            keywords_hit = {h["keyword"] for h in hits}
            pages = sorted({str(r["page"]) for r in hits}, key=lambda p: (len(p), p))
            controls = sorted({r["control"] for r in hits if "no control" not in r["control"]})

            if not hits:
                found = "No"
            elif len(keywords_hit) < len(keywords):
                found = "Partial"
            else:
                found = "Yes"

            if hits:
                evidence = "\n".join(f"p.{h['page']}: {h['text'][:120]}" for h in hits[:2])
            else:
                evidence = "No matches, absence supports a Weak rating"

            cells = table.add_row().cells
            write_cell(cells[0], threat, bold=True)
            shade(cells[0], "F2F2F2")
            write_cell(cells[1], ", ".join(keywords))
            write_cell(cells[2], f"{found} ({len(keywords_hit)}/{len(keywords)})")
            write_cell(cells[3], ", ".join("p." + p for p in pages[:6]) or "None")
            write_cell(cells[4], "; ".join(controls[:5]) or "None found")
            write_cell(cells[5], evidence)

        # give the evidence column most of the space
        widths = [1.05, 1.1, 0.5, 0.72, 0.9, 1.5]
        table.autofit = False
        layout = OxmlElement("w:tblLayout")
        layout.set(qn("w:type"), "fixed")
        table._tbl.tblPr.append(layout)
        for i, w in enumerate(widths):
            table.columns[i].width = Inches(w)
            for cell in table.columns[i].cells:
                cell.width = Inches(w)

        doc.add_paragraph()

    doc.save(out_path)


def process(pdf_path, framework):
    print(f"\nSearching {framework} ({os.path.basename(pdf_path)})")
    results, stats = search_pdf(pdf_path, framework)

    out_path = "./" + re.sub(r"[^\w\-]", "_", framework) + "_notebook.txt"
    write_notebook(results, stats, out_path)

    print(f"  {stats['pages']} pages, "
          f"{stats['keywords_found']}/{stats['keywords_searched']} keywords found, "
          f"{stats['total_matches']} matches")
    print(f"  saved {out_path}")
    return results


def main():
    parser = argparse.ArgumentParser(description="Search framework PDFs for EHR threat keywords.")
    parser.add_argument("--pdf", help="path to a single PDF")
    parser.add_argument("--framework", help='framework name, e.g. "NIST CSF 2.0"')
    parser.add_argument("--batch", metavar="FOLDER", help="process every PDF in a folder")
    parser.add_argument("--appendix", action="store_true", help="also write Appendix A as a Word document")
    args = parser.parse_args()

    all_results = []

    if args.batch:
        pdfs = sorted(glob.glob(os.path.join(args.batch, "*.pdf")))
        if not pdfs:
            print(f"No PDFs found in {args.batch}")
            return
        print(f"Found {len(pdfs)} PDF(s)")
        for pdf in pdfs:
            name = os.path.splitext(os.path.basename(pdf))[0]
            all_results.append((name, process(pdf, name)))

    elif args.pdf and args.framework:
        if not os.path.exists(args.pdf):
            print(f"PDF not found: {args.pdf}")
            return
        all_results.append((args.framework, process(args.pdf, args.framework)))

    else:
        parser.error("use --batch FOLDER, or both --pdf and --framework")

    if args.appendix:
        write_appendix_docx(all_results, "./Appendix_A_Keyword_Search.docx")
        print("\nsaved Appendix_A_Keyword_Search.docx")

if __name__ == "__main__":
    main()

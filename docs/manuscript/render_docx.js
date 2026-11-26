// Renders docs/manuscript/manuscript.json (made by build_manuscript.py) into
// Milestone2_Manuscript_Draft.docx at the repository root.
// With the argument 3 it renders manuscript_m3.json into submission/milestone3/Milestone3_Report.docx.
// With the argument 4 it renders manuscript_m4.json (build_manuscript_m4.py) into
// submission/milestone4/Milestone4_Report.docx.
// With the argument 5 it renders manuscript_m5.json (build_manuscript_m5.py) into
// submission/milestone5/Milestone5_Report.docx in an IEEE conference layout (renderIEEE below).
// Run from the repository root:  node docs/manuscript/render_docx.js [2|3|4|5]
// Needs the 'docx' npm package (npm install docx).
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, ImageRun, LevelFormat, Footer, PageNumber, TableLayoutType,
  SectionType, VerticalAlign,
} = require("docx");

const ROOT = path.resolve(__dirname, "..", "..");
const MILESTONE = process.argv[2] || "2";
const SETTINGS = {
  "2": { json: "manuscript.json", out: path.join(ROOT, "Milestone2_Manuscript_Draft.docx"),
         footer: "Trans-Boundary Smog Prediction, Milestone 02", title: "Trans-Boundary Smog Prediction: Milestone 2 report" },
  "3": { json: "manuscript_m3.json", out: path.join(ROOT, "submission", "milestone3", "Milestone3_Report.docx"),
         footer: "Trans-Boundary Smog Prediction, Milestone 03", title: "Trans-Boundary Smog Prediction: Milestone 3 report" },
  "4": { json: "manuscript_m4.json", out: path.join(ROOT, "submission", "milestone4", "Milestone4_Report.docx"),
         footer: "Forecasting trans-boundary smog spikes in Punjab, Milestone 04", title: "Forecasting Trans-Boundary Smog Spikes in Punjab" },
  "5": { json: "manuscript_m5.json", out: path.join(ROOT, "submission", "milestone5", "Milestone5_Report.docx"),
         footer: "Milestone 05", title: "Forecasting Trans-Boundary Smog Spikes in Punjab under Data Drift", style: "ieee" },
}[MILESTONE];
if (!SETTINGS) throw new Error("milestone must be 2, 3, 4 or 5, got " + MILESTONE);
const model = JSON.parse(fs.readFileSync(path.join(__dirname, SETTINGS.json), "utf8"));
// Layout follows the team's stream reports (Report_Weather.docx): US Letter, Arial, numbered blue headings
const FONT = "Arial";
const NAVY = "1F3864";
const BLUE = "2E5C8A";
const TEXT_W = 9792; // Letter (12240) minus 2 x 1224 margins, in DXA

// "**bold** and *italic*" -> TextRuns
function runs(text, opts = {}) {
  const out = [];
  const re = /(\*\*[^*]+\*\*|\*[^*]+\*)/g;
  let last = 0, m;
  while ((m = re.exec(text)) !== null) {
    if (m.index > last) out.push(new TextRun({ text: text.slice(last, m.index), ...opts }));
    const tok = m[0];
    if (tok.startsWith("**")) out.push(new TextRun({ text: tok.slice(2, -2), bold: true, ...opts }));
    else out.push(new TextRun({ text: tok.slice(1, -1), italics: true, ...opts }));
    last = m.index + tok.length;
  }
  if (last < text.length) out.push(new TextRun({ text: text.slice(last), ...opts }));
  return out;
}

function pngSize(file) {
  const b = fs.readFileSync(file);
  return { w: b.readUInt32BE(16), h: b.readUInt32BE(20) };
}

const border = { style: BorderStyle.SINGLE, size: 4, color: "9FB3C8" };
const borders = { top: border, bottom: border, left: border, right: border };

function makeTable(b) {
  const size = Math.round((b.font || 8) * 2);
  const total = b.widths.reduce((a, c) => a + c, 0);
  const widths = b.widths.map((w) => Math.round((w * TEXT_W) / total));
  widths[widths.length - 1] += TEXT_W - widths.reduce((a, c) => a + c, 0);
  const cell = (txt, i, header) => new TableCell({
    borders,
    width: { size: widths[i], type: WidthType.DXA },
    shading: header ? { fill: "DCE6F2", type: ShadingType.CLEAR, color: "auto" } : undefined,
    margins: { top: 30, bottom: 30, left: 70, right: 70 },
    children: [new Paragraph({ spacing: { before: 0, after: 0 }, children: runs(txt, { size, bold: header || undefined, font: FONT }) })],
  });
  const rows = [new TableRow({ tableHeader: true, children: b.header.map((h, i) => cell(h, i, true)) })];
  for (const r of b.rows) rows.push(new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, i, false)) }));
  return new Table({ width: { size: TEXT_W, type: WidthType.DXA }, columnWidths: widths, layout: TableLayoutType.FIXED, rows });
}

if (SETTINGS.style === "ieee") renderIEEE(model);
else renderAPA(model);

function renderAPA(model) {
const children = [];
for (const b of model.blocks) {
  switch (b.t) {
    case "title":
      children.push(new Paragraph({ spacing: { after: 60 },
        children: [new TextRun({ text: b.text, bold: true, size: 34, color: NAVY, font: FONT })] }));
      break;
    case "subtitle":
      children.push(new Paragraph({ spacing: { after: 60 },
        children: [new TextRun({ text: b.text, bold: true, size: 20, font: FONT })] }));
      break;
    case "authors":
      children.push(new Paragraph({ spacing: { after: 160 },
        children: [new TextRun({ text: b.text, size: 17, color: "7F7F7F", font: FONT })] }));
      break;
    case "h1":
      children.push(new Paragraph({ heading: HeadingLevel.HEADING_1, children: [new TextRun({ text: b.text })] }));
      break;
    case "h2":
      children.push(new Paragraph({ heading: HeadingLevel.HEADING_2, children: [new TextRun({ text: b.text })] }));
      break;
    case "h3":
      children.push(new Paragraph({ heading: HeadingLevel.HEADING_3, children: [new TextRun({ text: b.text })] }));
      break;
    case "p":
      children.push(new Paragraph({ spacing: { after: 100, line: 264 }, children: runs(b.text) }));
      break;
    case "bullets":
      for (const it of b.items)
        children.push(new Paragraph({ numbering: { reference: "bullets", level: 0 },
          spacing: { after: 40, line: 264 }, children: runs(it) }));
      break;
    case "keywords":
      children.push(new Paragraph({ spacing: { after: 200 },
        children: [new TextRun({ text: "Keywords: ", bold: true, size: 18, font: FONT }), ...runs(b.text, { size: 18 })] }));
      break;
    case "abstract":
      children.push(new Paragraph({ spacing: { before: 120, after: 60 },
        children: [new TextRun({ text: "Abstract", bold: true, size: 21, color: NAVY, font: FONT })] }));
      for (const it of b.items)
        children.push(new Paragraph({ spacing: { after: 60, line: 252 }, indent: { left: 360, right: 360 }, children: runs(it, { size: 18 }) }));
      break;
    case "apa":
      // APA 7 reference list: alphabetical, hanging indent, no numbers
      for (const it of b.items)
        children.push(new Paragraph({ spacing: { after: 70, line: 252 }, indent: { left: 480, hanging: 480 },
          children: runs(it, { size: 17 }) }));
      break;
    case "pagebreak":
      children.push(new Paragraph({ pageBreakBefore: true, children: [] }));
      break;
    case "refs":
      for (const it of b.items)
        children.push(new Paragraph({ numbering: { reference: "refs", level: 0 }, spacing: { after: 40 },
          children: runs(it, { size: 17 }) }));
      break;
    case "table":
      children.push(new Paragraph({ keepNext: true, spacing: { before: 120, after: 60 }, children: runs(b.caption, { size: 17 }) }));
      children.push(makeTable(b));
      children.push(new Paragraph({ spacing: { after: 100 }, children: b.note ? runs(b.note, { size: 16, italics: true }) : [] }));
      break;
    case "figure": {
      const { w, h } = pngSize(b.path);
      const wpx = Math.round(b.width_in * 96);
      const hpx = Math.round((wpx * h) / w);
      children.push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 40 },
        children: [new ImageRun({ type: "png", data: fs.readFileSync(b.path), transformation: { width: wpx, height: hpx },
          altText: { title: path.basename(b.path), description: b.caption.replace(/\*/g, ""), name: path.basename(b.path) } })] }));
      children.push(new Paragraph({ spacing: { after: 160 }, children: runs(b.caption, { size: 17 }) }));
      break;
    }
    default:
      throw new Error("unknown block " + b.t);
  }
}

const doc = new Document({
  creator: "Munir Tariq, Ismail Nooruddin, Bilal Ayub",
  title: SETTINGS.title,
  styles: {
    default: { document: { run: { font: FONT, size: 19 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 26, bold: true, font: FONT, color: NAVY }, paragraph: { spacing: { before: 240, after: 100 }, outlineLevel: 0, keepNext: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 21, bold: true, font: FONT, color: BLUE }, paragraph: { spacing: { before: 160, after: 70 }, outlineLevel: 1, keepNext: true } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { size: 19, bold: true, font: FONT }, paragraph: { spacing: { before: 120, after: 60 }, outlineLevel: 2, keepNext: true } },
    ],
  },
  numbering: { config: [
    { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 360, hanging: 220 } } } }] },
    { reference: "refs", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "[%1]", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 500, hanging: 500 } } } }] },
  ] },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1000, bottom: 950, left: 1224, right: 1224 } } },
    footers: { default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: SETTINGS.footer + "   |   Page ", size: 15, color: "7F7F7F" }),
                 new TextRun({ children: [PageNumber.CURRENT], size: 15, color: "7F7F7F" })] })] }) },
    children,
  }],
});

write(doc);
}

function write(doc) {
  Packer.toBuffer(doc).then((buf) => {
    const out = SETTINGS.out;
    fs.mkdirSync(path.dirname(out), { recursive: true });
    fs.writeFileSync(out, buf);
    console.log("wrote", out);
  });
}

// ---------------------------------------------------------------------------------------------
// IEEE conference layout (Milestone 5): US Letter, Times New Roman 10 pt, one-column title block,
// two-column body (3.5 in columns, 0.25 in gap), one-column appendix on a new page.
// Blocks: title, authors, affil, abstract{items}, indexterms, section{layout: "two"|"one", newpage},
// h1 (roman numeral in the text), h2 (letter in the text), p, bullets,
// table{label, caption, header, rows, widths, note, font}, figure{path, caption, width_in}, ieee_refs{items}.
// ---------------------------------------------------------------------------------------------
function renderIEEE(model) {
  const F = "Times New Roman";
  const PAGE_W = 12240, MARGIN_LR = 900;               // 0.625 in side margins
  const FULL_W = PAGE_W - 2 * MARGIN_LR;               // 10440 DXA = 7.25 in
  const GAP = 360;                                     // 0.25 in between columns
  const COL_W = (FULL_W - GAP) / 2;                    // 5040 DXA = 3.5 in
  const sz = (pt) => Math.round(pt * 2);
  const EM_DASH = "—";
  const sections = [];
  let current = { layout: "one", newpage: false, children: [] };
  const push = (x) => current.children.push(x);
  const width = () => (current.layout === "two" ? COL_W : FULL_W);
  const rule = { style: BorderStyle.SINGLE, size: 4, color: "000000" };
  const none = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };

  function table(b) {
    const W = width();
    const size = sz(b.font || 7.5);
    const total = b.widths.reduce((a, c) => a + c, 0);
    const widths = b.widths.map((w) => Math.round((w * W) / total));
    widths[widths.length - 1] += W - widths.reduce((a, c) => a + c, 0);
    const last = b.rows.length - 1;
    const cell = (txt, i, header, isLast) => new TableCell({
      borders: { top: header ? rule : none, bottom: header || isLast ? rule : none, left: none, right: none },
      width: { size: widths[i], type: WidthType.DXA },
      verticalAlign: VerticalAlign.CENTER,
      margins: { top: 15, bottom: 15, left: 45, right: 45 },
      children: [new Paragraph({ spacing: { before: 0, after: 0 }, alignment: (i === 0 || b.align === "left") ? AlignmentType.LEFT : AlignmentType.CENTER,
        children: runs(txt, { size, bold: header || undefined, font: F }) })],
    });
    const rows = [new TableRow({ tableHeader: true, children: b.header.map((h, i) => cell(h, i, true, false)) })];
    b.rows.forEach((r, k) => rows.push(new TableRow({ cantSplit: true, children: r.map((c, i) => cell(c, i, false, k === last)) })));
    return new Table({ width: { size: W, type: WidthType.DXA }, columnWidths: widths, layout: TableLayoutType.FIXED, rows });
  }

  for (const b of model.blocks) {
    switch (b.t) {
      case "section":
        if (current.children.length) sections.push(current);
        current = { layout: b.layout, newpage: !!b.newpage, children: [] };
        break;
      case "title":
        push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
          children: [new TextRun({ text: b.text, size: sz(22), font: F })] }));
        break;
      case "authors":
        push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 20 },
          children: [new TextRun({ text: b.text, size: sz(11), font: F })] }));
        break;
      case "affil":
        push(new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 200 },
          children: [new TextRun({ text: b.text, size: sz(9.5), italics: true, font: F })] }));
        break;
      case "abstract":
        b.items.forEach((it, k) => push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 40 },
          children: [...(k === 0 ? [new TextRun({ text: "Abstract", bold: true, italics: true, size: sz(9), font: F }),
                                    new TextRun({ text: EM_DASH, bold: true, size: sz(9), font: F })] : []),
                     ...runs(it, { size: sz(9), bold: true, font: F })] })));
        break;
      case "indexterms":
        push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 160 },
          children: [new TextRun({ text: "Index Terms", bold: true, italics: true, size: sz(9), font: F }),
                     new TextRun({ text: EM_DASH, bold: true, size: sz(9), font: F }),
                     ...runs(b.text, { size: sz(9), bold: true, font: F })] }));
        break;
      case "h1":
        push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 160, after: 60 },
          children: [new TextRun({ text: b.text, smallCaps: true, size: sz(10), font: F })] }));
        break;
      case "h2":
        push(new Paragraph({ keepNext: true, spacing: { before: 80, after: 40 },
          children: [new TextRun({ text: b.text, italics: true, size: sz(10), font: F })] }));
        break;
      case "p":
        push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 0, line: 240 },
          indent: { firstLine: b.noindent ? 0 : 200 }, children: runs(b.text, { size: sz(10), font: F }) }));
        break;
      case "bullets":
        for (const it of b.items)
          push(new Paragraph({ numbering: { reference: "ieee-bullets", level: 0 }, alignment: AlignmentType.JUSTIFIED,
            spacing: { after: 0, line: 240 }, children: runs(it, { size: sz(10), font: F }) }));
        break;
      case "table":
        push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 120, after: 0 },
          children: [new TextRun({ text: b.label, size: sz(8), font: F })] }));
        push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { after: 40 },
          children: runs(b.caption, { size: sz(8), smallCaps: true, font: F }) }));
        push(table(b));
        push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { before: 20, after: 120 },
          children: b.note ? runs(b.note, { size: sz(7.5), font: F }) : [] }));
        break;
      case "figure": {
        const { w, h } = pngSize(b.path);
        const wIn = Math.min(b.width_in, width() / 1440);
        const wpx = Math.round(wIn * 96);
        const hpx = Math.round((wpx * h) / w);
        push(new Paragraph({ alignment: AlignmentType.CENTER, keepNext: true, spacing: { before: 100, after: 20 },
          children: [new ImageRun({ type: "png", data: fs.readFileSync(b.path), transformation: { width: wpx, height: hpx },
            altText: { title: path.basename(b.path), description: b.caption.replace(/\*/g, ""), name: path.basename(b.path) } })] }));
        push(new Paragraph({ alignment: AlignmentType.JUSTIFIED, spacing: { after: 120 },
          children: runs(b.caption, { size: sz(8), font: F }) }));
        break;
      }
      case "ieee_refs":
        for (const it of b.items)
          push(new Paragraph({ numbering: { reference: "ieee-refs", level: 0 }, alignment: AlignmentType.JUSTIFIED,
            spacing: { after: 20 }, children: runs(it, { size: sz(8), font: F }) }));
        break;
      default:
        throw new Error("unknown IEEE block " + b.t);
    }
  }
  sections.push(current);

  const footer = new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
    children: [new TextRun({ children: [PageNumber.CURRENT], size: sz(8), font: F })] })] });
  const doc = new Document({
    creator: "Munir Tariq, Ismail Nooruddin, Bilal Ayub",
    title: SETTINGS.title,
    styles: { default: { document: { run: { font: F, size: sz(10) } } } },
    numbering: { config: [
      { reference: "ieee-bullets", levels: [{ level: 0, format: LevelFormat.BULLET, text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 240, hanging: 160 } } } }] },
      { reference: "ieee-refs", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "[%1]", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 400, hanging: 400 } } } }] },
    ] },
    sections: sections.map((sec, k) => ({
      properties: {
        type: k === 0 ? undefined : (sec.newpage ? SectionType.NEXT_PAGE : SectionType.CONTINUOUS),
        page: { size: { width: PAGE_W, height: 15840 }, margin: { top: 1080, bottom: 1440, left: MARGIN_LR, right: MARGIN_LR } },
        column: sec.layout === "two" ? { count: 2, space: GAP, equalWidth: true } : { count: 1 },
      },
      footers: { default: footer },
      children: sec.children,
    })),
  });
  write(doc);
}

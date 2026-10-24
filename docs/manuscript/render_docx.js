// Renders docs/manuscript/manuscript.json (made by build_manuscript.py) into
// Milestone2_Manuscript_Draft.docx at the repository root.
// With the argument 3 it renders manuscript_m3.json into submission/milestone3/Milestone3_Report.docx.
// Run from the repository root:  node docs/manuscript/render_docx.js [2|3]
// Needs the 'docx' npm package (npm install docx).
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, ImageRun, LevelFormat, Footer, PageNumber, TableLayoutType,
} = require("docx");

const ROOT = path.resolve(__dirname, "..", "..");
const MILESTONE = process.argv[2] || "2";
const SETTINGS = {
  "2": { json: "manuscript.json", out: path.join(ROOT, "Milestone2_Manuscript_Draft.docx"),
         footer: "Trans-Boundary Smog Prediction, Milestone 02", title: "Trans-Boundary Smog Prediction: Milestone 2 report" },
  "3": { json: "manuscript_m3.json", out: path.join(ROOT, "submission", "milestone3", "Milestone3_Report.docx"),
         footer: "Trans-Boundary Smog Prediction, Milestone 03", title: "Trans-Boundary Smog Prediction: Milestone 3 report" },
}[MILESTONE];
if (!SETTINGS) throw new Error("milestone must be 2 or 3, got " + MILESTONE);
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

Packer.toBuffer(doc).then((buf) => {
  const out = SETTINGS.out;
  fs.mkdirSync(path.dirname(out), { recursive: true });
  fs.writeFileSync(out, buf);
  console.log("wrote", out);
});

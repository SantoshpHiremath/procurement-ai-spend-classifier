const pptxgen = require("pptxgenjs");

// Palette: "Ocean Gradient" family, adapted — procurement/industrial feel,
// one dominant deep navy-teal, ice-blue supporting tone, sharp amber accent
// for flagged-risk callouts.
const NAVY = "0B2B3C";
const TEAL = "1C7293";
const ICE = "CADCFC";
const AMBER = "E8A33D";
const OFFWHITE = "F7F9FA";
const DARKTEXT = "16242C";
const MUTED = "5B7480";

let pres = new pptxgen();
pres.layout = "LAYOUT_WIDE"; // 13.3 x 7.5

const FONT_HEAD = "Cambria";
const FONT_BODY = "Calibri";

function addFooter(slide, pageNum) {
  slide.addText("Procurement Spend Classification & Data-Quality AI Tool — Illustrative synthetic-data project", {
    x: 0.5, y: 7.15, w: 9.5, h: 0.3, fontFace: FONT_BODY, fontSize: 9, color: MUTED, align: "left",
  });
  slide.addText(String(pageNum), {
    x: 12.6, y: 7.15, w: 0.4, h: 0.3, fontFace: FONT_BODY, fontSize: 9, color: MUTED, align: "right",
  });
}

// ---------------- Slide 1: Title ----------------
{
  const slide = pres.addSlide();
  slide.background = { color: NAVY };
  slide.addText("AI-Assisted Spend Classification\n& Data Quality for Procurement", {
    x: 0.9, y: 2.3, w: 11.5, h: 1.9, fontFace: FONT_HEAD, fontSize: 40, bold: true, color: "FFFFFF", align: "left",
  });
  slide.addText("Turning messy purchase-order data into a usable spend view — with AI", {
    x: 0.9, y: 4.15, w: 10.5, h: 0.6, fontFace: FONT_BODY, fontSize: 18, italic: true, color: ICE, align: "left",
  });
  slide.addText("Santosh Hiremath  |  Illustrative project on synthetic data  |  2026", {
    x: 0.9, y: 6.6, w: 10, h: 0.4, fontFace: FONT_BODY, fontSize: 12, color: ICE, align: "left",
  });
}

// ---------------- Slide 2: The business problem ----------------
{
  const slide = pres.addSlide();
  slide.background = { color: OFFWHITE };
  slide.addText("The problem: spend data is rarely clean enough to act on", {
    x: 0.6, y: 0.5, w: 12.1, h: 0.8, fontFace: FONT_HEAD, fontSize: 30, bold: true, color: NAVY,
  });

  const cards = [
    { stat: "44%", label: "of PO lines had a missing or\ninconsistent spend category", },
    { stat: "15", label: "duplicate invoice line pairs\n— overpayment risk", },
    { stat: "3", label: "price outliers 5–6× the\nnormal price for that item", },
  ];
  const cardW = 3.7, gap = 0.45, startX = 0.6, y = 2.1;
  cards.forEach((c, i) => {
    const x = startX + i * (cardW + gap);
    slide.addShape("roundRect", { x, y, w: cardW, h: 2.6, rectRadius: 0.12, fill: { color: "FFFFFF" }, line: { color: ICE, width: 1 }, shadow: { type: "outer", color: "1C2733", opacity: 0.18, blur: 6, offset: 3, angle: 90 } });
    slide.addText(c.stat, { x, y: y + 0.25, w: cardW, h: 1.0, align: "center", fontFace: FONT_HEAD, fontSize: 54, bold: true, color: TEAL });
    slide.addText(c.label, { x: x + 0.25, y: y + 1.35, w: cardW - 0.5, h: 1.1, align: "center", fontFace: FONT_BODY, fontSize: 14, color: DARKTEXT });
  });

  slide.addText("Category managers and sourcing teams can't build a reliable spend view, run supplier analysis, or catch overpayments when the underlying data looks like this — and cleaning it by hand doesn't scale.", {
    x: 0.6, y: 5.15, w: 12.1, h: 1.2, fontFace: FONT_BODY, fontSize: 15, color: DARKTEXT, align: "left",
  });
  addFooter(slide, 2);
}

// ---------------- Slide 3: The AI use case ----------------
{
  const slide = pres.addSlide();
  slide.background = { color: OFFWHITE };
  slide.addText("The AI use case: classify spend from the one field that's reliable", {
    x: 0.6, y: 0.5, w: 12.1, h: 0.8, fontFace: FONT_HEAD, fontSize: 28, bold: true, color: NAVY,
  });

  const steps = [
    { n: "1", t: "Item description", d: "Free-text field — always present, even when the category label is missing or wrong." },
    { n: "2", t: "AI classification", d: "A text-based model trained on manually-labeled examples predicts the spend category." },
    { n: "3", t: "Usable spend view", d: "Every line item gets a consistent, reliable category — ready for reporting and analysis." },
  ];
  const boxW = 3.5, gapX = 0.75, startX = 0.7, y = 2.3;
  steps.forEach((s, i) => {
    const x = startX + i * (boxW + gapX);
    slide.addShape("ellipse", { x: x, y: y, w: 0.7, h: 0.7, fill: { color: TEAL }, line: { type: "none" } });
    slide.addText(s.n, { x: x, y: y, w: 0.7, h: 0.7, align: "center", valign: "middle", fontFace: FONT_HEAD, fontSize: 24, bold: true, color: "FFFFFF" });
    slide.addText(s.t, { x: x - 0.1, y: y + 0.85, w: boxW + 0.2, h: 0.5, fontFace: FONT_HEAD, fontSize: 17, bold: true, color: NAVY });
    slide.addText(s.d, { x: x - 0.1, y: y + 1.35, w: boxW + 0.2, h: 1.4, fontFace: FONT_BODY, fontSize: 13, color: DARKTEXT });
    if (i < steps.length - 1) {
      slide.addText("→", { x: x + boxW + 0.05, y: y - 0.05, w: 0.65, h: 0.8, align: "center", fontFace: FONT_BODY, fontSize: 28, bold: true, color: ICE });
    }
  });

  slide.addShape("roundRect", { x: 0.6, y: 5.15, w: 12.1, h: 1.5, rectRadius: 0.1, fill: { color: NAVY }, line: { type: "none" } });
  slide.addText("Also flags likely duplicate invoice lines and price outliers within a category — a second, related use case built on the same clean spend view, aimed directly at overpayment and pricing-error risk.", {
    x: 1.0, y: 5.35, w: 11.3, h: 1.1, fontFace: FONT_BODY, fontSize: 14, color: "FFFFFF", align: "left", valign: "middle",
  });
  addFooter(slide, 3);
}

// ---------------- Slide 4: Results ----------------
{
  const slide = pres.addSlide();
  slide.background = { color: OFFWHITE };
  slide.addText("Results: verified against known outcomes, not just “it ran”", {
    x: 0.6, y: 0.5, w: 12.1, h: 0.8, fontFace: FONT_HEAD, fontSize: 28, bold: true, color: NAVY,
  });

  slide.addChart(pres.ChartType.bar, [
    {
      name: "Result",
      labels: ["Category\naccuracy", "Messy labels\nfixed", "Duplicates\ncaught", "Price outliers\ncaught"],
      values: [99.6, 99.8, 100, 100],
    },
  ], {
    x: 0.6, y: 1.7, w: 6.6, h: 4.2,
    chartColors: [TEAL],
    showTitle: true, title: "Verification results (%)", titleFontFace: FONT_HEAD, titleFontSize: 14, titleColor: NAVY,
    showValue: true, dataLabelPosition: "outEnd", dataLabelFontSize: 12, dataLabelColor: DARKTEXT,
    dataLabelFormatCode: "0.0",
    catAxisLabelFontSize: 11, catAxisLabelColor: DARKTEXT,
    valAxisLabelFontSize: 10, valAxisLabelColor: MUTED, valAxisMaxVal: 110, valAxisMinVal: 0,
    valGridLine: { color: "E3E9EC", size: 1 }, catGridLine: { style: "none" },
    showLegend: false, barDir: "col",
  });

  const notes = [
    "4,214 synthetic PO lines, 6 spend categories, 15 suppliers",
    "99.6% held-out accuracy — deliberately not 100%, to stay realistic",
    "All 14 injected duplicate pairs and 3 injected price outliers caught",
    "10 automated tests validate results against known ground truth",
  ];
  let ny = 1.9;
  notes.forEach((n) => {
    slide.addShape("ellipse", { x: 7.55, y: ny + 0.08, w: 0.12, h: 0.12, fill: { color: AMBER }, line: { type: "none" } });
    slide.addText(n, { x: 7.85, y: ny - 0.08, w: 4.9, h: 0.6, fontFace: FONT_BODY, fontSize: 13.5, color: DARKTEXT, valign: "top" });
    ny += 0.85;
  });
  addFooter(slide, 4);
}

// ---------------- Slide 5: Honest findings ----------------
{
  const slide = pres.addSlide();
  slide.background = { color: OFFWHITE };
  slide.addText("What good verification actually found", {
    x: 0.6, y: 0.5, w: 12.1, h: 0.8, fontFace: FONT_HEAD, fontSize: 28, bold: true, color: NAVY,
  });

  const findings = [
    {
      t: "A real detection gap, found and fixed",
      d: "Injecting outliers into a too-small data group let the outliers themselves skew the baseline, hiding 2 of 3 from detection. Fixed by requiring a larger comparison group — which also matches how a category manager would actually want this to work.",
    },
    {
      t: "A flagged “duplicate” that was a genuine coincidence, not a bug",
      d: "Two unrelated purchase records legitimately matched on every field by chance. The tool surfaces this rather than hiding it, because a category manager reviewing flagged duplicates faces exactly this same judgment call.",
    },
  ];
  let fy = 1.9;
  findings.forEach((f) => {
    slide.addShape("roundRect", { x: 0.6, y: fy, w: 12.1, h: 2.05, rectRadius: 0.1, fill: { color: "FFFFFF" }, line: { color: ICE, width: 1 } });
    slide.addText(f.t, { x: 1.0, y: fy + 0.2, w: 11.3, h: 0.5, fontFace: FONT_HEAD, fontSize: 16, bold: true, color: TEAL });
    slide.addText(f.d, { x: 1.0, y: fy + 0.75, w: 11.3, h: 1.15, fontFace: FONT_BODY, fontSize: 13.5, color: DARKTEXT });
    fy += 2.35;
  });
  addFooter(slide, 5);
}

// ---------------- Slide 6: Close ----------------
{
  const slide = pres.addSlide();
  slide.background = { color: NAVY };
  slide.addText("The pattern, not just the project", {
    x: 0.9, y: 0.9, w: 11.5, h: 0.9, fontFace: FONT_HEAD, fontSize: 32, bold: true, color: "FFFFFF",
  });
  slide.addText([
    { text: "Start from a real, messy business problem", options: { bullet: true, color: ICE, breakLine: true } },
    { text: "Build something that genuinely works", options: { bullet: true, color: ICE, breakLine: true } },
    { text: "Verify it against known outcomes, not assumptions", options: { bullet: true, color: ICE, breakLine: true } },
    { text: "Explain it clearly to a non-technical audience", options: { bullet: true, color: ICE } },
  ], {
    x: 0.9, y: 2.1, w: 8.5, h: 2.4, fontFace: FONT_BODY, fontSize: 18, paraSpaceAfter: 12,
  });
  slide.addText("This is a synthetic-data illustration of the approach I'd bring to translating procurement's AI use cases into working tools — not a claim of prior procurement-domain experience.", {
    x: 0.9, y: 5.1, w: 11.0, h: 1.2, fontFace: FONT_BODY, fontSize: 14, italic: true, color: ICE, align: "left",
  });
  slide.addText("Santosh Hiremath  |  santoshhiremath.de@gmail.com", {
    x: 0.9, y: 6.75, w: 10, h: 0.4, fontFace: FONT_BODY, fontSize: 12, color: ICE,
  });
}

pres.writeFile({ fileName: "procurement_ai_deck.pptx" }).then(() => {
  console.log("done");
});

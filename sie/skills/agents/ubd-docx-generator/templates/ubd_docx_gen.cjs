/* Node.js script to generate a filled UbD DOCX template
 * Usage: node ubd_docx_gen.cjs
 * Requires: npm install --prefix /tmp/node_proj docx
 * Output: TEAC_5003_UbD_Filled.docx
 */

const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  HeadingLevel, WidthType, ShadingType, TableLayoutType, VerticalAlign, PageBreak
} = require('/tmp/node_proj/node_modules/docx');
const fs = require('fs');

// ─── Cell helpers ────────────────────────────────────────────────────────────

function hCell(text) {
  return new TableCell({
    children: [new Paragraph({ children: [new TextRun({ text, bold: true })], spacing: { after: 40 } })],
    shading: { fill: "D9E2F3", type: ShadingType.CLEAR, color: "auto" },
    verticalAlign: VerticalAlign.CENTER,
  });
}

function dCell(text) {
  return new TableCell({
    children: [new Paragraph({ children: [new TextRun({ text })], spacing: { after: 40 } })],
    verticalAlign: VerticalAlign.CENTER,
  });
}

function bCell(text) {
  return new TableCell({
    children: [new Paragraph({ children: [new TextRun({ text, bold: true })], spacing: { after: 40 } })],
    verticalAlign: VerticalAlign.CENTER,
  });
}

function row(cells) { return new TableRow({ children: cells }); }

function makeTable(rows) {
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    layout: TableLayoutType.FIXED,
    rows,
  });
}

// ─── Paragraph helpers ───────────────────────────────────────────────────────

function h1(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_1, spacing: { before: 300, after: 150 } });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 200, after: 100 } });
}
function p(text) {
  return new Paragraph({ children: [new TextRun({ text })], spacing: { after: 80, line: 276 } });
}
function pb() {
  return new Paragraph({ children: [new PageBreak()], spacing: { before: 0, after: 0 } });
}

// ─── UNIT CONTENT — modify these values for your topic ────────────────────────

const UNIT = {
  year:         "Year 10",
  stage:        "Stage 5",
  topic:        "The Work Environment",
  duration:     "25 hours — Term 3 (8–10 weeks)",
  unitFocus:    "This unit explores the nature of work in Australia, examining rights and responsibilities of employees and employers, employment contracts, workplace health and safety, and contemporary issues such as the gig economy.",
  inquiryQuestions: "1. How do employment relationships function in Australia?\n2. What rights and responsibilities exist in the workplace?\n3. How has the changing nature of work impacted employees and employers?\n4. How can individuals effectively navigate and resolve workplace disputes?",
  outcomes:     "CO5-COM-01, CO5-RRI-01, CO5-DEC-01, CO5-PRO-01, CO5-WOR-01\nLife Skills: COLS-COM-01, COLS-RRI-01, COLS-DEC-01, COLS-PRO-01, COLS-WOR-01",
  priorLearning: "Students have completed units on Consumer and Financial Decisions and the Business Environment.",
  differentiation: "UDL framework: vocabulary glossaries, sentence starters, TEEC scaffold; infographics for visual learners; extension research tasks; Life Skills outcomes for students with disability.",
  formalTask:   "Workplace Dispute Resolution Report",
  taskDue:      "Term 3, Week 7",
  taskWeight:   "25%",
  // Assessment for/as/of learning
  afL: "Pre-test (Lesson 1); Exit tickets; Learning journals; Observation checklists",
  aaL: "Peer feedback on ICT quiz; Self-assessment checklists; Jigsaw collaboration",
  aoL: "Formal task: Workplace Dispute Resolution Report",
};

// ─── Content blocks (5 blocks × 5 hours = 25 hours) ────────────────────────

const BLOCKS = [
  {
    title: "Block 1: The Nature of Work (5 hours)",
    content: "Nature of work: Different forms of employment (full-time, part-time, casual, contract, gig economy). The labour market in Australia. Changing patterns of work (automation, gig economy, remote work).\n\nKey Concepts: Labour force, underemployment, unemployment, precarious work, casualisation",
    strategies: "Direct instruction with slides; Think-pair-share on types of employment; Venn diagram comparing employment types; Exit ticket.",
    resources: "PowerPoint slides; Fair Work Ombudsman infographic; Video: 'Future of Work' (ABC Education); Pre-test (original resource).",
    assessment: "Pre-test results analysed; Exit ticket; Observation",
  },
  {
    title: "Block 2: Rights and Responsibilities in the Workplace (5 hours)",
    content: "National Employment Standards (NES): Maximum hours, leave entitlements, flexible working arrangements. Fair Work Act 2009: Unfair dismissal, general protections. Award wages and enterprise agreements. Workplace Health and Safety: Duty of care, risk assessment, right to refuse unsafe work.\n\nKey Concepts: Employment contract, entitlements, loading, AWRS, discrimination",
    strategies: "Direct instruction; Case study analysis (Peter scenario); Jigsaw reading groups; Role-play: 'Negotiate an employment contract'; Digital exit ticket.",
    resources: "Fair Work Ombudsman website; WHS legislation fact sheet; Peter case study; Role-play cards (original); Google Forms ICT quiz.",
    assessment: "ICT resource completion; Peer feedback; Exit ticket",
  },
  {
    title: "Block 3: Employment Relationships and Workplace Culture (5 hours)",
    content: "Relationships in the workplace: Employer-employee obligations, union membership, collective bargaining. Workplace rights: Right to a safe workplace, right to join union, protection from discrimination. Workplace culture: Bystander action, bullying, harassment. Resolving disputes: Internal resolution, Fair Work Commission, mediation.\n\nKey Concepts: Enterprise agreement, collective bargaining, general protections, dispute resolution",
    strategies: "Case study analysis; Socratic seminar on workplace rights; WebQuest — Fair Work website exploration; Paragraph writing using TEEC scaffold.",
    resources: "Fair Work Commission resources; YouTube clips; TEEC writing scaffold (original); WebQuest worksheet",
    assessment: "TEEC paragraph (formative); Self-assessment checklist",
  },
  {
    title: "Block 4: Contemporary Issues in the Work Environment (5 hours)",
    content: "Gig economy: Uber, Deliveroo, Airtasker — rights of gig workers. Digital platforms and labour: Algorithmic management, rating systems. Globalisation and work: Offshoring, outsourcing, minimum standards. Future of work: AI, automation, reskilling.\n\nKey Concepts: Gig economy, algorithmic management, global labour standards",
    strategies: "Debate: 'Gig workers should have the same rights as permanent employees'; Research jigsaw groups; Digital presentation creation; Reflection journal.",
    resources: "News articles (The Guardian, ABC); Platform company case studies; Presentation templates; Reflection journal template",
    assessment: "Research task; Presentation; Learning journal",
  },
  {
    title: "Block 5: Assessment and Reflection (5 hours)",
    content: "Assessment preparation: Feedback on draft reports; Rubric deconstruction; Self-assessment against criteria; Peer editing workshop. Unit reflection: What have I learned about my rights? How does this connect to my future?\n\nKey Concepts: Synthesis and application of all prior concepts",
    strategies: "Feedback conference; Peer editing; Student-teacher conference; Reflection spiral.",
    resources: "Assessment rubric; Peer editing checklist; Reflection prompts",
    assessment: "Formal submission: Workplace Dispute Resolution Report",
  },
];

// ─── Glossary ─────────────────────────────────────────────────────────────────

const GLOSSARY = [
  ["Award", "A document that outlines an employee's minimum pay and conditions."],
  ["Cadetship", "Training in a full-time job, with time allocated to attend university or TAFE."],
  ["Casual", "Employed on an 'as needed' basis."],
  ["Common law contract", "When an employer and an individual employee negotiate a contract covering pay and conditions."],
  ["Discrimination", "Treating a person less favourably because of factors such as gender, ethnicity, religion or disability."],
  ["Employee", "Person who works for a wage or salary."],
  ["Employer", "Person who hires employees."],
  ["Employment contract", "A legally binding formal agreement between an employee and an employer."],
  ["Enterprise agreement", "Agreement about pay and conditions made at a workplace/enterprise level."],
  ["Entitlements", "Non-wage benefits such as long service leave or sick leave."],
  ["Full-time", "Continuing, ongoing employment working 38 hours or more per week."],
  ["Gig economy", "Work based on short-term contracts or freelance engagements through digital platforms."],
  ["Labour force", "People aged 15 and over who are either employed or unemployed."],
  ["Loading", "Extra pay to compensate casual employees for lack of access to entitlements."],
  ["National Employment Standards", "Minimum entitlements for all employees in Australia (Fair Work Act 2009)."],
  ["Part-time", "Ongoing employment working fewer than 38 hours per week."],
  ["Superannuation", "Regular contributions made by an employer to a nominated super fund for retirement savings."],
];

// ─── Document assembly ────────────────────────────────────────────────────────

function blockTable(block) {
  return makeTable([
    row([hCell("Content"), hCell("Teaching & Learning Strategies"), hCell("Resources"), hCell("Assessment")]),
    row([dCell(block.content), dCell(block.strategies), dCell(block.resources), dCell(block.assessment)]),
  ]);
}

const children = [
  // PAGE 1: UNIT OVERVIEW
  h1(`Stage 3 UbD: Unit of Work — ${UNIT.topic}`),
  p(`${UNIT.year} | ${UNIT.stage} | ${UNIT.duration}`),
  p(""),
  makeTable([
    row([hCell("Field"), hCell("Detail")]),
    row([bCell("Year & Stage"), dCell(`${UNIT.year}, ${UNIT.stage}`)]),
    row([bCell("Core Topic"), dCell(UNIT.topic)]),
    row([bCell("Duration"), dCell(UNIT.duration)]),
    row([bCell("Unit Focus"), dCell(UNIT.unitFocus)]),
    row([bCell("Key Inquiry Questions"), dCell(UNIT.inquiryQuestions)]),
    row([bCell("Syllabus Outcomes"), dCell(UNIT.outcomes)]),
    row([bCell("Prior Learning"), dCell(UNIT.priorLearning)]),
    row([bCell("Differentiation"), dCell(UNIT.differentiation)]),
  ]),

  // PAGE 2: ASSESSMENT
  pb(),
  h1("Stage 3: Assessment"),
  h2("Assessment for Learning (Formative)"),
  p(`• ${UNIT.afL}`),
  h2("Assessment as Learning"),
  p(`• ${UNIT.aaL}`),
  h2("Assessment of Learning (Summative)"),
  p(`• ${UNIT.aoL}`),
  h2("Formal Assessment Task Descriptor"),
  makeTable([
    row([hCell("SUBJECT"), dCell(`${UNIT.year} Commerce`)]),
    row([hCell("TOPIC"), dCell(UNIT.topic)]),
    row([hCell("Date Issued"), dCell("Term 3, Week 4")]),
    row([hCell("Date Due"), dCell(UNIT.taskDue)]),
    row([hCell("Type of Task"), dCell(UNIT.formalTask)]),
    row([hCell("MARKS"), dCell("/20")]),
    row([hCell("WEIGHTING"), dCell(UNIT.taskWeight)]),
    row([hCell("OUTCOMES TO BE ASSESSED"), dCell("CO5-COM-01: Applies consumer, financial, economic, business, legal, political and employment concepts and terminology.\nCO5-RRI-01: Researches and evaluates commercial and financial information.\nCO5-DEC-01: Analyses influences on consumer, financial, economic, business and employment decisions.\nCO5-PRO-01: Develops and implements plans designed to achieve goals.")]),
  ]),
  h2("Assessment Criteria"),
  p("Students will be assessed on:"),
  p("• Use correct employment concepts and terminology."),
  p("• Analyse the situation and the rights and responsibilities of workers and employers."),
  p("• Recommend legal and proper strategies to resolve a workplace issue."),
  p("• Structure information clearly in dispute resolution form."),

  // PAGES 3–7: CONTENT BLOCKS
  pb(),
  h1("Unit Content — 5-Hour Teaching Blocks"),
  ...BLOCKS.map(b => [h2(b.title), blockTable(b)]).flat(),

  // GLOSSARY
  pb(),
  h1("Stage 2: Glossary of Terms — The Work Environment"),
  makeTable([
    row([hCell("Term"), hCell("Meaning")]),
    ...GLOSSARY.map(([term, def]) => row([bCell(term), dCell(def)])),
  ]),

  // LESSON PLANS + JUSTIFICATION sections go here —
  // See the full working script: /opt/data/cache/documents/create_docx.cjs
];

const doc = new Document({
  styles: { default: { document: { run: { font: "Calibri", size: 22 } } } },
  sections: [{
    properties: { page: { margin: { top: 1080, bottom: 1080, left: 1080, right: 1080 } } },
    children,
  }],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('/opt/data/cache/documents/TEAC_5003_UbD_Filled.docx', buffer);
  console.log('SUCCESS: TEAC_5003_UbD_Filled.docx created');
}).catch(err => {
  console.error('ERROR:', err.message);
  process.exit(1);
});

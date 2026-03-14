const {
  Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
  AlignmentType, HeadingLevel, BorderStyle, WidthType, ShadingType,
  VerticalAlign, ExternalHyperlink, LevelFormat, UnderlineType,
  PageNumber, NumberFormat, Header, Footer, TabStopType,
} = require('docx');
const fs = require('fs');

// ── LIVE DATA (passed via CLI args or defaults) ──────────────────────────────
const args = process.argv.slice(2);
const liveArgs = {};
args.forEach(a => { const [k,v] = a.split('='); liveArgs[k] = v; });

const CITATIONS    = liveArgs.citations    || '3,248';
const HINDEX       = liveArgs.hindex       || '24';
const PEER_REVIEWS = liveArgs.peerReviews  || '149';
const JOURNALS     = liveArgs.journals     || '67';
const MANUSCRIPTS  = liveArgs.manuscripts  || '129';
const PUB_COUNT    = liveArgs.pubCount     || '193';
const DATE_STR     = liveArgs.date         || new Date().toLocaleDateString('en-US', {year:'numeric', month:'long', day:'numeric'});
const FIRST_AUTH   = liveArgs.firstAuth    || '20';
const SECOND_AUTH  = liveArgs.secondAuth   || '31';
const LAST_AUTH    = liveArgs.lastAuth     || '50';
const CORR_AUTH    = liveArgs.corrAuth     || '68';

// ── STYLE HELPERS ────────────────────────────────────────────────────────────
const NAVY = '0A1628';
const GOLD = 'B8953A';
const STEEL = '4A607E';
const MUTED = '6B84A0';
const BLACK = '000000';
const W = 12240; // page width DXA (8.5in)
const MARGIN = 1080; // 0.75in
const CW = W - 2 * MARGIN; // content width DXA

function run(text, opts = {}) {
  return new TextRun({ text, font: 'Calibri', size: 20, color: BLACK, ...opts });
}
function boldRun(text, opts = {}) {
  return run(text, { bold: true, ...opts });
}
function italicRun(text, opts = {}) {
  return run(text, { italics: true, ...opts });
}
function colorRun(text, color, opts = {}) {
  return run(text, { color, ...opts });
}
function linkRun(text, url) {
  return new ExternalHyperlink({ link: url, children: [
    new TextRun({ text, font: 'Calibri', size: 20, color: STEEL,
      underline: { type: UnderlineType.SINGLE, color: STEEL } })
  ]});
}

function para(children, opts = {}) {
  const p = { children: Array.isArray(children) ? children : [run(children)], ...opts };
  return new Paragraph(p);
}

function sectionHeading(title) {
  return new Paragraph({
    children: [boldRun(title, { color: NAVY, size: 22, allCaps: true })],
    spacing: { before: 240, after: 60 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 8, color: GOLD, space: 4 } },
  });
}

function twoColRow(left, right, leftWidth = 1400, rightWidth = null) {
  const rw = rightWidth || (CW - leftWidth);
  const borders = {
    top: { style: BorderStyle.NONE, size: 0 },
    bottom: { style: BorderStyle.NONE, size: 0 },
    left: { style: BorderStyle.NONE, size: 0 },
    right: { style: BorderStyle.NONE, size: 0 },
    insideVertical: { style: BorderStyle.NONE, size: 0 },
    insideHorizontal: { style: BorderStyle.NONE, size: 0 },
  };
  return new TableRow({ children: [
    new TableCell({ borders, width: { size: leftWidth, type: WidthType.DXA },
      margins: { top: 40, bottom: 40, left: 80, right: 80 },
      children: Array.isArray(left) ? left : [left] }),
    new TableCell({ borders, width: { size: rw, type: WidthType.DXA },
      margins: { top: 40, bottom: 40, left: 80, right: 80 },
      children: Array.isArray(right) ? right : [right] }),
  ]});
}

function simpleTable(rows, colWidths) {
  return new Table({
    width: { size: CW, type: WidthType.DXA },
    columnWidths: colWidths,
    borders: {
      top: { style: BorderStyle.NONE }, bottom: { style: BorderStyle.NONE },
      left: { style: BorderStyle.NONE }, right: { style: BorderStyle.NONE },
      insideVertical: { style: BorderStyle.NONE }, insideHorizontal: { style: BorderStyle.NONE },
    },
    rows,
  });
}

// ── PUBLICATIONS DATA ────────────────────────────────────────────────────────
// Full 193 publications will be loaded from JSON sidecar
const pubs = require('/home/claude/cv_pubs.json');

// ── BUILD DOCUMENT ──────────────────────────────────────────────────────────
function buildCV() {
  const children = [];

  // ── NAME BLOCK ─────────────────────────────────────────────────────────────
  children.push(new Paragraph({
    children: [boldRun('Reza Shahriarirad, M.D.', { size: 44, color: NAVY })],
    spacing: { after: 60 },
  }));
  children.push(para([
    boldRun('Email: ', { size: 18 }),
    run('R.shahriari1995@gmail.com', { size: 18 }),
    run('   |   Shahriarirad.reza@mayo.edu', { size: 18 }),
    run('   |   +1-507-218-6077', { size: 18 }),
  ], { spacing: { after: 40 } }));
  children.push(para([
    linkRun('Google Scholar', 'https://scholar.google.com/citations?user=mOE1KmEAAAAJ&hl=en'),
    run(' | ', { size: 18, color: MUTED }),
    linkRun('PubMed', 'https://www.ncbi.nlm.nih.gov/myncbi/reza.shahriari.1/bibliography/public/'),
    run(' | ', { size: 18, color: MUTED }),
    linkRun('Scopus', 'https://www.scopus.com/authid/detail.uri?authorId=57194698048'),
    run(' | ', { size: 18, color: MUTED }),
    linkRun('ResearchGate', 'https://www.researchgate.net/profile/Reza-Shahriarirad'),
    run(' | ', { size: 18, color: MUTED }),
    linkRun('Web of Science', 'https://www.webofscience.com/wos/author/record/ABC-9194-2020'),
    run(' | ', { size: 18, color: MUTED }),
    linkRun('LinkedIn', 'https://www.linkedin.com/in/reza-shahriarirad/'),
    run(' | ', { size: 18, color: MUTED }),
    linkRun('ORCID: 0000-0001-5454-495X', 'https://orcid.org/0000-0001-5454-495X'),
  ], { spacing: { after: 60 } }));
  children.push(new Paragraph({
    spacing: { after: 0 },
    border: { bottom: { style: BorderStyle.SINGLE, size: 12, color: NAVY, space: 4 } },
  }));

  // ── PERSONAL INFORMATION ───────────────────────────────────────────────────
  children.push(new Paragraph({ spacing: { before: 120, after: 0 } }));
  children.push(sectionHeading('Personal Information'));
  const piRows = [
    ['Surname', 'Shahriarirad'],
    ['Given name', 'Reza'],
    ['Current residence', 'Rochester, Minnesota, USA'],
    ['Date of CV', DATE_STR],
    ['Verified Reviews', PEER_REVIEWS],
    ['Total Citations', CITATIONS],
    ['H-index', HINDEX],
    ['Research Interests', 'Surgery · Minimally Invasive Surgery · Artificial Intelligence'],
  ];
  children.push(simpleTable(
    piRows.map(([l, r]) => twoColRow(
      para([italicRun(l, { color: MUTED, size: 18 })]),
      para([run(r, { size: 20 })]),
      2200, CW - 2200
    )),
    [2200, CW - 2200]
  ));

  // ── EDUCATION ─────────────────────────────────────────────────────────────
  children.push(new Paragraph({ spacing: { before: 120, after: 0 } }));
  children.push(sectionHeading('Education'));
  children.push(simpleTable([
    twoColRow(
      para([italicRun('2013 – 2020', { color: MUTED, size: 18 })]),
      [para([boldRun('Doctor of Medicine (M.D.)')]),
       para([italicRun('Shiraz University of Medical Sciences, Shiraz, Iran (SUMS)', { color: STEEL })])],
    ),
    twoColRow(
      para([italicRun('2009 – 2013', { color: MUTED, size: 18 })]),
      [para([boldRun('High School Diploma')]),
       para([italicRun('National Organization for Development of Exceptional Talents (SAMPAD), Shiraz, Iran', { color: STEEL })])],
    ),
  ], [1400, CW - 1400]));

  // ── EXPERIENCE ────────────────────────────────────────────────────────────
  children.push(new Paragraph({ spacing: { before: 120, after: 0 } }));
  children.push(sectionHeading('Working and Professional Experience'));
  children.push(simpleTable([
    twoColRow(
      para([italicRun('2024 – Present', { color: MUTED, size: 18 })]),
      [para([run('Surgery Innovation Center, '), italicRun('Mayo Clinic Rochester')]),
       para([italicRun('Research Fellow', { color: STEEL })]),
       para([run('Conducting 30+ IRB-approved research projects across plastic & reconstructive surgery, thoracic surgery, cardiac surgery, bariatric & abdominal wall reconstruction, oral & maxillofacial surgery, GI surgery, and trauma. Leading translational innovation projects and industry collaborations.', { size: 18, color: MUTED })])],
    ),
    twoColRow(
      para([italicRun('2018 – 2024', { color: MUTED, size: 18 })]),
      [para([run('Thoracic and Vascular Surgery Research Center, '), italicRun('Shiraz University of Medical Sciences')]),
       para([italicRun('Senior Researcher and Project Manager', { color: STEEL })])],
    ),
    twoColRow(
      para([italicRun('2020 – 2022', { color: MUTED, size: 18 })]),
      [para([run('Khatam-al-Anbiya Hospital, '), italicRun('Bushehr, Iran')]),
       para([italicRun('General Practitioner — Emergency Department (Ministry of Health mandatory medical service)', { color: STEEL })])],
    ),
    twoColRow(
      para([italicRun('2014 – 2020', { color: MUTED, size: 18 })]),
      [para([boldRun('Student Research Committee, '), italicRun('Shiraz University of Medical Sciences')]),
       para([italicRun('Research Trainee', { color: STEEL })])],
    ),
  ], [1400, CW - 1400]));

  // ── AWARDS ────────────────────────────────────────────────────────────────
  children.push(new Paragraph({ spacing: { before: 120, after: 0 } }));
  children.push(sectionHeading('Awards'));
  children.push(simpleTable([
    twoColRow(
      para([italicRun('Dec, 2023', { color: MUTED, size: 18 })]),
      [para([new ExternalHyperlink({ link: 'https://topresearcherslist.com/Home/Profile/760111', children: [
          new TextRun({ text: 'World Top 2% Scientists', bold: true, font: 'Calibri', size: 20, color: STEEL, underline: { type: UnderlineType.SINGLE } })
        ]})]),
       para([italicRun('Science-wide author databases of standardized citation indicators, Elsevier / Stanford World\'s Top 2% Scientists Report', { color: MUTED, size: 18 })])],
    ),
    twoColRow(
      para([italicRun('Oct 2020', { color: MUTED, size: 18 })]),
      [para([boldRun('National Outstanding Student Researcher')]),
       para([italicRun('Ministry of Health and Medical Education (National Student Research Committee), Iran', { color: MUTED, size: 18 })])],
    ),
  ], [1400, CW - 1400]));

  // ── LEADERSHIP ────────────────────────────────────────────────────────────
  children.push(new Paragraph({ spacing: { before: 120, after: 0 } }));
  children.push(sectionHeading('Leadership & Community Service'));
  children.push(simpleTable([
    twoColRow(
      para([italicRun('2020 – Present', { color: MUTED, size: 18 })]),
      [para([boldRun('Research Project Inspector and Mentoring Program (Shiraz University)')]),
       para([run('Founded and leads the Research Mentoring Program, mentoring 15 medical students in research methodology, scientific writing, and publication strategy — resulting in over 50 peer-reviewed publications. Serves as Research Project Inspector ensuring quality, ethics compliance, and methodological rigor.', { size: 18 })])],
    ),
  ], [1400, CW - 1400]));

  // ── SKILLS ────────────────────────────────────────────────────────────────
  children.push(new Paragraph({ spacing: { before: 120, after: 0 } }));
  children.push(sectionHeading('Skills'));
  children.push(new Table({
    width: { size: CW, type: WidthType.DXA },
    columnWidths: [Math.floor(CW/3), Math.floor(CW/3), CW - 2*Math.floor(CW/3)],
    rows: [
      new TableRow({ children: [
        new TableCell({ borders: {top:{style:BorderStyle.NONE},bottom:{style:BorderStyle.NONE},left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE},insideVertical:{style:BorderStyle.NONE}},
          width: {size:Math.floor(CW/3), type:WidthType.DXA}, margins:{top:40,bottom:40,left:80,right:80},
          children:[para([boldRun('Computing', {color: NAVY})])] }),
        new TableCell({ borders: {top:{style:BorderStyle.NONE},bottom:{style:BorderStyle.NONE},left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE},insideVertical:{style:BorderStyle.NONE}},
          width: {size:Math.floor(CW/3), type:WidthType.DXA}, margins:{top:40,bottom:40,left:80,right:80},
          children:[para([boldRun('Interpersonal', {color: NAVY})])] }),
        new TableCell({ borders: {top:{style:BorderStyle.NONE},bottom:{style:BorderStyle.NONE},left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE},insideVertical:{style:BorderStyle.NONE}},
          width: {size:CW-2*Math.floor(CW/3), type:WidthType.DXA}, margins:{top:40,bottom:40,left:80,right:80},
          children:[para([boldRun('Writing', {color: NAVY})])] }),
      ]}),
      new TableRow({ children: [
        new TableCell({ borders: {top:{style:BorderStyle.NONE},bottom:{style:BorderStyle.NONE},left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE}},
          width: {size:Math.floor(CW/3), type:WidthType.DXA}, margins:{top:40,bottom:40,left:80,right:80},
          children:[
            para([italicRun('SPSS (Good), MS Office (Good), Endnote (Good), Typing (90wpm), Corel Video Studio (Good), Python (Beginner), MATLAB (Beginner), NCSS (Beginner)', {size:18})]),
          ] }),
        new TableCell({ borders: {top:{style:BorderStyle.NONE},bottom:{style:BorderStyle.NONE},left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE}},
          width: {size:Math.floor(CW/3), type:WidthType.DXA}, margins:{top:40,bottom:40,left:80,right:80},
          children:[para([italicRun('Leadership, Presentation, Time Management, Effective Listening, Team Player, Problem-Solving', {size:18})])] }),
        new TableCell({ borders: {top:{style:BorderStyle.NONE},bottom:{style:BorderStyle.NONE},left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE}},
          width: {size:CW-2*Math.floor(CW/3), type:WidthType.DXA}, margins:{top:40,bottom:40,left:80,right:80},
          children:[para([italicRun('Scientific Editing, Translating (English ↔ Farsi)', {size:18})])] }),
      ]}),
    ],
  }));

  // ── PATENTS ───────────────────────────────────────────────────────────────
  children.push(new Paragraph({ spacing: { before: 120, after: 0 } }));
  children.push(sectionHeading('Patents and Innovations'));
  children.push(new Table({
    width: { size: CW, type: WidthType.DXA }, columnWidths: [1200, CW-2400, 1200],
    borders: {top:{style:BorderStyle.SINGLE,size:4,color:'CCCCCC'},bottom:{style:BorderStyle.SINGLE,size:4,color:'CCCCCC'},
      left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE},insideHorizontal:{style:BorderStyle.SINGLE,size:2,color:'EEEEEE'},insideVertical:{style:BorderStyle.NONE}},
    rows: [
      new TableRow({ tableHeader: true, children: [
        new TableCell({ shading:{fill:'F0F4F8',type:ShadingType.CLEAR}, margins:{top:60,bottom:60,left:100,right:100},
          width:{size:1200,type:WidthType.DXA}, children:[para([boldRun('Date', {size:18})])] }),
        new TableCell({ shading:{fill:'F0F4F8',type:ShadingType.CLEAR}, margins:{top:60,bottom:60,left:100,right:100},
          width:{size:CW-2400,type:WidthType.DXA}, children:[para([boldRun('Topic', {size:18})])] }),
        new TableCell({ shading:{fill:'F0F4F8',type:ShadingType.CLEAR}, margins:{top:60,bottom:60,left:100,right:100},
          width:{size:1200,type:WidthType.DXA}, children:[para([boldRun('Issuer / Reg. No.', {size:18})])] }),
      ]}),
      new TableRow({ children: [
        new TableCell({ margins:{top:60,bottom:60,left:100,right:100}, width:{size:1200,type:WidthType.DXA}, children:[para([italicRun('Apr 2021',{size:18})])] }),
        new TableCell({ margins:{top:60,bottom:60,left:100,right:100}, width:{size:CW-2400,type:WidthType.DXA}, children:[para([run('A Machine Learning-Based System for Detecting Leishmaniasis in Microscopic Images',{size:18})])] }),
        new TableCell({ margins:{top:60,bottom:60,left:100,right:100}, width:{size:1200,type:WidthType.DXA}, children:[para([run('IR · 140050140003000416',{size:18})])] }),
      ]}),
      new TableRow({ children: [
        new TableCell({ margins:{top:60,bottom:60,left:100,right:100}, width:{size:1200,type:WidthType.DXA}, children:[para([italicRun('Oct 2020',{size:18})])] }),
        new TableCell({ margins:{top:60,bottom:60,left:100,right:100}, width:{size:CW-2400,type:WidthType.DXA}, children:[para([run('Utilization of Chest Tube in Pediatric Caustic Injuries: A New Method for Esophageal Stenting',{size:18})])] }),
        new TableCell({ margins:{top:60,bottom:60,left:100,right:100}, width:{size:1200,type:WidthType.DXA}, children:[para([run('IR · 139950140003006653',{size:18})])] }),
      ]}),
    ],
  }));

  // ── PUBLICATIONS SUMMARY ──────────────────────────────────────────────────
  children.push(new Paragraph({ spacing: { before: 120, after: 0 } }));
  children.push(sectionHeading('Publications'));
  const pubMetrics = [
    ['Citations', CITATIONS, 'https://scholar.google.com/citations?user=mOE1KmEAAAAJ&hl=en'],
    ['H-index', HINDEX, null],
    ['Publications', PUB_COUNT, null],
    ['First author', FIRST_AUTH, null],
    ['Second / co-first author', SECOND_AUTH, null],
    ['Last author', LAST_AUTH, null],
    ['Corresponding author', CORR_AUTH, null],
  ];
  children.push(new Table({
    width: { size: CW, type: WidthType.DXA }, columnWidths: [2000, 2000, 2000],
    borders: {top:{style:BorderStyle.SINGLE,size:4,color:'CCCCCC'},bottom:{style:BorderStyle.SINGLE,size:4,color:'CCCCCC'},
      left:{style:BorderStyle.NONE},right:{style:BorderStyle.NONE},
      insideHorizontal:{style:BorderStyle.SINGLE,size:2,color:'EEEEEE'},insideVertical:{style:BorderStyle.NONE}},
    rows: [
      new TableRow({ tableHeader:true, children: [
        new TableCell({ shading:{fill:'F0F4F8',type:ShadingType.CLEAR}, margins:{top:60,bottom:60,left:100,right:100},
          width:{size:2000,type:WidthType.DXA}, children:[para([boldRun('Metrics',{size:18})])] }),
        new TableCell({ shading:{fill:'F0F4F8',type:ShadingType.CLEAR}, margins:{top:60,bottom:60,left:100,right:100},
          width:{size:2000,type:WidthType.DXA}, children:[para([run('',{size:18})])] }),
        new TableCell({ shading:{fill:'F0F4F8',type:ShadingType.CLEAR}, margins:{top:60,bottom:60,left:100,right:100},
          width:{size:2000,type:WidthType.DXA}, children:[para([run('',{size:18})])] }),
      ]}),
      ...pubMetrics.map(([label, val, url]) => new TableRow({ children: [
        new TableCell({ margins:{top:60,bottom:60,left:100,right:100}, width:{size:2000,type:WidthType.DXA}, children:[para([run('',{size:18})])] }),
        new TableCell({ margins:{top:60,bottom:60,left:100,right:100}, width:{size:2000,type:WidthType.DXA}, children:[para([run(label,{size:18})])] }),
        new TableCell({ margins:{top:60,bottom:60,left:100,right:100}, width:{size:2000,type:WidthType.DXA}, children:[
          url ? para([new ExternalHyperlink({link:url, children:[new TextRun({text:val,font:'Calibri',size:20,color:STEEL,bold:true,underline:{type:UnderlineType.SINGLE}})]})]) : para([boldRun(val)])
        ]}),
      ]})),
    ],
  }));
  children.push(para([run('Full list: '), new ExternalHyperlink({link:'https://scholar.google.com/citations?user=mOE1KmEAAAAJ&hl=en', children:[
    new TextRun({text:'Appendix A. List of Publications',font:'Calibri',size:20,color:STEEL,underline:{type:UnderlineType.SINGLE}})
  ]})], { spacing: { before: 80, after: 60 } }));

  // ── EDITOR & REVIEWER ─────────────────────────────────────────────────────
  children.push(new Paragraph({ spacing: { before: 120, after: 0 } }));
  children.push(sectionHeading('Editor & Reviewer Experience'));
  children.push(para([boldRun('Editor Roles', { color: NAVY })], { spacing: { before: 60, after: 40 } }));
  children.push(para([run('• PLOS One — '), italicRun('Guest Editor (June 2022)')]));
  children.push(para([run('• '), new ExternalHyperlink({link:'https://semj.brieflands.com/en/people/certificate/24156995f52b22cd8', children:[
    new TextRun({text:'Shiraz E-Medical Journal',font:'Calibri',size:20,color:STEEL,underline:{type:UnderlineType.SINGLE}})]}),
    run(' — '), italicRun('Associate Editor (August 2021)')]));
  children.push(para([boldRun('Reviewer Role', { color: NAVY })], { spacing: { before: 80, after: 40 } }));
  children.push(para([
    boldRun(PEER_REVIEWS), run(' peer reviews of '), boldRun(MANUSCRIPTS), run(' manuscripts in '), boldRun(JOURNALS), run(' international journals'),
  ]));
  children.push(para([run('Full list: '), new ExternalHyperlink({link:'https://www.webofscience.com/wos/author/record/ABC-9194-2020', children:[
    new TextRun({text:'Web of Science Reviewer Profile',font:'Calibri',size:20,color:STEEL,underline:{type:UnderlineType.SINGLE}})]})
  ], { spacing: { after: 60 } }));

  // ── PRESENTATIONS ─────────────────────────────────────────────────────────
  children.push(new Paragraph({ spacing: { before: 120, after: 0 } }));
  children.push(sectionHeading('Presentations'));
  children.push(para([
    boldRun('Conferences: '), run('Plastic Surgery Research Council (PSRC); Society of Surgical Oncology (SSO); AOFAS Annual Meeting 2025; Annual Balfour Surgery Research Symposium; Mayo Clinic AI Summit; Advanced Robotic Surgery Conference 2025; Organ Transplantation before and during the COVID-19 era; 31st Biennial Congress of ISUCRS; 10th National Burn Congress 2021; Transplantation; 26th European Paediatric Rheumatology e-Congress (PReS); NICOPA11; First National Congress on Animal Models in Experimental Medical Researches; 3rd Professor Amirhakimi Pediatric Congress; ISCOMS 2015', {size:18}),
  ], { spacing: { after: 40 } }));
  children.push(para([boldRun('Posters: '), run('12', {size:18})]));
  children.push(para([boldRun('Oral: '), run('2', {size:18})], { spacing: { after: 40 } }));
  children.push(para([run('Detailed list: Appendix C'), ]));

  // ── LANGUAGES & HOBBIES ───────────────────────────────────────────────────
  children.push(new Paragraph({ spacing: { before: 120, after: 0 } }));
  children.push(sectionHeading('Languages, Extracurricular Activities and Hobbies'));
  children.push(simpleTable([
    twoColRow(para([boldRun('Languages: ')]), para([italicRun('English (Fluent), Farsi (Native)')])),
    twoColRow(para([boldRun('Hobbies: ')]), [
      para([italicRun('Professional Guitarist — Several live stage and group performances')]),
      para([italicRun('Basketball — Member of middle and high school basketball team')]),
      para([italicRun('Camping and traveling')]),
      para([italicRun('Computer and Console Gaming')]),
    ]),
  ], [1800, CW - 1800]));

  // ── REFERENCES ────────────────────────────────────────────────────────────
  children.push(new Paragraph({ spacing: { before: 120, after: 0 } }));
  children.push(sectionHeading('References'));
  children.push(para([italicRun('Contact information available upon request', { color: MUTED, size: 18 })], { spacing: { after: 60 } }));
  const refs = [
    { name: 'Dr. Janani S. Reisenauer, MD', role: 'Professor of Surgery; Chair, Division of Thoracic Surgery; Interventional Pulmonary Medicine; Assistant Medical Director, Research Innovation and Business Development', inst: 'Department of Surgery, Mayo Clinic, Rochester, MN, USA', url: 'https://www.mayoclinic.org/biographies/reisenauer-janani-s-m-d/bio-20433096' },
    { name: 'Dr. Simon J. Laplante, MD', role: 'Assistant Professor of Bariatric Surgery, Division of Metabolic and Abdominal Wall Reconstructive Surgery', inst: 'Department of Surgery, Mayo Clinic, Rochester, MN, USA', url: 'https://www.mayoclinic.org/biographies/laplante-simon-j-m-d/bio-20573005' },
    { name: 'Dr. Kitty Y. Wu, MD, MSc, FRCSC', role: 'Assistant Professor of Plastic Surgery, Division of Plastic and Reconstructive Surgery', inst: 'Department of Surgery, Mayo Clinic, Rochester, MN, USA', url: 'https://www.mayoclinic.org/biographies/wu-kitty-y-m-d/bio-20552093' },
    { name: 'Dr. Aparna Vijayasekaran, MBBS', role: 'Assistant Professor of Plastic Surgery, Division of Plastic and Reconstructive Surgery', inst: 'Department of Surgery, Mayo Clinic, Rochester, MN, USA', url: 'https://www.mayoclinic.org/biographies/vijayasekaran-aparna-m-b-b-s/bio-20453484' },
    { name: 'Dr. Cornelius A. Thiels, DO, MBA, FACS', role: 'Associate Professor of Surgery and Health Services Research; Associate Chair of Innovation; Co-Director, Surgical AI² Lab', inst: 'Department of Surgery, Mayo Clinic, Rochester, MN, USA', url: 'https://www.mayoclinic.org/biographies/thiels-cornelius-a-d-o-m-b-a/bio-20519744' },
    { name: 'Dr. Soheil Ashkani-Esfahani, MD, MPH', role: 'Assistant Professor of Orthopedic Surgery, Harvard Medical School; Director, FARIL; Clinical Executive Director, Mass General Brigham Orthopaedic Registry', inst: 'Department of Orthopaedic Surgery, Massachusetts General Hospital, Boston, MA, USA', url: 'https://connects.catalyst.harvard.edu/profiles/display/Person/186262' },
    { name: 'Dr. Mohammad Javad Fallahi, MD', role: 'Associate Professor; Chair, Division of Internal Medicine; Pulmonology Division', inst: 'Department of Internal Medicine, Shiraz University of Medical Sciences, Shiraz, Iran', url: null },
    { name: 'Dr. Bizhan Ziaian, MD', role: 'Associate Professor of Thoracic Surgery; Director, Thoracic and Vascular Surgery Research Center (TAVS)', inst: 'Shiraz University of Medical Sciences, Shiraz, Iran', url: null },
    { name: 'Dr. Alireza Rezvani, MD', role: 'Assistant Professor of Hematology and Oncology; Vice Chancellor for Research', inst: 'Department of Internal Medicine, Shiraz University of Medical Sciences, Shiraz, Iran', url: null },
  ];
  refs.forEach((ref, i) => {
    children.push(para([
      boldRun(`${i+1}.  ${ref.name}`),
    ], { spacing: { before: 60, after: 20 } }));
    children.push(para([italicRun(ref.role, { size: 18, color: STEEL })]));
    children.push(para([italicRun(ref.inst, { size: 18, color: MUTED })], { spacing: { after: 40 } }));
  });

  // ── APPENDIX A: FULL PUBLICATIONS ─────────────────────────────────────────
  children.push(new Paragraph({ pageBreakBefore: true, children: [] }));
  children.push(sectionHeading('Appendix A. List of Publications'));
  children.push(para([italicRun('* Indicator of the corresponding author. Author name in bold = Reza Shahriarirad.', { size: 18, color: MUTED })], { spacing: { after: 80 } }));

  // Originals
  const originals = pubs.filter(p => p.type === 'original' || p.type === 'first');
  const cases = pubs.filter(p => p.type === 'case');
  const letters = pubs.filter(p => p.type === 'letter');

  children.push(para([boldRun('Original Articles, Reviews, and Meta-analyses', { color: NAVY })], { spacing: { before: 80, after: 60 } }));
  originals.forEach((pub, i) => {
    const auFormatted = pub.authors.replace(/Shahriarirad R\*?/g, m => m); // keep as-is, bold handled below
    children.push(para([
      run(`${i+1}.  `, { bold: true, size: 18 }),
      ...buildPubRuns(pub),
    ], { spacing: { after: 60 }, indent: { left: 360, hanging: 360 } }));
  });

  children.push(para([boldRun('Case Reports', { color: NAVY })], { spacing: { before: 120, after: 60 } }));
  cases.forEach((pub, i) => {
    children.push(para([
      run(`${originals.length + i + 1}.  `, { bold: true, size: 18 }),
      ...buildPubRuns(pub),
    ], { spacing: { after: 60 }, indent: { left: 360, hanging: 360 } }));
  });

  children.push(para([boldRun('Letters to Editor', { color: NAVY })], { spacing: { before: 120, after: 60 } }));
  letters.forEach((pub, i) => {
    children.push(para([
      run(`${originals.length + cases.length + i + 1}.  `, { bold: true, size: 18 }),
      ...buildPubRuns(pub),
    ], { spacing: { after: 60 }, indent: { left: 360, hanging: 360 } }));
  });

  // ── APPENDIX B: JOURNALS ──────────────────────────────────────────────────
  children.push(new Paragraph({ pageBreakBefore: true, children: [] }));
  children.push(sectionHeading('Appendix B. List of Journals Reviewed'));
  const journals = require('/home/claude/cv_journals.json');
  journals.forEach((j, i) => {
    children.push(para([run(`${i+1}. ${j.name}`, { size: 18 })]));
  });

  // ── APPENDIX C: PRESENTATIONS ─────────────────────────────────────────────
  children.push(new Paragraph({ pageBreakBefore: true, children: [] }));
  children.push(sectionHeading('Appendix C. List of Presentations'));
  const presentations = require('/home/claude/cv_presentations.json');
  presentations.forEach((p, i) => {
    children.push(para([
      boldRun(`${p.date} [${p.type}]: `, { size: 18 }),
      run(p.title, { size: 18 }),
    ]));
    children.push(para([italicRun(p.venue, { size: 17, color: MUTED })], { spacing: { after: 60 } }));
  });

  return children;
}

function buildPubRuns(pub) {
  // Bold "Shahriarirad R" in authors
  const authorParts = pub.authors.split(/(Shahriarirad R\*?)/);
  const authorRuns = [];
  authorParts.forEach(part => {
    if (part.match(/^Shahriarirad R/)) {
      authorRuns.push(new TextRun({ text: part, font: 'Calibri', size: 18, bold: true }));
    } else if (part) {
      authorRuns.push(new TextRun({ text: part, font: 'Calibri', size: 18 }));
    }
  });

  const titleRun = pub.url
    ? new ExternalHyperlink({ link: pub.url, children: [new TextRun({ text: pub.title + '.', font: 'Calibri', size: 18, color: STEEL, underline: { type: UnderlineType.SINGLE } })] })
    : new TextRun({ text: pub.title + '.', font: 'Calibri', size: 18 });

  return [
    ...authorRuns,
    new TextRun({ text: '. ', font: 'Calibri', size: 18 }),
    titleRun,
    new TextRun({ text: ' ', font: 'Calibri', size: 18 }),
    new TextRun({ text: pub.journal, font: 'Calibri', size: 18, italics: true }),
    new TextRun({ text: pub.year ? ` (${pub.year})` : '', font: 'Calibri', size: 18, color: MUTED }),
  ];
}

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: 'Calibri', size: 20, color: BLACK } },
    },
  },
  sections: [{
    properties: {
      page: {
        size: { width: W, height: 15840 },
        margin: { top: MARGIN, right: MARGIN, bottom: MARGIN, left: MARGIN },
      },
    },
    footers: {
      default: new Footer({
        children: [new Paragraph({
          alignment: AlignmentType.CENTER,
          children: [
            new TextRun({ text: 'Reza Shahriarirad, M.D.  ·  ', font: 'Calibri', size: 16, color: MUTED }),
            new TextRun({ children: [PageNumber.CURRENT], font: 'Calibri', size: 16, color: MUTED }),
            new TextRun({ text: ' of ', font: 'Calibri', size: 16, color: MUTED }),
            new TextRun({ children: [PageNumber.TOTAL_PAGES], font: 'Calibri', size: 16, color: MUTED }),
          ],
        })],
      }),
    },
    children: buildCV(),
  }],
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync('/home/claude/Shahriarirad_CV_Generated.docx', buffer);
  console.log('DOCX generated successfully');
}).catch(err => {
  console.error('Error:', err.message);
  process.exit(1);
});

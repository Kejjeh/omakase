const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        AlignmentType, BorderStyle, WidthType, ShadingType, TabStopType } = require('docx');
const fs = require('fs');

const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

const colW = [2340, 2340, 2340, 2340];
const blueBg = "E6F1FB";
const creamBg = "F1EFE8";
const greenBg = "E8F5E9";

function makeInfoTable(r) {
  function makeCell(label, value, bg, boldVal) {
    return new TableCell({
      borders: noBorders,
      width: { size: 2340, type: WidthType.DXA },
      shading: { fill: bg, type: ShadingType.CLEAR },
      margins: { top: 40, bottom: 40, left: 80, right: 80 },
      children: [new Paragraph({
        children: [
          new TextRun({ text: `${label}: `, font: "Arial", size: 17, color: "555555" }),
          new TextRun({ text: value, font: "Arial", size: 17, bold: boldVal !== false }),
        ]
      })]
    });
  }
  const byobBold = r.byob.toLowerCase().startsWith("yes");
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    columnWidths: colW,
    rows: [
      new TableRow({
        children: [
          makeCell("Price", r.price, blueBg),
          makeCell("Courses", r.courses, blueBg),
          makeCell("Session", r.session, greenBg),
          makeCell("BYOB", r.byob, creamBg, byobBold),
        ]
      })
    ]
  });
}

const restaurants = [
  {
    rank: 1, name: "Ishi Omakase Sushi & Premium Sake",
    location: "Park Slope - 70 5th Ave",
    price: "$85 / $105 / $125", courses: "~14 / ~16 / 18", session: "~105 min", byob: "No",
    desc: "3 tiers: Table $85 (served in flights), Table $105, Chef's Counter $125 (18, served directly by chef). Chef Jack was executive head chef at NOBU. Strongest chef pedigree on this list. Premium sake selection. No rush."
  },
  {
    rank: 2, name: "Mido Omakase",
    location: "Williamsburg - 221 S 1st St  |  West Village - 88 W 3rd St  |  UWS - 612 Amsterdam Ave",
    price: "$100 / $150", courses: "15 / 17", session: "75-90 min", byob: "No",
    desc: "Standard $100 (15). Premium $150 (3 appetizers, 13 sushi pieces, handroll, dessert). Chef Sato Cheuk trained in French haute cuisine then mastered Edomae sushi in Japan. Owner Ben Leung. Both from Hong Kong. Weekend brunch omakase $68 (10, Sat/Sun noon to 3pm)."
  },
  {
    rank: 3, name: "Shinzo Omakase",
    location: "East Village - 89 E 2nd St",
    price: "$69 / $138", courses: "13 / 26", session: "60 min", byob: "Yes, no corkage",
    desc: "Best value play: $69 gets 13. Can double to 26 for $138. Shinzo Special add-on +$25. BYOB with no corkage fee. 5 seatings per night. Great for a big appetite, bring your own sake night."
  },
  {
    rank: 4, name: "Sushi Saikou",
    location: "Nolita - 301 Elizabeth St",
    price: "$120", courses: "17", session: "75-90 min", byob: "No",
    desc: "Chef Alvin with 25+ years of experience. 17 at $120. Strong course to dollar ratio. Newer establishment generating buzz. High ratings across all review platforms."
  },
  {
    rank: 5, name: "Idashi Omakase",
    location: "Park Slope - 464 Bergen St",
    price: "$99", courses: "16", session: "90 min", byob: "Yes",
    desc: "16 courses: 3 appetizers, 10 nigiri, uni ikura mini don, handroll, dessert. Longest sessions on this list. No rush. Chef Ellis C with 10+ years experience. BYOB."
  },
  {
    rank: 6, name: "Sushi Yolo",
    location: "Hell's Kitchen - 348 W 57th St",
    price: "$109", courses: "14", session: "60-75 min", byob: "No",
    desc: "14 courses: 4 appetizers, 10 nigiri, 1 handroll, 1 dessert. Near Columbus Circle. Solid ratings, clean straightforward omakase experience."
  },
  {
    rank: 7, name: "Omakase by Korami",
    location: "Hell's Kitchen - 400A W 50th St",
    price: "$89", courses: "15", session: "60 min", byob: "No",
    desc: "10 seats, 3 chefs (William, Ryan, Kong). Known for intimate, chatty atmosphere with pop music soundtrack. 60 min time limit. Great for a social dinner."
  },
  {
    rank: 8, name: "Zen Sushi Omakase",
    location: "LES - 235 Eldridge St",
    price: "$89", courses: "14", session: "60-75 min", byob: "No",
    desc: "Chefs trained at Michelin starred restaurants. 75 to 85% of fish flown from Toyosu and Fukuoka markets within 24 hours. Strongest sourcing claim on this list."
  },
  {
    rank: 9, name: "Genki Omakase",
    location: "Greenwich Village - 552 LaGuardia Pl  |  LES - 111 Stanton St",
    price: "$75 / $98", courses: "13 / 15", session: "60 min", byob: "Yes, $50 corkage",
    desc: "13 at $75, 15 at $98. Chefs Jay and Brian. Two locations. BYOB but now charges $50 corkage. 60 min strict timing."
  },
  {
    rank: 10, name: "Thirteen Water",
    location: "East Village (East) - 208 E 7th St  |  Chelsea (West) - 366 W 30th St",
    price: "$75 / $85", courses: "13 / 15", session: "60-75 min", byob: "No",
    desc: "Chefs Aaron and Edison. U shaped counter. Known for a layered flavor concept where each piece is built with multiple textural and flavor components. East: $75/13. West (Chelsea): $85/15."
  },
  {
    rank: 11, name: "Sushi by M",
    location: "East Village (M1) - 300 E 5th St  |  East Village - 75 E 4th St  |  UES - 1575 2nd Ave",
    price: "$69 / $100", courses: "12 / 16", session: "60-75 min", byob: "No",
    desc: "Two tiers: $69 for 12, $100 for 16. Small counter + outdoor patio at M1. 2,190 Google reviews, the most reviewed on this entire list. Casual vibe. Three locations."
  },
  {
    rank: 12, name: "Mojo East",
    location: "LES - 85 Stanton St",
    price: "$55", courses: "13", session: "60 min", byob: "No",
    desc: "Cheapest on this list. No tipping policy (true $55 all in). Same founder as SourAji. Chefs Ken and Jay. Disney music soundtrack. Fun, lighthearted, budget friendly. Sister spot Mojo Omakase in Chelsea (177 9th Ave)."
  },
];

const children = [];

// Title - tighter spacing
children.push(new Paragraph({
  spacing: { after: 20 },
  children: [new TextRun({ text: "NYC Omakase - Top 12 Shortlist", font: "Arial", size: 34, bold: true })]
}));

children.push(new Paragraph({ spacing: { after: 200 }, children: [] }));

restaurants.forEach((r, i) => {
  // Rank left + Name centered on same line via tab
  children.push(new Paragraph({
    spacing: { before: i === 0 ? 0 : 200, after: 30 },
    tabStops: [{ type: TabStopType.CENTER, position: 5100 }],
    children: [
      new TextRun({ text: `#${r.rank}`, font: "Arial", size: 19, color: "888888" }),
      new TextRun({ text: "\t" }),
      new TextRun({ text: r.name, font: "Arial", size: 24, bold: true }),
    ]
  }));

  // Location - single line, centered
  children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 50 },
    children: [
      new TextRun({ text: r.location, font: "Arial", size: 18, color: "444444" }),
    ]
  }));

  // Info table
  children.push(makeInfoTable(r));

  // Description
  children.push(new Paragraph({
    spacing: { before: 60, after: 0 },
    children: [new TextRun({ text: r.desc, font: "Arial", size: 19 })]
  }));
});

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Arial", size: 19 } } },
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1080, right: 1080, bottom: 1080, left: 1080 },
      },
    },
    children,
  }]
});

Packer.toBuffer(doc).then(buffer => {
  fs.writeFileSync("/sessions/serene-inspiring-ramanujan/mnt/outputs/Omakase_Top12_compact.docx", buffer);
  console.log("Done! " + buffer.length + " bytes");
});

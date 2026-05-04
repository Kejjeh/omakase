const { Document, Packer, Paragraph, TextRun, Table, TableRow, TableCell,
        AlignmentType, BorderStyle, WidthType, ShadingType, TabStopType } = require('docx');
const fs = require('fs');

const noBorder = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
const noBorders = { top: noBorder, bottom: noBorder, left: noBorder, right: noBorder };

// Rebalanced: give Session and BYOB more room, shrink G/Y
// Total must = 9360 (US Letter minus 1.5" margins = 12240 - 2*1440 = 9360... wait margins are 1080)
// 12240 - 2*1080 = 10080 content width
const totalW = 10080;
const colW = [1800, 1600, 1700, 1700, 3280];
const blueBg = "E6F1FB";
const creamBg = "F1EFE8";
const greenBg = "E8F5E9";
const grayBg = "F0F0F0";

function makeInfoTable(r) {
  function makeCell(label, value, bg, w, boldVal) {
    return new TableCell({
      borders: noBorders,
      width: { size: w, type: WidthType.DXA },
      shading: { fill: bg, type: ShadingType.CLEAR },
      margins: { top: 40, bottom: 40, left: 60, right: 60 },
      verticalAlign: "center",
      children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [
          new TextRun({ text: `${label}: `, font: "Arial", size: 15, color: "555555" }),
          new TextRun({ text: value, font: "Arial", size: 15, bold: boldVal !== false }),
        ]
      })]
    });
  }
  const byobBold = r.byob.toLowerCase().startsWith("yes");
  return new Table({
    width: { size: totalW, type: WidthType.DXA },
    columnWidths: colW,
    rows: [
      new TableRow({
        children: [
          makeCell("Price", r.price, blueBg, colW[0]),
          makeCell("Courses", r.courses, blueBg, colW[1]),
          makeCell("Session", r.session, greenBg, colW[2]),
          makeCell("BYOB", r.byob, creamBg, colW[3], byobBold),
          makeCell("G / Y", r.ratings, grayBg, colW[4]),
        ]
      })
    ]
  });
}

const restaurants = [
  { rank: 1, name: "Sushi Yolo", tag: null, location: "Hell's Kitchen - 348 W 57th St",
    price: "$109", courses: "14", session: "60-75 min", byob: "No",
    ratings: "4.9 (231) / 5.0 (94)",
    desc: "14 courses: 4 appetizers, 10 nigiri, 1 handroll, 1 dessert. Near Columbus Circle. Solid ratings, clean straightforward omakase experience." },
  { rank: 2, name: "Mido Omakase", tag: null, location: "Williamsburg - 221 S 1st St  |  West Village - 88 W 3rd St  |  UWS - 612 Amsterdam Ave",
    price: "$100 / $150", courses: "15 / 17", session: "75-90 min", byob: "No",
    ratings: "5.0 (868) / 5.0 (43)",
    desc: "Standard $100 (15). Premium $150 (3 appetizers, 13 sushi pieces, handroll, dessert). Chef Sato Cheuk trained in French haute cuisine then mastered Edomae sushi in Japan. Owner Ben Leung. Both from Hong Kong. Weekend brunch omakase $68 (10, Sat/Sun noon to 3pm)." },
  { rank: 3, name: "Omakase by Korami", tag: null, location: "Hell's Kitchen - 400A W 50th St",
    price: "$89", courses: "15", session: "60 min", byob: "No",
    ratings: "4.8 (654) / 4.8 (546)",
    desc: "10 seats, 3 chefs (William, Ryan, Kong). Known for intimate, chatty atmosphere with pop music soundtrack. 60 min time limit. Great for a social dinner." },
  { rank: 4, name: "Kaki", tag: "Friend rec", location: "LES - 129 Rivington St",
    price: "$75-85", courses: "15", session: "75-90 min", byob: "Yes",
    ratings: "4.9 (219) / -",
    desc: "15 courses at a very accessible price point. Chef-driven LES spot known for creative presentations and a signature fire course. Intimate room, fresh fish, strong neighborhood following." },
  { rank: 5, name: "Sushi Saikou", tag: null, location: "Nolita - 301 Elizabeth St",
    price: "$120", courses: "17", session: "75-90 min", byob: "No",
    ratings: "4.9 (277) / 5.0 (36)",
    desc: "Chef Alvin with 25+ years of experience. 17 at $120. Strong course to dollar ratio. Newer establishment generating buzz. High ratings across all review platforms." },
  { rank: 6, name: "Shinzo Omakase", tag: null, location: "East Village - 89 E 2nd St",
    price: "$69 / $138", courses: "13 / 26", session: "60 min", byob: "Yes, no fee",
    ratings: "4.9 (967) / 4.7 (146)",
    desc: "Best value play: $69 gets 13. Can double to 26 for $138. Shinzo Special add-on +$25. BYOB with no fee. 5 seatings per night. Great for a big appetite, bring your own sake night." },
  { rank: 7, name: "Idashi Omakase", tag: null, location: "Park Slope - 464 Bergen St",
    price: "$99", courses: "16", session: "90 min", byob: "Yes",
    ratings: "4.9 (238) / 4.8 (42)",
    desc: "16 courses: 3 appetizers, 10 nigiri, uni ikura mini don, handroll, dessert. Longest sessions on this list. No rush. Chef Ellis C with 10+ years experience. BYOB." },
  { rank: 8, name: "Ishi Omakase Sushi & Premium Sake", tag: null, location: "Park Slope - 70 5th Ave",
    price: "$85 / $105 / $125", courses: "~14 / ~16 / 18", session: "~105 min", byob: "No",
    ratings: "4.8 (214) / 4.7 (73)",
    desc: "3 tiers: Table $85 (served in flights), Table $105, Chef's Counter $125 (18, served directly by chef). Chef Jack was executive head chef at NOBU. Strongest chef pedigree on this list. Premium sake selection. No rush." },
  { rank: 9, name: "Sushi by M", tag: null, location: "East Village (M1) - 300 E 5th St  |  East Village - 75 E 4th St  |  UES - 1575 2nd Ave",
    price: "$69 / $100", courses: "12 / 16", session: "60-75 min", byob: "No",
    ratings: "4.5 (951) / 4.5 (1,239)",
    desc: "Two tiers: $69 for 12, $100 for 16. Small counter + outdoor patio at M1. Most reviewed omakase on this list. Casual vibe. Three locations." },
  { rank: 10, name: "Zen Sushi Omakase", tag: null, location: "LES - 235 Eldridge St",
    price: "$89", courses: "14", session: "60-75 min", byob: "No",
    ratings: "4.9 (370) / 4.7 (50)",
    desc: "Chefs trained at Michelin starred restaurants. 75 to 85% of fish flown from Toyosu and Fukuoka markets within 24 hours. Strongest sourcing claim on this list." },
  { rank: 11, name: "Genki Omakase", tag: null, location: "Greenwich Village - 552 LaGuardia Pl  |  LES - 111 Stanton St",
    price: "$75 / $98", courses: "13 / 15", session: "60 min", byob: "Yes, $50 fee",
    ratings: "4.8 (1,401) / 4.5 (308)",
    desc: "13 at $75, 15 at $98. Chefs Jay and Brian. Two locations. BYOB but now charges $50 fee. 60 min strict timing." },
  { rank: 12, name: "Thirteen Water", tag: null, location: "East Village (East) - 208 E 7th St  |  Chelsea (West) - 366 W 30th St",
    price: "$75 / $85", courses: "13 / 15", session: "60-75 min", byob: "No",
    ratings: "4.6 (436) / 4.6 (282)",
    desc: "Chefs Aaron and Edison. U shaped counter. Known for a layered flavor concept where each piece is built with multiple textural and flavor components. East: $75/13. West (Chelsea): $85/15." },
  { rank: 13, name: "Mojo East", tag: null, location: "LES - 85 Stanton St",
    price: "$55", courses: "13", session: "60 min", byob: "No",
    ratings: "4.7 (326) / 4.5 (125)",
    desc: "Cheapest on this list. No tipping policy (true $55 all in). Same founder as SourAji. Chefs Ken and Jay. Disney music soundtrack. Fun, lighthearted, budget friendly. Sister spot Mojo Omakase in Chelsea (177 9th Ave)." },
  { rank: 14, name: "Shiki Omakase", tag: "Visited together", location: "SoHo - 71 W Houston St",
    price: "$65 / $100", courses: "12 / 17", session: "45-60 min", byob: "Yes, $20 fee",
    ratings: "4.5 (458) / 4.5 (653)",
    desc: "12-seat omakase run by chef duo Lin and Jackie. Name means \"four seasons\" in Japanese. Known for fast pacing and playful presentation. Seared A5 Wagyu highlight. BYOB with $20 fee." },
  { rank: 15, name: "Sushi Oku", tag: "Friend rec", location: "LES - 22 Orchard St",
    price: "$85 / $100", courses: "17", session: "75-90 min", byob: "No",
    ratings: "4.8 (67) / -",
    desc: "17 course omakase journey led by Executive Chef Kei Yoshino. Intimate 8-seat counter in the back of the old Scarr's Pizza space. $85 at dining tables, $100 at the sushi counter. Also offers okonomi (a la carte) and a sake bar. Traditional edomae technique." },
];

const children = [];

children.push(new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { after: 200 },
  children: [new TextRun({ text: "NYC Omakase - Top 15 Shortlist", font: "Arial", size: 34, bold: true })]
}));

restaurants.forEach((r, i) => {
  // Rank + tag + Name on same line
  const runs = [];
  runs.push(new TextRun({ text: `#${r.rank}`, font: "Arial", size: 19, color: "888888" }));
  
  if (r.tag) {
    const tagColor = r.tag === "Visited together" ? "C25A3C" : "E8900C";
    const tagBg = r.tag === "Visited together" ? "FBEAEA" : "FFF3E0";
    runs.push(new TextRun({ text: "  " }));
    runs.push(new TextRun({ text: ` ${r.tag} `, font: "Arial", size: 14, bold: true, color: tagColor,
      shading: { fill: tagBg, type: ShadingType.CLEAR } }));
  }
  
  runs.push(new TextRun({ text: "\t" }));
  runs.push(new TextRun({ text: r.name, font: "Arial", size: 24, bold: true }));

  children.push(new Paragraph({
    spacing: { before: i === 0 ? 0 : 200, after: 30 },
    tabStops: [{ type: TabStopType.CENTER, position: 5040 }],
    children: runs,
  }));

  // Location centered
  children.push(new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 50 },
    children: [
      new TextRun({ text: r.location, font: "Arial", size: 18, color: "444444" }),
    ]
  }));

  // Info table
  children.push(makeInfoTable(r));

  // Description - left aligned
  children.push(new Paragraph({
    alignment: AlignmentType.LEFT,
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
  fs.writeFileSync("/sessions/serene-inspiring-ramanujan/mnt/outputs/Omakase_Top15_v4.docx", buffer);
  console.log("Done! " + buffer.length + " bytes");
});

# Yelp Research Prompt (Italian — round 2)

Paste the following prompt into a Claude or ChatGPT deep research session. It will look up each restaurant on Yelp and return a structured JSON table you can save as `scripts/data/italian/yelp_cache.json` in the Omakase project folder (merge with the existing file, do not overwrite).

---

## PROMPT (copy everything below this line)

I need you to look up Yelp ratings for a list of 132 NYC Italian restaurants (trattorias, osterias, pizzerias, red-sauce houses, modern Italian, etc.). For each restaurant, please search Yelp and find:

1. **Yelp rating** (1-5 scale, half-star increments)
2. **Review count** (number of Yelp reviews)
3. **Yelp price level** ($ to $$$$)
4. **Yelp URL** (the full yelp.com link)

If a restaurant cannot be found on Yelp, mark it as `null` for all fields.

**Important notes:**
- These are all NYC restaurants (Manhattan, Brooklyn, Queens, Bronx)
- Many are common Italian names — use the neighborhood I provide to disambiguate carefully
- Some have multiple locations — match the one in the listed neighborhood
- If there are multiple Yelp listings for the same restaurant in the same neighborhood, use the one with the most reviews

**Multi-location brands that need careful disambiguation (confirmed pitfalls):**
- **Sant Ambroeus** — 5 NYC locations. Match the listed neighborhood (West Village, UES/Madison flagship, etc.)
- **Il Mulino vs Il Mulino Prime** — different concepts. "Il Mulino New York" = 86 W 3rd St Greenwich Village. "Il Mulino Prime" = Tribeca steakhouse, different page.
- **Patsy's vs Patsy's Pizzeria** — unrelated brands. "Patsy's Italian Restaurant" = W 56th St Midtown. "Patsy's Pizzeria" = East Harlem flagship.
- **Sottocasa** — separate pages for Harlem, Boerum Hill (Atlantic Ave), and Williamsburg/Greenpoint.
- **Grimaldi's, Tarallucci e Vino, La Pecora Bianca, Frankies (457 BK is active; 570 NYC is CLOSED — already filtered out)** — match by neighborhood.
- **Fiaschetteria Pistoia** — multiple pages. The 114 Christopher St West Village page is the active one.

**Output format:** Please return the results as a JSON object with this exact structure:

```json
{
  "Restaurant Name": {
    "yelp_rating": 4.5,
    "review_count": 234,
    "price_level": "$$$$",
    "yelp_url": "https://www.yelp.com/biz/restaurant-name-new-york",
    "yelp_name": "Restaurant Name As Listed On Yelp"
  },
  "Another Restaurant": {
    "yelp_rating": null,
    "review_count": null,
    "price_level": null,
    "yelp_url": null,
    "yelp_name": null
  }
}
```

**Here is the full list of 132 restaurants:**

1. San Sabino | Manhattan (West Village / Greenwich Village)
2. Villa Mosconi | Manhattan (West Village / Greenwich Village)
3. Torrisi Bar & Restaurant | Manhattan (West Village / Greenwich Village)
4. Roscioli | Manhattan (West Village / Greenwich Village)
5. Sant Ambroeus West Village | Manhattan (West Village / Greenwich Village)
6. Malaparte | Manhattan (West Village / Greenwich Village)
7. Da Toscano | Manhattan (West Village / Greenwich Village)
8. Fiaschetteria Pistoia | Manhattan (West Village / Greenwich Village)
9. Osteria Nonnino | Manhattan (West Village / Greenwich Village)
10. Arthur & Sons NY Italian | Manhattan (West Village / Greenwich Village)
11. Da Andrea | Manhattan (West Village / Greenwich Village)
12. Il Mulino New York | Manhattan (West Village / Greenwich Village)
13. Olio e Più | Manhattan (West Village / Greenwich Village)
14. Lavagna | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
15. Il Posto Accanto | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
16. Supper | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
17. Cacio e Pepe | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
18. John's of 12th Street | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
19. Forsythia | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
20. Altro Paradiso | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
21. Pasquale Jones | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
22. Sandro's | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
23. Gelso & Grand | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
24. Parm | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
25. Café Mars | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
26. Olmo | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
27. Borgo | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
28. Briscola Trattoria | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
29. Maialino Vicino | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
30. Rezdôra | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
31. La Pecora Bianca | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
32. Bar Primi | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
33. Il Mulino Prime | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
34. Ai Fiori | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
35. Marea | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
36. Quality Italian | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
37. Patsy's | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
38. Massara | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
39. Bad Roman | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
40. Giulietta | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
41. Ci Siamo | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
42. Bar Tulia | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
43. Santi | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
44. Ribalta | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
45. Don Antonio | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
46. Kesté Pizza & Vino | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
47. Elio's | Manhattan (Upper East Side / Upper West Side / Harlem)
48. Sant Ambroeus UES | Manhattan (Upper East Side / Upper West Side / Harlem)
49. Sempre Oggi | Manhattan (Upper East Side / Upper West Side / Harlem)
50. Cafe Fiorello | Manhattan (Upper East Side / Upper West Side / Harlem)
51. Lincoln Ristorante | Manhattan (Upper East Side / Upper West Side / Harlem)
52. Tarallucci e Vino | Manhattan (Upper East Side / Upper West Side / Harlem)
53. Patsy's Pizzeria | Manhattan (Upper East Side / Upper West Side / Harlem)
54. Sottocasa Harlem | Manhattan (Upper East Side / Upper West Side / Harlem)
55. Misi | Brooklyn (Williamsburg / Greenpoint)
56. I Cavallini | Brooklyn (Williamsburg / Greenpoint)
57. Bamonte's | Brooklyn (Williamsburg / Greenpoint)
58. Aurora | Brooklyn (Williamsburg / Greenpoint)
59. Fabbrica | Brooklyn (Williamsburg / Greenpoint)
60. Sauced | Brooklyn (Williamsburg / Greenpoint)
61. Sottocasa Greenpoint | Brooklyn (Williamsburg / Greenpoint)
62. Frankies 457 Spuntino | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
63. F&F Pizzeria | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
64. Cafe Spaghetti | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
65. Cremini's | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
66. Lucali | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
67. Marco Polo Ristorante | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
68. Ferdinando's Focacceria / Bar Ferdinando | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
69. Noodle Pudding | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
70. River Deli | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
71. al di là Trattoria | Brooklyn (Park Slope / Gowanus / Prospect Heights)
72. Lillo Cucina Italiana | Brooklyn (Park Slope / Gowanus / Prospect Heights)
73. Roberta's | Brooklyn (Bushwick / Bed-Stuy / Crown Heights)
74. Faro | Brooklyn (Bushwick / Bed-Stuy / Crown Heights)
75. Saraghina | Brooklyn (Bushwick / Bed-Stuy / Crown Heights)
76. Gargiulo's | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
77. Tommaso's | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
78. Il Colosseo | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
79. Ortobello's | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
80. Randazzo's Clam Bar | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
81. Michael's of Brooklyn | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
82. Ponte Vecchio | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
83. Gino's of Bay Ridge | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
84. Positano Restaurant | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
85. Lombardo's of Bay Ridge | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
86. Greenhouse Cafe | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
87. La Nonna | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
88. LaRina Pastificio & Vino | Brooklyn (Fort Greene / DUMBO)
89. Locanda Vini & Olii | Brooklyn (Fort Greene / DUMBO)
90. Cecconi's DUMBO | Brooklyn (Fort Greene / DUMBO)
91. Grimaldi's | Brooklyn (Fort Greene / DUMBO)
92. Park Side Restaurant | Queens
93. Trattoria L'Incontro | Queens
94. Don Peppe | Queens
95. Manducatis | Queens
96. Manducatis Rustica | Queens
97. Vesta Trattoria & Wine Bar | Queens
98. Il Bambino | Queens
99. Vite Vinosteria | Queens
100. Via Trenta | Queens
101. Via Vai | Queens
102. Sac's Place | Queens
103. Rialto Ristorante | Queens
104. Il Poeta | Queens
105. Bruno Ristorante | Queens
106. Vetro by Russo's on the Bay | Queens
107. Lenny's Clam Bar | Queens
108. Matteo's of Howard Beach | Queens
109. Riviera Ristorante | Queens
110. Il Bacco | Queens
111. Rosa's Pizza | Queens
112. Il Nonno | Queens
113. Sotto La Luna | Queens
114. Macoletta | Queens
115. Palermo Restaurant | Queens
116. Roberto's | Bronx
117. Dominick's | Bronx
118. Mario's | Bronx
119. Zero Otto Nove (Trattoria) | Bronx
120. Tra di Noi | Bronx
121. Enzo's of Arthur Ave | Bronx
122. Antonio's Trattoria | Bronx
123. Pasquale's Rigoletto | Bronx
124. Emilia's | Bronx
125. Ann & Tony's | Bronx
126. Patricia's of Morris Park | Bronx
127. Emilio's of Morris Park | Bronx
128. F&J Pine Restaurant | Bronx
129. Louie & Ernie's Pizza | Bronx
130. Sammy's Fish Box / Shrimp Box | Bronx
131. Beccofino | Bronx
132. Fratelli | Bronx

Please return the complete JSON object with all 132 restaurants. Take your time and be thorough — accuracy matters more than speed. If you're unsure about a match, include a note in the entry.

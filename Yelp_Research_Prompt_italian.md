# Yelp Research Prompt (Italian)

Paste the following prompt into a Claude or ChatGPT Deep Research session. Then copy the resulting report (as markdown) and paste it back to me — I'll parse it into the cache file.

---

## PROMPT (copy everything below this line)

I need you to look up Yelp ratings for a list of 154 NYC Italian restaurants (trattorias, osterias, pizzerias, red-sauce houses, modern Italian, etc.). For each restaurant, please search Yelp and report:

1. **Yelp rating** (1-5 scale, half-star increments)
2. **Review count** (number of Yelp reviews)
3. **Yelp price level** ($ to $$$$)
4. **Yelp URL** (the full yelp.com link)
5. **Yelp name** (the exact name as listed on Yelp, if it differs from my list)

If a restaurant cannot be found on Yelp, say so explicitly for that entry.

**Important notes:**
- These are all NYC restaurants (Manhattan, Brooklyn, Queens, Bronx)
- Many are common Italian names — use the neighborhood I provide to disambiguate carefully
- Some have multiple locations — match the one in the listed neighborhood
- If there are multiple Yelp listings for the same restaurant in the same neighborhood, use the one with the most reviews

**Here is the full list of 154 restaurants:**

1. Via Carota | Manhattan (West Village / Greenwich Village)
2. Don Angie | Manhattan (West Village / Greenwich Village)
3. San Sabino | Manhattan (West Village / Greenwich Village)
4. L'Artusi | Manhattan (West Village / Greenwich Village)
5. I Sodi | Manhattan (West Village / Greenwich Village)
6. Bar Pisellino | Manhattan (West Village / Greenwich Village)
7. Gene's Restaurant | Manhattan (West Village / Greenwich Village)
8. Villa Mosconi | Manhattan (West Village / Greenwich Village)
9. Babbo Ristorante | Manhattan (West Village / Greenwich Village)
10. Lupa | Manhattan (West Village / Greenwich Village)
11. Carbone | Manhattan (West Village / Greenwich Village)
12. Emilio's Ballato | Manhattan (West Village / Greenwich Village)
13. Rubirosa | Manhattan (West Village / Greenwich Village)
14. Torrisi Bar & Restaurant | Manhattan (West Village / Greenwich Village)
15. Roscioli | Manhattan (West Village / Greenwich Village)
16. Bar Pitti | Manhattan (West Village / Greenwich Village)
17. Sant Ambroeus West Village | Manhattan (West Village / Greenwich Village)
18. Malaparte | Manhattan (West Village / Greenwich Village)
19. Da Toscano | Manhattan (West Village / Greenwich Village)
20. Fiaschetteria Pistoia | Manhattan (West Village / Greenwich Village)
21. Osteria Nonnino | Manhattan (West Village / Greenwich Village)
22. Arthur & Sons NY Italian | Manhattan (West Village / Greenwich Village)
23. Frankies 570 Spuntino | Manhattan (West Village / Greenwich Village)
24. Da Andrea | Manhattan (West Village / Greenwich Village)
25. Il Mulino New York | Manhattan (West Village / Greenwich Village)
26. Olio e Più | Manhattan (West Village / Greenwich Village)
27. Lavagna | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
28. Il Posto Accanto | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
29. Supper | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
30. Cacio e Pepe | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
31. John's of 12th Street | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
32. Forsythia | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
33. Una Pizza Napoletana | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
34. Scarr's Pizza | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
35. Altro Paradiso | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
36. Pasquale Jones | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
37. Lodi | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
38. Sandro's | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
39. Gelso & Grand | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
40. Parm | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
41. Café Mars | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
42. Olmo | Manhattan (Nolita / SoHo / NoHo / Lower East Side / East Village)
43. Locanda Verde | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
44. Borgo | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
45. Briscola Trattoria | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
46. Maialino Vicino | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
47. Rezdôra | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
48. La Pecora Bianca | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
49. Bar Primi | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
50. Il Mulino Prime | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
51. Ai Fiori | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
52. Marea | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
53. Quality Italian | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
54. Patsy's | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
55. Massara | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
56. Bad Roman | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
57. Giulietta | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
58. Ci Siamo | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
59. Bar Tulia | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
60. Santi | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
61. Ribalta | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
62. Don Antonio | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
63. Kesté Pizza & Vino | Manhattan (Tribeca / Chelsea / Flatiron / Gramercy / NoMad / Midtown)
64. Rao's | Manhattan (Upper East Side / Upper West Side / Harlem)
65. Elio's | Manhattan (Upper East Side / Upper West Side / Harlem)
66. Sant Ambroeus UES | Manhattan (Upper East Side / Upper West Side / Harlem)
67. Sempre Oggi | Manhattan (Upper East Side / Upper West Side / Harlem)
68. Cafe Fiorello | Manhattan (Upper East Side / Upper West Side / Harlem)
69. Lincoln Ristorante | Manhattan (Upper East Side / Upper West Side / Harlem)
70. Tarallucci e Vino | Manhattan (Upper East Side / Upper West Side / Harlem)
71. Patsy's Pizzeria | Manhattan (Upper East Side / Upper West Side / Harlem)
72. Sottocasa Harlem | Manhattan (Upper East Side / Upper West Side / Harlem)
73. Lilia | Brooklyn (Williamsburg / Greenpoint)
74. Misi | Brooklyn (Williamsburg / Greenpoint)
75. I Cavallini | Brooklyn (Williamsburg / Greenpoint)
76. Bamonte's | Brooklyn (Williamsburg / Greenpoint)
77. Aurora | Brooklyn (Williamsburg / Greenpoint)
78. Fabbrica | Brooklyn (Williamsburg / Greenpoint)
79. Sauced | Brooklyn (Williamsburg / Greenpoint)
80. Sottocasa Greenpoint | Brooklyn (Williamsburg / Greenpoint)
81. Frankies 457 Spuntino | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
82. F&F Pizzeria | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
83. Cafe Spaghetti | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
84. Cremini's | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
85. Lucali | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
86. Marco Polo Ristorante | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
87. Ferdinando's Focacceria / Bar Ferdinando | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
88. Noodle Pudding | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
89. River Deli | Brooklyn (Carroll Gardens / Cobble Hill / Boerum Hill)
90. al di là Trattoria | Brooklyn (Park Slope / Gowanus / Prospect Heights)
91. Lillo Cucina Italiana | Brooklyn (Park Slope / Gowanus / Prospect Heights)
92. Roberta's | Brooklyn (Bushwick / Bed-Stuy / Crown Heights)
93. Faro | Brooklyn (Bushwick / Bed-Stuy / Crown Heights)
94. Saraghina | Brooklyn (Bushwick / Bed-Stuy / Crown Heights)
95. Gargiulo's | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
96. L&B Spumoni Gardens | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
97. Tommaso's | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
98. Il Colosseo | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
99. Ortobello's | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
100. Randazzo's Clam Bar | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
101. Michael's of Brooklyn | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
102. Di Fara Pizza | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
103. Ponte Vecchio | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
104. Gino's of Bay Ridge | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
105. Positano Restaurant | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
106. Lombardo's of Bay Ridge | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
107. Greenhouse Cafe | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
108. La Nonna | Brooklyn (Coney Island / Gravesend / Bensonhurst / Bay Ridge / Mapleton)
109. LaRina Pastificio & Vino | Brooklyn (Fort Greene / DUMBO)
110. Locanda Vini & Olii | Brooklyn (Fort Greene / DUMBO)
111. Cecconi's DUMBO | Brooklyn (Fort Greene / DUMBO)
112. Juliana's Pizza | Brooklyn (Fort Greene / DUMBO)
113. Grimaldi's | Brooklyn (Fort Greene / DUMBO)
114. Park Side Restaurant | Queens
115. Trattoria L'Incontro | Queens
116. Don Peppe | Queens
117. Manducatis | Queens
118. Manducatis Rustica | Queens
119. Vesta Trattoria & Wine Bar | Queens
120. Il Bambino | Queens
121. Vite Vinosteria | Queens
122. Via Trenta | Queens
123. Via Vai | Queens
124. Sac's Place | Queens
125. Rialto Ristorante | Queens
126. Il Poeta | Queens
127. Bruno Ristorante | Queens
128. Vetro by Russo's on the Bay | Queens
129. Lenny's Clam Bar | Queens
130. Matteo's of Howard Beach | Queens
131. Riviera Ristorante | Queens
132. Il Bacco | Queens
133. Rosa's Pizza | Queens
134. Il Nonno | Queens
135. Sotto La Luna | Queens
136. Macoletta | Queens
137. Palermo Restaurant | Queens
138. Roberto's | Bronx
139. Dominick's | Bronx
140. Mario's | Bronx
141. Zero Otto Nove (Trattoria) | Bronx
142. Tra di Noi | Bronx
143. Enzo's of Arthur Ave | Bronx
144. Antonio's Trattoria | Bronx
145. Pasquale's Rigoletto | Bronx
146. Emilia's | Bronx
147. Ann & Tony's | Bronx
148. Patricia's of Morris Park | Bronx
149. Emilio's of Morris Park | Bronx
150. F&J Pine Restaurant | Bronx
151. Louie & Ernie's Pizza | Bronx
152. Sammy's Fish Box / Shrimp Box | Bronx
153. Beccofino | Bronx
154. Fratelli | Bronx

Please cover all 154 restaurants. Take your time and be thorough — accuracy matters more than speed. If you're unsure about a match, say so.

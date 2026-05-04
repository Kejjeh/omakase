# Yelp Research Prompt

Paste the following prompt into a Claude or ChatGPT deep research session. It will look up each restaurant on Yelp and return a structured JSON table you can save as `scripts/yelp_cache.json` in the Omakase project folder.

---

## PROMPT (copy everything below this line)

I need you to look up Yelp ratings for a list of 149 NYC omakase/sushi restaurants. For each restaurant, please search Yelp and find:

1. **Yelp rating** (1-5 scale, half-star increments)
2. **Review count** (number of Yelp reviews)
3. **Yelp price level** ($ to $$$$)
4. **Yelp URL** (the full yelp.com link)

If a restaurant cannot be found on Yelp, mark it as `null` for all fields.

**Important notes:**
- These are all NYC restaurants (Manhattan and Brooklyn)
- Many have "Omakase" in the name — search for the full name first, then try without "Omakase" if not found
- Some have multiple locations — prefer the Manhattan or Brooklyn location
- If there are multiple Yelp listings for the same restaurant, use the one with the most reviews
- I've included the neighborhood to help disambiguate

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

**Here is the full list of 149 restaurants:**

1. Hatsuhana | Manhattan (Midtown East)
2. Akimori | Manhattan (UES/UWS/Midtown)
3. Gosuke | Manhattan (Midtown)
4. Hoseki | Manhattan (Saks 5th Ave)
5. Inase | Manhattan (UWS)
6. Kizuna Omakase | Manhattan (UWS)
7. Kun Tsuki Omakase | Manhattan (UWS)
8. Mari.ne Handroll | Manhattan (Bryant Park)
9. Masuda Omakase | Manhattan (Midtown)
10. Nare Sushi | Manhattan (Midtown)
11. Omakase 33 | Manhattan (Midtown)
12. Shihou Omakase | Manhattan (Midtown)
13. Shogun Omakase | Manhattan (Midtown East)
14. Sushi Beauu | Manhattan (Midtown)
15. Sushi Kaito | Manhattan (UWS)
16. Sushi Masu | Manhattan (UWS)
17. Sushi Yasuda | Manhattan (Midtown East)
18. Sushi You | Manhattan (Midtown East)
19. Trust Bae | Manhattan (Midtown)
20. Uka Omakase | Manhattan (UWS)
21. Uogashi | Manhattan (Theater District)
22. Zama Omakase | Manhattan (UWS)
23. Chemistry Room | Manhattan (Midtown West)
24. Korami Omakase | Manhattan (Hell's Kitchen)
25. Mojo Omakase | Manhattan (Midtown West)
26. Sushiichi | Manhattan (Hell's Kitchen)
27. Sushi Lab | Manhattan (Times Sq/Midtown)
28. Sendo | Manhattan (Midtown East)
29. Sushi Sasabune | Manhattan (UES / UWS)
30. Omakase Sushi Dairo | Manhattan (Gramercy/Midtown)
31. Tsumo | Manhattan (Kips Bay / UES)
32. One Bite Omakase | Manhattan (UES / Lower Manh.)
33. ROKI | Manhattan (Flatiron)
34. Shinn East | Manhattan (East Village)
35. Sushi Blossoms | Manhattan (Chelsea/Midtown)
36. Sushi Suite 1001 | Manhattan (NoMad)
37. Tokyo Bar | Manhattan
38. KazuNori | Manhattan (NoMad/Midtown)
39. Hasaki | Manhattan (East Village)
40. KAWA Omakase | Manhattan (East Village)
41. Kissaki | Manhattan (Flatiron / UES)
42. Mayanoki | Manhattan (East Village)
43. Mido Omakase | Brooklyn (Williamsburg)
44. Moko | Manhattan (East Village)
45. Omakase by Teisui | Manhattan (East Village)
46. Robataya | Manhattan (East Village)
47. Sanyuu West | Manhattan (Chelsea)
48. Shinzo Omakase | Manhattan (East Village)
49. SourAji | Manhattan (East Village)
50. Sugarfish | Manhattan
51. Sushi by Bou | Manhattan
52. Sushi by M | Manhattan (East Village)
53. Sushi Dojo | Manhattan (East Village)
54. Sushi Seki | Manhattan (Chelsea / UES)
55. Thirteen Water | Manhattan (East Village)
56. Domodomo | Manhattan (Flatiron/SoHo)
57. Genki Omakase | Manhattan (Greenwich Village)
58. Kanoyama | Manhattan (East Village)
59. Kazumi Omakase | Manhattan (Greenwich Village)
60. Nozomi NYC | Manhattan & Brooklyn
61. Saishin | Manhattan (Meatpacking)
62. Shota Omakase | Brooklyn (Williamsburg)
63. Sushi Yashin | Manhattan / Brooklyn
64. U Omakase | Brooklyn (Greenpoint)
65. Bondi Sushi | Brooklyn (Greenpoint)
66. Douska | Manhattan (LES)
67. Matsunori | Manhattan (LES / Bowery)
68. Mishik | Manhattan (Hudson Square)
69. Sushi 456 | Manhattan (West Village)
70. Sushi Hayashi | Brooklyn (Williamsburg)
71. Sushi Nakazawa | Manhattan (West Village)
72. Sushi on Jones | Manhattan/Brooklyn
73. Sushi On Me | Brooklyn / Queens
74. Takumi Omakase | Manhattan (LES)
75. Ume Williamsburg | Brooklyn (Williamsburg)
76. Yoshino | Manhattan (NoHo)
77. Zen Sushi Omakase | Manhattan (LES)
78. Sushi Ryusei | Manhattan (Murray Hill/Midtown)
79. Blue Ribbon Sushi | Manhattan (SoHo)
80. Kintsugi | Manhattan (SoHo)
81. Maaser Omakase | Manhattan (SoHo / West Vil.)
82. Momoya | Manhattan (SoHo)
83. Nami Nori | Manhattan (SoHo/West Village)
84. Sekai Omakase | Manhattan (South Village)
85. Shiki Omakase | Manhattan (SoHo)
86. Sushi by Bae | Manhattan (SoHo)
87. Sushi Ikumi | Manhattan (SoHo)
88. Sushi Lin | Manhattan
89. Sushi Ouji | Manhattan (SoHo / Lower Manh.)
90. Atto Omakase | Manhattan (UES)
91. Noz Market | Manhattan (UES)
92. Oyishi Sushi | Manhattan (UES)
93. Sushi Jin | Manhattan (UES)
94. Sushi Koya | Manhattan (UES)
95. Sushi Yolo | Manhattan (UES)
96. Tatsuda Omakase | Manhattan (UES)
97. Fuku Omakase | Manhattan (Lower Manhattan)
98. Hatsu Omakase | Manhattan (Lower Manhattan)
99. Kinzan Omakase | Manhattan (Lower Manhattan)
100. Kyuubi Omakase | Manhattan (Lower Manhattan)
101. Mitsuru | Manhattan (Lower Manhattan)
102. Mojo East | Manhattan (Lower Manhattan)
103. Mori | Manhattan (Lower Manhattan)
104. Nobu Downtown | Manhattan (FiDi)
105. Omakase by No Name | Manhattan (Lower Manh.)
106. Saikou | Manhattan (Lower Manhattan)
107. Sake Kawa | Manhattan (Lower Manhattan)
108. SHHH Omakase | Manhattan (Lower Manhattan)
109. Shinsen | Manhattan (Lower Manhattan)
110. Shirokuro | Manhattan (Lower Manhattan)
111. Shoshin | Manhattan (Lower Manhattan)
112. Sushi Daizen | Manhattan (FiDi)
113. Sushi Kai | Manhattan
114. Sushi Makoto | Manhattan (Lower Manhattan)
115. Taikun | Manhattan (Lower Manhattan)
116. Towa | Manhattan (Lower Manhattan)
117. Unique Omakase | Manhattan (Lower Manhattan)
118. Yokox Omakase | Manhattan (Lower Manhattan)
119. Sushi Tsushima | Manhattan (Midtown East)
120. Iwak Sushi | Brooklyn
121. Junsui Omakase | Brooklyn (DUMBO)
122. Kinjo | Brooklyn (DUMBO)
123. Luya Omakase | Brooklyn
124. Miro Sushi | Brooklyn
125. Neta Shari | Brooklyn (Bensonhurst)
126. Omakase by Hiro | Brooklyn (Sheepshead Bay)
127. Sora | Brooklyn
128. Sushi Katsuei | Brooklyn / Manhattan
129. Sushi Uesugi | Brooklyn
130. Yamashiro | Brooklyn
131. E Sushi II | Brooklyn (Flatbush)
132. KIMYO | Brooklyn (Park Slope/Downtown)
133. Ki Sushi | Brooklyn (Prospect Heights)
134. Koma Sushi | Brooklyn (Flatbush)
135. Sushi Koju | Brooklyn (Boerum Hill)
136. Hanaya Omakase | Manhattan (UES/Midtown)
137. Joji | Manhattan (Midtown East)
138. Koete Omakase | Manhattan (UES/Theater Dist.)
139. Shinpi | Manhattan (Upper Manhattan)
140. Sushi Ann | Manhattan (Midtown East)
141. Sushi Goda | Manhattan (Upper Manhattan)
142. Sushi W | Manhattan (UWS/UES/East Vil.)
143. Sushi Yugen | Manhattan (Upper Manhattan)
144. Gohan Sushi | Brooklyn (Bay Ridge)
145. Idashi Omakase | Brooklyn (Park Slope)
146. Ishi Omakase | Brooklyn (Park Slope)
147. Oita Sushi | Brooklyn (Park Slope)
148. Uotora | Brooklyn (Crown Heights)
149. Tanoshi Sushi | Manhattan (UES / Lenox Hill)

Please return the complete JSON object with all 149 restaurants. Take your time and be thorough — accuracy matters more than speed. If you're unsure about a match, include a note in the entry.

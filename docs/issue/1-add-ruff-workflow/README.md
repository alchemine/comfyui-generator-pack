# #1 Add ruff workflow

## 이슈
- GitHub Actions에 ruff 검사가 없다.
- `pyproject.toml`에 의존성 선언이 남아 있다.

## 해결책
- `.github/workflows/ruff.yml`을 추가한다. `ruff check .`와 `ruff format --check .`를 실행한다.
- `pyproject.toml`에 `[tool.ruff]` 설정을 추가한다.
- `pyproject.toml`에서 `dependencies`를 지운다. 의존성은 `requirements.txt`에만 적는다.
- `ruff check --fix`로 쓰지 않는 import와 공백만 있는 빈 줄을 지운다. `ruff format`으로 13개 파일의 형식을 맞춘다.
- 버전을 1.0.1로 올린다.

## 테스트 계획
| 테스트 | 기대 결과 |
|---|---|
| `ruff check .` | `All checks passed!` |
| `ruff format --check .` | 다시 형식을 맞출 파일이 없다 |

## 테스트 결과
### 수정 전
```
nodes/tags.py:11:8: F401 [*] `numbers` imported but unused
nodes/tags.py:477:1: W293 [*] Blank line contains whitespace
nodes/tags.py:481:1: W293 [*] Blank line contains whitespace
nodes/tags.py:560:1: W293 [*] Blank line contains whitespace
nodes/tags.py:564:1: W293 [*] Blank line contains whitespace
Found 5 errors.
[*] 5 fixable with the `--fix` option.
unformatted: File would be reformatted
   --> nodes/lib/artifact.py:12:1
    |
11  | """
12  +
13  | import os
--------------------------------------------------------------------------------
19  |
    - RELEASE = ("https://github.com/alchemine/comfyui-generator-pack"
    -            "/releases/download/%s/%s")
20  + RELEASE = "https://github.com/alchemine/comfyui-generator-pack/releases/download/%s/%s"
21  |
--------------------------------------------------------------------------------
41  | BUNDLE_TAG = "data-v1.0.0"
    - BUNDLE_SHA256 = ("b18caa14ffb77c3364e1c03ab77a43c1"
    -                  "972f1745a3b1b4dd6cee61f7c352c33b")
42  + BUNDLE_SHA256 = "b18caa14ffb77c3364e1c03ab77a43c1972f1745a3b1b4dd6cee61f7c352c33b"
43  |
--------------------------------------------------------------------------------
57  |
    -     archive = ensure(resource(BUNDLE), url_for(BUNDLE_TAG, BUNDLE),
    -                      BUNDLE_SHA256, "resources", "2MB")
58  +     archive = ensure(
59  +         resource(BUNDLE), url_for(BUNDLE_TAG, BUNDLE), BUNDLE_SHA256, "resources", "2MB"
60  +     )
61  |     try:
--------------------------------------------------------------------------------
104 |
    -     logger.info("[%s] downloading %s%s from %s"
    -                 % (label, os.path.basename(path), note and " (%s)" % note, url))
105 +     logger.info(
106 +         "[%s] downloading %s%s from %s"
107 +         % (label, os.path.basename(path), note and " (%s)" % note, url)
108 +     )
109 |     os.makedirs(os.path.dirname(path), exist_ok=True)
--------------------------------------------------------------------------------
119 |                 "%s checksum mismatch (corrupt or stale download)"
    -                 % os.path.basename(path))
120 +                 % os.path.basename(path)
121 +             )
122 |         os.replace(tmp, path)
    |

unformatted: File would be reformatted
   --> nodes/lib/tag_alias.py:25:1
    |
24  | """
25  +
26  | import csv
--------------------------------------------------------------------------------
75  |         groups.setdefault(name, [name]).append(alias)
    -     logger.debug("[TagAlias] %d aliases over %d tags", len(owner),
    -                  len(canonical))
76  +     logger.debug("[TagAlias] %d aliases over %d tags", len(owner), len(canonical))
77  |     return groups
--------------------------------------------------------------------------------
106 |                 added += 1
    -     logger.debug("[TagAlias] %d alias spellings added to a %d-tag index",
    -                  added, len(index) - added)
107 +     logger.debug(
108 +         "[TagAlias] %d alias spellings added to a %d-tag index",
109 +         added,
110 +         len(index) - added,
111 +     )
112 |     return index
    |

unformatted: File would be reformatted
  --> nodes/lib/tag_avoid.py:32:11
   |
31 | _URL = artifact.url_for("data-v1.0.0", "avoidance_v1.npz")
   - _SHA256 = ("fad88158098e6e1f6a4f90cf24f85eb7"
   -            "d312b1f489858a6f1c1c9ac0a3441b26")
32 + _SHA256 = "fad88158098e6e1f6a4f90cf24f85eb7d312b1f489858a6f1c1c9ac0a3441b26"
33 |
--------------------------------------------------------------------------------
39 |
40 +
41 | class Avoidance:
--------------------------------------------------------------------------------
45 |         import numpy as np
46 +
47 |         if path == _PATH:
   |

unformatted: File would be reformatted
   --> nodes/lib/tag_category.py:19:1
    |
18  | """
19  +
20  | import json
--------------------------------------------------------------------------------
42  |         def load(name):
    -             path = (artifact.bundled("group", name) if directory == _DIR
    -                     else os.path.join(directory, name))
43  +             path = (
44  +                 artifact.bundled("group", name)
45  +                 if directory == _DIR
46  +                 else os.path.join(directory, name)
47  +             )
48  |             with open(path, encoding="utf-8") as f:
--------------------------------------------------------------------------------
56  |         self.names = list(cats["priority"])
    -         self._fallback = len(self.names) - 1        # "etc"
57  +         self._fallback = len(self.names) - 1  # "etc"
58  |
--------------------------------------------------------------------------------
133 |         import numpy as np
    -         cats = np.fromiter((self.category_of(t) for t in vocab),
    -                            dtype=np.int8, count=len(vocab))
    -         levels = np.fromiter((self.rating_of(t) for t in vocab),
    -                              dtype=np.int8, count=len(vocab))
134 +
135 +         cats = np.fromiter(
136 +             (self.category_of(t) for t in vocab), dtype=np.int8, count=len(vocab)
137 +         )
138 +         levels = np.fromiter(
139 +             (self.rating_of(t) for t in vocab), dtype=np.int8, count=len(vocab)
140 +         )
141 |         return cats, levels
--------------------------------------------------------------------------------
181 |         head, _, share = item.partition(":")
    -         ranks = tuple(r for r in (rank_of.get(part.strip().lower())
    -                                   for part in head.split("+"))
    -                       if r is not None)
182 +         ranks = tuple(
183 +             r
184 +             for r in (rank_of.get(part.strip().lower()) for part in head.split("+"))
185 +             if r is not None
186 +         )
187 |         if not ranks:
--------------------------------------------------------------------------------
226 |     # hand the leftovers to whoever was rounded down hardest
    -     for k in sorted(range(len(groups)), key=lambda i: exact[i] - caps[i],
    -                     reverse=True)[:spare]:
227 +     for k in sorted(range(len(groups)), key=lambda i: exact[i] - caps[i], reverse=True)[
228 +         :spare
229 +     ]:
230 |         caps[k] += 1
    |

unformatted: File would be reformatted
  --> nodes/lib/tag_copyright.py:34:11
   |
33 | _URL = artifact.url_for("data-v1.0.0", "copyright_v1.npz")
   - _SHA256 = ("9539fcd6a0271dd4234a244114aabbd5"
   -            "bdf4fe823de53a2cd56f9ecdb931f31e")
34 + _SHA256 = "9539fcd6a0271dd4234a244114aabbd5bdf4fe823de53a2cd56f9ecdb931f31e"
35 |
--------------------------------------------------------------------------------
43 | # Calibrated on labeled tags -- the build log prints the table.
   - CHAR_SHARE = 0.5    # above aqua hair 0.45 (Miku), below bat wings 0.55
   - CHAR_LIFT = 20.0    # true signatures sit at x64-x222
   - COPY_SHARE = 0.6    # above serafuku 0.36, witch hat 0.40
   - COPY_LIFT = 8.0     # geta/no headwear x6 stay; mob cap x9, umamusume x66 go
44 + CHAR_SHARE = 0.5  # above aqua hair 0.45 (Miku), below bat wings 0.55
45 + CHAR_LIFT = 20.0  # true signatures sit at x64-x222
46 + COPY_SHARE = 0.6  # above serafuku 0.36, witch hat 0.40
47 + COPY_LIFT = 8.0  # geta/no headwear x6 stay; mob cap x9, umamusume x66 go
48 |
--------------------------------------------------------------------------------
54 |         import numpy as np
55 +
56 |         if path == _PATH:
57 |             artifact.ensure(path, _URL, _SHA256, "Copyright", "2MB")
58 |         data = np.load(path, allow_pickle=False)
   -         sig = (((data["char_score"].astype(np.float64) >= CHAR_SHARE)
   -                 & (data["char_lift"].astype(np.float64) >= CHAR_LIFT))
   -                | ((data["copy_score"].astype(np.float64) >= COPY_SHARE)
   -                   & (data["copy_lift"].astype(np.float64) >= COPY_LIFT)))
59 +         sig = (
60 +             (data["char_score"].astype(np.float64) >= CHAR_SHARE)
61 +             & (data["char_lift"].astype(np.float64) >= CHAR_LIFT)
62 +         ) | (
63 +             (data["copy_score"].astype(np.float64) >= COPY_SHARE)
64 +             & (data["copy_lift"].astype(np.float64) >= COPY_LIFT)
65 +         )
66 |         table = {str(t): bool(s) for t, s in zip(data["tags"], sig)}
67 |         extra = _extra_tags()
68 |         self.mask = np.fromiter(
   -             (table.get(t, False) or t.replace("_", " ") in extra
   -              for t in vocab),
   -             dtype=bool, count=len(vocab))
69 +             (table.get(t, False) or t.replace("_", " ") in extra for t in vocab),
70 +             dtype=bool,
71 +             count=len(vocab),
72 +         )
73 |
--------------------------------------------------------------------------------
78 |     try:
   -         with open(artifact.bundled("copyright_blacklist.txt"),
   -                   encoding="utf-8") as fh:
79 +         with open(artifact.bundled("copyright_blacklist.txt"), encoding="utf-8") as fh:
80 |             for line in fh:
   |

unformatted: File would be reformatted
   --> nodes/lib/tag_data.py:10:13
    |
9   | COLORS = [
    -     "white", "black", "red", "blue", "pink", "purple", "green",
    -     "yellow", "brown", "grey", "orange", "aqua",
10  +     "white",
11  +     "black",
12  +     "red",
13  +     "blue",
14  +     "pink",
15  +     "purple",
16  +     "green",
17  +     "yellow",
18  +     "brown",
19  +     "grey",
20  +     "orange",
21  +     "aqua",
22  | ]
--------------------------------------------------------------------------------
28  | CLOTHES_HEADWEAR = [
    -     "hat", "balaclava", "coif", "crown", "diadem", "headdress", "maid headdress",
    -     "headscarf", "hijab", "tiara", "veil", "wimple", "beret", "baseball cap",
    -     "witch hat", "santa hat", "top hat", "mini top hat", "beanie", "sun hat",
    -     "straw hat", "peaked cap", "garrison cap", "cabbie hat", "bucket hat",
    -     "fedora", "nurse cap", "chef hat", "party hat", "sailor hat", "cowboy hat",
    -     "hard hat", "mob cap", "nightcap", "pirate hat", "police hat", "shako cap",
    -     "tokin hat", "animal hat", "fur hat", "flat cap", "boater hat",
    -     "pillbox hat", "tricorne", "bicorne", "deerstalker", "sombrero", "ushanka",
    -     "visor cap", "helmet", "winged helmet", "pith helmet", "motorcycle helmet",
29  +     "hat",
30  +     "balaclava",
31  +     "coif",
32  +     "crown",
33  +     "diadem",
34  +     "headdress",
35  +     "maid headdress",
36  +     "headscarf",
37  +     "hijab",
38  +     "tiara",
39  +     "veil",
40  +     "wimple",
41  +     "beret",
42  +     "baseball cap",
43  +     "witch hat",
44  +     "santa hat",
45  +     "top hat",
46  +     "mini top hat",
47  +     "beanie",
48  +     "sun hat",
49  +     "straw hat",
50  +     "peaked cap",
51  +     "garrison cap",
52  +     "cabbie hat",
53  +     "bucket hat",
54  +     "fedora",
55  +     "nurse cap",
56  +     "chef hat",
57  +     "party hat",
58  +     "sailor hat",
59  +     "cowboy hat",
60  +     "hard hat",
61  +     "mob cap",
62  +     "nightcap",
63  +     "pirate hat",
64  +     "police hat",
65  +     "shako cap",
66  +     "tokin hat",
67  +     "animal hat",
68  +     "fur hat",
69  +     "flat cap",
70  +     "boater hat",
71  +     "pillbox hat",
72  +     "tricorne",
73  +     "bicorne",
74  +     "deerstalker",
75  +     "sombrero",
76  +     "ushanka",
77  +     "visor cap",
78  +     "helmet",
79  +     "winged helmet",
80  +     "pith helmet",
81  +     "motorcycle helmet",
82  | ]
83  |
84  | CLOTHES_TOP = [
    -     "shirt", "blouse", "frilled shirt", "sleeveless shirt", "collared shirt",
    -     "dress shirt", "off-shoulder shirt", "striped shirt", "t-shirt",
    -     "compression shirt", "bustier", "crop top", "camisole", "cardigan",
    -     "cardigan vest", "corset", "sweater", "turtleneck", "turtleneck sweater",
    -     "sleeveless turtleneck", "ribbed sweater", "aran sweater", "sweater vest",
    -     "tank top", "tube top", "bandeau", "underbust", "vest", "waistcoat",
    -     "hoodie", "halterneck", "criss-cross halter", "stringer", "nightgown",
85  +     "shirt",
86  +     "blouse",
87  +     "frilled shirt",
88  +     "sleeveless shirt",
89  +     "collared shirt",
90  +     "dress shirt",
91  +     "off-shoulder shirt",
92  +     "striped shirt",
93  +     "t-shirt",
94  +     "compression shirt",
95  +     "bustier",
96  +     "crop top",
97  +     "camisole",
98  +     "cardigan",
99  +     "cardigan vest",
100 +     "corset",
101 +     "sweater",
102 +     "turtleneck",
103 +     "turtleneck sweater",
104 +     "sleeveless turtleneck",
105 +     "ribbed sweater",
106 +     "aran sweater",
107 +     "sweater vest",
108 +     "tank top",
109 +     "tube top",
110 +     "bandeau",
111 +     "underbust",
112 +     "vest",
113 +     "waistcoat",
114 +     "hoodie",
115 +     "halterneck",
116 +     "criss-cross halter",
117 +     "stringer",
118 +     "nightgown",
119 | ]
120 |
121 | CLOTHES_BOTTOM = [
    -     "skirt", "pants", "shorts", "bloomers", "buruma", "chaps", "kilt",
    -     "bell-bottoms", "capri pants", "detached pants", "jeans", "cutoff jeans",
    -     "lowleg pants", "yoga pants", "pelvic curtain", "petticoat", "sarong",
    -     "bike shorts", "denim shorts", "dolphin shorts", "gym shorts",
    -     "lowleg shorts", "micro shorts", "pleated shorts", "short shorts",
    -     "bubble skirt", "cargo skirt", "high-waist skirt", "long skirt",
    -     "lowleg skirt", "microskirt", "miniskirt", "overall skirt", "overskirt",
    -     "plaid skirt", "pleated skirt", "suspender skirt", "tutu", "sweatpants",
    -     "hakama", "hakama skirt", "hakama pants",
122 +     "skirt",
123 +     "pants",
124 +     "shorts",
125 +     "bloomers",
126 +     "buruma",
127 +     "chaps",
128 +     "kilt",
129 +     "bell-bottoms",
130 +     "capri pants",
131 +     "detached pants",
132 +     "jeans",
133 +     "cutoff jeans",
134 +     "lowleg pants",
135 +     "yoga pants",
136 +     "pelvic curtain",
137 +     "petticoat",
138 +     "sarong",
139 +     "bike shorts",
140 +     "denim shorts",
141 +     "dolphin shorts",
142 +     "gym shorts",
143 +     "lowleg shorts",
144 +     "micro shorts",
145 +     "pleated shorts",
146 +     "short shorts",
147 +     "bubble skirt",
148 +     "cargo skirt",
149 +     "high-waist skirt",
150 +     "long skirt",
151 +     "lowleg skirt",
152 +     "microskirt",
153 +     "miniskirt",
154 +     "overall skirt",
155 +     "overskirt",
156 +     "plaid skirt",
157 +     "pleated skirt",
158 +     "suspender skirt",
159 +     "tutu",
160 +     "sweatpants",
161 +     "hakama",
162 +     "hakama skirt",
163 +     "hakama pants",
164 | ]
165 |
166 | CLOTHES_FULL = [
167 |     # dresses
    -     "dress", "sweater dress", "sundress", "pinafore dress", "wedding dress",
    -     "china dress", "sailor dress", "armored dress", "frilled dress",
    -     "off-shoulder dress", "strapless dress", "long dress", "short dress",
168 +     "dress",
169 +     "sweater dress",
170 +     "sundress",
171 +     "pinafore dress",
172 +     "wedding dress",
173 +     "china dress",
174 +     "sailor dress",
175 +     "armored dress",
176 +     "frilled dress",
177 +     "off-shoulder dress",
178 +     "strapless dress",
179 +     "long dress",
180 +     "short dress",
181 |     "collared dress",
182 |     # swimwear / bodywear
    -     "swimsuit", "one-piece swimsuit", "bikini", "string bikini", "micro bikini",
    -     "lowleg bikini", "thong bikini", "sports bikini", "leaf bikini",
    -     "side-tie bikini bottom", "venus bikini", "tankini",
    -     "competition swimsuit", "school swimsuit", "slingshot swimsuit",
    -     "swim briefs", "jammers", "legskin", "rash guard", "bikini armor",
    -     "leotard", "strapless leotard", "see-through leotard", "playboy bunny",
    -     "bodysuit", "bodystocking", "jumpsuit", "short jumpsuit", "romper",
    -     "unitard", "overalls", "wetsuit", "springsuit", "diving suit", "bikesuit",
    -     "racing suit", "mecha pilot suit", "plugsuit", "hazmat suit", "g-suit",
183 +     "swimsuit",
184 +     "one-piece swimsuit",
185 +     "bikini",
186 +     "string bikini",
187 +     "micro bikini",
188 +     "lowleg bikini",
189 +     "thong bikini",
190 +     "sports bikini",
191 +     "leaf bikini",
192 +     "side-tie bikini bottom",
193 +     "venus bikini",
194 +     "tankini",
195 +     "competition swimsuit",
196 +     "school swimsuit",
197 +     "slingshot swimsuit",
198 +     "swim briefs",
199 +     "jammers",
200 +     "legskin",
201 +     "rash guard",
202 +     "bikini armor",
203 +     "leotard",
204 +     "strapless leotard",
205 +     "see-through leotard",
206 +     "playboy bunny",
207 +     "bodysuit",
208 +     "bodystocking",
209 +     "jumpsuit",
210 +     "short jumpsuit",
211 +     "romper",
212 +     "unitard",
213 +     "overalls",
214 +     "wetsuit",
215 +     "springsuit",
216 +     "diving suit",
217 +     "bikesuit",
218 +     "racing suit",
219 +     "mecha pilot suit",
220 +     "plugsuit",
221 +     "hazmat suit",
222 +     "g-suit",
223 |     # traditional
    -     "kimono", "yukata", "furisode", "uchikake", "layered kimono",
    -     "short kimono", "hanbok", "ao dai", "hanfu", "changpao", "longpao",
    -     "dirndl", "deel", "thobe", "robe", "bathrobe", "open robe", "tunic",
    -     "cassock", "loincloth", "harem outfit",
224 +     "kimono",
225 +     "yukata",
226 +     "furisode",
227 +     "uchikake",
228 +     "layered kimono",
229 +     "short kimono",
230 +     "hanbok",
231 +     "ao dai",
232 +     "hanfu",
233 +     "changpao",
234 +     "longpao",
235 +     "dirndl",
236 +     "deel",
237 +     "thobe",
238 +     "robe",
239 +     "bathrobe",
240 +     "open robe",
241 +     "tunic",
242 +     "cassock",
243 +     "loincloth",
244 +     "harem outfit",
245 |     # uniforms / outfits
    -     "school uniform", "serafuku", "gakuran", "meiji schoolgirl uniform",
    -     "gym uniform", "military uniform", "band uniform", "track suit",
    -     "pajamas", "maid", "miko", "nontraditional miko", "nun", "waitress",
    -     "cheerleader", "santa costume", "superhero costume", "ghost costume",
    -     "animal costume", "kigurumi", "costume", "cosplay",
    -     "suit", "business suit", "pant suit", "skirt suit", "tuxedo",
    -     "formal clothes", "armor",
246 +     "school uniform",
247 +     "serafuku",
248 +     "gakuran",
249 +     "meiji schoolgirl uniform",
250 +     "gym uniform",
251 +     "military uniform",
252 +     "band uniform",
253 +     "track suit",
254 +     "pajamas",
255 +     "maid",
256 +     "miko",
257 +     "nontraditional miko",
258 +     "nun",
259 +     "waitress",
260 +     "cheerleader",
261 +     "santa costume",
262 +     "superhero costume",
263 +     "ghost costume",
264 +     "animal costume",
265 +     "kigurumi",
266 +     "costume",
267 +     "cosplay",
268 +     "suit",
269 +     "business suit",
270 +     "pant suit",
271 +     "skirt suit",
272 +     "tuxedo",
273 +     "formal clothes",
274 +     "armor",
275 | ]
276 |
277 | CLOTHES_OUTERWEAR = [
    -     "coat", "jacket", "duffel coat", "fur coat", "fur-trimmed coat",
    -     "long coat", "overcoat", "peacoat", "raincoat", "yellow raincoat",
    -     "see-through raincoat", "trench coat", "winter coat", "blazer",
    -     "cropped jacket", "letterman jacket", "safari jacket", "suit jacket",
    -     "sukajan", "tailcoat", "poncho", "cape", "capelet", "cloak", "side cape",
    -     "shawl", "stole", "surcoat", "tabard", "haori", "happi", "hanten",
    -     "shrug", "scapular",
278 +     "coat",
279 +     "jacket",
280 +     "duffel coat",
281 +     "fur coat",
282 +     "fur-trimmed coat",
283 +     "long coat",
284 +     "overcoat",
285 +     "peacoat",
286 +     "raincoat",
287 +     "yellow raincoat",
288 +     "see-through raincoat",
289 +     "trench coat",
290 +     "winter coat",
291 +     "blazer",
292 +     "cropped jacket",
293 +     "letterman jacket",
294 +     "safari jacket",
295 +     "suit jacket",
296 +     "sukajan",
297 +     "tailcoat",
298 +     "poncho",
299 +     "cape",
300 +     "capelet",
301 +     "cloak",
302 +     "side cape",
303 +     "shawl",
304 +     "stole",
305 +     "surcoat",
306 +     "tabard",
307 +     "haori",
308 +     "happi",
309 +     "hanten",
310 +     "shrug",
311 +     "scapular",
312 | ]
313 |
314 | CLOTHES_FOOTWEAR = [
    -     "shoes", "boots", "ankle boots", "armored boots", "cowboy boots",
    -     "high heel boots", "knee boots", "lace-up boots", "rubber boots",
    -     "thigh boots", "work boots", "platform boots", "pointy boots",
    -     "open-toe boots", "winged boots", "sneakers", "high tops", "converse",
    -     "dress shoes", "loafers", "oxfords", "saddle shoes", "flats",
    -     "high heels", "pumps", "stiletto heels", "wedge heels", "platform heels",
    -     "mary janes", "platform footwear", "platform shoes", "platform sandals",
    -     "sandals", "cross-laced sandals", "flip-flops", "gladiator sandals",
    -     "geta", "okobo", "sports sandals", "waraji", "zouri", "monk shoes",
    -     "open-toe shoes", "pointy shoes", "slippers", "animal slippers",
    -     "ballet slippers", "crocs", "uwabaki", "winged sandals", "winged shoes",
    -     "winged slippers", "mules",
315 +     "shoes",
316 +     "boots",
317 +     "ankle boots",
318 +     "armored boots",
319 +     "cowboy boots",
320 +     "high heel boots",
321 +     "knee boots",
322 +     "lace-up boots",
323 +     "rubber boots",
324 +     "thigh boots",
325 +     "work boots",
326 +     "platform boots",
327 +     "pointy boots",
328 +     "open-toe boots",
329 +     "winged boots",
330 +     "sneakers",
331 +     "high tops",
332 +     "converse",
333 +     "dress shoes",
334 +     "loafers",
335 +     "oxfords",
336 +     "saddle shoes",
337 +     "flats",
338 +     "high heels",
339 +     "pumps",
340 +     "stiletto heels",
341 +     "wedge heels",
342 +     "platform heels",
343 +     "mary janes",
344 +     "platform footwear",
345 +     "platform shoes",
346 +     "platform sandals",
347 +     "sandals",
348 +     "cross-laced sandals",
349 +     "flip-flops",
350 +     "gladiator sandals",
351 +     "geta",
352 +     "okobo",
353 +     "sports sandals",
354 +     "waraji",
355 +     "zouri",
356 +     "monk shoes",
357 +     "open-toe shoes",
358 +     "pointy shoes",
359 +     "slippers",
360 +     "animal slippers",
361 +     "ballet slippers",
362 +     "crocs",
363 +     "uwabaki",
364 +     "winged sandals",
365 +     "winged shoes",
366 +     "winged slippers",
367 +     "mules",
368 | ]
369 |
370 | CLOTHES_LEGWEAR = [
    -     "thighhighs", "kneehighs", "over-kneehighs", "pantyhose",
    -     "thighband pantyhose", "leggings", "leg warmers", "socks", "ankle socks",
    -     "bobby socks", "loose socks", "tabi", "toe socks", "tube socks",
    -     "fishnets", "fishnet pantyhose", "fishnet thighhighs", "bare legs",
371 +     "thighhighs",
372 +     "kneehighs",
373 +     "over-kneehighs",
374 +     "pantyhose",
375 +     "thighband pantyhose",
376 +     "leggings",
377 +     "leg warmers",
378 +     "socks",
379 +     "ankle socks",
380 +     "bobby socks",
381 +     "loose socks",
382 +     "tabi",
383 +     "toe socks",
384 +     "tube socks",
385 +     "fishnets",
386 +     "fishnet pantyhose",
387 +     "fishnet thighhighs",
388 +     "bare legs",
389 | ]
390 |
391 | CLOTHES_UNDERWEAR = [
    -     "underwear", "bra", "panties", "lingerie", "babydoll", "negligee",
    -     "boxers", "briefs", "boxer briefs", "sports bra", "strapless bra",
    -     "garter belt", "fundoshi", "sarashi", "chest sarashi", "underwear only",
392 +     "underwear",
393 +     "bra",
394 +     "panties",
395 +     "lingerie",
396 +     "babydoll",
397 +     "negligee",
398 +     "boxers",
399 +     "briefs",
400 +     "boxer briefs",
401 +     "sports bra",
402 +     "strapless bra",
403 +     "garter belt",
404 +     "fundoshi",
405 +     "sarashi",
406 +     "chest sarashi",
407 +     "underwear only",
408 | ]
--------------------------------------------------------------------------------
413 |     "bottom": ["skirt", "pants", "shorts"],
    -     "full": ["dress", "bikini", "swimsuit", "one-piece swimsuit", "leotard",
    -              "bodysuit", "kimono"],
414 +     "full": [
415 +         "dress",
416 +         "bikini",
417 +         "swimsuit",
418 +         "one-piece swimsuit",
419 +         "leotard",
420 +         "bodysuit",
421 +         "kimono",
422 +     ],
423 |     "outerwear": ["jacket", "coat", "cape"],
--------------------------------------------------------------------------------
434 | POSE = [
    -     "standing", "sitting", "kneeling", "on one knee", "lying", "on back",
    -     "on side", "on stomach", "reclining", "squatting", "crouching",
    -     "all fours", "crawling", "walking", "running", "jumping", "hopping",
    -     "pouncing", "midair", "falling", "floating", "flying", "straddling",
    -     "thigh straddling", "upright straddle", "seiza", "wariza", "yokozuwari",
    -     "indian style", "lotus position", "butterfly sitting", "fetal position",
    -     "figure four sitting", "standing on one leg", "leaning forward",
    -     "leaning back", "bent over", "arched back", "top-down bottom-up",
    -     "upside-down", "handstand", "headstand", "stretching", "fighting stance",
    -     "battoujutsu stance", "hugging own legs", "knees to chest", "prostration",
    -     "cowering", "balancing", "sitting on lap", "sitting on person",
    -     "spread eagle position", "yoga", "chest stand", "faceplant",
435 +     "standing",
436 +     "sitting",
437 +     "kneeling",
438 +     "on one knee",
439 +     "lying",
440 +     "on back",
441 +     "on side",
442 +     "on stomach",
443 +     "reclining",
444 +     "squatting",
445 +     "crouching",
446 +     "all fours",
447 +     "crawling",
448 +     "walking",
449 +     "running",
450 +     "jumping",
451 +     "hopping",
452 +     "pouncing",
453 +     "midair",
454 +     "falling",
455 +     "floating",
456 +     "flying",
457 +     "straddling",
458 +     "thigh straddling",
459 +     "upright straddle",
460 +     "seiza",
461 +     "wariza",
462 +     "yokozuwari",
463 +     "indian style",
464 +     "lotus position",
465 +     "butterfly sitting",
466 +     "fetal position",
467 +     "figure four sitting",
468 +     "standing on one leg",
469 +     "leaning forward",
470 +     "leaning back",
471 +     "bent over",
472 +     "arched back",
473 +     "top-down bottom-up",
474 +     "upside-down",
475 +     "handstand",
476 +     "headstand",
477 +     "stretching",
478 +     "fighting stance",
479 +     "battoujutsu stance",
480 +     "hugging own legs",
481 +     "knees to chest",
482 +     "prostration",
483 +     "cowering",
484 +     "balancing",
485 +     "sitting on lap",
486 +     "sitting on person",
487 +     "spread eagle position",
488 +     "yoga",
489 +     "chest stand",
490 +     "faceplant",
491 | ]
492 |
493 | EXPRESSION = [
    -     "smile", "grin", "evil smile", "evil grin", "light smile", "sad smile",
    -     "seductive smile", "crazy smile", "forced smile", "smirk", "smug",
    -     "doyagao", "happy", "sad", "angry", "annoyed", "frown", "pout",
    -     "serious", "expressionless", "surprised", "scared", "worried", "nervous",
    -     "embarrassed", "flustered", "confused", "bored", "sleepy", "determined",
    -     "thinking", "pensive", "disgust", "disdain", "despair", "depressed",
    -     "excited", "shy", "envy", "grimace", "scowl", "glaring", "screaming",
    -     "sobbing", "crying", "tears", "drunk", "crazy", "clenched teeth",
    -     "panicking", "horrified", "lonely", "unamused", "exhausted", "frustrated",
    -     "gloom (expression)", "kubrick stare", "staring", "wince", "sulking",
494 +     "smile",
495 +     "grin",
496 +     "evil smile",
497 +     "evil grin",
498 +     "light smile",
499 +     "sad smile",
500 +     "seductive smile",
501 +     "crazy smile",
502 +     "forced smile",
503 +     "smirk",
504 +     "smug",
505 +     "doyagao",
506 +     "happy",
507 +     "sad",
508 +     "angry",
509 +     "annoyed",
510 +     "frown",
511 +     "pout",
512 +     "serious",
513 +     "expressionless",
514 +     "surprised",
515 +     "scared",
516 +     "worried",
517 +     "nervous",
518 +     "embarrassed",
519 +     "flustered",
520 +     "confused",
521 +     "bored",
522 +     "sleepy",
523 +     "determined",
524 +     "thinking",
525 +     "pensive",
526 +     "disgust",
527 +     "disdain",
528 +     "despair",
529 +     "depressed",
530 +     "excited",
531 +     "shy",
532 +     "envy",
533 +     "grimace",
534 +     "scowl",
535 +     "glaring",
536 +     "screaming",
537 +     "sobbing",
538 +     "crying",
539 +     "tears",
540 +     "drunk",
541 +     "crazy",
542 +     "clenched teeth",
543 +     "panicking",
544 +     "horrified",
545 +     "lonely",
546 +     "unamused",
547 +     "exhausted",
548 +     "frustrated",
549 +     "gloom (expression)",
550 +     "kubrick stare",
551 +     "staring",
552 +     "wince",
553 +     "sulking",
554 | ]
555 |
556 | HAIR_LENGTH = [
    -     "bald", "bald female", "very short hair", "short hair", "medium hair",
    -     "long hair", "very long hair", "absurdly long hair", "big hair",
557 +     "bald",
558 +     "bald female",
559 +     "very short hair",
560 +     "short hair",
561 +     "medium hair",
562 +     "long hair",
563 +     "very long hair",
564 +     "absurdly long hair",
565 +     "big hair",
566 | ]
567 |
568 | HAIR_STYLE = [
    -     "bob cut", "inverted bob", "bowl cut", "pixie cut", "buzz cut",
    -     "crew cut", "undercut", "flattop", "wolf cut", "hime cut",
    -     "jellyfish cut", "mullet", "braid", "braids", "braided bangs",
    -     "front braid", "side braid", "crown braid", "single braid", "twin braids",
    -     "low twin braids", "multiple braids", "rope braid", "french braid",
    -     "cornrows", "dreadlocks", "box braids", "braided ponytail", "ponytail",
    -     "folded ponytail", "front ponytail", "high ponytail", "low ponytail",
    -     "short ponytail", "side ponytail", "high side ponytail",
    -     "low side ponytail", "split ponytail", "topknot", "twintails",
    -     "low twintails", "short twintails", "uneven twintails", "tri tails",
    -     "quad tails", "one side up", "two side up", "half updo", "hair bun",
    -     "single hair bun", "double bun", "braided bun", "cone hair bun",
    -     "donut hair bun", "heart hair bun", "hair rings", "single hair ring",
    -     "drill hair", "twin drills", "single drill", "ringlets", "afro",
    -     "huge afro", "pompadour", "mohawk", "quiff", "beehive hairdo",
    -     "curly hair", "wavy hair", "straight hair", "messy hair", "spiked hair",
    -     "flipped hair", "hair flaps", "fluffy hair", "low-tied long hair",
    -     "multi-tied hair", "chonmage", "hair down", "hair up",
569 +     "bob cut",
570 +     "inverted bob",
571 +     "bowl cut",
572 +     "pixie cut",
573 +     "buzz cut",
574 +     "crew cut",
575 +     "undercut",
576 +     "flattop",
577 +     "wolf cut",
578 +     "hime cut",
579 +     "jellyfish cut",
580 +     "mullet",
581 +     "braid",
582 +     "braids",
583 +     "braided bangs",
584 +     "front braid",
585 +     "side braid",
586 +     "crown braid",
587 +     "single braid",
588 +     "twin braids",
589 +     "low twin braids",
590 +     "multiple braids",
591 +     "rope braid",
592 +     "french braid",
593 +     "cornrows",
594 +     "dreadlocks",
595 +     "box braids",
596 +     "braided ponytail",
597 +     "ponytail",
598 +     "folded ponytail",
599 +     "front ponytail",
600 +     "high ponytail",
601 +     "low ponytail",
602 +     "short ponytail",
603 +     "side ponytail",
604 +     "high side ponytail",
605 +     "low side ponytail",
606 +     "split ponytail",
607 +     "topknot",
608 +     "twintails",
609 +     "low twintails",
610 +     "short twintails",
611 +     "uneven twintails",
612 +     "tri tails",
613 +     "quad tails",
614 +     "one side up",
615 +     "two side up",
616 +     "half updo",
617 +     "hair bun",
618 +     "single hair bun",
619 +     "double bun",
620 +     "braided bun",
621 +     "cone hair bun",
622 +     "donut hair bun",
623 +     "heart hair bun",
624 +     "hair rings",
625 +     "single hair ring",
626 +     "drill hair",
627 +     "twin drills",
628 +     "single drill",
629 +     "ringlets",
630 +     "afro",
631 +     "huge afro",
632 +     "pompadour",
633 +     "mohawk",
634 +     "quiff",
635 +     "beehive hairdo",
636 +     "curly hair",
637 +     "wavy hair",
638 +     "straight hair",
639 +     "messy hair",
640 +     "spiked hair",
641 +     "flipped hair",
642 +     "hair flaps",
643 +     "fluffy hair",
644 +     "low-tied long hair",
645 +     "multi-tied hair",
646 +     "chonmage",
647 +     "hair down",
648 +     "hair up",
649 | ]
650 |
    - HAIR_COLOR = (
    -     ["%s hair" % c for c in COLORS if c != "yellow"]
    -     + ["blonde hair", "light blue hair", "light brown hair", "dark blue hair",
    -        "platinum blonde hair", "multicolored hair", "gradient hair",
    -        "streaked hair", "two-tone hair", "colored inner hair",
    -        "split-color hair", "rainbow hair", "colored tips"]
    - )
651 + HAIR_COLOR = ["%s hair" % c for c in COLORS if c != "yellow"] + [
652 +     "blonde hair",
653 +     "light blue hair",
654 +     "light brown hair",
655 +     "dark blue hair",
656 +     "platinum blonde hair",
657 +     "multicolored hair",
658 +     "gradient hair",
659 +     "streaked hair",
660 +     "two-tone hair",
661 +     "colored inner hair",
662 +     "split-color hair",
663 +     "rainbow hair",
664 +     "colored tips",
665 + ]
666 |
    - EYE_COLOR = (
    -     ["%s eyes" % c for c in COLORS]
    -     + ["yellow eyes", "amber eyes", "light blue eyes", "dark blue eyes",
    -        "heterochromia", "multicolored eyes"]
    - )
667 + EYE_COLOR = ["%s eyes" % c for c in COLORS] + [
668 +     "yellow eyes",
669 +     "amber eyes",
670 +     "light blue eyes",
671 +     "dark blue eyes",
672 +     "heterochromia",
673 +     "multicolored eyes",
674 + ]
675 |
676 | BACKGROUND = [
    -     "indoors", "outdoors",
677 +     "indoors",
678 +     "outdoors",
679 |     # simple backgrounds
    -     "simple background", "two-tone background", "gradient background",
    -     "multicolored background", "starry background", "checkered background",
    -     "striped background", "polka dot background", "floral background",
    -     "sparkle background", "abstract background",
680 +     "simple background",
681 +     "two-tone background",
682 +     "gradient background",
683 +     "multicolored background",
684 +     "starry background",
685 +     "checkered background",
686 +     "striped background",
687 +     "polka dot background",
688 +     "floral background",
689 +     "sparkle background",
690 +     "abstract background",
691 |     # rooms / buildings
    -     "bedroom", "bathroom", "bathtub", "classroom", "clubroom", "kitchen",
    -     "library", "living room", "dining room", "office", "cubicle", "infirmary",
    -     "cafeteria", "changing room", "locker room", "fitting room", "fitness gym",
    -     "school gym", "laboratory", "stage", "storage room", "closet", "dungeon",
    -     "prison cell", "ballroom", "courtroom", "workshop", "hotel room",
    -     "messy room", "otaku room", "cafe", "restaurant", "bar", "izakaya",
    -     "tavern", "casino", "nightclub", "church", "cathedral", "mosque",
    -     "shrine", "temple", "pagoda", "synagogue", "castle", "hospital", "school",
    -     "school entrance", "rooftop", "ruins", "sewer", "hallway", "apartment",
    -     "house", "hotel", "hut", "shack", "barn", "greenhouse", "conservatory",
    -     "garage", "gas station", "factory", "warehouse", "refinery",
    -     "power plant", "construction site", "military base", "bunker", "arcade",
    -     "aquarium", "zoo", "museum", "art gallery", "planetarium", "observatory",
    -     "stadium", "arena", "theater", "movie theater", "amphitheater",
    -     "bowling alley", "skating rink", "mall", "supermarket",
    -     "convenience store", "bookstore", "bakery", "flower shop", "pharmacy",
    -     "salon", "market", "market stall", "amusement park", "ferris wheel",
    -     "carousel", "roller coaster", "onsen", "graveyard", "skyscraper",
    -     "lighthouse", "windmill", "treehouse", "train station", "airport",
    -     "hangar", "control tower", "prison", "tomb", "clock tower", "bell tower",
692 +     "bedroom",
693 +     "bathroom",
694 +     "bathtub",
695 +     "classroom",
696 +     "clubroom",
697 +     "kitchen",
698 +     "library",
699 +     "living room",
700 +     "dining room",
701 +     "office",
702 +     "cubicle",
703 +     "infirmary",
704 +     "cafeteria",
705 +     "changing room",
706 +     "locker room",
707 +     "fitting room",
708 +     "fitness gym",
709 +     "school gym",
710 +     "laboratory",
711 +     "stage",
712 +     "storage room",
713 +     "closet",
714 +     "dungeon",
715 +     "prison cell",
716 +     "ballroom",
717 +     "courtroom",
718 +     "workshop",
719 +     "hotel room",
720 +     "messy room",
721 +     "otaku room",
722 +     "cafe",
723 +     "restaurant",
724 +     "bar",
725 +     "izakaya",
726 +     "tavern",
727 +     "casino",
728 +     "nightclub",
729 +     "church",
730 +     "cathedral",
731 +     "mosque",
732 +     "shrine",
733 +     "temple",
734 +     "pagoda",
735 +     "synagogue",
736 +     "castle",
737 +     "hospital",
738 +     "school",
739 +     "school entrance",
740 +     "rooftop",
741 +     "ruins",
742 +     "sewer",
743 +     "hallway",
744 +     "apartment",
745 +     "house",
746 +     "hotel",
747 +     "hut",
748 +     "shack",
749 +     "barn",
750 +     "greenhouse",
751 +     "conservatory",
752 +     "garage",
753 +     "gas station",
754 +     "factory",
755 +     "warehouse",
756 +     "refinery",
757 +     "power plant",
758 +     "construction site",
759 +     "military base",
760 +     "bunker",
761 +     "arcade",
762 +     "aquarium",
763 +     "zoo",
764 +     "museum",
765 +     "art gallery",
766 +     "planetarium",
767 +     "observatory",
768 +     "stadium",
769 +     "arena",
770 +     "theater",
771 +     "movie theater",
772 +     "amphitheater",
773 +     "bowling alley",
774 +     "skating rink",
775 +     "mall",
776 +     "supermarket",
777 +     "convenience store",
778 +     "bookstore",
779 +     "bakery",
780 +     "flower shop",
781 +     "pharmacy",
782 +     "salon",
783 +     "market",
784 +     "market stall",
785 +     "amusement park",
786 +     "ferris wheel",
787 +     "carousel",
788 +     "roller coaster",
789 +     "onsen",
790 +     "graveyard",
791 +     "skyscraper",
792 +     "lighthouse",
793 +     "windmill",
794 +     "treehouse",
795 +     "train station",
796 +     "airport",
797 +     "hangar",
798 +     "control tower",
799 +     "prison",
800 +     "tomb",
801 +     "clock tower",
802 +     "bell tower",
803 |     # outdoor / nature
    -     "beach", "shore", "ocean", "lake", "river", "pond", "stream", "waterfall",
    -     "poolside", "pool", "canyon", "cave", "cliff", "desert", "oasis",
    -     "forest", "bamboo forest", "jungle", "meadow", "mountain", "volcano",
    -     "hill", "island", "floating island", "glacier", "wasteland", "savannah",
    -     "wetland", "nature", "park", "playground", "garden", "flower field",
    -     "wheat field", "rice paddy", "field", "city", "cityscape", "town",
    -     "village", "rural", "street", "alley", "sidewalk", "crosswalk", "road",
    -     "dirt road", "highway", "path", "bridge", "tunnel", "harbor", "pier",
    -     "dock", "jetty", "fountain", "parking lot", "seascape", "railroad tracks",
    -     "railroad crossing", "running track", "soccer field", "landscape",
    -     "space", "moon", "planet", "asteroid", "space station",
    -     "vehicle interior", "car interior", "bus interior", "train interior",
    -     "airplane interior", "cockpit", "spacecraft interior",
804 +     "beach",
805 +     "shore",
806 +     "ocean",
807 +     "lake",
808 +     "river",
809 +     "pond",
810 +     "stream",
811 +     "waterfall",
812 +     "poolside",
813 +     "pool",
814 +     "canyon",
815 +     "cave",
816 +     "cliff",
817 +     "desert",
818 +     "oasis",
819 +     "forest",
820 +     "bamboo forest",
821 +     "jungle",
822 +     "meadow",
823 +     "mountain",
824 +     "volcano",
825 +     "hill",
826 +     "island",
827 +     "floating island",
828 +     "glacier",
829 +     "wasteland",
830 +     "savannah",
831 +     "wetland",
832 +     "nature",
833 +     "park",
834 +     "playground",
835 +     "garden",
836 +     "flower field",
837 +     "wheat field",
838 +     "rice paddy",
839 +     "field",
840 +     "city",
841 +     "cityscape",
842 +     "town",
843 +     "village",
844 +     "rural",
845 +     "street",
846 +     "alley",
847 +     "sidewalk",
848 +     "crosswalk",
849 +     "road",
850 +     "dirt road",
851 +     "highway",
852 +     "path",
853 +     "bridge",
854 +     "tunnel",
855 +     "harbor",
856 +     "pier",
857 +     "dock",
858 +     "jetty",
859 +     "fountain",
860 +     "parking lot",
861 +     "seascape",
862 +     "railroad tracks",
863 +     "railroad crossing",
864 +     "running track",
865 +     "soccer field",
866 +     "landscape",
867 +     "space",
868 +     "moon",
869 +     "planet",
870 +     "asteroid",
871 +     "space station",
872 +     "vehicle interior",
873 +     "car interior",
874 +     "bus interior",
875 +     "train interior",
876 +     "airplane interior",
877 +     "cockpit",
878 +     "spacecraft interior",
879 | ]
880 |
881 | # Accessories never conflict; used only for detection / reporting.
882 | ACCESSORIES = [
    -     "gloves", "elbow gloves", "fingerless gloves", "mittens", "scarf",
    -     "necktie", "bowtie", "choker", "collar", "necklace", "earrings",
    -     "bracelet", "ring", "belt", "apron", "hair bow", "hair ribbon",
    -     "hairband", "hair ornament", "hairclip", "hair flower", "glasses",
    -     "sunglasses", "mask", "eyepatch", "wrist cuffs", "detached sleeves",
    -     "arm warmers", "suspenders", "sash",
883 +     "gloves",
884 +     "elbow gloves",
885 +     "fingerless gloves",
886 +     "mittens",
887 +     "scarf",
888 +     "necktie",
889 +     "bowtie",
890 +     "choker",
891 +     "collar",
892 +     "necklace",
893 +     "earrings",
894 +     "bracelet",
895 +     "ring",
896 +     "belt",
897 +     "apron",
898 +     "hair bow",
899 +     "hair ribbon",
900 +     "hairband",
901 +     "hair ornament",
902 +     "hairclip",
903 +     "hair flower",
904 +     "glasses",
905 +     "sunglasses",
906 +     "mask",
907 +     "eyepatch",
908 +     "wrist cuffs",
909 +     "detached sleeves",
910 +     "arm warmers",
911 +     "suspenders",
912 +     "sash",
913 | ]
--------------------------------------------------------------------------------
971 | PATTERN_EXCEPTIONS = {
    -     "suit jacket",       # jacket, not suit -> caught by explicit list anyway
972 +     "suit jacket",  # jacket, not suit -> caught by explicit list anyway
973 |     "swim cap",
    -     "kneecap", "kneecaps",
974 +     "kneecap",
975 +     "kneecaps",
976 |     "bracelet",
    -     "zebra print", "cow print",
    -     "closed eyes", "half-closed eyes", "empty eyes", "rolling eyes",
    -     "cross-eyed", "wide-eyed",
977 +     "zebra print",
978 +     "cow print",
979 +     "closed eyes",
980 +     "half-closed eyes",
981 +     "empty eyes",
982 +     "rolling eyes",
983 +     "cross-eyed",
984 +     "wide-eyed",
985 | }
    |

unformatted: File would be reformatted
   --> nodes/lib/tag_guard.py:5:1
    |
4   | """
5   +
6   | import re
--------------------------------------------------------------------------------
10  |     from .tag_data import (
    -         CLOTHES, CLOTHES_CONFLICTS, CATEGORIES, ACCESSORIES,
    -         PATTERNS, PATTERN_EXCEPTIONS,
11  +         CLOTHES,
12  +         CLOTHES_CONFLICTS,
13  +         CATEGORIES,
14  +         ACCESSORIES,
15  +         PATTERNS,
16  +         PATTERN_EXCEPTIONS,
17  |     )
--------------------------------------------------------------------------------
21  |     from tag_data import (
    -         CLOTHES, CLOTHES_CONFLICTS, CATEGORIES, ACCESSORIES,
    -         PATTERNS, PATTERN_EXCEPTIONS,
22  +         CLOTHES,
23  +         CLOTHES_CONFLICTS,
24  +         CATEGORIES,
25  +         ACCESSORIES,
26  +         PATTERNS,
27  +         PATTERN_EXCEPTIONS,
28  |     )
29  |
30  | MODES = ("auto", "off", "ban_all")
    - CATEGORY_NAMES = ("clothes", "pose", "expression", "hair_length",
    -                   "hair_style", "hair_color", "eye_color", "background")
31  + CATEGORY_NAMES = (
32  +     "clothes",
33  +     "pose",
34  +     "expression",
35  +     "hair_length",
36  +     "hair_style",
37  +     "hair_color",
38  +     "eye_color",
39  +     "background",
40  + )
41  |
--------------------------------------------------------------------------------
81  |         # for longer suffixes only, to avoid e.g. "zebra" ~ "bra".
    -         if (tag == suffix or tag.endswith(" " + suffix)
    -                 or (len(suffix) >= 5 and tag.endswith(suffix))):
82  +         if (
83  +             tag == suffix
84  +             or tag.endswith(" " + suffix)
85  +             or (len(suffix) >= 5 and tag.endswith(suffix))
86  +         ):
87  |             return (cat, sub)
--------------------------------------------------------------------------------
109 | _SUBJECT_TAGS = {
    -     "solo", "solo focus", "male focus", "female focus",
    -     "multiple boys", "multiple girls", "no humans", "everyone",
110 +     "solo",
111 +     "solo focus",
112 +     "male focus",
113 +     "female focus",
114 +     "multiple boys",
115 +     "multiple girls",
116 +     "no humans",
117 +     "everyone",
118 |     "loli",
--------------------------------------------------------------------------------
151 |             import numpy as np
    -             artifact.ensure(_COOC_PATH, _COOC_URL, _COOC_SHA256,
    -                             "tag_guard", "26MB")
152 +
153 +             artifact.ensure(_COOC_PATH, _COOC_URL, _COOC_SHA256, "tag_guard", "26MB")
154 |             data = np.load(_COOC_PATH)
--------------------------------------------------------------------------------
185 |         import numpy as np
186 +
187 |         pos = np.nonzero(ids == j)[0]
--------------------------------------------------------------------------------
207 |
    - BUCKETS = ("characters", "clothes", "body", "expression", "pose",
    -            "background", "objects", "nsfw", "others", "compositions")
208 + BUCKETS = (
209 +     "characters",
210 +     "clothes",
211 +     "body",
212 +     "expression",
213 +     "pose",
214 +     "background",
215 +     "objects",
216 +     "nsfw",
217 +     "others",
218 +     "compositions",
219 + )
220 |
--------------------------------------------------------------------------------
253 |
254 +
255 | def bucket_of(tag):
--------------------------------------------------------------------------------
319 |     x = min(max(x, 0.0), 1.0)
    -     return lift_th * base ** x
320 +     return lift_th * base**x
321 |
--------------------------------------------------------------------------------
339 |         same_cat = tag_cat is not None and tag_cat == classify(ref)[0]
    -         base = (_LIFT_CURVE_BASE_CLOTHES if tag_clothes and _is_clothes(ref)
    -                 else _LIFT_CURVE_BASE)
340 +         base = (
341 +             _LIFT_CURVE_BASE_CLOTHES
342 +             if tag_clothes and _is_clothes(ref)
343 +             else _LIFT_CURVE_BASE
344 +         )
345 |         if lift < _pair_lift_th(cos, cos_th, lift_th, base) and (
    -                 cos >= cos_th or same_cat):
346 +             cos >= cos_th or same_cat
347 +         ):
348 |             return ref
--------------------------------------------------------------------------------
385 |
    - def filter_by_conflicts(generated_prompt, locked_prompt="",
    -                         cos_th=0.75, lift_th=0.2,
    -                         restrict_category=None):
386 + def filter_by_conflicts(
387 +     generated_prompt, locked_prompt="", cos_th=0.75, lift_th=0.2, restrict_category=None
388 + ):
389 |     """Data-driven filter: drop generated tags that conflict with locked
--------------------------------------------------------------------------------
477 |     # same bar is_conflict actually judged against.
    -     cos_stars = (cos_th,
    -                  cos_th + (1 - cos_th) / 3,
    -                  cos_th + 2 * (1 - cos_th) / 3)
478 +     cos_stars = (cos_th, cos_th + (1 - cos_th) / 3, cos_th + 2 * (1 - cos_th) / 3)
479 |     note = ""
480 |     if len(rows) > _TABLE_MAX_ROWS:
481 |         import random
482 +
483 |         removed = [r for r in rows if r[4] == "REMOVED"]
484 |         kept = [r for r in rows if r[4] != "REMOVED"]
485 |         n_kept = max(0, _TABLE_MAX_ROWS - len(removed))
486 |         note = "(showing %d of %d kept rows, sampled)" % (
    -             min(n_kept, len(kept)), len(kept))
487 +             min(n_kept, len(kept)),
488 +             len(kept),
489 +         )
490 |         rows = removed + random.sample(kept, min(n_kept, len(kept)))
--------------------------------------------------------------------------------
505 |         else:
    -             base = (_LIFT_CURVE_BASE_CLOTHES if _is_clothes(t) and _is_clothes(ref)
    -                     else _LIFT_CURVE_BASE)
506 +             base = (
507 +                 _LIFT_CURVE_BASE_CLOTHES
508 +                 if _is_clothes(t) and _is_clothes(ref)
509 +                 else _LIFT_CURVE_BASE
510 +             )
511 |             th_pair = _pair_lift_th(cos, cos_th, lift_th, base)
--------------------------------------------------------------------------------
519 |         # cos/lift right-aligned, text columns left-aligned
    -         out = [row[i].rjust(widths[i]) if i in (2, 3) else row[i].ljust(widths[i])
    -                for i in range(6)]
520 +         out = [
521 +             row[i].rjust(widths[i]) if i in (2, 3) else row[i].ljust(widths[i])
522 +             for i in range(6)
523 +         ]
524 |         return "| %s |" % " | ".join(out)
525 |
    -     lines = [fmt(header),
    -              "|%s|" % "|".join("-" * (w + 2) for w in widths)]
526 +     lines = [fmt(header), "|%s|" % "|".join("-" * (w + 2) for w in widths)]
527 |     lines.extend(fmt(r) for r in cells)
--------------------------------------------------------------------------------
537 |
538 +
539 | def cooc_available():
540 |     return bool(_load_cooc())
541 |
542 |
    - def build_ban_tags(prompt, modes=None, clothes_strict=False,
    -                    use_underscores=False, extra_ban=""):
543 + def build_ban_tags(
544 +     prompt, modes=None, clothes_strict=False, use_underscores=False, extra_ban=""
545 + ):
546 |     """Build a ban list from the locked prompt.
--------------------------------------------------------------------------------
575 |             ban.update(normalize(t) for t in CLOTHES[sub])
    -         detected = sorted(t for k, v in found.items()
    -                           if k.startswith("clothes/") for t in v)
    -         report.append("clothes: detected %s -> banning subcategories %s"
    -                       % (", ".join(detected), ", ".join(sorted(banned_subs))))
576 +         detected = sorted(
577 +             t for k, v in found.items() if k.startswith("clothes/") for t in v
578 +         )
579 +         report.append(
580 +             "clothes: detected %s -> banning subcategories %s"
581 +             % (", ".join(detected), ", ".join(sorted(banned_subs)))
582 +         )
583 |
--------------------------------------------------------------------------------
591 |             ban.update(normalize(t) for t in cat_tags)
    -             report.append("%s: detected %s -> banning rest of category"
    -                           % (cat, ", ".join(sorted(found[cat]))))
592 +             report.append(
593 +                 "%s: detected %s -> banning rest of category"
594 +                 % (cat, ", ".join(sorted(found[cat])))
595 +             )
596 |
--------------------------------------------------------------------------------
607 |
    - def filter_generated(generated_prompt, locked_prompt="", modes=None,
    -                      clothes_strict=False):
608 + def filter_generated(
609 +     generated_prompt, locked_prompt="", modes=None, clothes_strict=False
610 + ):
611 |     """Remove tags from generated_prompt that conflict with locked_prompt
--------------------------------------------------------------------------------
638 |                 if mode != "off":
    -                     present_subs = {k.split("/")[1] for k in seen
    -                                     if k.startswith("clothes/")}
639 +                     present_subs = {
640 +                         k.split("/")[1] for k in seen if k.startswith("clothes/")
641 +                     }
642 |                     conflict = set()
    |

unformatted: File would be reformatted
   --> nodes/lib/tag_solo.py:37:1
    |
36  | """
37  +
38  | import re
--------------------------------------------------------------------------------
59  | # covers the other reading.
    - _NOT_FEMALE_ONLY = frozenset({
    -     "futanari", "newhalf", "otoko no ko", "male focus", "multiple boys",
    -     "1boy", "2boys", "3boys", "4boys", "5boys", "6+boys",
    - })
60  + _NOT_FEMALE_ONLY = frozenset(
61  +     {
62  +         "futanari",
63  +         "newhalf",
64  +         "otoko no ko",
65  +         "male focus",
66  +         "multiple boys",
67  +         "1boy",
68  +         "2boys",
69  +         "3boys",
70  +         "4boys",
71  +         "5boys",
72  +         "6+boys",
73  +     }
74  + )
75  |
76  | # Subject tags that put more than one character in the picture whatever
77  | # the counts say, so a prompt carrying one is never "alone".
    - _CROWD = frozenset({
    -     "solo focus", "multiple girls", "multiple boys", "multiple others",
    -     "everyone",
    - })
78  + _CROWD = frozenset(
79  +     {
80  +         "solo focus",
81  +         "multiple girls",
82  +         "multiple boys",
83  +         "multiple others",
84  +         "everyone",
85  +     }
86  + )
87  |
--------------------------------------------------------------------------------
127 |     female = not (tags & _NOT_FEMALE_ONLY) and any(
    -         m.group(2) == "girl" for m in counted)
128 +         m.group(2) == "girl" for m in counted
129 +     )
130 |     return True, female
--------------------------------------------------------------------------------
141 |     import numpy as np
142 +
143 |     sections = _sections() or {}
144 |     multi = sections.get("multi_person", frozenset())
145 |     male = sections.get("male_anatomy", frozenset())
146 |     spelled = [t.replace("_", " ") for t in vocab]
    -     return (np.array([_ANOTHER in t or t in multi for t in spelled]),
    -             np.array([t in male for t in spelled]))
147 +     return (
148 +         np.array([_ANOTHER in t or t in multi for t in spelled]),
149 +         np.array([t in male for t in spelled]),
150 +     )
    |

unformatted: File would be reformatted
   --> nodes/lib/tag_subject.py:37:11
    |
36  | _URL = artifact.url_for("data-v1.0.0", "subject_joint_v1.npz")
    - _SHA256 = ("7cd0b1c461e81198cb30a5ea46037eb4"
    -            "a949c5a0a5ef6e1383039756b19be71e")
37  + _SHA256 = "7cd0b1c461e81198cb30a5ea46037eb4a949c5a0a5ef6e1383039756b19be71e"
38  |
--------------------------------------------------------------------------------
44  |
45  +
46  | class SubjectJoint:
--------------------------------------------------------------------------------
50  |         import numpy as np
51  +
52  |         if path == _PATH:
--------------------------------------------------------------------------------
90  |         self._sig = self._sig[order]
    -         self.indptr = np.searchsorted(veto_pair[order],
    -                                       np.arange(len(pair_a) + 1))
91  +         self.indptr = np.searchsorted(veto_pair[order], np.arange(len(pair_a) + 1))
92  |         self._size = len(vocab)
--------------------------------------------------------------------------------
105 |                 if k is None:
    -                     continue                  # pair too rare to have data
106 +                     continue  # pair too rare to have data
107 |                 lo, hi = self.indptr[k], self.indptr[k + 1]
    |

unformatted: File would be reformatted
   --> nodes/lib/tag_suggest.py:17:1
    |
16  | """
17  +
18  | import math
19  | import re
20  |
    - from . import (artifact, tag_alias, tag_avoid, tag_category,
    -                tag_copyright, tag_solo,
    -                tag_subject, tag_veto)
21  + from . import (
22  +     artifact,
23  +     tag_alias,
24  +     tag_avoid,
25  +     tag_category,
26  +     tag_copyright,
27  +     tag_solo,
28  +     tag_subject,
29  +     tag_veto,
30  + )
31  | from .tag_category import RATING_ORDER
    - from .tag_veto import (normalize, split_prompt_tags, weight_of,
    -                        DEFAULT_LIFT_TH)
32  + from .tag_veto import normalize, split_prompt_tags, weight_of, DEFAULT_LIFT_TH
33  | from .utils import get_logger
34  |
35  | DEFAULT_MIN_COUNT = 5000
    - _MIN_REPEL_LIFT = 1e-6               # keeps log() finite on stored zeros
36  + _MIN_REPEL_LIFT = 1e-6  # keeps log() finite on stored zeros
37  |
--------------------------------------------------------------------------------
71  | # likely than chance given the context (combined lift >= 2)
    - _EOS_LOG_LIFT = 0.6931471805599453   # ln(2)
    - _FALLBACK_TARGET_LEN = 31            # solo-post median, if len_hist absent
72  + _EOS_LOG_LIFT = 0.6931471805599453  # ln(2)
73  + _FALLBACK_TARGET_LEN = 31  # solo-post median, if len_hist absent
74  |
--------------------------------------------------------------------------------
98  | # no entry of its own in "hand_up" versus "looking_up".
    - _PARTICLES = frozenset("""
99  + _PARTICLES = frozenset(
100 +     """
101 |     on in at to of by with from into onto under over above below behind
102 |     between around against across through beside near up down out off
103 |     back together apart forward aside away
    - """.split())
104 + """.split()
105 + )
106 |
--------------------------------------------------------------------------------
150 |     if stage and len(words) == 1:
    -         return stage                          # the opener is the whole tag
    -     at = next((i for i, w in enumerate(words)
    -                if i > 0 and w in _PARTICLES), None)
151 +         return stage  # the opener is the whole tag
152 +     at = next((i for i, w in enumerate(words) if i > 0 and w in _PARTICLES), None)
153 |     if at is None:
154 |         return stage + (("W", _depluralize(words[-1])),)
155 |     left = ("L", "_".join(_depluralize(w) for w in words[:at]))
    -     if at == len(words) - 1:                  # particle, nothing follows
156 +     if at == len(words) - 1:  # particle, nothing follows
157 |         return stage + (left,)
    -     return stage + (left, ("R", "_".join(words[at + 1:])))
158 +     return stage + (left, ("R", "_".join(words[at + 1 :])))
159 |
--------------------------------------------------------------------------------
176 | _ANCHOR_CATEGORIES = ("background", "objects")
    - _ANCHOR_MIN_COUNT = 20000            # common enough to be a familiar scene
    - _ANCHOR_MIN_STRENGTH = 3.4           # ~the top quartile of that pool
    - _ANCHOR_NEIGHBOURS = 32              # how many neighbours the mean spans
    - _ANCHOR_MAX_LEVEL = 1                # sensitive; rating still caps on top
177 + _ANCHOR_MIN_COUNT = 20000  # common enough to be a familiar scene
178 + _ANCHOR_MIN_STRENGTH = 3.4  # ~the top quartile of that pool
179 + _ANCHOR_NEIGHBOURS = 32  # how many neighbours the mean spans
180 + _ANCHOR_MAX_LEVEL = 1  # sensitive; rating still caps on top
181 |
--------------------------------------------------------------------------------
199 | # asked for and the other path did not apply.
    - _IMPLIED_FEMALE = ("1girl", "2girls", "3girls", "4girls", "5girls",
    -                    "6+girls", "multiple_girls")
200 + _IMPLIED_FEMALE = (
201 +     "1girl",
202 +     "2girls",
203 +     "3girls",
204 +     "4girls",
205 +     "5girls",
206 +     "6+girls",
207 +     "multiple_girls",
208 + )
209 | _GIRL_COUNT_RE = re.compile(r"^\d+\+?girls?$|^multiple_girls$")
--------------------------------------------------------------------------------
217 | _SUGGEST_URL = artifact.url_for("data-v1.0.0", "suggest_v1.1.npz")
    - _SUGGEST_SHA256 = ("90248ad9142e28b76d008071cbebfa92c7162c1a"
    -                    "b75002b7011423266d69248f")
218 + _SUGGEST_SHA256 = "90248ad9142e28b76d008071cbebfa92c7162c1ab75002b7011423266d69248f"
219 |
--------------------------------------------------------------------------------
228 |         import numpy as np
229 +
230 |         self._np = np
231 |         if path == _SUGGEST_PATH:
    -             artifact.ensure(path, _SUGGEST_URL, _SUGGEST_SHA256,
    -                             "TagSuggest", "106MB")
232 +             artifact.ensure(path, _SUGGEST_URL, _SUGGEST_SHA256, "TagSuggest", "106MB")
233 |         data = np.load(path)
234 |         self.vocab = [str(t) for t in data["tags"]]
235 |         # same alias folding as TagVeto: old and new spellings share a row
    -         self.index = tag_alias.expand_index(
    -             {t: i for i, t in enumerate(self.vocab)})
236 +         self.index = tag_alias.expand_index({t: i for i, t in enumerate(self.vocab)})
237 |         # per-rating-tier tables; tiers are cumulative (g < s < q < e).
--------------------------------------------------------------------------------
242 |         neg_ids = data.get("neg_ids", None)
    -         neg_lift = (data["neg_lift"].astype(np.float32)
    -                     if "neg_lift" in data else None)
243 +         neg_lift = data["neg_lift"].astype(np.float32) if "neg_lift" in data else None
244 |         for r in ("g", "s", "q", "e"):
--------------------------------------------------------------------------------
250 |                     "len_hist": data[f"len_hist_{r}"].astype(np.float64),
    -                     "posts": (float(data[f"posts_{r}"])
    -                               if f"posts_{r}" in data else 0.0),
251 +                     "posts": (
252 +                         float(data[f"posts_{r}"]) if f"posts_{r}" in data else 0.0
253 +                     ),
254 |                     "neg_ids": neg_ids,
--------------------------------------------------------------------------------
261 |                 "lift": data["nbr_lift"].astype(np.float32),
    -                 "len_hist": (data["len_hist"].astype(np.float64)
    -                              if "len_hist" in data else None),
262 +                 "len_hist": (
263 +                     data["len_hist"].astype(np.float64) if "len_hist" in data else None
264 +                 ),
265 |                 "neg_ids": None,
266 |                 "neg_lift": None,
267 |             }
    -         self._labels = None          # lazy (category, rating) arrays
    -         self._avoid = None           # lazy avoidance table
    -         self._franchise = None       # lazy copyright-signature mask
    -         self._blacklist = None       # (pattern, mask) of the last regex
    -         self._slots = None           # lazy (slot ids per tag, count)
    -         self._solo = None            # lazy (multi-person, male) vetoes
    -         self._anchors = None         # lazy cold-start anchor pool
    -         self._subject = None         # lazy subject-conjunction table
    -         self._veto_ids = None        # lazy vocab mapped onto TagVeto's
268 +         self._labels = None  # lazy (category, rating) arrays
269 +         self._avoid = None  # lazy avoidance table
270 +         self._franchise = None  # lazy copyright-signature mask
271 +         self._blacklist = None  # (pattern, mask) of the last regex
272 +         self._slots = None  # lazy (slot ids per tag, count)
273 +         self._solo = None  # lazy (multi-person, male) vetoes
274 +         self._anchors = None  # lazy cold-start anchor pool
275 +         self._subject = None  # lazy subject-conjunction table
276 +         self._veto_ids = None  # lazy vocab mapped onto TagVeto's
277 |
--------------------------------------------------------------------------------
281 |             source = tag_category.load_labels()
    -             self._labels = (source, source.arrays(self.vocab)) if source \
    -                 else (None, (None, None))
282 +             self._labels = (
283 +                 (source, source.arrays(self.vocab)) if source else (None, (None, None))
284 +             )
285 |         return self._labels
--------------------------------------------------------------------------------
329 |             ids = np.zeros((len(self.vocab), width), dtype=np.int32)
    -             index[None] = 0                           # the empty slot
330 +             index[None] = 0  # the empty slot
331 |             for i, tag in enumerate(self.vocab):
--------------------------------------------------------------------------------
359 |                 return self._anchors
    -             ranks = [source.names.index(n) for n in _ANCHOR_CATEGORIES
    -                      if n in source.names]
360 +             ranks = [
361 +                 source.names.index(n) for n in _ANCHOR_CATEGORIES if n in source.names
362 +             ]
363 |             lift = tier["lift"]
--------------------------------------------------------------------------------
369 |                 & (level_of <= _ANCHOR_MAX_LEVEL)
    -                 & np.isin(cat_of, ranks))[0]
370 +                 & np.isin(cat_of, ranks)
371 +             )[0]
372 |             if not len(pool):
--------------------------------------------------------------------------------
395 |         drawing_characters = (
    -             joint is not None and cat_of is not None
    -             and (allowed is None
    -                  or (source is not None and "characters" in source.names
    -                      and source.names.index("characters") in allowed)))
396 +             joint is not None
397 +             and cat_of is not None
398 +             and (
399 +                 allowed is None
400 +                 or (
401 +                     source is not None
402 +                     and "characters" in source.names
403 +                     and source.names.index("characters") in allowed
404 +                 )
405 +             )
406 +         )
407 |         if drawing_characters:
--------------------------------------------------------------------------------
428 |             row_lift = tier["lift"][i]
    -             real = row_lift > 0                      # drop padding
429 +             real = row_lift > 0  # drop padding
430 |             attract[tier["ids"][i][real]] += np.log(row_lift[real])
431 |             if tier["neg_ids"] is None:
432 |                 continue
433 |             neg_ids = tier["neg_ids"][i]
    -             real = neg_ids >= 0                      # -1 is padding
434 +             real = neg_ids >= 0  # -1 is padding
435 |             repel[neg_ids[real]] += np.log(
    -                 np.maximum(tier["neg_lift"][i][real], _MIN_REPEL_LIFT))
436 +                 np.maximum(tier["neg_lift"][i][real], _MIN_REPEL_LIFT)
437 +             )
438 |         return attract, repel
--------------------------------------------------------------------------------
455 |         except re.error as exc:
    -             logger.error("[TagSuggest] ignoring invalid blacklist regex %r (%s)"
    -                   % (pattern, exc), exc_info=True)
456 +             logger.error(
457 +                 "[TagSuggest] ignoring invalid blacklist regex %r (%s)"
458 +                 % (pattern, exc),
459 +                 exc_info=True,
460 +             )
461 |             return None
462 |         mask = np.fromiter(
463 |             (rx.search(t.replace("_", " ")) is not None for t in self.vocab),
    -             dtype=bool, count=len(self.vocab))
464 +             dtype=bool,
465 +             count=len(self.vocab),
466 +         )
467 |         self._blacklist = (pattern, mask)
--------------------------------------------------------------------------------
526 |
    -     def _eligible(self, counts, min_count, rating, level_of, cat_of,
    -                   allowed, blacklist, filter_copyright=True):
527 +     def _eligible(
528 +         self,
529 +         counts,
530 +         min_count,
531 +         rating,
532 +         level_of,
533 +         cat_of,
534 +         allowed,
535 +         blacklist,
536 +         filter_copyright=True,
537 +     ):
538 |         """Tags allowed to be drawn at all, before any context is read.
--------------------------------------------------------------------------------
576 |         # a few composition tags have ~0 solo-corpus count; floor at 1
    -         prior = np.log(np.maximum(counts.astype(np.float64), 1.0)
    -                        / counts.sum())
577 +         prior = np.log(np.maximum(counts.astype(np.float64), 1.0) / counts.sum())
578 |         w = self._rating_log_weights(rating)
--------------------------------------------------------------------------------
582 |
    -     def suggest(self, inputs, m=10, min_count=DEFAULT_MIN_COUNT,
    -                 lift_th=DEFAULT_LIFT_TH, temperature=0.0,
    -                 top_k=0, top_p=1.0, min_p=0.0, seed=0, rating="e",
    -                 categories="", blacklist="", quota_total=None,
    -                 avoid_alpha=tag_avoid.DEFAULT_ALPHA,
    -                 momentum=DEFAULT_MOMENTUM,
    -                 repetition_penalty=DEFAULT_REPETITION_PENALTY,
    -                 filter_copyright=True):
583 +     def suggest(
584 +         self,
585 +         inputs,
586 +         m=10,
587 +         min_count=DEFAULT_MIN_COUNT,
588 +         lift_th=DEFAULT_LIFT_TH,
589 +         temperature=0.0,
590 +         top_k=0,
591 +         top_p=1.0,
592 +         min_p=0.0,
593 +         seed=0,
594 +         rating="e",
595 +         categories="",
596 +         blacklist="",
597 +         quota_total=None,
598 +         avoid_alpha=tag_avoid.DEFAULT_ALPHA,
599 +         momentum=DEFAULT_MOMENTUM,
600 +         repetition_penalty=DEFAULT_REPETITION_PENALTY,
601 +         filter_copyright=True,
602 +     ):
603 |         """Return up to m tags (Danbooru form) that go with the inputs.
--------------------------------------------------------------------------------
644 |         tags = [normalize(t) for t in inputs]
    -         ids = [self.index[t] for t, w in zip(tags, weights)
    -                if w > 0 and t in self.index]
    -         avoid = [(self.index[t], -w) for t, w in zip(tags, weights)
    -                  if w <= 0 and t in self.index]
645 +         ids = [
646 +             self.index[t] for t, w in zip(tags, weights) if w > 0 and t in self.index
647 +         ]
648 +         avoid = [
649 +             (self.index[t], -w)
650 +             for t, w in zip(tags, weights)
651 +             if w <= 0 and t in self.index
652 +         ]
653 |         rng = np.random.default_rng(seed)
654 |
655 |         source, (cat_of, level_of) = self.labels()
    -         allowed, quota = (tag_category.parse_categories(categories,
    -                                                         source.names)
    -                           if source else (None, None))
656 +         allowed, quota = (
657 +             tag_category.parse_categories(categories, source.names)
658 +             if source
659 +             else (None, None)
660 +         )
661 |         used = {}
--------------------------------------------------------------------------------
693 |         log_prior = self._log_prior(counts, level_of, rating)
    -         eligible = self._eligible(counts, min_count, rating, level_of,
    -                                   cat_of, allowed, blacklist,
    -                                   filter_copyright)
694 +         eligible = self._eligible(
695 +             counts,
696 +             min_count,
697 +             rating,
698 +             level_of,
699 +             cat_of,
700 +             allowed,
701 +             blacklist,
702 +             filter_copyright,
703 +         )
704 |         log_lift, log_repel = self._log_lift_sum(ids, tier)
--------------------------------------------------------------------------------
715 |         # slot of m rather than arriving on top of it
    -         chosen, refs = list(seeded), [t for t, w in zip(tags, weights)
    -                                      if t and w > 0]
716 +         chosen, refs = list(seeded), [t for t, w in zip(tags, weights) if t and w > 0]
717 |         banned = self._repel_veto(ids, tier, lift_th, avoid_alpha)
718 |         for t in refs:
719 |             if t in self.index:
720 |                 banned[self.index[t]] = True
    -         for j, _ in avoid:                    # asked for less, not none --
    -             banned[j] = True                  # but never more
721 +         for j, _ in avoid:  # asked for less, not none --
722 +             banned[j] = True  # but never more
723 |
--------------------------------------------------------------------------------
759 |         slot_of, n_slots = self.slots()
    -         log_penalty = (math.log(repetition_penalty)
    -                        if repetition_penalty > 1 else 0.0)
760 +         log_penalty = math.log(repetition_penalty) if repetition_penalty > 1 else 0.0
761 |         slot_used = np.zeros(n_slots, dtype=np.int32)
762 |         if log_penalty:
763 |             np.add.at(slot_used, slot_of[ids].ravel(), 1)
    -             slot_used[0] = 0                      # the empty slot never hits
764 +             slot_used[0] = 0  # the empty slot never hits
765 |
--------------------------------------------------------------------------------
771 |                 while refs_judged < len(refs):
    -                     banned |= veto.conflict_mask(
    -                         veto_ids, refs[refs_judged], lift_th)
772 +                     banned |= veto.conflict_mask(veto_ids, refs[refs_judged], lift_th)
773 |                     refs_judged += 1
774 |             # candidates: some attraction, allowed, not ruled out
775 |             ok = (log_lift > 0) & eligible & ~banned
776 |             if quota and cat_of is not None:
    -                 spent = [r for r, (key, cap) in quota.items()
    -                          if used.get(key, 0) >= cap]
777 +                 spent = [
778 +                     r for r, (key, cap) in quota.items() if used.get(key, 0) >= cap
779 +                 ]
780 |                 if spent:
--------------------------------------------------------------------------------
785 |             if auto and log_lift[cand].max() < _EOS_LOG_LIFT:
    -                 break                                 # nothing left to say
786 +                 break  # nothing left to say
787 |             # only the candidates can be picked, so the score and the
788 |             # sampling filters run over them alone rather than over a
789 |             # 20k vector that is masked off almost everywhere
    -             logits = (log_prior[cand] + log_lift[cand] + log_repel[cand])
790 +             logits = log_prior[cand] + log_lift[cand] + log_repel[cand]
791 |             if log_penalty:
792 |                 hits = slot_used[slot_of[cand]].sum(axis=1)
793 |                 logits = logits - log_penalty * hits
    -             j = int(cand[self._pick(logits, rng, temperature,
    -                                     top_k, top_p, min_p)])
794 +             j = int(cand[self._pick(logits, rng, temperature, top_k, top_p, min_p)])
795 |             tag = self.vocab[j]
796 |             chosen.append(tag)
    -             refs.append(tag)                          # picks must cohere
    -             banned[j] = True                          # and cannot repeat
797 +             refs.append(tag)  # picks must cohere
798 +             banned[j] = True  # and cannot repeat
799 |             if log_penalty:
--------------------------------------------------------------------------------
805 |                     used[budget[0]] = used.get(budget[0], 0) + 1
    -             gain, loss = self._log_lift_sum([j], tier)   # re-condition
806 +             gain, loss = self._log_lift_sum([j], tier)  # re-condition
807 |             log_lift += momentum * gain
--------------------------------------------------------------------------------
857 |
    - def suggest_tags(prompt, n=10, min_count=DEFAULT_MIN_COUNT,
    -                  temperature=0.0, top_k=0, top_p=1.0, min_p=0.0, seed=0,
    -                  rating="e", categories="", blacklist="",
    -                  lift_th=DEFAULT_LIFT_TH, quota_total=None,
    -                  avoid_alpha=tag_avoid.DEFAULT_ALPHA,
    -                  momentum=DEFAULT_MOMENTUM,
    -                  repetition_penalty=DEFAULT_REPETITION_PENALTY,
    -                  filter_copyright=True):
858 + def suggest_tags(
859 +     prompt,
860 +     n=10,
861 +     min_count=DEFAULT_MIN_COUNT,
862 +     temperature=0.0,
863 +     top_k=0,
864 +     top_p=1.0,
865 +     min_p=0.0,
866 +     seed=0,
867 +     rating="e",
868 +     categories="",
869 +     blacklist="",
870 +     lift_th=DEFAULT_LIFT_TH,
871 +     quota_total=None,
872 +     avoid_alpha=tag_avoid.DEFAULT_ALPHA,
873 +     momentum=DEFAULT_MOMENTUM,
874 +     repetition_penalty=DEFAULT_REPETITION_PENALTY,
875 +     filter_copyright=True,
876 + ):
877 |     """Comma-separated prompt in, list of suggested tags (space form) out."""
878 |     engine = load_suggest()
879 |     inputs = split_prompt_tags(prompt)
    -     tags = engine.suggest(inputs, m=n, min_count=min_count,
    -                           lift_th=lift_th,
    -                           temperature=temperature, top_k=top_k,
    -                           top_p=top_p, min_p=min_p, seed=seed, rating=rating,
    -                           categories=categories, blacklist=blacklist,
    -                           quota_total=quota_total,
    -                           avoid_alpha=avoid_alpha, momentum=momentum,
    -                           repetition_penalty=repetition_penalty,
    -                           filter_copyright=filter_copyright)
880 +     tags = engine.suggest(
881 +         inputs,
882 +         m=n,
883 +         min_count=min_count,
884 +         lift_th=lift_th,
885 +         temperature=temperature,
886 +         top_k=top_k,
887 +         top_p=top_p,
888 +         min_p=min_p,
889 +         seed=seed,
890 +         rating=rating,
891 +         categories=categories,
892 +         blacklist=blacklist,
893 +         quota_total=quota_total,
894 +         avoid_alpha=avoid_alpha,
895 +         momentum=momentum,
896 +         repetition_penalty=repetition_penalty,
897 +         filter_copyright=filter_copyright,
898 +     )
899 |     # keep emoticon tags (^_^, o_o) intact: only wordlike tags get spaces
    -     return [t.replace("_", " ") if re.search(r"[a-z]", t) else t
    -             for t in tags]
900 +     return [t.replace("_", " ") if re.search(r"[a-z]", t) else t for t in tags]
    |

unformatted: File would be reformatted
   --> nodes/lib/tag_veto.py:24:1
    |
23  | """
24  +
25  | import re
--------------------------------------------------------------------------------
40  | _VETO_URL = artifact.url_for("data-v1.0.0", "tag_veto.npz")
    - _VETO_SHA256 = ("3fb3603bcadef8e8add34eb742836215e3c98264"
    -                 "cbcdec7007b16c2215b4bb37")
41  + _VETO_SHA256 = "3fb3603bcadef8e8add34eb742836215e3c98264cbcdec7007b16c2215b4bb37"
42  |
--------------------------------------------------------------------------------
47  | _SUBJECT_RE = re.compile(r"^\d+\+?(boy|girl|other)s?$")
    - _SUBJECT_TAGS = {"solo", "solo_focus", "male_focus", "female_focus",
    -                  "multiple_boys", "multiple_girls", "multiple_others",
    -                  "no_humans", "everyone"}
48  + _SUBJECT_TAGS = {
49  +     "solo",
50  +     "solo_focus",
51  +     "male_focus",
52  +     "female_focus",
53  +     "multiple_boys",
54  +     "multiple_girls",
55  +     "multiple_others",
56  +     "no_humans",
57  +     "everyone",
58  + }
59  |
--------------------------------------------------------------------------------
139 |         # "(blonde hair:1.2)" is one tag and normalize() handles it
    -         if stripped.startswith("(") and stripped.endswith(")") \
    -                 and "," in stripped:
140 +         if stripped.startswith("(") and stripped.endswith(")") and "," in stripped:
141 |             inner = _WEIGHT_RE.sub("", stripped[1:-1].strip()).strip()
--------------------------------------------------------------------------------
163 |         import numpy as np
164 +
165 |         self._np = np
--------------------------------------------------------------------------------
172 |         # any way Danbooru ever has; self.vocab stays the real names
    -         self.index = tag_alias.expand_index(
    -             {t: i for i, t in enumerate(self.vocab)})
173 +         self.index = tag_alias.expand_index({t: i for i, t in enumerate(self.vocab)})
174 |         self._n = len(self.vocab)
--------------------------------------------------------------------------------
188 |         self._starved_row = np.array(
    -             [self._starved.get(t, -1) for t in self.vocab], dtype=np.int64)
    -         self._is_subject_row = np.array(
    -             [is_subject(t) for t in self.vocab], dtype=bool)
189 +             [self._starved.get(t, -1) for t in self.vocab], dtype=np.int64
190 +         )
191 +         self._is_subject_row = np.array([is_subject(t) for t in self.vocab], dtype=bool)
192 |         self._cooc_all = data["starved_cooc"]
--------------------------------------------------------------------------------
200 |             frozenset((self.vocab[i], self.vocab[j])): self.vocab[t]
    -             for i, j, t in zip(data["bridge_a"], data["bridge_b"],
    -                                data["bridge_t"])
201 +             for i, j, t in zip(data["bridge_a"], data["bridge_b"], data["bridge_t"])
202 |         }
--------------------------------------------------------------------------------
229 |         observed = float(self._cooc_all[row, j])
    -         expected = (self._counts_all[self.index[a]] * self._counts_all[j]
    -                     / self._n_all)
230 +         expected = self._counts_all[self.index[a]] * self._counts_all[j] / self._n_all
231 |         if expected < E_MIN:
--------------------------------------------------------------------------------
236 |         """First reference tag that cand contradicts, or None."""
    -         cand_subject = is_subject(cand)          # same for every ref
237 +         cand_subject = is_subject(cand)  # same for every ref
238 |         for ref in refs:
--------------------------------------------------------------------------------
268 |         # conflict() applies one pair at a time
    -         judged = ((cand_ids >= 0) & (cand_ids != ri)
    -                   & (self._is_subject_row[np.maximum(cand_ids, 0)]
    -                      == is_subject(ref)))
269 +         judged = (
270 +             (cand_ids >= 0)
271 +             & (cand_ids != ri)
272 +             & (self._is_subject_row[np.maximum(cand_ids, 0)] == is_subject(ref))
273 +         )
274 |         idx = np.nonzero(judged)[0]
--------------------------------------------------------------------------------
282 |         # the pair that way. Everything else comes from the stored pairs.
    -         lift = np.ones(len(idx), dtype=np.float64)   # 1.0 = no veto
283 +         lift = np.ones(len(idx), dtype=np.float64)  # 1.0 = no veto
284 |         starved_ref = self._starved.get(ref)
285 |         starved_j = self._starved_row[j]
    -         unfiltered = (np.ones(len(idx), dtype=bool) if starved_ref is not None
    -                       else starved_j >= 0)
286 +         unfiltered = (
287 +             np.ones(len(idx), dtype=bool) if starved_ref is not None else starved_j >= 0
288 +         )
289 |
--------------------------------------------------------------------------------
298 |             observed = self._cooc_all[row, other].astype(np.float64)
    -             expected = (self._counts_all[owner] * self._counts_all[other]
    -                         / self._n_all)
299 +             expected = self._counts_all[owner] * self._counts_all[other] / self._n_all
300 |             with np.errstate(divide="ignore", invalid="ignore"):
301 |                 # below the E gate the corpus has no sample to judge with
    -                 lift[sel] = np.where(expected >= E_MIN, observed / expected,
    -                                      1.0)
302 +                 lift[sel] = np.where(expected >= E_MIN, observed / expected, 1.0)
303 |
--------------------------------------------------------------------------------
319 |         np = self._np
    -         return np.array([self.index.get(t, -1) for t in tags],
    -                         dtype=np.int64)
320 +         return np.array([self.index.get(t, -1) for t in tags], dtype=np.int64)
321 |
--------------------------------------------------------------------------------
352 |             else:
    -                 rows.append(Verdict(raw, tag, False, "suggestion", ref,
    -                                     self.pair_lift(tag, ref)))
353 +                 rows.append(
354 +                     Verdict(
355 +                         raw, tag, False, "suggestion", ref, self.pair_lift(tag, ref)
356 +                     )
357 +                 )
358 |         return rows
--------------------------------------------------------------------------------
373 |
    - def filter_by_veto(generated_prompt, fixed_prompt="",
    -                    lift_th=DEFAULT_LIFT_TH):
374 + def filter_by_veto(generated_prompt, fixed_prompt="", lift_th=DEFAULT_LIFT_TH):
375 |     """Drop generated tags that contradict the fixed tags (or earlier
--------------------------------------------------------------------------------
395 |     if not row.keep:
    -         return (row.tag, row.ref, "%.3f" % row.lift, "VETOED",
    -                 veto.bridge_for(row.tag, row.ref) or "-")
396 +         return (
397 +             row.tag,
398 +             row.ref,
399 +             "%.3f" % row.lift,
400 +             "VETOED",
401 +             veto.bridge_for(row.tag, row.ref) or "-",
402 +         )
403 |     verdict = "kept" if row.tag in veto.index else "kept (OOV)"
--------------------------------------------------------------------------------
415 |         import random
416 +
417 |         vetoed = [c for c in cells if c[3] == "VETOED"]
418 |         kept = [c for c in cells if c[3] != "VETOED"]
419 |         cells = vetoed + random.sample(
    -             kept, min(max(0, _TABLE_MAX_ROWS - len(vetoed)), len(kept)))
420 +             kept, min(max(0, _TABLE_MAX_ROWS - len(vetoed)), len(kept))
421 +         )
422 |
423 |     header = ("tag", "vs", "lift", "verdict", "bridge")
    -     widths = [max(len(row[col]) for row in [header] + cells)
    -               for col in range(len(header))]
424 +     widths = [
425 +         max(len(row[col]) for row in [header] + cells) for col in range(len(header))
426 +     ]
427 |
428 |     def fmt(row):
429 |         return "| %s |" % " | ".join(
430 |             cell.rjust(w) if col == 2 else cell.ljust(w)
    -             for col, (cell, w) in enumerate(zip(row, widths)))
431 +             for col, (cell, w) in enumerate(zip(row, widths))
432 +         )
433 |
434 |     lines = [fmt(header), "|%s|" % "|".join("-" * (w + 2) for w in widths)]
435 |     lines += [fmt(c) for c in cells]
    -     lines.append("(veto: lift < %.2f, E >= %.0f; bridge = the tag naming "
    -                  "the overlap, informational only)" % (lift_th, E_MIN))
436 +     lines.append(
437 +         "(veto: lift < %.2f, E >= %.0f; bridge = the tag naming "
438 +         "the overlap, informational only)" % (lift_th, E_MIN)
439 +     )
440 |     return "\n".join(lines)
    |

unformatted: File would be reformatted
  --> nodes/lib/utils.py:47:42
   |
46 |             node = match.group(1)
   -             message = message[match.end():]
47 +             message = message[match.end() :]
48 |         else:
--------------------------------------------------------------------------------
64 |         # INFO/WARNING/ERROR are the levels actually used; 7 fits the longest.
   -         handler.setFormatter(_NodeTagFormatter(
   -             "%(asctime)s | %(levelname)-7s | %(message)s",
   -             datefmt="%Y-%m-%d %H:%M:%S",
   -         ))
65 +         handler.setFormatter(
66 +             _NodeTagFormatter(
67 +                 "%(asctime)s | %(levelname)-7s | %(message)s",
68 +                 datefmt="%Y-%m-%d %H:%M:%S",
69 +             )
70 +         )
71 |         logger.addHandler(handler)
--------------------------------------------------------------------------------
87 |         except Exception:
   -             get_logger().error("unexpected error in '%s'", func.__name__,
   -                                exc_info=True)
88 +             get_logger().error("unexpected error in '%s'", func.__name__, exc_info=True)
89 |             raise
   |

unformatted: File would be reformatted
    --> nodes/tags.py:28:31
     |
27   | from .lib.tag_veto import filter_by_veto, veto_available
     - from .lib.tag_suggest import (suggest_tags, suggest_available,
     -                               DEFAULT_MOMENTUM,
     -                               DEFAULT_REPETITION_PENALTY)
28   + from .lib.tag_suggest import (
29   +     suggest_tags,
30   +     suggest_available,
31   +     DEFAULT_MOMENTUM,
32   +     DEFAULT_REPETITION_PENALTY,
33   + )
34   |
--------------------------------------------------------------------------------
90   | # vocabulary nobody should have to memorise to sort a prompt.
     - CATEGORY_ORDER = "characters, body, expressions, pose, clothes, objects, background, compositions"
91   + CATEGORY_ORDER = (
92   +     "characters, body, expressions, pose, clothes, objects, background, compositions"
93   + )
94   |
--------------------------------------------------------------------------------
139  |     """
     -     counts = {name: (counts.get(name + _SHARE_SUFFIX, default)
     -                      if counts.get(name, True) else 0.0)
     -               for name, default in CATEGORY_DEFAULTS.items()}
140  +     counts = {
141  +         name: (
142  +             counts.get(name + _SHARE_SUFFIX, default) if counts.get(name, True) else 0.0
143  +         )
144  +         for name, default in CATEGORY_DEFAULTS.items()
145  +     }
146  |     if all(v == 0.0 for v in counts.values()):
--------------------------------------------------------------------------------
194  |         for form in _WILDCARD_FORMS:
     -             blacklist_tags = blacklist_tags.replace(form.format(key=key),
     -                                                     joined)
195  +             blacklist_tags = blacklist_tags.replace(form.format(key=key), joined)
196  |     patterns = []
--------------------------------------------------------------------------------
226  |                     if first_row and i == 0:
     -                         row = f"│ {label:<{col_width1-2}} │ {wline.ljust(col_width2)} │"
227  +                         row = (
228  +                             f"│ {label:<{col_width1 - 2}} │ {wline.ljust(col_width2)} │"
229  +                         )
230  |                     else:
     -                         row = f"│ {'':<{col_width1-2}} │ {wline.ljust(col_width2)} │"
231  +                         row = f"│ {'':<{col_width1 - 2}} │ {wline.ljust(col_width2)} │"
232  |                     out.append(row)
--------------------------------------------------------------------------------
242  |         # NOTE. 2: space for tags
     -         top = f"┌{'─'*col_width1}┬{'─'*(2+col_width2)}┐"
     -         mid = f"├{'─'*col_width1}┼{'─'*(2+col_width2)}┤"
     -         bot = f"└{'─'*col_width1}┴{'─'*(2+col_width2)}┘"
243  +         top = f"┌{'─' * col_width1}┬{'─' * (2 + col_width2)}┐"
244  +         mid = f"├{'─' * col_width1}┼{'─' * (2 + col_width2)}┤"
245  +         bot = f"└{'─' * col_width1}┴{'─' * (2 + col_width2)}┘"
246  |
--------------------------------------------------------------------------------
408  |
     -
409  |     @classmethod
--------------------------------------------------------------------------------
461  |     """Filter blacklisted tags from a prompt. Regular expression is used to match tags."""
     -
462  |
--------------------------------------------------------------------------------
483  |         fixed_tags_set = {
     -             
     -                 cls.normalize_tag(t)
     -                 for t in re.split(r"BREAK|,", fixed_tags)
     -                 if t.strip()
     -             
484  +             cls.normalize_tag(t) for t in re.split(r"BREAK|,", fixed_tags) if t.strip()
485  |         }
--------------------------------------------------------------------------------
544  |
     -
545  |     @classmethod
--------------------------------------------------------------------------------
561  |         fixed_tags_set = {
     -             
     -                 cls.normalize_tag(t)
     -                 for t in re.split(r"BREAK|,", fixed_tags)
     -                 if t.strip()
     -             
562  +             cls.normalize_tag(t) for t in re.split(r"BREAK|,", fixed_tags) if t.strip()
563  |         }
--------------------------------------------------------------------------------
615  |
     -
616  |     @classmethod
--------------------------------------------------------------------------------
933  |         "required": {
     -             "text": ("STRING", {
     -                 "forceInput": True,
     -                 "tooltip": "The prompt to extend. Its tags condition every "
     -                            "pick and are never filtered themselves. Tags "
     -                            "outside the 20,811-tag vocabulary are ignored "
     -                            "silently -- Danbooru spells a bar "
     -                            "'bar_(place)', not 'bar'.",
     -             }),
     -             "n": ("INT", {
     -                 "default": 15, "min": 0, "max": 100,
     -                 "tooltip": "How many tags to add, counted after "
     -                            "post-processing. 0 = auto: the length is drawn "
     -                            "from the corpus and generation also stops early "
     -                            "once nothing is clearly better than chance.",
     -             }),
934  +             "text": (
935  +                 "STRING",
936  +                 {
937  +                     "forceInput": True,
938  +                     "tooltip": "The prompt to extend. Its tags condition every "
939  +                     "pick and are never filtered themselves. Tags "
940  +                     "outside the 20,811-tag vocabulary are ignored "
941  +                     "silently -- Danbooru spells a bar "
942  +                     "'bar_(place)', not 'bar'.",
943  +                 },
944  +             ),
945  +             "n": (
946  +                 "INT",
947  +                 {
948  +                     "default": 15,
949  +                     "min": 0,
950  +                     "max": 100,
951  +                     "tooltip": "How many tags to add, counted after "
952  +                     "post-processing. 0 = auto: the length is drawn "
953  +                     "from the corpus and generation also stops early "
954  +                     "once nothing is clearly better than chance.",
955  +                 },
956  +             ),
957  |             **{
958  |                 key: widget
959  |                 for name, share in CATEGORY_DEFAULTS.items()
960  |                 for key, widget in (
     -                     (name, ("BOOLEAN", {
     -                         "default": True,
     -                         "tooltip": "Allow %s tags at all. Switching it off "
     -                                    "hands its share to the categories still "
     -                                    "on rather than shrinking the output."
     -                                    % name,
     -                     })),
     -                     (name + _SHARE_SUFFIX, ("FLOAT", {
     -                         "default": share, "min": CATEGORY_UNCAPPED,
     -                         "max": 1.0, "step": 0.05,
     -                         "tooltip": "How much of the output %s may take, "
     -                                    "relative to the other categories that "
     -                                    "are on: with only pose 0.2 and "
     -                                    "expressions 0.1, ten tags come back 7 "
     -                                    "and 3. -1 = allowed with no share of "
     -                                    "its own." % name,
     -                     })),
961  +                     (
962  +                         name,
963  +                         (
964  +                             "BOOLEAN",
965  +                             {
966  +                                 "default": True,
967  +                                 "tooltip": "Allow %s tags at all. Switching it off "
968  +                                 "hands its share to the categories still "
969  +                                 "on rather than shrinking the output." % name,
970  +                             },
971  +                         ),
972  +                     ),
973  +                     (
974  +                         name + _SHARE_SUFFIX,
975  +                         (
976  +                             "FLOAT",
977  +                             {
978  +                                 "default": share,
979  +                                 "min": CATEGORY_UNCAPPED,
980  +                                 "max": 1.0,
981  +                                 "step": 0.05,
982  +                                 "tooltip": "How much of the output %s may take, "
983  +                                 "relative to the other categories that "
984  +                                 "are on: with only pose 0.2 and "
985  +                                 "expressions 0.1, ten tags come back 7 "
986  +                                 "and 3. -1 = allowed with no share of "
987  +                                 "its own." % name,
988  +                             },
989  +                         ),
990  +                     ),
991  |                 )
992  |             },
     -             "lift_threshold": ("FLOAT", {
     -                 "default": 0.1, "min": 0.0, "max": 0.5, "step": 0.01,
     -                 "tooltip": "Veto strength. A candidate is banned when the "
     -                            "corpus expected it alongside a prompt tag often "
     -                            "enough (>= 15 posts) and it still came in below "
     -                            "this fraction of chance. Raise it when the "
     -                            "output contradicts the prompt in ways the data "
     -                            "merely discourages; 0.1 only catches pairs that "
     -                            "essentially never co-occur.",
     -             }),
     -             "momentum": ("FLOAT", {
     -                 "default": DEFAULT_MOMENTUM, "min": 0.0, "max": 1.0,
     -                 "step": 0.05,
     -                 "tooltip": "How much each generated tag conditions the ones "
     -                            "after it. 0 = every tag answers to the prompt "
     -                            "alone and they have nothing to do with each "
     -                            "other. 1 = a pick counts as much as a prompt "
     -                            "tag, so the output reads as one scene but can "
     -                            "wander off into its own subject.",
     -             }),
     -             "repetition_penalty": ("FLOAT", {
     -                 "default": DEFAULT_REPETITION_PENALTY,
     -                 "min": 1.0, "max": 10.0, "step": 0.1,
     -                 "tooltip": "Divide a tag's odds by this for every tag "
     -                            "already in the prompt that varies along the "
     -                            "same axis -- the same last word ('<colour> "
     -                            "skin'), or the same half of a linking word "
     -                            "('hands on own face' / 'hands on own head'). "
     -                            "2.0 halves them each time, so a second needs "
     -                            "twice the evidence the first did and a third "
     -                            "needs four times; 1.0 turns it off. Counters "
     -                            "momentum, which pulls hardest along the axis "
     -                            "it just moved on. Exact repeats are blocked "
     -                            "outright and are not what this controls.",
     -             }),
     -             "rating": (list(RATINGS) + ["all", "random"], {
     -                 "default": "all",
     -                 "tooltip": "Explicitness ceiling, on both halves of the "
     -                            "statistic: the co-occurrence tables come from "
     -                            "the matching corpus slice, and tags rated above "
     -                            "the request are masked. It is a ceiling, not a "
     -                            "target, so a named rating also gets a nudge "
     -                            "toward itself -- 'explicit' would otherwise "
     -                            "merely permit rather than lean. 'all' caps and "
     -                            "favours nothing, leaving the prompt to decide: "
     -                            "a nude prompt draws explicit tags, a school "
     -                            "uniform one draws none. 'random' picks one of "
     -                            "the four from the seed instead, each equally "
     -                            "likely -- a capped draw every time, but a "
     -                            "different cap on the next seed.",
     -             }),
     -             "temperature": ("FLOAT", {
     -                 "default": 1.0, "min": 0.0, "max": 5.0, "step": 0.05,
     -                 "tooltip": "Sampling randomness. 0 = always take the best "
     -                            "candidate, which makes the seed irrelevant and "
     -                            "every run identical. Higher spreads the picks "
     -                            "over weaker candidates.",
     -             }),
     -             "top_k": ("INT", {
     -                 "default": 0, "min": 0, "max": 500,
     -                 "tooltip": "Sample from this many best candidates per step. "
     -                            "0 = no limit. Ignored at temperature 0.",
     -             }),
     -             "top_p": ("FLOAT", {
     -                 "default": 0.95, "min": 0.0, "max": 1.0, "step": 0.01,
     -                 "tooltip": "Keep the best candidates adding up to this much "
     -                            "probability. 1.0 = no limit. Watch out for 0, "
     -                            "which leaves exactly one candidate and turns "
     -                            "sampling back into greedy picking.",
     -             }),
     -             "min_p": ("FLOAT", {
     -                 "default": 0.05, "min": 0.0, "max": 1.0, "step": 0.01,
     -                 "tooltip": "Drop candidates below this fraction of the best "
     -                            "candidate's probability. 0 = off.",
     -             }),
     -             "min_count": ("INT", {
     -                 "default": 100, "min": 100, "max": 1000000, "step": 100,
     -                 "tooltip": "Ignore tags with fewer than this many posts in "
     -                            "the requested rating tier. The default is the "
     -                            "vocabulary floor, i.e. no filtering. Raise it "
     -                            "when a prompt keeps surfacing tags too obscure "
     -                            "for your model to have learned.",
     -             }),
993  +             "lift_threshold": (
994  +                 "FLOAT",
995  +                 {
996  +                     "default": 0.1,
997  +                     "min": 0.0,
998  +                     "max": 0.5,
999  +                     "step": 0.01,
1000 +                     "tooltip": "Veto strength. A candidate is banned when the "
1001 +                     "corpus expected it alongside a prompt tag often "
1002 +                     "enough (>= 15 posts) and it still came in below "
1003 +                     "this fraction of chance. Raise it when the "
1004 +                     "output contradicts the prompt in ways the data "
1005 +                     "merely discourages; 0.1 only catches pairs that "
1006 +                     "essentially never co-occur.",
1007 +                 },
1008 +             ),
1009 +             "momentum": (
1010 +                 "FLOAT",
1011 +                 {
1012 +                     "default": DEFAULT_MOMENTUM,
1013 +                     "min": 0.0,
1014 +                     "max": 1.0,
1015 +                     "step": 0.05,
1016 +                     "tooltip": "How much each generated tag conditions the ones "
1017 +                     "after it. 0 = every tag answers to the prompt "
1018 +                     "alone and they have nothing to do with each "
1019 +                     "other. 1 = a pick counts as much as a prompt "
1020 +                     "tag, so the output reads as one scene but can "
1021 +                     "wander off into its own subject.",
1022 +                 },
1023 +             ),
1024 +             "repetition_penalty": (
1025 +                 "FLOAT",
1026 +                 {
1027 +                     "default": DEFAULT_REPETITION_PENALTY,
1028 +                     "min": 1.0,
1029 +                     "max": 10.0,
1030 +                     "step": 0.1,
1031 +                     "tooltip": "Divide a tag's odds by this for every tag "
1032 +                     "already in the prompt that varies along the "
1033 +                     "same axis -- the same last word ('<colour> "
1034 +                     "skin'), or the same half of a linking word "
1035 +                     "('hands on own face' / 'hands on own head'). "
1036 +                     "2.0 halves them each time, so a second needs "
1037 +                     "twice the evidence the first did and a third "
1038 +                     "needs four times; 1.0 turns it off. Counters "
1039 +                     "momentum, which pulls hardest along the axis "
1040 +                     "it just moved on. Exact repeats are blocked "
1041 +                     "outright and are not what this controls.",
1042 +                 },
1043 +             ),
1044 +             "rating": (
1045 +                 list(RATINGS) + ["all", "random"],
1046 +                 {
1047 +                     "default": "all",
1048 +                     "tooltip": "Explicitness ceiling, on both halves of the "
1049 +                     "statistic: the co-occurrence tables come from "
1050 +                     "the matching corpus slice, and tags rated above "
1051 +                     "the request are masked. It is a ceiling, not a "
1052 +                     "target, so a named rating also gets a nudge "
1053 +                     "toward itself -- 'explicit' would otherwise "
1054 +                     "merely permit rather than lean. 'all' caps and "
1055 +                     "favours nothing, leaving the prompt to decide: "
1056 +                     "a nude prompt draws explicit tags, a school "
1057 +                     "uniform one draws none. 'random' picks one of "
1058 +                     "the four from the seed instead, each equally "
1059 +                     "likely -- a capped draw every time, but a "
1060 +                     "different cap on the next seed.",
1061 +                 },
1062 +             ),
1063 +             "temperature": (
1064 +                 "FLOAT",
1065 +                 {
1066 +                     "default": 1.0,
1067 +                     "min": 0.0,
1068 +                     "max": 5.0,
1069 +                     "step": 0.05,
1070 +                     "tooltip": "Sampling randomness. 0 = always take the best "
1071 +                     "candidate, which makes the seed irrelevant and "
1072 +                     "every run identical. Higher spreads the picks "
1073 +                     "over weaker candidates.",
1074 +                 },
1075 +             ),
1076 +             "top_k": (
1077 +                 "INT",
1078 +                 {
1079 +                     "default": 0,
1080 +                     "min": 0,
1081 +                     "max": 500,
1082 +                     "tooltip": "Sample from this many best candidates per step. "
1083 +                     "0 = no limit. Ignored at temperature 0.",
1084 +                 },
1085 +             ),
1086 +             "top_p": (
1087 +                 "FLOAT",
1088 +                 {
1089 +                     "default": 0.95,
1090 +                     "min": 0.0,
1091 +                     "max": 1.0,
1092 +                     "step": 0.01,
1093 +                     "tooltip": "Keep the best candidates adding up to this much "
1094 +                     "probability. 1.0 = no limit. Watch out for 0, "
1095 +                     "which leaves exactly one candidate and turns "
1096 +                     "sampling back into greedy picking.",
1097 +                 },
1098 +             ),
1099 +             "min_p": (
1100 +                 "FLOAT",
1101 +                 {
1102 +                     "default": 0.05,
1103 +                     "min": 0.0,
1104 +                     "max": 1.0,
1105 +                     "step": 0.01,
1106 +                     "tooltip": "Drop candidates below this fraction of the best "
1107 +                     "candidate's probability. 0 = off.",
1108 +                 },
1109 +             ),
1110 +             "min_count": (
1111 +                 "INT",
1112 +                 {
1113 +                     "default": 100,
1114 +                     "min": 100,
1115 +                     "max": 1000000,
1116 +                     "step": 100,
1117 +                     "tooltip": "Ignore tags with fewer than this many posts in "
1118 +                     "the requested rating tier. The default is the "
1119 +                     "vocabulary floor, i.e. no filtering. Raise it "
1120 +                     "when a prompt keeps surfacing tags too obscure "
1121 +                     "for your model to have learned.",
1122 +                 },
1123 +             ),
1124 |         },
1125 |         "optional": {
     -             "replace_underscores": ("BOOLEAN", {
     -                 "default": True,
     -                 "tooltip": "Write tags as 'blue eyes' rather than "
     -                            "'blue_eyes'.",
     -             }),
     -             "filter_tags": ("BOOLEAN", {
     -                 "default": True,
     -                 "tooltip": "Drop duplicates and blacklisted tags from the "
     -                            "finished prompt.",
     -             }),
     -             "filter_subtags": ("BOOLEAN", {
     -                 "default": True,
     -                 "tooltip": "Drop tags another tag already implies, keeping "
     -                            "'white dog' over 'dog'. It can eat a pick the "
     -                            "sampler just made, which is why the node asks "
     -                            "for replacements until n survive.",
     -             }),
     -             "filter_copyright": ("BOOLEAN", {
     -                 "default": True,
     -                 "tooltip": "Drop candidate tags owned by one character or "
     -                            "one franchise -- a tag whose posts mostly carry "
     -                            "the same character (crescent hat ornament) or "
     -                            "the same copyright (mini hakkero). Keeps a "
     -                            "library from turning into Patchouli's library. "
     -                            "Tags you typed yourself are never dropped.",
     -             }),
     -             "order_tags": ("BOOLEAN", {
     -                 "default": True,
     -                 "tooltip": "Return the added tags grouped by kind -- "
     -                            "subject, body, expressions, pose, clothes, "
     -                            "scene -- so the same settings put the same "
     -                            "kinds of tag in the same place. Off keeps the "
     -                            "order they were drawn. The input prompt is "
     -                            "never reordered.",
     -             }),
     -             "blacklist": ("STRING", {
     -                 "default": "", "multiline": False,
     -                 "tooltip": "Regex matched against each candidate tag in "
     -                            "spaced form, case-insensitively: 'hair|eyes' "
     -                            "drops every hair and eye tag. It filters "
     -                            "candidates rather than results, so n tags still "
     -                            "come back. Use '|', not commas.",
     -             }),
1126 +             "replace_underscores": (
1127 +                 "BOOLEAN",
1128 +                 {
1129 +                     "default": True,
1130 +                     "tooltip": "Write tags as 'blue eyes' rather than 'blue_eyes'.",
1131 +                 },
1132 +             ),
1133 +             "filter_tags": (
1134 +                 "BOOLEAN",
1135 +                 {
1136 +                     "default": True,
1137 +                     "tooltip": "Drop duplicates and blacklisted tags from the "
1138 +                     "finished prompt.",
1139 +                 },
1140 +             ),
1141 +             "filter_subtags": (
1142 +                 "BOOLEAN",
1143 +                 {
1144 +                     "default": True,
1145 +                     "tooltip": "Drop tags another tag already implies, keeping "
1146 +                     "'white dog' over 'dog'. It can eat a pick the "
1147 +                     "sampler just made, which is why the node asks "
1148 +                     "for replacements until n survive.",
1149 +                 },
1150 +             ),
1151 +             "filter_copyright": (
1152 +                 "BOOLEAN",
1153 +                 {
1154 +                     "default": True,
1155 +                     "tooltip": "Drop candidate tags owned by one character or "
1156 +                     "one franchise -- a tag whose posts mostly carry "
1157 +                     "the same character (crescent hat ornament) or "
1158 +                     "the same copyright (mini hakkero). Keeps a "
1159 +                     "library from turning into Patchouli's library. "
1160 +                     "Tags you typed yourself are never dropped.",
1161 +                 },
1162 +             ),
1163 +             "order_tags": (
1164 +                 "BOOLEAN",
1165 +                 {
1166 +                     "default": True,
1167 +                     "tooltip": "Return the added tags grouped by kind -- "
1168 +                     "subject, body, expressions, pose, clothes, "
1169 +                     "scene -- so the same settings put the same "
1170 +                     "kinds of tag in the same place. Off keeps the "
1171 +                     "order they were drawn. The input prompt is "
1172 +                     "never reordered.",
1173 +                 },
1174 +             ),
1175 +             "blacklist": (
1176 +                 "STRING",
1177 +                 {
1178 +                     "default": "",
1179 +                     "multiline": False,
1180 +                     "tooltip": "Regex matched against each candidate tag in "
1181 +                     "spaced form, case-insensitively: 'hair|eyes' "
1182 +                     "drops every hair and eye tag. It filters "
1183 +                     "candidates rather than results, so n tags still "
1184 +                     "come back. Use '|', not commas.",
1185 +                 },
1186 +             ),
1187 |             "seed": (
1188 |                 "INT",
     -                 {"default": 0, "min": 0, "max": 0xFFFFFFFFFFFFFFFF,
     -                  "control_after_generate": True,
     -                  "tooltip": "Reproducibility. The same seed and settings "
     -                             "always give the same tags -- unless "
     -                             "temperature is 0, where the seed does nothing "
     -                             "at all."},
1189 +                 {
1190 +                     "default": 0,
1191 +                     "min": 0,
1192 +                     "max": 0xFFFFFFFFFFFFFFFF,
1193 +                     "control_after_generate": True,
1194 +                     "tooltip": "Reproducibility. The same seed and settings "
1195 +                     "always give the same tags -- unless "
1196 +                     "temperature is 0, where the seed does nothing "
1197 +                     "at all.",
1198 +                 },
1199 |             ),
--------------------------------------------------------------------------------
1215 |     @classmethod
     -     def _postprocess(cls, prompt, text, blacklist, replace_underscores,
     -                      filter_tags, filter_subtags):
1216 +     def _postprocess(
1217 +         cls, prompt, text, blacklist, replace_underscores, filter_tags, filter_subtags
1218 +     ):
1219 |         """Run the ProcessTags pipeline over a prompt.
--------------------------------------------------------------------------------
1254 |             generated = draw(asked if wanted else n)
     -             processed = process(f"{base.strip().rstrip(',')}, "
     -                                 + ", ".join(_escape_brackets(t)
     -                                             for t in generated))
1255 +             processed = process(
1256 +                 f"{base.strip().rstrip(',')}, "
1257 +                 + ", ".join(_escape_brackets(t) for t in generated)
1258 +             )
1259 |             survived = [t for t in _split_tags(processed) if t not in seen]
--------------------------------------------------------------------------------
1269 |             # was filtered and the sampler is the one falling short.
     -             asked = min(-(-asked * wanted // max(len(survived), 1))
     -                         + attempt + 1,
     -                         cls._MAX_ASKED_FACTOR * wanted + 16)
1270 +             asked = min(
1271 +                 -(-asked * wanted // max(len(survived), 1)) + attempt + 1,
1272 +                 cls._MAX_ASKED_FACTOR * wanted + 16,
1273 +             )
1274 |         if wanted and len(kept) < wanted:
1275 |             logger.warning(
1276 |                 "[TagsGenerator] only %d of %d tags after %d rounds -- lower "
1277 |                 "lift_threshold or min_count, or relax blacklist and "
     -                 "categories", len(kept), wanted, cls._MAX_ROUNDS,
1278 +                 "categories",
1279 +                 len(kept),
1280 +                 wanted,
1281 +                 cls._MAX_ROUNDS,
1282 |             )
--------------------------------------------------------------------------------
1321 |         momentum, repetition_penalty = _legacy_knobs(
     -             categories, momentum, repetition_penalty)
1322 +             categories, momentum, repetition_penalty
1323 +         )
1324 |         spec = _categories_spec(categories)
1325 |
1326 |         def process(prompt):
     -             return cls._postprocess(prompt, text, blacklist,
     -                                     replace_underscores, filter_tags,
     -                                     filter_subtags)
1327 +             return cls._postprocess(
1328 +                 prompt,
1329 +                 text,
1330 +                 blacklist,
1331 +                 replace_underscores,
1332 +                 filter_tags,
1333 +                 filter_subtags,
1334 +             )
1335 |
--------------------------------------------------------------------------------
1355 |             return suggest_tags(
     -                 text, n=m, min_count=min_count, temperature=temperature,
     -                 top_k=top_k, top_p=top_p, min_p=min_p, seed=seed,
     -                 rating=rating, categories=spec, blacklist=blacklist_rx,
1356 +                 text,
1357 +                 n=m,
1358 +                 min_count=min_count,
1359 +                 temperature=temperature,
1360 +                 top_k=top_k,
1361 +                 top_p=top_p,
1362 +                 min_p=min_p,
1363 +                 seed=seed,
1364 +                 rating=rating,
1365 +                 categories=spec,
1366 +                 blacklist=blacklist_rx,
1367 |                 lift_th=lift_threshold,
--------------------------------------------------------------------------------
1379 |             return (base,)
     -         kept = _sort_by_category(kept, CATEGORY_ORDER if order_tags else "",
     -                                  lambda t: (t,))
1380 +         kept = _sort_by_category(
1381 +             kept, CATEGORY_ORDER if order_tags else "", lambda t: (t,)
1382 +         )
1383 |         return (", ".join(base_tags + kept),)
--------------------------------------------------------------------------------
1408 |         momentum, repetition_penalty = _legacy_knobs(
     -             categories, momentum, repetition_penalty)
     -         return (text, n, lift_threshold, rating, temperature, top_k, top_p,
     -                 min_p, seed, min_count, blacklist, replace_underscores,
     -                 filter_tags, filter_subtags, filter_copyright, momentum,
     -                 repetition_penalty, order_tags,
     -                 tuple(sorted(categories.items())))
1409 +             categories, momentum, repetition_penalty
1410 +         )
1411 +         return (
1412 +             text,
1413 +             n,
1414 +             lift_threshold,
1415 +             rating,
1416 +             temperature,
1417 +             top_k,
1418 +             top_p,
1419 +             min_p,
1420 +             seed,
1421 +             min_count,
1422 +             blacklist,
1423 +             replace_underscores,
1424 +             filter_tags,
1425 +             filter_subtags,
1426 +             filter_copyright,
1427 +             momentum,
1428 +             repetition_penalty,
1429 +             order_tags,
1430 +             tuple(sorted(categories.items())),
1431 +         )
1432 |
--------------------------------------------------------------------------------
1513 |     COLORS = (
     -         "black", "white", "aqua", "beige", "blue", "brown", "green", "grey",
     -         "lavender", "maroon", "pink", "purple", "red", "silver", "violet",
     -         "yellow", "multicolored",
1514 +         "black",
1515 +         "white",
1516 +         "aqua",
1517 +         "beige",
1518 +         "blue",
1519 +         "brown",
1520 +         "green",
1521 +         "grey",
1522 +         "lavender",
1523 +         "maroon",
1524 +         "pink",
1525 +         "purple",
1526 +         "red",
1527 +         "silver",
1528 +         "violet",
1529 +         "yellow",
1530 +         "multicolored",
1531 |     )
--------------------------------------------------------------------------------
1632 |
     -         for group in cls._order_groups(cls._group(tags),
     -                                CATEGORY_ORDER if order_tags else ""):
1633 +         for group in cls._order_groups(
1634 +             cls._group(tags), CATEGORY_ORDER if order_tags else ""
1635 +         ):
1636 |             lines.append(cls._cap_group(group, cap) if cap > 0 else group)
--------------------------------------------------------------------------------
1648 |     ) -> tuple:
     -         return (text, special_first, cap, prefix_tags, special_pattern,
     -                 order_tags)
     -
     -
1649 +         return (text, special_first, cap, prefix_tags, special_pattern, order_tags)
     |

13 files would be reformatted, 6 files already formatted
```

### 수정 후
```
All checks passed!
19 files already formatted
```

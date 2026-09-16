"""Tag -> category mapping data.

Sources: Danbooru wiki tag groups (tag_group:attire, posture, face_tags,
hair, hair_styles, hair_color, locations), fetched 2026-07-20.
Edit the lists below to customize. Tags use spaces (not underscores);
matching is case/underscore-insensitive.
"""

COLORS = [
    "white", "black", "red", "blue", "pink", "purple", "green",
    "yellow", "brown", "grey", "orange", "aqua",
]

# ---------------------------------------------------------------------------
# Clothes subcategories
# ---------------------------------------------------------------------------

CLOTHES_HEADWEAR = [
    "hat", "balaclava", "coif", "crown", "diadem", "headdress", "maid headdress",
    "headscarf", "hijab", "tiara", "veil", "wimple", "beret", "baseball cap",
    "witch hat", "santa hat", "top hat", "mini top hat", "beanie", "sun hat",
    "straw hat", "peaked cap", "garrison cap", "cabbie hat", "bucket hat",
    "fedora", "nurse cap", "chef hat", "party hat", "sailor hat", "cowboy hat",
    "hard hat", "mob cap", "nightcap", "pirate hat", "police hat", "shako cap",
    "tokin hat", "animal hat", "fur hat", "flat cap", "boater hat",
    "pillbox hat", "tricorne", "bicorne", "deerstalker", "sombrero", "ushanka",
    "visor cap", "helmet", "winged helmet", "pith helmet", "motorcycle helmet",
]

CLOTHES_TOP = [
    "shirt", "blouse", "frilled shirt", "sleeveless shirt", "collared shirt",
    "dress shirt", "off-shoulder shirt", "striped shirt", "t-shirt",
    "compression shirt", "bustier", "crop top", "camisole", "cardigan",
    "cardigan vest", "corset", "sweater", "turtleneck", "turtleneck sweater",
    "sleeveless turtleneck", "ribbed sweater", "aran sweater", "sweater vest",
    "tank top", "tube top", "bandeau", "underbust", "vest", "waistcoat",
    "hoodie", "halterneck", "criss-cross halter", "stringer", "nightgown",
]

CLOTHES_BOTTOM = [
    "skirt", "pants", "shorts", "bloomers", "buruma", "chaps", "kilt",
    "bell-bottoms", "capri pants", "detached pants", "jeans", "cutoff jeans",
    "lowleg pants", "yoga pants", "pelvic curtain", "petticoat", "sarong",
    "bike shorts", "denim shorts", "dolphin shorts", "gym shorts",
    "lowleg shorts", "micro shorts", "pleated shorts", "short shorts",
    "bubble skirt", "cargo skirt", "high-waist skirt", "long skirt",
    "lowleg skirt", "microskirt", "miniskirt", "overall skirt", "overskirt",
    "plaid skirt", "pleated skirt", "suspender skirt", "tutu", "sweatpants",
    "hakama", "hakama skirt", "hakama pants",
]

CLOTHES_FULL = [
    # dresses
    "dress", "sweater dress", "sundress", "pinafore dress", "wedding dress",
    "china dress", "sailor dress", "armored dress", "frilled dress",
    "off-shoulder dress", "strapless dress", "long dress", "short dress",
    "collared dress",
    # swimwear / bodywear
    "swimsuit", "one-piece swimsuit", "bikini", "string bikini", "micro bikini",
    "lowleg bikini", "thong bikini", "sports bikini", "leaf bikini",
    "side-tie bikini bottom", "venus bikini", "tankini",
    "competition swimsuit", "school swimsuit", "slingshot swimsuit",
    "swim briefs", "jammers", "legskin", "rash guard", "bikini armor",
    "leotard", "strapless leotard", "see-through leotard", "playboy bunny",
    "bodysuit", "bodystocking", "jumpsuit", "short jumpsuit", "romper",
    "unitard", "overalls", "wetsuit", "springsuit", "diving suit", "bikesuit",
    "racing suit", "mecha pilot suit", "plugsuit", "hazmat suit", "g-suit",
    # traditional
    "kimono", "yukata", "furisode", "uchikake", "layered kimono",
    "short kimono", "hanbok", "ao dai", "hanfu", "changpao", "longpao",
    "dirndl", "deel", "thobe", "robe", "bathrobe", "open robe", "tunic",
    "cassock", "loincloth", "harem outfit",
    # uniforms / outfits
    "school uniform", "serafuku", "gakuran", "meiji schoolgirl uniform",
    "gym uniform", "military uniform", "band uniform", "track suit",
    "pajamas", "maid", "miko", "nontraditional miko", "nun", "waitress",
    "cheerleader", "santa costume", "superhero costume", "ghost costume",
    "animal costume", "kigurumi", "costume", "cosplay",
    "suit", "business suit", "pant suit", "skirt suit", "tuxedo",
    "formal clothes", "armor",
]

CLOTHES_OUTERWEAR = [
    "coat", "jacket", "duffel coat", "fur coat", "fur-trimmed coat",
    "long coat", "overcoat", "peacoat", "raincoat", "yellow raincoat",
    "see-through raincoat", "trench coat", "winter coat", "blazer",
    "cropped jacket", "letterman jacket", "safari jacket", "suit jacket",
    "sukajan", "tailcoat", "poncho", "cape", "capelet", "cloak", "side cape",
    "shawl", "stole", "surcoat", "tabard", "haori", "happi", "hanten",
    "shrug", "scapular",
]

CLOTHES_FOOTWEAR = [
    "shoes", "boots", "ankle boots", "armored boots", "cowboy boots",
    "high heel boots", "knee boots", "lace-up boots", "rubber boots",
    "thigh boots", "work boots", "platform boots", "pointy boots",
    "open-toe boots", "winged boots", "sneakers", "high tops", "converse",
    "dress shoes", "loafers", "oxfords", "saddle shoes", "flats",
    "high heels", "pumps", "stiletto heels", "wedge heels", "platform heels",
    "mary janes", "platform footwear", "platform shoes", "platform sandals",
    "sandals", "cross-laced sandals", "flip-flops", "gladiator sandals",
    "geta", "okobo", "sports sandals", "waraji", "zouri", "monk shoes",
    "open-toe shoes", "pointy shoes", "slippers", "animal slippers",
    "ballet slippers", "crocs", "uwabaki", "winged sandals", "winged shoes",
    "winged slippers", "mules",
]

CLOTHES_LEGWEAR = [
    "thighhighs", "kneehighs", "over-kneehighs", "pantyhose",
    "thighband pantyhose", "leggings", "leg warmers", "socks", "ankle socks",
    "bobby socks", "loose socks", "tabi", "toe socks", "tube socks",
    "fishnets", "fishnet pantyhose", "fishnet thighhighs", "bare legs",
]

CLOTHES_UNDERWEAR = [
    "underwear", "bra", "panties", "lingerie", "babydoll", "negligee",
    "boxers", "briefs", "boxer briefs", "sports bra", "strapless bra",
    "garter belt", "fundoshi", "sarashi", "chest sarashi", "underwear only",
]

# expanded with COLORS at import time (see bottom):
_COLOR_EXPAND = {
    "top": ["shirt", "sweater", "vest", "hoodie", "tank top", "crop top"],
    "bottom": ["skirt", "pants", "shorts"],
    "full": ["dress", "bikini", "swimsuit", "one-piece swimsuit", "leotard",
             "bodysuit", "kimono"],
    "outerwear": ["jacket", "coat", "cape"],
    "footwear": ["footwear", "boots", "shoes", "high heels", "sandals"],
    "legwear": ["thighhighs", "pantyhose", "socks", "kneehighs", "legwear"],
    "underwear": ["panties", "bra"],
    "headwear": ["headwear", "hat", "beret", "cap"],
}

# ---------------------------------------------------------------------------
# Other categories
# ---------------------------------------------------------------------------

POSE = [
    "standing", "sitting", "kneeling", "on one knee", "lying", "on back",
    "on side", "on stomach", "reclining", "squatting", "crouching",
    "all fours", "crawling", "walking", "running", "jumping", "hopping",
    "pouncing", "midair", "falling", "floating", "flying", "straddling",
    "thigh straddling", "upright straddle", "seiza", "wariza", "yokozuwari",
    "indian style", "lotus position", "butterfly sitting", "fetal position",
    "figure four sitting", "standing on one leg", "leaning forward",
    "leaning back", "bent over", "arched back", "top-down bottom-up",
    "upside-down", "handstand", "headstand", "stretching", "fighting stance",
    "battoujutsu stance", "hugging own legs", "knees to chest", "prostration",
    "cowering", "balancing", "sitting on lap", "sitting on person",
    "spread eagle position", "yoga", "chest stand", "faceplant",
]

EXPRESSION = [
    "smile", "grin", "evil smile", "evil grin", "light smile", "sad smile",
    "seductive smile", "crazy smile", "forced smile", "smirk", "smug",
    "doyagao", "happy", "sad", "angry", "annoyed", "frown", "pout",
    "serious", "expressionless", "surprised", "scared", "worried", "nervous",
    "embarrassed", "flustered", "confused", "bored", "sleepy", "determined",
    "thinking", "pensive", "disgust", "disdain", "despair", "depressed",
    "excited", "shy", "envy", "grimace", "scowl", "glaring", "screaming",
    "sobbing", "crying", "tears", "drunk", "crazy", "clenched teeth",
    "panicking", "horrified", "lonely", "unamused", "exhausted", "frustrated",
    "gloom (expression)", "kubrick stare", "staring", "wince", "sulking",
]

HAIR_LENGTH = [
    "bald", "bald female", "very short hair", "short hair", "medium hair",
    "long hair", "very long hair", "absurdly long hair", "big hair",
]

HAIR_STYLE = [
    "bob cut", "inverted bob", "bowl cut", "pixie cut", "buzz cut",
    "crew cut", "undercut", "flattop", "wolf cut", "hime cut",
    "jellyfish cut", "mullet", "braid", "braids", "braided bangs",
    "front braid", "side braid", "crown braid", "single braid", "twin braids",
    "low twin braids", "multiple braids", "rope braid", "french braid",
    "cornrows", "dreadlocks", "box braids", "braided ponytail", "ponytail",
    "folded ponytail", "front ponytail", "high ponytail", "low ponytail",
    "short ponytail", "side ponytail", "high side ponytail",
    "low side ponytail", "split ponytail", "topknot", "twintails",
    "low twintails", "short twintails", "uneven twintails", "tri tails",
    "quad tails", "one side up", "two side up", "half updo", "hair bun",
    "single hair bun", "double bun", "braided bun", "cone hair bun",
    "donut hair bun", "heart hair bun", "hair rings", "single hair ring",
    "drill hair", "twin drills", "single drill", "ringlets", "afro",
    "huge afro", "pompadour", "mohawk", "quiff", "beehive hairdo",
    "curly hair", "wavy hair", "straight hair", "messy hair", "spiked hair",
    "flipped hair", "hair flaps", "fluffy hair", "low-tied long hair",
    "multi-tied hair", "chonmage", "hair down", "hair up",
]

HAIR_COLOR = (
    ["%s hair" % c for c in COLORS if c != "yellow"]
    + ["blonde hair", "light blue hair", "light brown hair", "dark blue hair",
       "platinum blonde hair", "multicolored hair", "gradient hair",
       "streaked hair", "two-tone hair", "colored inner hair",
       "split-color hair", "rainbow hair", "colored tips"]
)

EYE_COLOR = (
    ["%s eyes" % c for c in COLORS]
    + ["yellow eyes", "amber eyes", "light blue eyes", "dark blue eyes",
       "heterochromia", "multicolored eyes"]
)

BACKGROUND = [
    "indoors", "outdoors",
    # simple backgrounds
    "simple background", "two-tone background", "gradient background",
    "multicolored background", "starry background", "checkered background",
    "striped background", "polka dot background", "floral background",
    "sparkle background", "abstract background",
    # rooms / buildings
    "bedroom", "bathroom", "bathtub", "classroom", "clubroom", "kitchen",
    "library", "living room", "dining room", "office", "cubicle", "infirmary",
    "cafeteria", "changing room", "locker room", "fitting room", "fitness gym",
    "school gym", "laboratory", "stage", "storage room", "closet", "dungeon",
    "prison cell", "ballroom", "courtroom", "workshop", "hotel room",
    "messy room", "otaku room", "cafe", "restaurant", "bar", "izakaya",
    "tavern", "casino", "nightclub", "church", "cathedral", "mosque",
    "shrine", "temple", "pagoda", "synagogue", "castle", "hospital", "school",
    "school entrance", "rooftop", "ruins", "sewer", "hallway", "apartment",
    "house", "hotel", "hut", "shack", "barn", "greenhouse", "conservatory",
    "garage", "gas station", "factory", "warehouse", "refinery",
    "power plant", "construction site", "military base", "bunker", "arcade",
    "aquarium", "zoo", "museum", "art gallery", "planetarium", "observatory",
    "stadium", "arena", "theater", "movie theater", "amphitheater",
    "bowling alley", "skating rink", "mall", "supermarket",
    "convenience store", "bookstore", "bakery", "flower shop", "pharmacy",
    "salon", "market", "market stall", "amusement park", "ferris wheel",
    "carousel", "roller coaster", "onsen", "graveyard", "skyscraper",
    "lighthouse", "windmill", "treehouse", "train station", "airport",
    "hangar", "control tower", "prison", "tomb", "clock tower", "bell tower",
    # outdoor / nature
    "beach", "shore", "ocean", "lake", "river", "pond", "stream", "waterfall",
    "poolside", "pool", "canyon", "cave", "cliff", "desert", "oasis",
    "forest", "bamboo forest", "jungle", "meadow", "mountain", "volcano",
    "hill", "island", "floating island", "glacier", "wasteland", "savannah",
    "wetland", "nature", "park", "playground", "garden", "flower field",
    "wheat field", "rice paddy", "field", "city", "cityscape", "town",
    "village", "rural", "street", "alley", "sidewalk", "crosswalk", "road",
    "dirt road", "highway", "path", "bridge", "tunnel", "harbor", "pier",
    "dock", "jetty", "fountain", "parking lot", "seascape", "railroad tracks",
    "railroad crossing", "running track", "soccer field", "landscape",
    "space", "moon", "planet", "asteroid", "space station",
    "vehicle interior", "car interior", "bus interior", "train interior",
    "airplane interior", "cockpit", "spacecraft interior",
]

# Accessories never conflict; used only for detection / reporting.
ACCESSORIES = [
    "gloves", "elbow gloves", "fingerless gloves", "mittens", "scarf",
    "necktie", "bowtie", "choker", "collar", "necklace", "earrings",
    "bracelet", "ring", "belt", "apron", "hair bow", "hair ribbon",
    "hairband", "hair ornament", "hairclip", "hair flower", "glasses",
    "sunglasses", "mask", "eyepatch", "wrist cuffs", "detached sleeves",
    "arm warmers", "suspenders", "sash",
]

# ---------------------------------------------------------------------------
# Pattern rules: (suffix, category, subcategory)
# Applied in order to tags NOT found in explicit lists ("white frilled dress"
# still classifies as clothes/full). Suffix matches whole last word(s).
# ---------------------------------------------------------------------------

PATTERNS = [
    ("bikini", "clothes", "full"),
    ("swimsuit", "clothes", "full"),
    ("dress", "clothes", "full"),
    ("leotard", "clothes", "full"),
    ("bodysuit", "clothes", "full"),
    ("kimono", "clothes", "full"),
    ("uniform", "clothes", "full"),
    ("costume", "clothes", "full"),
    ("suit", "clothes", "full"),
    ("shirt", "clothes", "top"),
    ("sweater", "clothes", "top"),
    ("blouse", "clothes", "top"),
    ("vest", "clothes", "top"),
    ("hoodie", "clothes", "top"),
    ("skirt", "clothes", "bottom"),
    ("pants", "clothes", "bottom"),
    ("shorts", "clothes", "bottom"),
    ("jeans", "clothes", "bottom"),
    ("jacket", "clothes", "outerwear"),
    ("coat", "clothes", "outerwear"),
    ("cape", "clothes", "outerwear"),
    ("cloak", "clothes", "outerwear"),
    ("boots", "clothes", "footwear"),
    ("shoes", "clothes", "footwear"),
    ("heels", "clothes", "footwear"),
    ("sandals", "clothes", "footwear"),
    ("sneakers", "clothes", "footwear"),
    ("slippers", "clothes", "footwear"),
    ("footwear", "clothes", "footwear"),
    ("thighhighs", "clothes", "legwear"),
    ("pantyhose", "clothes", "legwear"),
    ("kneehighs", "clothes", "legwear"),
    ("socks", "clothes", "legwear"),
    ("legwear", "clothes", "legwear"),
    ("panties", "clothes", "underwear"),
    ("bra", "clothes", "underwear"),
    ("hat", "clothes", "headwear"),
    ("cap", "clothes", "headwear"),
    ("helmet", "clothes", "headwear"),
    ("headwear", "clothes", "headwear"),
    ("ponytail", "hair_style", None),
    ("twintails", "hair_style", None),
    ("braid", "hair_style", None),
    ("braids", "hair_style", None),
    ("hair bun", "hair_style", None),
    ("background", "background", None),
]

# Tags that must never match patterns (false positives).
PATTERN_EXCEPTIONS = {
    "suit jacket",       # jacket, not suit -> caught by explicit list anyway
    "swim cap",
    "kneecap", "kneecaps",
    "bracelet",
    "zebra print", "cow print",
    "closed eyes", "half-closed eyes", "empty eyes", "rolling eyes",
    "cross-eyed", "wide-eyed",
}


def _expand_colors(base_list, subcat_key):
    out = list(base_list)
    for item in _COLOR_EXPAND.get(subcat_key, []):
        for c in COLORS:
            tag = "%s %s" % (c, item)
            if tag not in out:
                out.append(tag)
    return out


CLOTHES = {
    "headwear": _expand_colors(CLOTHES_HEADWEAR, "headwear"),
    "top": _expand_colors(CLOTHES_TOP, "top"),
    "bottom": _expand_colors(CLOTHES_BOTTOM, "bottom"),
    "full": _expand_colors(CLOTHES_FULL, "full"),
    "outerwear": _expand_colors(CLOTHES_OUTERWEAR, "outerwear"),
    "footwear": _expand_colors(CLOTHES_FOOTWEAR, "footwear"),
    "legwear": _expand_colors(CLOTHES_LEGWEAR, "legwear"),
    "underwear": _expand_colors(CLOTHES_UNDERWEAR, "underwear"),
}

# Which clothes subcategories conflict with which.
CLOTHES_CONFLICTS = {
    "full": {"full", "top", "bottom", "underwear"},
    "top": {"top", "full"},
    "bottom": {"bottom", "full"},
    "underwear": {"underwear", "full"},
    "outerwear": {"outerwear"},
    "headwear": {"headwear"},
    "footwear": {"footwear"},
    "legwear": {"legwear"},
}

CATEGORIES = {
    "pose": POSE,
    "expression": EXPRESSION,
    "hair_length": HAIR_LENGTH,
    "hair_style": HAIR_STYLE,
    "hair_color": HAIR_COLOR,
    "eye_color": EYE_COLOR,
    "background": BACKGROUND,
}

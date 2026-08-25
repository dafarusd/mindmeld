"""Mind Meld knowledge base.

Every entity carries a ternary vector over ATTRIBUTES:
    YES = 1.0, NO = 0.0, MAYBE = 0.5 (genuinely ambiguous for ordinary people).

The engine uses these as ground truth for BOTH game directions, so the AI can
never contradict itself inside a round. Accuracy of this file is the product.
"""

YES, NO, MAYBE = 1.0, 0.0, 0.5

from pathlib import Path

ATTRIBUTES = [
    "alive_today",
    "is_animal",
    "is_human",
    "is_real",
    "is_fictional",
    "is_mammal",
    "is_bird",
    "is_sea_creature",
    "is_insect",
    "is_reptile",
    "can_fly",
    "can_swim",
    "lives_in_water",
    "has_fur",
    "has_wings",
    "has_tail",
    "four_legs",
    "kept_as_pet",
    "is_dangerous",
    "bigger_than_breadbox",
    "found_in_home",
    "is_electronic",
    "made_of_metal",
    "is_edible",
    "is_liquid",
    "is_round",
    "makes_music",
    "is_wearable",
    "is_vehicle",
    "is_tool",
    "is_furniture",
    "is_plant",
    "is_toy",
    "associated_with_sport",
    "is_celebrity",
    "from_screen",
    "is_historical",
    "is_female",
    "is_scientist",
    "is_artist_or_musician",
    "is_ruler_or_politician",
    "is_athlete",
    "is_sweet",
    "is_fruit_or_veg",
    "is_dairy",
    "served_cold",
    "has_superpowers",
    "is_villain",
    "from_ancient_times",
    "has_wheels",
    "two_wheeled",
    "handheld",
    "used_for_cleaning",
    "tells_time",
    "has_screen",
    "has_long_neck",
    "wears_a_costume",
    "played_with_racket",
    "is_royal",
    "is_tech_or_business",
    "is_animated",
    "is_mythological",
    "has_stripes",
    "has_spots",
    "is_black_and_white",
    "is_public_transport",
    "is_emergency",
    "is_fast_food",
    "is_classical_music",
    "fronted_a_band",
    "known_for_dance",
    "from_before_1800",
    "studied_stars",
    "studied_electricity",
    "studied_living_things",
    "uses_a_ball",
    "played_on_ice_or_snow",
    "uses_a_bat_or_stick",
    "played_by_kicking",
    "uses_weapons",
    "done_in_water",
    "sat_or_slept_on",
    "has_doors_or_drawers",
    "gives_light",
    "hangs_on_wall_or_window",
    "used_in_bathroom",
    "used_for_writing",
    "used_when_raining",
    "lives_in_a_cage",
    "has_a_trunk",
    "hops",
    "has_antlers",
    "is_pink",
    "active_at_night",
    "has_many_arms",
    "is_alcoholic",
    "is_a_hot_drink",
    "is_a_condiment",
    "contains_meat",
    "is_japanese",
    "carries_cargo",
    "runs_in_city",
    "connects_to_internet",
    "is_a_detective",
    "is_a_spy",
    "searches_for_treasure",
    "from_space_or_scifi",
    "from_wizard_world",
    "barks",
    "purrs_or_meows",
    "turns_screws",
    "is_a_grain",
    "eaten_with_hands",
    "is_australian",
    "pecks_wood",
    "common_city_bird",
    "famous_for_its_tail",
    "was_a_military_leader",
    "was_american_president",
    "civil_rights_icon",
]

ATTR_INDEX = {name: i for i, name in enumerate(ATTRIBUTES)}
NUM_ATTRS = len(ATTRIBUTES)

BASE = {name: NO for name in ATTRIBUTES}


def archetype(**kwargs):
    vec = dict(BASE)
    vec.update(kwargs)
    return vec


MAMMAL = archetype(
    alive_today=YES, is_animal=YES, is_real=YES, is_mammal=YES,
    has_fur=YES, has_tail=YES, four_legs=YES,
)
BIRD = archetype(
    alive_today=YES, is_animal=YES, is_real=YES, is_bird=YES,
    has_wings=YES, can_fly=YES, has_tail=YES,
)
SEA = archetype(
    alive_today=YES, is_animal=YES, is_real=YES, is_sea_creature=YES,
    lives_in_water=YES, can_swim=YES,
)
INSECT = archetype(
    alive_today=YES, is_animal=YES, is_real=YES, is_insect=YES,
)
REPTILE = archetype(
    alive_today=YES, is_animal=YES, is_real=YES, is_reptile=YES,
)
OBJECT = archetype(is_real=YES, found_in_home=MAYBE)
FOOD = archetype(is_real=YES, is_edible=YES, found_in_home=YES)
TOOL = archetype(is_real=YES, is_tool=YES, made_of_metal=MAYBE, found_in_home=MAYBE)
VEHICLE = archetype(is_real=YES, is_vehicle=YES, bigger_than_breadbox=YES, made_of_metal=YES)
INSTRUMENT = archetype(is_real=YES, makes_music=YES, found_in_home=MAYBE)
PERSON = archetype(alive_today=YES, is_human=YES, is_real=YES, is_celebrity=YES)
FIGURE = archetype(alive_today=NO, is_human=YES, is_real=YES, is_celebrity=YES, is_historical=YES)
CHARACTER = archetype(is_human=MAYBE, is_fictional=YES, from_screen=YES, is_celebrity=MAYBE)
PLANT = archetype(alive_today=YES, is_real=YES, is_plant=YES)
SPORT = archetype(is_real=YES, associated_with_sport=YES)


def _build():
    table: dict[str, dict] = {}

    def add(name, base, blurb, **overrides):
        vec = dict(base)
        vec.update(overrides)
        table[name] = {"name": name, "blurb": blurb, "vec": vec}

    add("dog", MAMMAL, "loyal household companion", kept_as_pet=YES, barks=YES)
    add("cat", MAMMAL, "aloof household hunter", kept_as_pet=YES, purrs_or_meows=YES)
    add("horse", MAMMAL, "ridden for work and sport", bigger_than_breadbox=YES, associated_with_sport=MAYBE)
    add("elephant", MAMMAL, "largest land animal, with a trunk", bigger_than_breadbox=YES, has_a_trunk=YES)
    add("lion", MAMMAL, "maned big cat, savanna hunter", is_dangerous=YES, bigger_than_breadbox=YES, purrs_or_meows=MAYBE)
    add("tiger", MAMMAL, "striped big cat", is_dangerous=YES, bigger_than_breadbox=YES, purrs_or_meows=MAYBE, has_stripes=YES)
    add("bear", MAMMAL, "large omnivore of the forests", is_dangerous=YES, bigger_than_breadbox=YES)
    add("wolf", MAMMAL, "pack hunter, ancestor of the dog", is_dangerous=MAYBE)
    add("fox", MAMMAL, "cunning red-coated omnivore")
    add("rabbit", MAMMAL, "long-eared burrower", kept_as_pet=MAYBE, hops=YES)
    add("dolphin", MAMMAL, "playful marine mammal", can_swim=YES, lives_in_water=YES, four_legs=NO, has_fur=NO)
    add("whale", MAMMAL, "largest animal on Earth", can_swim=YES, lives_in_water=YES, four_legs=NO, has_fur=NO, bigger_than_breadbox=YES)
    add("bat", MAMMAL, "the only flying mammal", can_fly=YES, has_wings=YES, four_legs=NO, active_at_night=YES)
    add("monkey", MAMMAL, "tree-swinging primate", four_legs=NO)
    add("giraffe", MAMMAL, "tallest land animal", bigger_than_breadbox=YES, has_long_neck=YES)
    add("mouse", MAMMAL, "small rodent", kept_as_pet=MAYBE)
    add("cow", MAMMAL, "farm animal that gives milk", bigger_than_breadbox=YES)
    add("pig", MAMMAL, "pink farm animal", is_pink=MAYBE)
    add("penguin", BIRD, "flightless bird that waddles and swims", can_fly=NO, can_swim=YES)
    add("eagle", BIRD, "bird of prey with keen eyes")
    add("owl", BIRD, "nocturnal hunter with a rotating head", active_at_night=YES)
    add("parrot", BIRD, "talking tropical bird", kept_as_pet=YES, lives_in_a_cage=MAYBE)
    add("chicken", BIRD, "farm bird that lays eggs", can_fly=MAYBE, is_edible=YES, contains_meat=YES)
    add("duck", BIRD, "water bird that quacks", can_swim=YES)
    add("flamingo", BIRD, "pink bird that stands on one leg", is_pink=YES)
    add("shark", SEA, "apex predator of the ocean", is_dangerous=YES, bigger_than_breadbox=YES)
    add("octopus", SEA, "eight-armed master of disguise", has_many_arms=YES)
    add("goldfish", SEA, "classic bowl pet", kept_as_pet=YES, lives_in_a_cage=MAYBE)
    add("jellyfish", SEA, "stinging drifter", is_dangerous=MAYBE)
    add("crab", SEA, "sideways-walking shellfish", is_edible=YES)
    add("seahorse", SEA, "horse-headed fish, males give birth")
    add("snake", REPTILE, "legless slitherer, some venomous", is_dangerous=MAYBE, has_tail=YES, kept_as_pet=MAYBE)
    add("crocodile", REPTILE, "armored ambush predator", is_dangerous=YES, can_swim=YES, four_legs=YES, has_tail=YES, bigger_than_breadbox=YES)
    add("turtle", REPTILE, "shelled slowpoke", can_swim=YES, four_legs=YES, kept_as_pet=MAYBE)
    add("spider", INSECT, "eight-legged web weaver", is_dangerous=MAYBE, found_in_home=YES)
    add("ant", INSECT, "colony worker that lifts many times its weight", found_in_home=MAYBE)
    add("bee", INSECT, "pollinator that makes honey", can_fly=YES, has_wings=YES, is_dangerous=MAYBE)
    add("butterfly", INSECT, "colorful winged metamorph", can_fly=YES, has_wings=YES)

    add("chair", OBJECT, "you sit on it", is_furniture=YES, found_in_home=YES, bigger_than_breadbox=MAYBE, sat_or_slept_on=YES)
    add("table", OBJECT, "flat surface on legs", is_furniture=YES, found_in_home=YES, bigger_than_breadbox=YES)
    add("bed", OBJECT, "you sleep on it", is_furniture=YES, found_in_home=YES, bigger_than_breadbox=YES, sat_or_slept_on=YES)
    add("sofa", OBJECT, "living-room lounging", is_furniture=YES, found_in_home=YES, bigger_than_breadbox=YES, sat_or_slept_on=YES)
    add("lamp", OBJECT, "lights a room", found_in_home=YES, is_electronic=YES, gives_light=YES)
    add("television", OBJECT, "moving pictures in the living room", found_in_home=YES, is_electronic=YES, bigger_than_breadbox=YES, has_screen=YES)
    add("refrigerator", OBJECT, "keeps food cold", found_in_home=YES, is_electronic=YES, bigger_than_breadbox=YES, made_of_metal=YES, has_doors_or_drawers=YES)
    add("microwave", OBJECT, "heats food in minutes", found_in_home=YES, is_electronic=YES, made_of_metal=MAYBE)
    add("mirror", OBJECT, "shows your reflection", found_in_home=YES, handheld=MAYBE, hangs_on_wall_or_window=YES)
    add("toothbrush", OBJECT, "cleans teeth", found_in_home=YES, handheld=YES, used_for_cleaning=YES, used_in_bathroom=YES)
    add("clock", OBJECT, "tells the time", found_in_home=YES, is_round=MAYBE, tells_time=YES)
    add("smartphone", OBJECT, "pocket computer", found_in_home=YES, is_electronic=YES, handheld=YES, has_screen=YES, connects_to_internet=YES)
    add("laptop", OBJECT, "portable computer", found_in_home=YES, is_electronic=YES, has_screen=YES, connects_to_internet=YES)
    add("washing machine", OBJECT, "cleans clothes", found_in_home=YES, is_electronic=YES, bigger_than_breadbox=YES, used_for_cleaning=YES)
    add("vacuum cleaner", OBJECT, "sucks up dust", found_in_home=YES, is_electronic=YES, used_for_cleaning=YES)
    add("umbrella", OBJECT, "keeps rain off", found_in_home=YES, handheld=YES, used_when_raining=YES)
    add("candle", OBJECT, "wax light source", found_in_home=YES, gives_light=YES, handheld=YES)
    add("camera", OBJECT, "captures photographs", is_electronic=MAYBE, found_in_home=MAYBE, handheld=YES)
    add("book", OBJECT, "bound pages of words", found_in_home=YES, handheld=YES)
    add("pencil", OBJECT, "writes in graphite", found_in_home=YES, handheld=YES, used_for_writing=YES)
    add("key", OBJECT, "opens locks", made_of_metal=YES, found_in_home=YES, handheld=YES)
    add("coin", OBJECT, "metal money", made_of_metal=YES, is_round=YES, handheld=YES)
    add("backpack", OBJECT, "carried on your back", is_wearable=YES, found_in_home=YES)
    add("glasses", OBJECT, "worn on the face to see better", is_wearable=YES, handheld=YES)
    add("watch", OBJECT, "time on your wrist", is_wearable=YES, tells_time=YES, handheld=YES)
    add("shoe", OBJECT, "worn on feet", is_wearable=YES, found_in_home=YES)
    add("hat", OBJECT, "worn on the head", is_wearable=YES)
    add("balloon", OBJECT, "inflated party floater", is_round=YES, is_toy=MAYBE, handheld=YES)
    add("teddy bear", OBJECT, "stuffed comfort toy", is_toy=YES, has_fur=MAYBE, found_in_home=YES, handheld=YES)
    add("dice", OBJECT, "rolled for random numbers", is_toy=MAYBE, handheld=YES)

    add("hammer", TOOL, "drives nails", made_of_metal=YES, handheld=YES)
    add("screwdriver", TOOL, "turns screws", made_of_metal=YES, handheld=YES, turns_screws=YES)
    add("saw", TOOL, "cuts wood", made_of_metal=YES, is_dangerous=MAYBE, handheld=YES)
    add("drill", TOOL, "bores holes", is_electronic=MAYBE, made_of_metal=MAYBE, handheld=YES)
    add("wrench", TOOL, "turns nuts and bolts", made_of_metal=YES, handheld=YES)

    add("car", VEHICLE, "four-wheeled road transport", four_legs=NO, has_wheels=YES)
    add("bicycle", VEHICLE, "pedal-powered two-wheeler", associated_with_sport=MAYBE, has_wheels=YES, two_wheeled=YES, made_of_metal=MAYBE)
    add("motorcycle", VEHICLE, "motorized two-wheeler", has_wheels=YES, two_wheeled=YES)
    add("airplane", VEHICLE, "flies passengers through the sky", can_fly=YES, has_wings=YES)
    add("boat", VEHICLE, "floats on water", can_swim=NO, lives_in_water=NO)
    add("train", VEHICLE, "runs on rails", has_wheels=NO)
    add("helicopter", VEHICLE, "hovers with rotors", can_fly=YES)
    add("bus", VEHICLE, "carries many passengers", has_wheels=YES, is_public_transport=YES, runs_in_city=YES)
    add("skateboard", VEHICLE, "four small wheels and a deck", is_toy=MAYBE, associated_with_sport=YES, bigger_than_breadbox=NO, made_of_metal=NO, has_wheels=YES, handheld=MAYBE)
    add("rocket", VEHICLE, "carries payloads to space", can_fly=YES)

    add("guitar", INSTRUMENT, "six-stringed strummer")
    add("piano", INSTRUMENT, "eighty-eight keys", bigger_than_breadbox=YES)
    add("drum", INSTRUMENT, "hit it to play it", is_round=YES)
    add("violin", INSTRUMENT, "bowed strings")
    add("trumpet", INSTRUMENT, "brass and bright", made_of_metal=YES)
    add("flute", INSTRUMENT, "breath across a hole", made_of_metal=MAYBE)

    add("pizza", FOOD, "round flatbread with toppings", is_round=YES, eaten_with_hands=MAYBE)
    add("apple", FOOD, "crunchy round fruit", is_round=YES, is_plant=MAYBE, is_fruit_or_veg=YES)
    add("banana", FOOD, "yellow curved fruit", is_fruit_or_veg=YES, is_sweet=YES)
    add("bread", FOOD, "baked staple", is_a_grain=MAYBE)
    add("cheese", FOOD, "aged dairy", is_dairy=YES)
    add("egg", FOOD, "oval protein", is_round=MAYBE)
    add("coffee", FOOD, "dark morning brew", is_liquid=YES, is_a_hot_drink=YES)
    add("milk", FOOD, "white dairy drink", is_liquid=YES, is_dairy=YES)
    add("chocolate", FOOD, "sweet cocoa treat", is_sweet=YES)
    add("hamburger", FOOD, "patty in a bun", is_round=MAYBE, contains_meat=YES, is_fast_food=YES, eaten_with_hands=YES)
    add("carrot", FOOD, "orange root vegetable", is_plant=MAYBE, is_fruit_or_veg=YES)
    add("ice cream", FOOD, "frozen sweet dessert", is_sweet=YES, served_cold=YES, is_dairy=MAYBE)

    add("soccer", SPORT, "eleven-a-side, feet only", uses_a_ball=YES, played_by_kicking=YES)
    add("basketball", SPORT, "hoops and dribbling", uses_a_ball=YES)
    add("tennis", SPORT, "rackets and a net", played_with_racket=YES, uses_a_ball=YES)
    add("chess", SPORT, "sixty-four squares of war", found_in_home=YES)
    add("swimming", SPORT, "racing through water", can_swim=YES, done_in_water=YES)
    add("boxing", SPORT, "gloved combat in a ring", is_dangerous=MAYBE)

    add("tree", PLANT, "woody giant with leaves", bigger_than_breadbox=YES)
    add("flower", PLANT, "colorful blooming plant")
    add("cactus", PLANT, "spiky desert survivor", found_in_home=MAYBE, kept_as_pet=NO)
    add("grass", PLANT, "green ground cover")

    add("Albert Einstein", FIGURE, "physicist behind relativity, wild hair", is_scientist=YES)
    add("Leonardo da Vinci", FIGURE, "Renaissance painter and inventor", is_artist_or_musician=YES, from_before_1800=YES)
    add("Cleopatra", FIGURE, "last pharaoh of Egypt", is_female=YES, is_ruler_or_politician=YES, from_ancient_times=YES, from_before_1800=YES, is_royal=YES)
    add("Napoleon", FIGURE, "French emperor, famously short of temper", is_ruler_or_politician=YES, was_a_military_leader=YES)
    add("William Shakespeare", FIGURE, "playwright of the Globe", is_artist_or_musician=YES, from_before_1800=YES)
    add("Mozart", FIGURE, "child-prodigy composer", makes_music=YES, is_artist_or_musician=YES, is_classical_music=YES, from_before_1800=YES)
    add("Marie Curie", FIGURE, "two-time Nobel scientist", is_scientist=YES, is_female=YES)
    add("Abraham Lincoln", FIGURE, "rail-splitter president with a tall hat", is_ruler_or_politician=YES, was_american_president=YES)
    add("Elvis Presley", FIGURE, "the King of Rock and Roll", makes_music=YES, is_artist_or_musician=YES)
    add("Beyoncé", PERSON, "queen of pop performance", makes_music=YES, is_artist_or_musician=YES, is_female=YES)
    add("Taylor Swift", PERSON, "record-breaking singer-songwriter", makes_music=YES, is_artist_or_musician=YES, is_female=YES)
    add("Michael Jordan", PERSON, "basketball legend who flew", associated_with_sport=YES, is_athlete=YES, uses_a_ball=YES)
    add("Cristiano Ronaldo", PERSON, "goal-scoring football icon", associated_with_sport=YES, is_athlete=YES, uses_a_ball=YES, played_by_kicking=YES)
    add("Serena Williams", PERSON, "grand-slam tennis champion", associated_with_sport=YES, is_athlete=YES, is_female=YES)
    add("Muhammad Ali", FIGURE, "floated like a butterfly, stung like a bee", associated_with_sport=YES, is_athlete=YES)

    add("Sherlock Holmes", CHARACTER, "consulting detective of Baker Street", is_human=YES, wears_a_costume=NO, is_a_detective=YES)
    add("Dracula", CHARACTER, "Transylvanian vampire count", is_human=MAYBE, is_dangerous=YES, is_villain=YES, has_superpowers=MAYBE)
    add("Superman", CHARACTER, "last son of Krypton", can_fly=YES, is_human=NO, has_superpowers=YES, wears_a_costume=YES, from_space_or_scifi=YES)
    add("Mickey Mouse", CHARACTER, "whistling cartoon mouse", is_animal=YES, is_human=NO, is_mammal=YES, four_legs=NO)
    add("Mario", CHARACTER, "plumber who jumps on turtles", is_human=YES, wears_a_costume=YES)
    add("Harry Potter", CHARACTER, "the boy who lived", is_human=YES, has_superpowers=YES, from_wizard_world=YES)
    add("Darth Vader", CHARACTER, "masked Sith lord, father issues", is_human=MAYBE, is_dangerous=YES, is_villain=YES, has_superpowers=YES, wears_a_costume=YES, from_space_or_scifi=YES)
    add("Spider-Man", CHARACTER, "web-slinging wall-crawler", is_human=YES, has_superpowers=YES, wears_a_costume=YES)
    add("Batman", CHARACTER, "caped detective of Gotham", is_human=YES, wears_a_costume=YES, is_a_detective=MAYBE)
    add("Elsa", CHARACTER, "ice-powered queen who lets it go", is_human=YES, makes_music=MAYBE, is_female=YES, has_superpowers=YES)
    add("Shrek", CHARACTER, "ogre with layers", is_human=NO, bigger_than_breadbox=YES)
    add("Yoda", CHARACTER, "small green Jedi master", is_human=NO, has_superpowers=YES, from_space_or_scifi=YES)
    add("Pikachu", CHARACTER, "electric mouse companion", is_animal=YES, is_human=NO, has_superpowers=YES)
    add("Santa Claus", CHARACTER, "gift-bringer of the North Pole", is_human=YES, from_screen=MAYBE, alive_today=NO, has_superpowers=MAYBE)
    add("Zeus", CHARACTER, "thunderbolt-throwing king of the gods", is_human=MAYBE, from_screen=MAYBE, is_dangerous=YES, has_superpowers=YES, from_ancient_times=YES, is_mythological=YES, is_royal=YES)

    add("kangaroo", MAMMAL, "bounding marsupial with a pouch", bigger_than_breadbox=YES, hops=YES, is_australian=YES)
    add("koala", MAMMAL, "eucalyptus-munching tree hugger", is_australian=YES)
    add("panda", MAMMAL, "bamboo-eating bear in monochrome", is_black_and_white=YES, bigger_than_breadbox=YES)
    add("zebra", MAMMAL, "striped savanna grazer", has_stripes=YES, bigger_than_breadbox=YES)
    add("deer", MAMMAL, "antlered forest grazer", bigger_than_breadbox=YES, has_antlers=YES)
    add("squirrel", MAMMAL, "nut-hoarding tree acrobat")
    add("hedgehog", MAMMAL, "spiny garden ball", has_spots=NO)
    add("otter", MAMMAL, "playful river swimmer", can_swim=YES)
    add("raccoon", MAMMAL, "masked trash bandit")
    add("hamster", MAMMAL, "wheel-running pocket pet", kept_as_pet=YES, lives_in_a_cage=YES)
    add("guinea pig", MAMMAL, "squeaking cage companion", kept_as_pet=YES, lives_in_a_cage=YES)
    add("camel", MAMMAL, "desert ship with humps", bigger_than_breadbox=YES)
    add("gorilla", MAMMAL, "powerful gentle ape", four_legs=NO, is_dangerous=MAYBE, bigger_than_breadbox=YES)
    add("polar bear", MAMMAL, "white giant of the ice", is_dangerous=YES, bigger_than_breadbox=YES, can_swim=YES)

    add("crow", BIRD, "black bird of omens and puzzles")
    add("swan", BIRD, "elegant white glider", can_swim=YES, bigger_than_breadbox=MAYBE)
    add("peacock", BIRD, "tail-feather showoff", famous_for_its_tail=YES)
    add("pigeon", BIRD, "city square regular", common_city_bird=YES)
    add("turkey", BIRD, "holiday centerpiece bird", can_fly=MAYBE, is_edible=YES)
    add("ostrich", BIRD, "largest bird, cannot fly", can_fly=NO, bigger_than_breadbox=YES)
    add("woodpecker", BIRD, "tree-drumming bird", pecks_wood=YES)

    add("squid", SEA, "ten-armed ink sprayer", has_many_arms=YES)
    add("starfish", SEA, "five-armed tidepool star", can_swim=NO)
    add("eel", SEA, "slippery snake of the sea")
    add("lobster", SEA, "clawed delicacy", is_edible=YES)
    add("seal", MAMMAL, "barking ocean acrobat", can_swim=YES, lives_in_water=MAYBE, four_legs=NO)
    add("walrus", MAMMAL, "tusked arctic lounger", can_swim=YES, lives_in_water=MAYBE, four_legs=NO, bigger_than_breadbox=YES)
    add("stingray", SEA, "flat glider with a sting", is_dangerous=MAYBE)
    add("clownfish", SEA, "orange anemone dweller", kept_as_pet=MAYBE)
    add("shrimp", SEA, "small curled crustacean", is_edible=YES)

    add("lizard", REPTILE, "sun-basking skitterer", kept_as_pet=MAYBE, four_legs=YES, has_tail=YES)
    add("frog", REPTILE, "leaping pond singer", is_reptile=NO, can_swim=YES, lives_in_water=MAYBE, four_legs=YES, has_tail=NO, hops=YES)
    add("scorpion", INSECT, "armored stinger of the desert", is_insect=NO, is_dangerous=YES)
    add("mosquito", INSECT, "whining blood-sipper", can_fly=YES, has_wings=YES, is_dangerous=MAYBE)
    add("ladybug", INSECT, "spotted red garden beetle", can_fly=YES, has_wings=YES, has_spots=YES)
    add("worm", INSECT, "soil-tunneling wriggler", is_insect=NO)
    add("snail", INSECT, "shell-carrying slowpoke", is_insect=NO)

    add("pillow", OBJECT, "head's bedtime landing pad", found_in_home=YES, bigger_than_breadbox=MAYBE, sat_or_slept_on=MAYBE)
    add("blanket", OBJECT, "bedtime warmth layer", found_in_home=YES)
    add("toilet", OBJECT, "porcelain necessity", found_in_home=YES, bigger_than_breadbox=YES, used_in_bathroom=YES)
    add("sink", OBJECT, "basin with taps", found_in_home=YES, made_of_metal=MAYBE, used_in_bathroom=YES)
    add("oven", OBJECT, "bakes and roasts", found_in_home=YES, is_electronic=MAYBE, made_of_metal=YES, bigger_than_breadbox=YES)
    add("dishwasher", OBJECT, "cleans the dishes", found_in_home=YES, is_electronic=YES, bigger_than_breadbox=YES, used_for_cleaning=YES)
    add("kettle", OBJECT, "boils water for tea", found_in_home=YES, is_electronic=MAYBE, made_of_metal=MAYBE, handheld=MAYBE)
    add("toaster", OBJECT, "browns the bread", found_in_home=YES, is_electronic=YES, made_of_metal=YES, handheld=MAYBE)
    add("electric fan", OBJECT, "spins air at you", found_in_home=YES, is_electronic=YES)
    add("heater", OBJECT, "warms the room", found_in_home=YES, is_electronic=YES)
    add("speaker", OBJECT, "plays sound aloud", found_in_home=YES, is_electronic=YES, makes_music=YES)
    add("headphones", OBJECT, "private sound on your ears", is_electronic=YES, is_wearable=YES, makes_music=YES)
    add("wifi router", OBJECT, "blinks the internet into the air", found_in_home=YES, is_electronic=YES, connects_to_internet=YES)
    add("printer", OBJECT, "puts pixels on paper", found_in_home=YES, is_electronic=YES, bigger_than_breadbox=MAYBE)
    add("desk", OBJECT, "work surface of the office", is_furniture=YES, found_in_home=YES, bigger_than_breadbox=YES)
    add("wardrobe", OBJECT, "clothes storage cabinet", is_furniture=YES, found_in_home=YES, bigger_than_breadbox=YES, has_doors_or_drawers=YES)
    add("carpet", OBJECT, "soft floor covering", found_in_home=YES, bigger_than_breadbox=YES)
    add("curtains", OBJECT, "window dressings", found_in_home=YES, hangs_on_wall_or_window=YES)
    add("trash can", OBJECT, "holds the garbage", found_in_home=YES, bigger_than_breadbox=MAYBE)
    add("broom", OBJECT, "sweeps the floor", found_in_home=YES, used_for_cleaning=YES, handheld=YES)
    add("mop", OBJECT, "wet-cleans the floor", found_in_home=YES, used_for_cleaning=YES, handheld=YES)
    add("sponge", OBJECT, "squishy scrubber", found_in_home=YES, used_for_cleaning=YES, handheld=YES)
    add("soap", OBJECT, "lathering cleanser", found_in_home=YES, used_for_cleaning=YES, handheld=YES, used_in_bathroom=YES)
    add("shampoo", OBJECT, "hair-washing potion", found_in_home=YES, used_for_cleaning=YES, is_liquid=YES, handheld=YES, used_in_bathroom=YES)
    add("towel", OBJECT, "dries you off", found_in_home=YES, handheld=MAYBE, used_in_bathroom=YES)
    add("hairbrush", OBJECT, "tames the mane", found_in_home=YES, handheld=YES)

    add("axe", TOOL, "chops wood", made_of_metal=YES, is_dangerous=YES, handheld=YES)
    add("pliers", TOOL, "grips and twists", made_of_metal=YES, handheld=YES)
    add("scissors", TOOL, "two blades that snip", made_of_metal=YES, handheld=YES, is_dangerous=MAYBE, found_in_home=YES)
    add("ladder", TOOL, "climbs you to height", bigger_than_breadbox=YES, made_of_metal=MAYBE)

    add("truck", VEHICLE, "hauls heavy loads", has_wheels=YES, carries_cargo=YES)
    add("ambulance", VEHICLE, "rushes patients to hospital", has_wheels=YES, is_emergency=YES)
    add("police car", VEHICLE, "flashing lights of the law", has_wheels=YES, is_emergency=YES)
    add("fire truck", VEHICLE, "red rescuer with a ladder", has_wheels=YES, is_emergency=YES)
    add("taxi", VEHICLE, "metered ride for hire", has_wheels=YES, is_public_transport=MAYBE, runs_in_city=YES)
    add("submarine", VEHICLE, "underwater vessel", has_wheels=NO, made_of_metal=YES)
    add("hot air balloon", VEHICLE, "floats on hot air", can_fly=YES, has_wheels=NO, made_of_metal=NO, is_round=MAYBE)
    add("scooter", VEHICLE, "stand-up two-wheeler", has_wheels=YES, two_wheeled=YES, bigger_than_breadbox=NO)
    add("tram", VEHICLE, "street-running rail car", has_wheels=NO, is_public_transport=YES, runs_in_city=YES)
    add("golf cart", VEHICLE, "putters around the course", has_wheels=YES, associated_with_sport=YES)

    add("saxophone", INSTRUMENT, "smooth brass honker", made_of_metal=YES)
    add("cello", INSTRUMENT, "deep-voiced string giant", bigger_than_breadbox=MAYBE)
    add("harp", INSTRUMENT, "angelic plucked strings", bigger_than_breadbox=YES)
    add("harmonica", INSTRUMENT, "pocket blues blower", handheld=YES)
    add("microphone", INSTRUMENT, "amplifies the voice", makes_music=MAYBE, is_electronic=YES, handheld=YES)

    add("sushi", FOOD, "Japanese rice and fish rolls", served_cold=MAYBE, is_japanese=YES)
    add("pasta", FOOD, "Italian noodles", is_a_grain=MAYBE)
    add("rice", FOOD, "tiny grains, global staple", is_a_grain=YES)
    add("steak", FOOD, "seared cut of beef", contains_meat=YES)
    add("salad", FOOD, "bowl of greens", is_fruit_or_veg=YES)
    add("soup", FOOD, "hot liquid meal", is_liquid=YES)
    add("sandwich", FOOD, "filling between bread", eaten_with_hands=YES)
    add("taco", FOOD, "folded tortilla with filling", is_fast_food=YES, eaten_with_hands=YES)
    add("burrito", FOOD, "wrapped tortilla bundle", is_fast_food=MAYBE)
    add("donut", FOOD, "fried ring of sweetness", is_sweet=YES, is_round=YES, is_fast_food=MAYBE, eaten_with_hands=YES)
    add("cake", FOOD, "celebration centerpiece", is_sweet=YES)
    add("cookie", FOOD, "small sweet baked disc", is_sweet=YES, is_round=YES, handheld=YES, eaten_with_hands=YES)
    add("candy", FOOD, "pure sugar treat", is_sweet=YES, handheld=YES)
    add("honey", FOOD, "golden bee-made syrup", is_sweet=YES, is_liquid=YES)
    add("popcorn", FOOD, "popped corn puffs")
    add("french fries", FOOD, "golden fried potato sticks", is_fast_food=YES)
    add("ketchup", FOOD, "red tomato sauce", is_liquid=YES, is_a_condiment=YES)
    add("beer", FOOD, "brewed adult drink", is_liquid=YES, is_alcoholic=YES)
    add("wine", FOOD, "fermented grape drink", is_liquid=YES, is_alcoholic=YES)
    add("tea", FOOD, "steeped leaf drink", is_liquid=YES, is_a_hot_drink=YES)
    add("orange juice", FOOD, "fresh-squeezed citrus drink", is_liquid=YES, is_sweet=YES)
    add("orange", FOOD, "citrus fruit in its own wrapper", is_round=YES, is_fruit_or_veg=YES, is_sweet=MAYBE)
    add("strawberry", FOOD, "red berry with seeds outside", is_sweet=YES, is_fruit_or_veg=YES)
    add("grapes", FOOD, "vine-grown bunch fruit", is_sweet=YES, is_fruit_or_veg=YES, is_round=YES)
    add("potato", FOOD, "earthy tuber", is_fruit_or_veg=YES)
    add("onion", FOOD, "layered tear-jerker", is_fruit_or_veg=YES, is_round=YES)
    add("tomato", FOOD, "red fruit masquerading as vegetable", is_fruit_or_veg=YES, is_round=YES)
    add("broccoli", FOOD, "tiny green tree vegetable", is_fruit_or_veg=YES)
    add("mushroom", FOOD, "umbrella of the forest floor", is_plant=NO, is_fruit_or_veg=MAYBE)

    add("rose", PLANT, "thorny symbol of love", found_in_home=MAYBE)
    add("venus flytrap", PLANT, "carnivorous snapper", found_in_home=MAYBE, is_dangerous=MAYBE)
    add("bamboo", PLANT, "giant grass pandas love", bigger_than_breadbox=YES)

    add("golf", SPORT, "eighteen holes of quiet frustration", uses_a_ball=YES)
    add("american football", SPORT, "helmets and touchdowns", uses_a_ball=YES)
    add("baseball", SPORT, "bats, balls, and nine innings", uses_a_ball=YES, uses_a_bat_or_stick=YES)
    add("ice hockey", SPORT, "sticks and pucks on ice", played_on_ice_or_snow=YES, uses_a_bat_or_stick=YES)
    add("skiing", SPORT, "downhill speed on snow", played_on_ice_or_snow=YES)
    add("surfing", SPORT, "riding ocean waves", can_swim=MAYBE, done_in_water=YES)
    add("archery", SPORT, "bows and bullseyes", is_dangerous=MAYBE, uses_weapons=YES)
    add("fencing", SPORT, "swordplay with rules", is_dangerous=MAYBE, uses_weapons=YES)
    add("gymnastics", SPORT, "flips and perfect tens")

    add("Isaac Newton", FIGURE, "gravity's apple-inspired describer", is_scientist=YES, from_before_1800=YES)
    add("Galileo", FIGURE, "telescope-pointing heretic of Pisa", is_scientist=YES, from_before_1800=YES, studied_stars=YES)
    add("Charles Darwin", FIGURE, "evolution's bearded voyager", is_scientist=YES, studied_living_things=YES)
    add("Nikola Tesla", FIGURE, "alternating-current wizard", is_scientist=YES, studied_electricity=YES)
    add("Thomas Edison", FIGURE, "light-bulb industrialist", is_scientist=MAYBE, is_tech_or_business=YES, studied_electricity=MAYBE)
    add("Beethoven", FIGURE, "deaf composer of the Ninth", makes_music=YES, is_artist_or_musician=YES, is_classical_music=YES)
    add("Vincent van Gogh", FIGURE, "starry-eared painter", is_artist_or_musician=YES)
    add("Pablo Picasso", FIGURE, "cube-smashing painter", is_artist_or_musician=YES)
    add("Frida Kahlo", FIGURE, "unibrow icon of Mexican art", is_artist_or_musician=YES, is_female=YES)
    add("Oprah Winfrey", PERSON, "talk-show empress", is_female=YES, from_screen=YES, is_tech_or_business=MAYBE)
    add("Barack Obama", PERSON, "44th US president", is_ruler_or_politician=YES, was_american_president=YES)
    add("Mahatma Gandhi", FIGURE, "nonviolent liberator of India", is_ruler_or_politician=YES, civil_rights_icon=YES)
    add("Nelson Mandela", FIGURE, "prisoner-turned-president", is_ruler_or_politician=YES, civil_rights_icon=YES)
    add("Joan of Arc", FIGURE, "maiden warrior of Orleans", is_female=YES, from_before_1800=YES)
    add("Alexander the Great", FIGURE, "Macedonian world-conqueror", is_ruler_or_politician=YES, from_ancient_times=YES, from_before_1800=YES, was_a_military_leader=YES)
    add("Julius Caesar", FIGURE, "crossed the Rubicon, beware the Ides", is_ruler_or_politician=YES, from_ancient_times=YES, from_before_1800=YES, was_a_military_leader=YES)
    add("Socrates", FIGURE, "question-asking father of philosophy", from_ancient_times=YES, from_before_1800=YES)
    add("Freddie Mercury", FIGURE, "queen's legendary frontman", makes_music=YES, is_artist_or_musician=YES, fronted_a_band=YES)
    add("Madonna", PERSON, "material girl of pop", is_female=YES, makes_music=YES, is_artist_or_musician=YES)
    add("Michael Jackson", FIGURE, "moonwalking king of pop", makes_music=YES, is_artist_or_musician=YES, known_for_dance=YES)
    add("Elon Musk", PERSON, "rockets-and-tweets billionaire", is_tech_or_business=YES)
    add("Bill Gates", PERSON, "Microsoft cofounder turned philanthropist", is_tech_or_business=YES)
    add("Steve Jobs", FIGURE, "turtlenecked Apple visionary", is_tech_or_business=YES)
    add("Usain Bolt", PERSON, "fastest human alive", associated_with_sport=YES, is_athlete=YES, uses_a_ball=NO)
    add("Tiger Woods", PERSON, "golf's tiger", associated_with_sport=YES, is_athlete=YES, uses_a_ball=YES)
    add("LeBron James", PERSON, "basketball's chosen one", associated_with_sport=YES, is_athlete=YES, uses_a_ball=YES)
    add("Lionel Messi", PERSON, "diminutive football magician", associated_with_sport=YES, is_athlete=YES, uses_a_ball=YES, played_by_kicking=YES)
    add("Simone Biles", PERSON, "gravity-defying gymnast", associated_with_sport=YES, is_athlete=YES, is_female=YES)

    add("Godzilla", CHARACTER, "king of the monsters", is_human=NO, bigger_than_breadbox=YES, is_dangerous=YES, is_reptile=MAYBE)
    add("King Kong", CHARACTER, "eighth wonder of the world", is_human=NO, bigger_than_breadbox=YES, is_dangerous=MAYBE, is_mammal=MAYBE)
    add("Frankenstein's monster", CHARACTER, "stitched-together creation", is_human=MAYBE, is_dangerous=MAYBE, bigger_than_breadbox=YES)
    add("James Bond", CHARACTER, "shaken-not-stirred secret agent", is_human=YES, is_dangerous=YES, is_a_spy=YES)
    add("Indiana Jones", CHARACTER, "whip-cracking archaeologist", is_human=YES, searches_for_treasure=YES)
    add("Luke Skywalker", CHARACTER, "farm boy turned Jedi", is_human=YES, has_superpowers=YES, from_space_or_scifi=YES)
    add("Gandalf", CHARACTER, "grey wanderer of Middle-earth", is_human=MAYBE, has_superpowers=YES, from_wizard_world=YES)
    add("Frodo", CHARACTER, "ring-bearing hobbit", is_human=NO)
    add("Gollum", CHARACTER, "precious-obsessed cave dweller", is_human=NO, is_villain=MAYBE)
    add("Dumbledore", CHARACTER, "half-moon-spectacled headmaster", is_human=YES, has_superpowers=YES, from_wizard_world=YES)
    add("Hermione Granger", CHARACTER, "brightest witch of her age", is_human=YES, is_female=YES, has_superpowers=YES, from_wizard_world=YES)
    add("Homer Simpson", CHARACTER, "donut-loving nuclear safety inspector", is_human=YES, is_animated=YES)
    add("SpongeBob", CHARACTER, "porous optimist of Bikini Bottom", is_human=NO, is_animated=YES, lives_in_water=YES, is_animal=MAYBE)
    add("Bugs Bunny", CHARACTER, "carrot-chomping wise guy", is_human=NO, is_animated=YES, is_animal=YES, is_mammal=YES)
    add("Donald Duck", CHARACTER, "sailor-suited hothead", is_human=NO, is_animated=YES, is_animal=YES, is_bird=YES)
    add("Sonic", CHARACTER, "blue hedgehog at light speed", is_human=NO, is_animal=YES, is_animated=YES, has_superpowers=YES)
    add("Link", CHARACTER, "green-tunic hero of Hyrule", is_human=YES)
    add("Princess Zelda", CHARACTER, "royal sage of Hyrule", is_human=YES, is_female=YES, is_royal=YES)
    add("Lara Croft", CHARACTER, "tomb-raiding adventurer", is_human=YES, is_female=YES, searches_for_treasure=YES)
    add("Wonder Woman", CHARACTER, "amazonian warrior princess", is_human=YES, is_female=YES, has_superpowers=YES, wears_a_costume=YES, is_royal=MAYBE)
    add("Iron Man", CHARACTER, "genius in a metal suit", is_human=YES, wears_a_costume=YES, has_superpowers=MAYBE, made_of_metal=MAYBE)
    add("Hulk", CHARACTER, "green anger-management case", is_human=MAYBE, has_superpowers=YES, bigger_than_breadbox=YES, is_dangerous=MAYBE)
    add("Thor", CHARACTER, "hammer-wielding thunder god", is_human=MAYBE, has_superpowers=YES, is_mythological=MAYBE)
    add("Joker", CHARACTER, "clown prince of crime", is_human=YES, is_villain=YES, is_dangerous=YES, wears_a_costume=YES)
    add("Maleficent", CHARACTER, "horned mistress of evil", is_female=YES, is_villain=YES, has_superpowers=YES)
    add("Cinderella", CHARACTER, "glass-slippered princess", is_human=YES, is_female=YES, is_royal=MAYBE, is_animated=MAYBE)
    add("Snow White", CHARACTER, "fairest of them all", is_human=YES, is_female=YES, is_royal=MAYBE, is_animated=MAYBE)
    add("Ariel", CHARACTER, "mermaid who traded her voice", is_human=MAYBE, is_female=YES, is_animated=MAYBE, lives_in_water=MAYBE, can_swim=YES)
    add("Moana", CHARACTER, "ocean-chosen wayfinder", is_human=YES, is_female=YES, is_animated=YES)
    add("Goku", CHARACTER, "saiyan raised on Earth", is_human=NO, has_superpowers=YES, is_animated=YES)
    add("Naruto", CHARACTER, "ninja who never gives up", is_human=YES, has_superpowers=YES, is_animated=YES)
    add("Hello Kitty", CHARACTER, "mouthless global icon cat", is_animal=YES, is_human=NO, is_animated=YES, is_mammal=YES)
    add("Barbie", CHARACTER, "fashion doll come to life", is_human=YES, is_female=YES, is_animated=MAYBE, is_toy=MAYBE)

    add("leopard", MAMMAL, "spotted big cat of the trees", is_dangerous=YES, bigger_than_breadbox=YES, has_spots=YES, purrs_or_meows=MAYBE)
    add("sloth", MAMMAL, "slowest mammal, hangs upside down", found_in_home=NO)
    add("platypus", MAMMAL, "egg-laying duck-billed oddity", is_australian=YES, can_swim=YES, four_legs=YES)
    add("hyena", MAMMAL, "laughing scavenger", is_dangerous=MAYBE)
    add("donkey", MAMMAL, "stubborn beast of burden", bigger_than_breadbox=YES)
    add("llama", MAMMAL, "fluffy spitting pack animal", bigger_than_breadbox=YES)
    add("vulture", BIRD, "circling scavenger of the sky")
    add("hummingbird", BIRD, "hovering nectar sipper", handheld=NO)
    add("toucan", BIRD, "oversized colorful bill")
    add("orca", MAMMAL, "black-and-white ocean apex hunter", is_black_and_white=YES, can_swim=YES, lives_in_water=YES, four_legs=NO, has_fur=NO, bigger_than_breadbox=YES, is_dangerous=YES)
    add("manatee", MAMMAL, "gentle sea cow", can_swim=YES, lives_in_water=YES, four_legs=NO, has_fur=NO, bigger_than_breadbox=YES)
    add("pufferfish", SEA, "inflating spiky defender", is_dangerous=MAYBE, is_round=MAYBE)
    add("dragonfly", INSECT, "helicopter of the pond", can_fly=YES, has_wings=YES)
    add("beetle", INSECT, "armored crawler")
    add("caterpillar", INSECT, "future butterfly")
    add("moth", INSECT, "night-flying dust wings", can_fly=YES, has_wings=YES, active_at_night=YES)
    add("cockroach", INSECT, "unkillable kitchen invader", found_in_home=YES)

    add("bagel", FOOD, "boiled-then-baked ring", is_round=YES, is_a_grain=YES, eaten_with_hands=YES)
    add("croissant", FOOD, "flaky crescent of butter", is_sweet=MAYBE, eaten_with_hands=YES)
    add("pancakes", FOOD, "flat griddled breakfast stack", is_round=YES, is_sweet=MAYBE)
    add("bacon", FOOD, "crispy cured strips", contains_meat=YES)
    add("sausage", FOOD, "seasoned ground-meat link", contains_meat=YES)
    add("tofu", FOOD, "soybean protein block")
    add("avocado", FOOD, "creamy green stone fruit", is_fruit_or_veg=YES)
    add("pineapple", FOOD, "spiky tropical sweetness", is_fruit_or_veg=YES, is_sweet=YES)
    add("coconut", FOOD, "hairy tropical hard shell", is_fruit_or_veg=YES, is_round=YES)
    add("lemon", FOOD, "sour yellow citrus", is_fruit_or_veg=YES, is_round=MAYBE)
    add("garlic", FOOD, "pungent vampire repellent", is_fruit_or_veg=YES)

    add("remote control", OBJECT, "couch-bound channel changer", found_in_home=YES, is_electronic=YES, handheld=YES)
    add("light bulb", OBJECT, "glass globe of light", gives_light=YES, is_electronic=MAYBE, found_in_home=YES, handheld=YES)
    add("scarf", OBJECT, "neck warmer", is_wearable=YES, found_in_home=YES)
    add("belt", OBJECT, "waist cincher", is_wearable=YES, found_in_home=YES)
    add("gloves", OBJECT, "hand warmers", is_wearable=YES, found_in_home=YES)
    add("wallet", OBJECT, "pocket money holder", handheld=YES, found_in_home=YES)
    add("sunglasses", OBJECT, "shades for bright days", is_wearable=YES, handheld=YES)
    add("helmet", OBJECT, "head protector", is_wearable=YES, associated_with_sport=MAYBE)

    add("ukulele", INSTRUMENT, "tiny four-string strummer", handheld=YES)
    add("banjo", INSTRUMENT, "twangy round-bodied picker", is_round=YES)
    add("accordion", INSTRUMENT, "squeezing bellows box", bigger_than_breadbox=MAYBE)

    add("Neil Armstrong", FIGURE, "first boot on the moon", studied_stars=MAYBE)
    add("Amelia Earhart", FIGURE, "vanished pioneer of the skies", is_female=YES)
    add("Ada Lovelace", FIGURE, "first programmer in history", is_female=YES, is_scientist=MAYBE, is_tech_or_business=MAYBE)
    add("Alan Turing", FIGURE, "codebreaker father of computing", is_scientist=YES, is_tech_or_business=MAYBE)
    add("Stephen Hawking", FIGURE, "black-hole mind in a wheelchair", is_scientist=YES, studied_stars=YES)
    add("J.K. Rowling", PERSON, "author of the boy wizard", is_female=YES, is_artist_or_musician=YES)
    add("Bob Marley", FIGURE, "reggae prophet of peace", makes_music=YES, is_artist_or_musician=YES)
    add("Lady Gaga", PERSON, "meat-dress pop avant-gardist", is_female=YES, makes_music=YES, is_artist_or_musician=YES, known_for_dance=MAYBE)

    add("Groot", CHARACTER, "three-word tree guardian", is_human=NO, is_plant=MAYBE, has_superpowers=MAYBE, from_space_or_scifi=YES)
    add("Jack Sparrow", CHARACTER, "drunken compass-spinning pirate", is_human=YES, searches_for_treasure=MAYBE)
    add("Winnie the Pooh", CHARACTER, "honey-stuffed bear of very little brain", is_animal=YES, is_human=NO, is_mammal=YES, is_animated=YES)
    add("Scooby-Doo", CHARACTER, "snack-driven mystery mutt", is_animal=YES, is_human=NO, is_mammal=YES, is_animated=YES, barks=YES, is_a_detective=MAYBE)
    add("Garfield", CHARACTER, "lasagna-loving Monday hater", is_animal=YES, is_human=NO, is_mammal=YES, is_animated=YES, purrs_or_meows=YES)
    add("Snoopy", CHARACTER, "doghouse philosopher beagle", is_animal=YES, is_human=NO, is_mammal=YES, is_animated=YES, barks=YES)
    add("Bart Simpson", CHARACTER, "el barto, underachiever and proud", is_human=YES, is_animated=YES)
    add("Peter Griffin", CHARACTER, "rhode island's roundest dad", is_human=YES, is_animated=YES)
    add("Minnie Mouse", CHARACTER, "polka-dot bow mouse", is_animal=YES, is_human=NO, is_mammal=YES, is_animated=YES, is_female=YES)
    add("Olaf", CHARACTER, "warm-hug-loving snowman", is_human=NO, is_animated=YES, served_cold=YES)
    add("Simba", CHARACTER, "the lion king himself", is_animal=YES, is_human=NO, is_mammal=YES, is_animated=YES, is_royal=YES)
    add("Nemo", CHARACTER, "lost little clownfish", is_animal=YES, is_human=NO, is_animated=YES, lives_in_water=YES, can_swim=YES)
    add("Woody", CHARACTER, "pull-string cowboy doll", is_human=YES, is_animated=YES, is_toy=YES, wears_a_costume=YES)
    add("Buzz Lightyear", CHARACTER, "to infinity and beyond", is_human=YES, is_animated=YES, is_toy=YES, wears_a_costume=YES, from_space_or_scifi=YES)

    return table


ENTITIES = _build()


def _merge_learned() -> None:
    import json

    path = Path(__file__).resolve().parent.parent / "data" / "learned.json"
    learned: dict = {}
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                learned = raw
        except (json.JSONDecodeError, OSError):
            pass
    for key in [k for k, v in ENTITIES.items() if v.get("learned") and k not in learned]:
        del ENTITIES[key]
    for key, entry in learned.items():
        if isinstance(entry, dict) and "vec" in entry and key not in ENTITIES:
            ENTITIES[key] = {"name": key, "blurb": entry.get("blurb", "learned from a challenger"), "vec": {a: entry["vec"].get(a, MAYBE) for a in ATTRIBUTES}, "learned": True}


_merge_learned()

ENTITY_NAMES = sorted(ENTITIES.keys())

ATTR_MATRIX = [tuple(ENTITIES[n]["vec"][a] for a in ATTRIBUTES) for n in ENTITY_NAMES]


def reload() -> None:
    """Re-merge learned entities and rebuild indexes (for long-lived servers)."""
    global ENTITY_NAMES, ATTR_MATRIX
    _merge_learned()
    ENTITY_NAMES = sorted(ENTITIES.keys())
    ATTR_MATRIX = [tuple(ENTITIES[n]["vec"][a] for a in ATTRIBUTES) for n in ENTITY_NAMES]

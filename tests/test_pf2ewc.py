import pf2e_wealth_calculator.pf2ewc as pf
import pytest


@pytest.mark.parametrize(
    "item_name, amount, item_info",
    [
        # General
        (
            "longsword",
            1,
            pf.ItemInfo(
                "longsword", pf.Money(gp=1), "weapons", "base weapons", 0, "common", 1
            ),
        ),
        # Multi-word item
        (
            "composite longbow",
            2,
            pf.ItemInfo(
                "composite longbow",
                pf.Money(gp=40),
                "weapons",
                "base weapons",
                0,
                "common",
                2,
            ),
        ),
        # Multi-word specific item
        (
            "storm flash",
            1,
            pf.ItemInfo(
                "storm flash",
                pf.Money(gp=4000),
                "weapons",
                "specific magic weapons",
                14,
                "common",
                1,
            ),
        ),
        # Multi-word specific item with a grade
        (
            "storm flash (greater)",
            1,
            pf.ItemInfo(
                "storm flash (greater)",
                pf.Money(gp=21000),
                "weapons",
                "specific magic weapons",
                18,
                "common",
                1,
            ),
        ),
        # Currency
        (
            "25 gp",
            1,
            pf.ItemInfo(
                "25 gp",
                pf.Money(gp=25, origin="currency"),
                "currency",
                "none",
                0,
                "common",
                0,
            ),
        ),
        (
            "12 sp",
            4,
            pf.ItemInfo(
                "12 sp",
                pf.Money(sp=48, origin="currency"),
                "currency",
                "none",
                0,
                "common",
                0,
            ),
        ),
        # Uncommon rarity
        (
            "kukri",
            1,
            pf.ItemInfo(
                "kukri", pf.Money(sp=6), "weapons", "base weapons", 0, "uncommon", "L"
            ),
        ),
        # Different category (armor)
        (
            "breastplate",
            1,
            pf.ItemInfo(
                "breastplate", pf.Money(gp=8), "armor", "base armor", 0, "common", 2
            ),
        ),
        # Different category (adventuring gear)
        (
            "compass",
            1,
            pf.ItemInfo(
                "compass", pf.Money(gp=1), "adventuring gear", "none", 0, "common", 0
            ),
        ),
        # Different category (alchemical items)
        (
            "flayleaf",
            1,
            pf.ItemInfo(
                "flayleaf",
                pf.Money(gp=1),
                "alchemical items",
                "drugs",
                0,
                "common",
                "L",
            ),
        ),
        # Different category (animals and gear)
        (
            "rabbit",
            1,
            pf.ItemInfo(
                "rabbit", pf.Money(gp=1), "animals and gear", "animals", 0, "common"
            ),
        ),
        # Different category (adjustments)
        (
            "reinforced surcoat",
            1,
            pf.ItemInfo(
                "reinforced surcoat",
                pf.Money(gp=2),
                "adjustments",
                "none",
                0,
                "uncommon",
                "L",
            ),
        ),
        # Different category (staves)
        (
            "staff of the dreamlands",
            1,
            pf.ItemInfo(
                "staff of the dreamlands",
                pf.Money(gp=250),
                "staves",
                "none",
                6,
                "uncommon",
                1,
            ),
        ),
        # Different category (shields)
        (
            "buckler",
            1,
            pf.ItemInfo(
                "buckler", pf.Money(gp=1), "shields", "base shields", 0, "common", "L"
            ),
        ),
    ],
)
def test_parse(item_name, amount, item_info):
    assert pf.parse_database(item_name, amount) == item_info


@pytest.mark.parametrize(
    "item_name, amount, category, item_info",
    [
        # Restrict armor
        (
            "chain",
            1,
            "armor",
            pf.ItemInfo("chain", pf.Money(), "error", "none", 0, "common", 0),
        ),
        (
            "chain mail",
            1,
            "armor",
            pf.ItemInfo(
                "chain mail",
                pf.Money(gp=6),
                "armor",
                "base armor",
                0,
                "common",
                2,
            ),
        ),
    ],
)
def test_parse_restricted(item_name, amount, category, item_info):
    assert pf.parse_database(item_name, amount, restrict_cat=category) == item_info


@pytest.mark.parametrize(
    "item_name, amount, item_info",
    [
        # General low-grade
        (
            "silver maul low",
            1,
            pf.ItemInfo(
                "silver maul (low-grade)",
                pf.Money(gp=40),
                "weapons",
                "base weapons",
                2,
                "common",
                2,
            ),
        ),
        # Multi-word item standard-grade
        (
            "noqual meteor hammer standard",
            1,
            pf.ItemInfo(
                "noqual meteor hammer (standard-grade)",
                pf.Money(gp=1600),
                "weapons",
                "base weapons",
                12,
                "rare",
                2,
            ),
        ),
        # Multi-word material low-grade
        (
            "cold iron naginata (low)",
            1,
            pf.ItemInfo(
                "cold iron naginata (low-grade)",
                pf.Money(gp=40),
                "weapons",
                "base weapons",
                2,
                "uncommon",
                2,
            ),
        ),
        # Multi-word item and material high-grade
        (
            "sovereign steel war lance high",
            1,
            pf.ItemInfo(
                "sovereign steel war lance (high-grade)",
                pf.Money(gp=32000),
                "weapons",
                "base weapons",
                19,
                "rare",
                2,
            ),
        ),
        # Different category (armor)
        (
            "silver breastplate low",
            1,
            pf.ItemInfo(
                "silver breastplate (low-grade)",
                pf.Money(gp=140),
                "armor",
                "base armor",
                5,
                "common",
                2,
            ),
        ),
        # Multi-word armor
        (
            "adamantine full plate (high)",
            1,
            pf.ItemInfo(
                "adamantine full plate (high-grade)",
                pf.Money(gp=32000),
                "armor",
                "base armor",
                19,
                "uncommon",
                4,
            ),
        ),
        # Precious shields
        (
            "silver shield low",
            1,
            pf.ItemInfo(
                "silver shield (low-grade)",
                pf.Money(gp=34),
                "shields",
                "base shields",
                2,
                "common",
                1,
            ),
        ),
        # Bucklers and tower shields are different from shields
        (
            "silver buckler low",
            1,
            pf.ItemInfo(
                "silver buckler (low-grade)",
                pf.Money(gp=30),
                "shields",
                "base shields",
                2,
                "common",
                "L",
            ),
        ),
        (
            "adamantine tower shield (high)",
            1,
            pf.ItemInfo(
                "adamantine tower shield (high-grade)",
                pf.Money(gp=8800),
                "shields",
                "base shields",
                16,
                "uncommon",
                4,
            ),
        ),
        # Test the only wooden precious shield
        (
            "darkwood shield standard",
            1,
            pf.ItemInfo(
                "darkwood shield (standard-grade)",
                pf.Money(gp=440),
                "shields",
                "base shields",
                8,
                "uncommon",
                1,
            ),
        ),
    ],
)
def test_parse_precious(item_name, amount, item_info):
    assert pf.parse_database(item_name, amount) == item_info


@pytest.mark.parametrize(
    "item_name, amount, item_info",
    [
        # Potency only
        (
            "+1 falchion",
            1,
            pf.ItemInfo(
                "+1 falchion",
                pf.Money(gp=38),
                "weapons",
                "base weapons",
                2,
                "common",
                2,
            ),
        ),
        # Potency and striking
        (
            "+1 striking greataxe",
            1,
            pf.ItemInfo(
                "+1 striking greataxe",
                pf.Money(gp=102),
                "weapons",
                "base weapons",
                4,
                "common",
                2,
            ),
        ),
        # Potency, striking and property
        (
            "+1 striking cunning guisarme",
            1,
            pf.ItemInfo(
                "+1 striking cunning guisarme",
                pf.Money(gp=242),
                "weapons",
                "base weapons",
                5,
                "uncommon",
                2,
            ),
        ),
        # Multi-word item
        (
            "+1 striking hand adze",
            1,
            pf.ItemInfo(
                "+1 striking hand adze",
                pf.Money(sp=5, gp=100),
                "weapons",
                "base weapons",
                4,
                "common",
                "L",
            ),
        ),
        # With precious material
        (
            "+1 striking silver kukri low",
            1,
            pf.ItemInfo(
                "+1 striking silver kukri (low-grade)",
                pf.Money(gp=140),
                "weapons",
                "base weapons",
                4,
                "uncommon",
                "L",
            ),
        ),
        # Grade
        (
            "+2 greater striking rapier",
            1,
            pf.ItemInfo(
                "+2 greater striking rapier",
                pf.Money(gp=2002),
                "weapons",
                "base weapons",
                12,
                "common",
                1,
            ),
        ),
        # Multiple grades
        (
            "+2 greater striking greater extending frost whip",
            1,
            pf.ItemInfo(
                "+2 greater striking greater extending frost whip",
                pf.Money(sp=1, gp=5500),
                "weapons",
                "base weapons",
                13,
                "common",
                1,
            ),
        ),
        # Everything everywhere all at once
        (
            "+3 major striking greater brilliant ancestral echoing major fanged sovereign steel tengu gale blade (high-grade)",
            1,
            pf.ItemInfo(
                "+3 major striking greater brilliant ancestral echoing major fanged sovereign steel tengu gale blade (high-grade)",
                pf.Money(gp=111_500),
                "weapons",
                "base weapons",
                19,
                "rare",
                "L",
            ),
        ),
        # Different category (armor)
        (
            "+1 chain mail",
            1,
            pf.ItemInfo(
                "+1 chain mail", pf.Money(gp=166), "armor", "base armor", 5, "common", 2
            ),
        ),
        # Multiple runes
        (
            "+1 resilient invisibility padded armor",
            1,
            pf.ItemInfo(
                "+1 resilient invisibility padded armor",
                pf.Money(sp=2, gp=1000),
                "armor",
                "base armor",
                8,
                "common",
                "L",
            ),
        ),
        # Precious material and grades
        (
            "+2 greater resilient bitter greater shadow djezet scale mail standard",
            1,
            pf.ItemInfo(
                "+2 greater resilient bitter greater shadow djezet scale mail (standard-grade)",
                pf.Money(gp=7085),
                "armor",
                "base armor",
                14,
                "rare",
                2,
            ),
        ),
        # Handwraps
        (
            "+1 striking frost handwraps of mighty blows",
            1,
            pf.ItemInfo(
                "+1 striking frost handwraps of mighty blows",
                pf.Money(gp=600),
                "weapons",
                "other worn items",
                8,
                "common",
                0,
            ),
        ),
    ],
)
def test_runes(item_name, amount, item_info):
    assert pf.rune_calculator(item_name, amount) == item_info


@pytest.mark.parametrize(
    "rar1, rar2, result",
    [
        ("common", "common", "common"),
        ("common", "uncommon", "uncommon"),
        ("common", "rare", "rare"),
        ("uncommon", "common", "uncommon"),
        ("uncommon", "uncommon", "uncommon"),
        ("uncommon", "rare", "rare"),
        ("rare", "common", "rare"),
        ("rare", "uncommon", "rare"),
        ("rare", "rare", "rare"),
    ],
)
def test_rarity_order(rar1, rar2, result):
    assert pf.get_higher_rarity(rar1, rar2) == result

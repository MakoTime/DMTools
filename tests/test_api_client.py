from api.client import SRDClient


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, payloads):
        self.payloads = payloads

    def get(self, url, **kwargs):
        return FakeResponse(self.payloads[url])


def test_fetch_collection_hydrates_race_traits():
    base = "https://example.test/api/2014/"
    payloads = {
        f"{base}races": {"results": [{"url": "/api/2014/races/elf"}]},
        f"{base}races/elf": {
            "name": "Elf",
            "traits": [{"name": "Darkvision", "url": "/api/2014/traits/darkvision"}],
        },
        f"{base}traits/darkvision": {
            "name": "Darkvision",
            "desc": ["You can see in darkness within 60 feet of you."],
        },
    }

    races = SRDClient(
        session=FakeSession(payloads),
        base_url=base,
    ).fetch_collection("races")

    assert races[0]["traits"] == [{
        "name": "Darkvision",
        "desc": ["You can see in darkness within 60 feet of you."],
    }]


def test_fetch_collection_hydrates_class_levels_and_features():
    base = "https://example.test/api/2014/"
    payloads = {
        f"{base}classes": {"results": [{"url": "/api/2014/classes/wizard"}]},
        f"{base}classes/wizard": {
            "name": "Wizard",
            "class_levels": "/api/2014/classes/wizard/levels",
        },
        f"{base}classes/wizard/levels": [{
            "level": 1,
            "features": [{"name": "Spellcasting", "url": "/api/2014/features/spellcasting"}],
        }],
        f"{base}features/spellcasting": {
            "name": "Spellcasting",
            "desc": ["You have learned to unravel the basic workings of magic."],
        },
    }

    classes = SRDClient(session=FakeSession(payloads), base_url=base).fetch_collection("classes")

    assert classes[0]["class_levels"][0]["features"] == [{
        "name": "Spellcasting",
        "desc": ["You have learned to unravel the basic workings of magic."],
    }]


def test_fetch_collection_resources_hydrates_race_traits():
    base = "https://example.test/api/2014/"
    payloads = {
        f"{base}races": {"results": [{"url": "/api/2014/races/elf"}]},
        f"{base}races/elf": {
            "name": "Elf",
            "traits": [{"name": "Darkvision", "url": "/api/2014/traits/darkvision"}],
        },
        f"{base}traits/darkvision": {
            "name": "Darkvision",
            "desc": ["You can see in darkness within 60 feet of you."],
        },
    }

    resources = SRDClient(
        session=FakeSession(payloads),
        base_url=base,
    ).fetch_collection_resources("races")

    assert resources[0]["payload"]["traits"] == [{
        "name": "Darkvision",
        "desc": ["You can see in darkness within 60 feet of you."],
    }]


def test_fetch_collection_resources_hydrates_class_levels_and_features():
    base = "https://example.test/api/2014/"
    payloads = {
        f"{base}classes": {"results": [{"url": "/api/2014/classes/wizard"}]},
        f"{base}classes/wizard": {
            "name": "Wizard",
            "class_levels": "/api/2014/classes/wizard/levels",
        },
        f"{base}classes/wizard/levels": [{
            "level": 1,
            "features": [{"name": "Spellcasting", "url": "/api/2014/features/spellcasting"}],
        }],
        f"{base}features/spellcasting": {
            "name": "Spellcasting",
            "desc": ["You have learned to unravel the basic workings of magic."],
        },
    }

    resources = SRDClient(session=FakeSession(payloads), base_url=base).fetch_collection_resources("classes")

    assert resources[0]["payload"]["class_levels"][0]["features"] == [{
        "name": "Spellcasting",
        "desc": ["You have learned to unravel the basic workings of magic."],
    }]


def test_fetch_collection_resources_hydrates_subclass_levels_and_features():
    base = "https://example.test/api/2014/"
    payloads = {
        f"{base}subclasses": {"results": [{"url": "/api/2014/subclasses/lore"}]},
        f"{base}subclasses/lore": {
            "name": "College of Lore",
            "class": {"name": "Bard"},
            "subclass_levels": "/api/2014/subclasses/lore/levels",
        },
        f"{base}subclasses/lore/levels": [{
            "level": 3,
            "features": [{"name": "Cutting Words", "url": "/api/2014/features/cutting-words"}],
        }],
        f"{base}features/cutting-words": {
            "name": "Cutting Words",
            "desc": ["You learn how to inspire others."],
        },
    }

    resources = SRDClient(session=FakeSession(payloads), base_url=base).fetch_collection_resources("subclasses")

    assert resources[0]["payload"]["subclass_levels"][0]["features"] == [{
        "name": "Cutting Words",
        "desc": ["You learn how to inspire others."],
    }]
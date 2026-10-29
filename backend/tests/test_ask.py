from app import ask, graph_store

KNOWN = [
    {"name": "TSMC", "type": "Company", "aliases": ["taiwan semiconductor"]},
    {"name": "Apple", "type": "Company", "aliases": []},
    {"name": "ASML", "type": "Company", "aliases": []},
]


def N(name, t="Company"):
    return {"name": name, "type": t}


def E(t, conf=1.0):
    return {"type": t, "evidence": f"ev-{t}", "sources": ["http://x"], "confidence": conf}


def test_direction():
    assert ask.detect_direction("Who supplies TSMC?") == "upstream"
    assert ask.detect_direction("What does Apple depend on?") == "upstream"
    assert ask.detect_direction("What happens to Apple if TSMC is disrupted?") == "downstream"


def test_link_entities_by_name_alias_and_seed():
    names = {e["name"] for e in ask.link_entities("What if Taiwan Semiconductor stops, does Apple Inc. suffer?", KNOWN)}
    assert names == {"TSMC", "Apple"}
    assert ask.link_entities("Tell me about bananas", KNOWN) == []


def test_answer_downstream_filters_to_connecting_paths(monkeypatch):
    monkeypatch.setattr(graph_store, "known_entities", lambda n=300: KNOWN)
    rows = {
        "company:tsmc": [{"nodes": [N("TSMC"), N("Apple")], "edges": [E("SUPPLIES")]}],
        "company:apple": [],
    }
    monkeypatch.setattr(graph_store, "paths_from", lambda key, h=3, limit=80: rows.get(key, []))
    out = ask.answer("What happens to Apple if TSMC is disrupted?")
    assert out["direction"] == "downstream"
    assert out["paths"][0]["chain"] == "TSMC -SUPPLIES-> Apple"
    assert out["related_companies"] == ["Apple"]


def test_answer_upstream_and_unknown(monkeypatch):
    monkeypatch.setattr(graph_store, "known_entities", lambda n=300: KNOWN)
    monkeypatch.setattr(graph_store, "paths_to", lambda key, h=3, limit=80:
                        [{"nodes": [N("ASML"), N("TSMC")], "edges": [E("SUPPLIES", 0.9)]}])
    out = ask.answer("Who supplies TSMC?")
    assert out["related_companies"] == ["ASML"] and out["paths"][0]["weakest_confidence"] == 0.9
    assert "No entity" in ask.answer("what about bananas?")["note"]
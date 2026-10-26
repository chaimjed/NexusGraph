from app.resolve import acronym, acronym_prefix, norm, resolve
from app.schemas import EntityType as E, Extraction, Relation, RelationType as R


def rel(s, t, st=E.COMPANY, tt=E.COMPANY, relation=R.SUPPLIES):
    return Relation(source=s, source_type=st, relation=relation, target=t,
                    target_type=tt, evidence="x", confidence=0.9)


KNOWN = [
    {"name": "TSMC", "type": "Company", "aliases": []},
    {"name": "Apple", "type": "Company", "aliases": []},
    {"name": "ASML", "type": "Company", "aliases": []},
]


def pairs(out):
    return {(r.source, r.target) for r in out.relations}


def test_norm_and_acronym():
    assert norm("Apple Inc.") == "apple"
    assert norm("ASML Holding") == "asml"
    assert acronym("Taiwan Semiconductor Manufacturing Co.") == "tsmc"


def test_variants_merge_into_known_names():
    res = Extraction(relations=[rel("Taiwan Semiconductor Manufacturing Company", "Apple Inc."),
                                rel("ASML Holding", "TSMC")])
    out, _ = resolve(res, KNOWN)
    assert pairs(out) == {("TSMC", "Apple"), ("ASML", "TSMC")}


def test_alias_is_learned_then_reused():
    _, upd = resolve(Extraction(relations=[rel("Taiwan Semiconductor Manufacturing Company", "Apple")]), KNOWN)
    assert ("Company", "TSMC", "taiwan semiconductor manufacturing") in upd
    known2 = [{"name": "TSMC", "type": "Company", "aliases": ["taiwan semiconductor manufacturing"]}] + KNOWN[1:]
    out, _ = resolve(Extraction(relations=[rel("Taiwan Semiconductor", "Apple")]), known2)
    assert out.relations[0].source == "TSMC"


def test_events_are_not_fuzzy_merged():
    known = [{"name": "China export ban 2023", "type": "Event", "aliases": []}]
    out, _ = resolve(Extraction(relations=[rel("China export ban 2024", "TSMC", st=E.EVENT, relation=R.AFFECTS)]), known)
    assert out.relations[0].source == "China export ban 2024"


def test_acronym_matches_short_name_both_ways():
    assert acronym_prefix("TSMC", "Taiwan Semiconductor")
    assert acronym_prefix("Taiwan Semiconductor", "TSMC")
    assert not acronym_prefix("Apple", "Taiwan Semiconductor")


def test_seed_canonicalises_even_with_empty_graph():
    res = Extraction(relations=[rel("Taiwan Semiconductor Manufacturing Co.", "Apple Inc."),
                                rel("ASML Holding", "Taiwan Semiconductor"),
                                rel("NVIDIA Corp.", "TSMC")])
    out, upd = resolve(res, [])
    assert pairs(out) == {("TSMC", "Apple"), ("ASML", "TSMC"), ("Nvidia", "TSMC")}
    assert ("Company", "TSMC", "taiwan semiconductor") in upd
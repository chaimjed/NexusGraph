from app.extract import clean
from app.schemas import EntityType as E, Extraction, Relation, RelationType as R, entity_key


def rel(src, tgt, conf=0.9, relation=R.SUPPLIES, st=E.COMPANY, tt=E.COMPANY):
    return Relation(source=src, source_type=st, relation=relation, target=tgt,
                    target_type=tt, evidence="x", confidence=conf)


def test_entity_key_normalises_case_and_spaces():
    assert entity_key("  Intel   Corp ", E.COMPANY) == "company:intel corp"


def test_clean_drops_self_loops_low_confidence_and_duplicates():
    res = Extraction(relations=[
        rel("Intel", "Intel"),
        rel("ASML", "Intel", conf=0.3),
        rel("ASML", "Intel"),
        rel("asml", "INTEL"),
    ])
    out = clean(res, min_confidence=0.6)
    assert len(out.relations) == 1
    assert out.relations[0].source == "ASML"


def test_strip_fences_and_parse():
    from app.llm import strip_fences
    raw = '```json\n{"relations": []}\n```'
    assert Extraction.model_validate_json(strip_fences(raw)).relations == []
def test_clean_drops_invalid_type_combinations():
    from app.schemas import EntityType as E, RelationType as R
    bad = rel("Nvidia", "China", tt=E.LOCATION)                       # SUPPLIES -> Location
    ok = rel("Nvidia", "Apple")
    ev = rel("Export ban 2025", "Nvidia", st=E.EVENT, relation=R.AFFECTS)
    out = clean(Extraction(relations=[bad, ok, ev]), min_confidence=0.6)
    assert [(r.source, r.target) for r in out.relations] == [("Nvidia", "Apple"), ("Export ban 2025", "Nvidia")]

def test_clean_drops_approval_as_supply_but_keeps_real_supply():
    from app.schemas import EntityType as E, RelationType as R
    approval = Relation(source="Nvidia", source_type=E.COMPANY, relation=R.SUPPLIES, target="Tencent",
                        target_type=E.COMPANY, confidence=0.9,
                        evidence="the Commerce Department approving around 10 Chinese firms to purchase the chips")
    real = Relation(source="ASML", source_type=E.COMPANY, relation=R.SUPPLIES, target="TSMC",
                    target_type=E.COMPANY, confidence=0.9,
                    evidence="ASML supplies machines to TSMC under a licence")
    out = clean(Extraction(relations=[approval, real]), min_confidence=0.6)
    assert [x.source for x in out.relations] == ["ASML"]


def test_clean_drops_backing_as_hosts_and_hedged_approval():
    backing = rel("Shenzhen", "SiCarrier", relation=R.HOSTS, st=E.LOCATION)
    backing = backing.model_copy(update={"evidence": "a maker backed by the Shenzhen municipal government"})
    site = rel("South Korea", "Samsung", relation=R.HOSTS, st=E.LOCATION)
    site = site.model_copy(update={"evidence": "Samsung has memory plants in South Korea"})
    hedged = rel("Nvidia", "Tencent").model_copy(update={
        "evidence": "approved Tencent to purchase H200 chips, but Nvidia has shipped very few"})
    out = clean(Extraction(relations=[backing, site, hedged]), min_confidence=0.6)
    assert [(r.source, r.target) for r in out.relations] == [("South Korea", "Samsung")]
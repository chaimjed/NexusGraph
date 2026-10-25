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

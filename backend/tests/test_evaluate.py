from app.evaluate import norm_rel, score_case


def R(rel, s, t):
    return norm_rel(rel, s, t)


def test_perfect_match_with_name_variants():
    preds = [R("SUPPLIES", "ASML Holding", "Taiwan Semiconductor"), R("INPUT_TO", "neon", "Samsung")]
    gold = [R("SUPPLIES", "ASML", "TSMC"), R("INPUT_TO", "neon gas", "Samsung")]
    tp, fp, fn = score_case(preds, gold)
    assert (tp, fp, fn) == (2, [], [])


def test_false_positive_and_miss():
    tp, fp, fn = score_case([R("SUPPLIES", "Nvidia", "Tencent")], [R("SUPPLIES", "ASML", "TSMC")])
    assert tp == 0 and len(fp) == 1 and len(fn) == 1


def test_optional_is_not_an_error_and_negative_case_flags_extras():
    opt = [R("AFFECTS", "approval", "Nvidia")]
    assert score_case([R("AFFECTS", "Some event", "Nvidia")], [], opt)[1] == []
    assert len(score_case([R("SUPPLIES", "SiCarrier", "Huawei")], [], opt)[1]) == 1


def test_affects_matches_on_target_only():
    tp, fp, fn = score_case([R("AFFECTS", "China gallium export ban 2026", "Infineon")],
                            [R("AFFECTS", "export ban", "Infineon")])
    assert tp == 1 and not fp and not fn
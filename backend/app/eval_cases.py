"""Hand-labelled evaluation cases.

gold     = relations the extractor MUST find        (relation, source, target)
optional = relations that are acceptable but not required (not counted as errors)
An empty gold list means: the extractor should find NOTHING in this text.
AFFECTS relations are matched on the target only (event names vary a lot).
Add your own cases from real articles at the end of the list.
"""

CASES = [
    {"id": "direct-supply",
     "text": "ASML supplies extreme ultraviolet lithography machines to TSMC and Samsung.",
     "gold": [("SUPPLIES", "ASML", "TSMC"), ("SUPPLIES", "ASML", "Samsung")]},

    {"id": "long-names",
     "text": "Taiwan Semiconductor Manufacturing Company makes processors for Advanced Micro Devices.",
     "gold": [("SUPPLIES", "TSMC", "AMD")]},

    {"id": "facility-location",
     "text": "Intel opened a new chip factory in Arizona last year.",
     "gold": [("HOSTS", "Arizona", "Intel")]},

    {"id": "material-input",
     "text": "Samsung depends on neon gas imports for its chip lithography lines.",
     "gold": [("INPUT_TO", "neon gas", "Samsung")]},

    {"id": "event-affects",
     "text": "A 2026 export ban on gallium by China is disrupting production at Infineon.",
     "gold": [("AFFECTS", "export ban", "Infineon")],
     "optional": [("AFFECTS", "export ban", "gallium"), ("AFFECTS", "export ban", "China")]},

    {"id": "supplier-list",
     "text": "Nexperia's Chinese plant now buys wafers from Wuxi NCE Power and Yangjie Technology.",
     "gold": [("SUPPLIES", "Wuxi NCE Power", "Nexperia"), ("SUPPLIES", "Yangjie Technology", "Nexperia")]},

    {"id": "chain",
     "text": "TSMC buys photoresist from JSR. TSMC manufactures processors for Apple.",
     "gold": [("SUPPLIES", "JSR", "TSMC"), ("SUPPLIES", "TSMC", "Apple")],
     "optional": [("INPUT_TO", "photoresist", "TSMC")]},

    {"id": "assembly",
     "text": "Foxconn assembles iPhones for Apple at its plant in Zhengzhou, China.",
     "gold": [("SUPPLIES", "Foxconn", "Apple")],
     "optional": [("HOSTS", "Zhengzhou", "Foxconn"), ("HOSTS", "China", "Foxconn")]},

    # ---- negatives: the extractor should return nothing ----
    {"id": "neg-dateline",
     "text": "Paris, France--(Newsfile Corp. - October 20, 2026) - Sequans Communications S.A. announced it will hold a conference call to review its quarterly results.",
     "gold": []},

    {"id": "neg-works-with",
     "text": "SiCarrier is a chip-equipment maker that works with Huawei on research projects.",
     "gold": []},

    {"id": "neg-competitor",
     "text": "Cambricon is seen as an alternative to Nvidia in the Chinese AI chip market.",
     "gold": []},

    {"id": "neg-approval",
     "text": "The US Commerce Department approved Tencent and ByteDance to purchase H200 chips, but Nvidia says it has shipped very few so far.",
     "gold": [],
     "optional": [("AFFECTS", "approval", "Nvidia"), ("AFFECTS", "approval", "Tencent"),
                  ("AFFECTS", "approval", "ByteDance"), ("AFFECTS", "approval", "H200")]},

    {"id": "neg-hedged",
     "text": "Unconfirmed reports suggest Samsung may supply memory chips to Tesla, though neither company has commented.",
     "gold": []},
]
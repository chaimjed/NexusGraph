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
    {
    "id": "real-01",
    "text": "Micron buys specialty gases from Linde and sells memory chips to Dell.",
    "gold": [("SUPPLIES", "Linde", "Micron"), ("SUPPLIES", "Micron", "Dell")]
    },
        # ---- direction and phrasing variants ----
    {"id": "reversed-buyer-first",
     "text": "Dell buys its memory chips from Micron.",
     "gold": [("SUPPLIES", "Micron", "Dell")]},

    {"id": "passive-voice",
     "text": "Apple's processors are manufactured by TSMC.",
     "gold": [("SUPPLIES", "TSMC", "Apple")]},

    {"id": "two-suppliers-one-customer",
     "text": "Lam Research and Tokyo Electron both sell etching tools to SK Hynix.",
     "gold": [("SUPPLIES", "Lam Research", "SK Hynix"), ("SUPPLIES", "Tokyo Electron", "SK Hynix")]},

    {"id": "hosts-new-fab",
     "text": "Samsung is building a new chip fab in Texas.",
     "gold": [("HOSTS", "Texas", "Samsung")]},

{"id": "event-natural-disaster",
     "text": "A 2026 earthquake in Taiwan halted production at TSMC for two days.",
     "gold": [("AFFECTS", "earthquake", "TSMC")],
     "optional": [("AFFECTS", "earthquake", "Taiwan"), ("HOSTS", "Taiwan", "TSMC")]},


    # ---- more negatives ----
    {"id": "neg-investor",
     "text": "SoftBank holds a majority stake in Arm and has invested billions in AI start-ups.",
     "gold": []},

    {"id": "neg-rivals",
     "text": "AMD competes with Intel in the server processor market.",
     "gold": []},

    {"id": "neg-partnership",
     "text": "Intel and Microsoft announced a partnership to promote AI-enabled PCs.",
     "gold": []},

    {"id": "neg-vague",
     "text": "Companies across the industry are diversifying their supply chains to reduce risk.",
     "gold": []},

    {"id": "neg-denied",
     "text": "Nvidia denied that it has supplied any chips to Huawei.",
     "gold": []},

    {"id": "neg-country-customer",
     "text": "China imported record volumes of chipmaking equipment from the Netherlands last year.",
     "gold": []},
         {"id": "neg-backed-by-government",
     "text": "SiCarrier is a semiconductor equipment maker backed by the Shenzhen municipal government.",
     "gold": []},

    {"id": "real-hosts-countries",
     "text": "Samsung and SK Hynix have memory plants in South Korea and large operations in China.",
     "gold": [("HOSTS", "South Korea", "Samsung"), ("HOSTS", "South Korea", "SK Hynix"),
              ("HOSTS", "China", "Samsung"), ("HOSTS", "China", "SK Hynix")]},

    {"id": "real-foundry",
     "text": "TSMC, the contract manufacturer that fabricates chips for Nvidia, said demand remains strong.",
     "gold": [("SUPPLIES", "TSMC", "Nvidia")]},
]
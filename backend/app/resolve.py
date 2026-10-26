"""Entity resolution: map name variants to one canonical node (no LLM calls)."""
import re
from difflib import SequenceMatcher

from .extract import clean
from .schemas import Extraction

SUFFIX = re.compile(
    r"\b(incorporated|inc|corporation|corp|company|co|limited|ltd|plc|llc|holdings?|group)\b"
)
STOP = {"of", "the", "and"}

# Well-known companies: canonical display name -> other names. Extend freely.
SEED = {
    "TSMC": ["taiwan semiconductor", "taiwan semiconductor manufacturing"],
    "ASML": [],
    "Intel": [],
    "Nvidia": [],
    "Apple": [],
    "AMD": ["advanced micro devices"],
    "Qualcomm": [],
    "Broadcom": [],
    "Samsung": ["samsung electronics"],
    "SK Hynix": [],
    "Micron": ["micron technology"],
    "Tokyo Electron": [],
    "Applied Materials": [],
    "Lam Research": [],
    "GlobalFoundries": [],
    "Foxconn": ["hon hai", "hon hai precision industry"],
}


def norm(name: str) -> str:
    s = re.sub(r"[^\w\s]", " ", name.lower())
    s = " ".join(s.split())
    s = re.sub(r"^the\s+", "", s)
    return " ".join(SUFFIX.sub(" ", s).split())


def acronym(name: str) -> str:
    words = [w for w in re.sub(r"[^\w\s]", " ", name).split() if w.lower() not in STOP]
    return "".join(w[0] for w in words).lower() if len(words) >= 3 else ""


SEED_INDEX = {norm(form): canon for canon, forms in SEED.items() for form in [canon, *forms]}


def _same(n: str, acr: str, form: str, exact_only: bool) -> bool:
    if n == form:
        return True
    if exact_only:
        return False
    if acr and acr == form.replace(" ", ""):
        return True
    a, b = set(n.split()), set(form.split())
    if len(a) >= 2 and len(b) >= 2 and (a <= b or b <= a):
        return True
    return SequenceMatcher(None, n, form).ratio() >= 0.92


def acronym_prefix(a: str, b: str) -> bool:
    """True if one name is an ALL-CAPS acronym starting with the initials of the other (TSMC ~ Taiwan Semiconductor)."""
    for short, long_ in ((a, b), (b, a)):
        s = short.strip()
        words = norm(long_).split()
        if s.isupper() and " " not in s and 3 <= len(s) <= 6 and len(words) >= 2:
            ini = "".join(w[0] for w in words)
            if s.lower().startswith(ini) and len(ini) < len(s) <= len(ini) + 3:
                return True
    return False


def resolve(result: Extraction, known: list[dict]) -> tuple[Extraction, list[tuple]]:
    """Return (relations with canonical names, [(type, canonical_name, alias), ...] to persist)."""
    pools: dict[str, list[dict]] = {}
    for k in known:
        pools.setdefault(k["type"], []).append(
            {"name": k["name"], "aliases": list(k.get("aliases") or [])}
        )
    updates: list[tuple] = []

    def canon(name: str, etype) -> str:
        t = etype.value
        pool = pools.setdefault(t, [])
        alias_form, acr = norm(name), acronym(name)
        if t == "Company" and alias_form in SEED_INDEX:
            name = SEED_INDEX[alias_form]  # canonical spelling of a well-known company
        n = norm(name)
        exact = t == "Event"
        if n:
            for c in pool:
                forms = [norm(c["name"]), *c["aliases"]]
                hit = any(_same(n, acr, f, exact) for f in forms)
                hit = hit or (not exact and n.replace(" ", "") == acronym(c["name"]))
                hit = hit or (not exact and acronym_prefix(name, c["name"]))
                if hit:
                    if alias_form and alias_form != norm(c["name"]) and alias_form not in c["aliases"]:
                        c["aliases"].append(alias_form)
                        updates.append((t, c["name"], alias_form))
                    return c["name"]
        entry = {"name": name, "aliases": []}
        if alias_form and alias_form != n:
            entry["aliases"].append(alias_form)
            updates.append((t, name, alias_form))
        pool.append(entry)
        return name

    rels = [
        r.model_copy(update={"source": canon(r.source, r.source_type),
                             "target": canon(r.target, r.target_type)})
        for r in result.relations
    ]
    return clean(Extraction(relations=rels)), updates
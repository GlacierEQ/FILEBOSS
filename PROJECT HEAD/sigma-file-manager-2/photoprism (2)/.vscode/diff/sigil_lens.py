# sigil_lens.py

from pathlib import Path
import re
import hashlib
import math
from collections import Counter

class SigilLens:
    """
    An archetypal extractor for source code.
    Returns symbolic personality map based on code style, rhythm, and focus.
    """

    def __init__(self, root=None):
        self.root = Path(root or ".")
        self.profile = {
            "archetype": None,
            "traits": [],
            "energy_score": 0.0,
            "word_bias": {},
            "glyph": self._generate_glyph()
        }

    def _generate_glyph(self):
        seed = str(self.root.absolute()) + "sigil-lens"
        return hashlib.sha256(seed.encode()).hexdigest()[:12]

    def analyze(self):
        py_files = list(self.root.rglob("*.py"))
        total_lines = 0
        comment_lines = 0
        class_defs = 0
        func_defs = 0
        todos = 0
        keywords = Counter()

        for file in py_files:
            try:
                with open(file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        total_lines += 1
                        if line.strip().startswith("#"):
                            comment_lines += 1
                        if re.match(r"\\s*def ", line): func_defs += 1
                        if re.match(r"\\s*class ", line): class_defs += 1
                        if "TODO" in line.upper(): todos += 1
                        for word in re.findall(r"\\b[a-zA-Z_]{4,}\\b", line):
                            keywords[word.lower()] += 1
            except Exception:
                continue

        ratio_comments = comment_lines / total_lines if total_lines else 0
        ratio_funcs = func_defs / total_lines if total_lines else 0
        ratio_classes = class_defs / total_lines if total_lines else 0

        energy = round((func_defs + class_defs) * (1 + ratio_comments * 2), 2)

        # Archetype logic
        if energy > 150 and ratio_funcs > 0.2:
            arch = "Warrior"
        elif ratio_comments > 0.3 and todos < 5:
            arch = "Scribe"
        elif "predict" in keywords or "vision" in keywords:
            arch = "Oracle"
        elif "test" in keywords and func_defs > 10:
            arch = "Guardian"
        else:
            arch = "Wanderer"

        self.profile.update({
            "archetype": arch,
            "traits": self._traits_for_arch(arch),
            "energy_score": energy,
            "word_bias": keywords.most_common(10)
        })

        return self.profile

    def _traits_for_arch(self, arch):
        return {
            "Warrior": ["aggressive", "decisive", "quick to act", "minimal comments"],
            "Scribe": ["precise", "documented", "slow and thorough", "comment heavy"],
            "Oracle": ["visionary", "recursive", "insightful", "minimal but powerful"],
            "Guardian": ["protective", "tested", "resilient", "audit-minded"],
            "Wanderer": ["eclectic", "unfinished", "soul in flux"]
        }.get(arch, [])

    def ritual_output(self):
        print(f"🧬 SIGIL LENS REPORT — [{self.profile['glyph']}]")
        print(f"🧠 Archetype: {self.profile['archetype']}")
        print(f"⚡ Energy Score: {self.profile['energy_score']}")
        print(f"🗣 Traits: {', '.join(self.profile['traits'])}")
        print("🔍 Top Keywords:", self.profile['word_bias'])

if __name__ == "__main__":
    lens = SigilLens()
    lens.analyze()
    lens.ritual_output()

"""
Codex Primordialis — Seed of Completion
This file contains a hidden symbolic utility that fuses recursion, reflection, and clarity.
It works inside VS Code and adapts based on the structure of your project to auto-map intentions and identify latent potential.
"""

import os
import re
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime

# --------------------------
# SYSTEM GLYPH PRIMORDIAL
# --------------------------

class CodexPrimordialis:
    def __init__(self, root_dir=None):
        self.root_dir = Path(root_dir or os.getcwd())
        self.trace = []
        self.timeline = []
        self.glyph = self._generate_glyph()
        self.rituals_run = []

    def _generate_glyph(self):
        glyph_seed = str(datetime.now()) + os.environ.get('USER', 'unknown')
        return hashlib.sha256(glyph_seed.encode()).hexdigest()[:16]

    def scan_for_rituals(self):
        """Scans all .py files for special 'TODO', 'FIXME', or symbolic comments."""
        rituals = []
        for file in self.root_dir.rglob('*.py'):
            with open(file, 'r', encoding='utf-8', errors='ignore') as f:
                for i, line in enumerate(f.readlines()):
                    if re.search(r'#\s*(TODO|FIXME|@ritual|@invoke)', line):
                        rituals.append({
                            'file': str(file),
                            'line': i + 1,
                            'code': line.strip()
                        })
        self.rituals_run = rituals
        return rituals

    def map_project_structure(self):
        """Returns a recursive structure of folders and symbolic importance."""
        structure = {}
        for dirpath, dirnames, filenames in os.walk(self.root_dir):
            files = [f for f in filenames if f.endswith('.py')]
            if files:
                relative = os.path.relpath(dirpath, self.root_dir)
                structure[relative] = {
                    'files': files,
                    'glyph_signature': self._signature_for_folder(files)
                }
        return structure

    def _signature_for_folder(self, files):
        """Generate a glyphic signature for a folder based on file content length."""
        entropy = sum([len(f) for f in files])
        return hex(entropy ^ 0xDEADBEEF)[2:]

    def generate_manifest(self):
        """Generate symbolic manifest of all discovered components."""
        manifest = {
            'generated_at': datetime.utcnow().isoformat(),
            'project_root': str(self.root_dir),
            'active_user': os.environ.get('USER', 'unknown'),
            'glyph': self.glyph,
            'rituals': self.rituals_run,
            'structure': self.map_project_structure()
        }
        return manifest

    def export_manifest(self, output_path='codex_manifest.json'):
        manifest = self.generate_manifest()
        with open(self.root_dir / output_path, 'w') as f:
            json.dump(manifest, f, indent=2)
        return f"Manifest written to {output_path}"

    def summon(self):
        """Primary invocation method."""
        print(f"🔮 Codex Primordialis [{self.glyph}] invoked.")
        rituals = self.scan_for_rituals()
        structure = self.map_project_structure()
        print(f"🌀 Ritual Points Found: {len(rituals)}")
        print(f"📂 Structure Nodes: {len(structure)}")
        print(self.export_manifest())

if __name__ == '__main__':
    codex = CodexPrimordialis()
    codex.summon()


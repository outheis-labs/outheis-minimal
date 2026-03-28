#!/usr/bin/env python3
"""
Build the outheis website from docs/.

Reads markdown files from docs/, adds Jekyll frontmatter,
generates navigation, and outputs to web/.
"""

import os
import re
import shutil
from pathlib import Path

ROOT = Path(__file__).parent.parent
DOCS = ROOT / "docs"
WEB = ROOT / "web"

# Navigation structure (order matters)
NAV_STRUCTURE = [
    ("Home", "/", "index.md"),
    ("Philosophy", "/philosophy/", "philosophy/index.md"),
    ("Design", "/design/", "design/index.md", [
        ("Overview", "/design/", "design/index.md"),
        ("OS Principles", "/design/01-why-os-principles", "design/01-why-os-principles.md"),
        ("Systems Survey", "/design/02-systems-survey", "design/02-systems-survey.md"),
        ("Architecture", "/design/03-architecture", "design/03-architecture.md"),
        ("Data Formats", "/design/04-data-formats", "design/04-data-formats.md"),
        ("Related Work", "/design/05-related-work", "design/05-related-work.md"),
        ("Agent Prompts", "/design/06-agent-prompts", "design/06-agent-prompts.md"),
    ]),
    ("Implementation", "/implementation/", "implementation/index.md", [
        ("Current State", "/implementation/architecture", "implementation/architecture.md"),
        ("Memory & Rules", "/implementation/memory", "implementation/memory.md"),
        ("CLI Guide", "/implementation/guide", "implementation/guide.md"),
    ]),
]


def extract_title(content: str, filepath: Path) -> str:
    """Extract title from first H1 or filename."""
    match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
    if match:
        return match.group(1).strip()
    return filepath.stem.replace('-', ' ').title()


def has_frontmatter(content: str) -> bool:
    """Check if content already has YAML frontmatter."""
    return content.startswith('---\n')


def add_frontmatter(content: str, title: str) -> str:
    """Add Jekyll frontmatter if not present."""
    if has_frontmatter(content):
        return content
    return f'---\ntitle: "{title}"\n---\n\n{content}'


def process_markdown(src: Path, dst: Path):
    """Process a markdown file: add frontmatter, copy to web/."""
    content = src.read_text(encoding='utf-8')
    title = extract_title(content, src)
    content = add_frontmatter(content, title)
    
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(content, encoding='utf-8')
    print(f"  {src.relative_to(DOCS)} → {dst.relative_to(WEB)}")


def copy_assets():
    """Copy assets to web/."""
    assets_src = DOCS / "_assets"
    
    if not assets_src.exists():
        return
    
    # Copy logo to assets/
    logo_src = assets_src / "logo.svg"
    if logo_src.exists():
        dst = WEB / "assets" / "logo.svg"
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(logo_src, dst)
        print(f"  _assets/logo.svg → assets/logo.svg")
    
    # Copy favicons to root
    for f in assets_src.glob("favicon*"):
        shutil.copy(f, WEB / f.name)
        print(f"  _assets/{f.name} → {f.name}")
    
    for f in assets_src.glob("*.png"):
        if f.name != "logo.svg":
            shutil.copy(f, WEB / f.name)
            print(f"  _assets/{f.name} → {f.name}")
    
    webmanifest = assets_src / "site.webmanifest"
    if webmanifest.exists():
        shutil.copy(webmanifest, WEB / "site.webmanifest")
        print(f"  _assets/site.webmanifest → site.webmanifest")


def build_docs():
    """Build all documentation."""
    print("Building docs → web/")
    print()
    
    # Process markdown files
    for md_file in DOCS.rglob("*.md"):
        if md_file.parent.name.startswith("_"):
            continue
        
        rel_path = md_file.relative_to(DOCS)
        
        # Convert index.md to directory structure for Jekyll
        if md_file.name == "index.md":
            dst = WEB / rel_path
        else:
            # Non-index files: keep as-is for now
            dst = WEB / rel_path
        
        process_markdown(md_file, dst)
    
    print()
    print("Copying assets...")
    copy_assets()
    
    print()
    print("Done.")


if __name__ == "__main__":
    build_docs()

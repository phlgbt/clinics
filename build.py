#!/usr/bin/env python3
"""
Build script for the HIV/STI/Sexual Health Clinic Directory.

Merges two source files into the final index.html:
  - core.json    : facility facts sourced from PhilHealth's OHAT PDF
                    (name, address, phone, email, accreditation, type).
                    Regenerate this wholesale each time a new PDF snapshot
                    is parsed.
  - socials.json  : hand-verified social media links, keyed by exact
                    facility name as it appears in core.json. This file
                    represents real research effort and should NOT be
                    regenerated from scratch -- only added to.

The two are joined by facility name and injected into template.html in
place of the __CLINIC_DATA__ placeholder to produce index.html.

Usage:
    python3 build.py

Run this after editing core.json or socials.json, or after adding new
entries to socials.json following a refresh of core.json.
"""
import json
import sys

CORE_PATH = "core.json"
SOCIALS_PATH = "socials.json"
TEMPLATE_PATH = "template.html"
OUTPUT_PATH = "index.html"


def build():
    with open(CORE_PATH, encoding="utf-8") as f:
        core = json.load(f)
    with open(SOCIALS_PATH, encoding="utf-8") as f:
        socials = json.load(f)

    merged = []
    matched = 0
    for entry in core:
        record = dict(entry)
        record["socials"] = socials.get(entry["name"], {})
        if record["socials"]:
            matched += 1
        merged.append(record)

    # Flag any socials.json entries that didn't match anything in core.json --
    # this is the main failure mode when core.json is refreshed from a new
    # PDF and a facility's name changed slightly. These links aren't lost,
    # just orphaned; worth reviewing rather than silently dropping.
    core_names = {e["name"] for e in core}
    orphaned = [name for name in socials if name not in core_names]

    print(f"core.json: {len(core)} facility records")
    print(f"socials.json: {len(socials)} verified entries")
    print(f"Merged: {matched} facilities matched to a social link")
    if orphaned:
        print(f"\nWARNING: {len(orphaned)} socials.json name(s) did not match any facility in core.json:")
        for name in orphaned:
            print(f"  - {name!r}")
        print("These links are preserved in socials.json but are not currently attached to any facility.")
        print("Check whether the facility was renamed, removed, or merged in the new core.json.\n")

    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        template = f.read()

    if "__CLINIC_DATA__" not in template:
        print(f"ERROR: {TEMPLATE_PATH} has no __CLINIC_DATA__ placeholder.", file=sys.stderr)
        sys.exit(1)

    data_json = json.dumps(merged, ensure_ascii=False, separators=(",", ":"))
    output = template.replace("__CLINIC_DATA__", data_json)

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write(output)

    print(f"Wrote {OUTPUT_PATH} ({len(output):,} bytes)")


if __name__ == "__main__":
    build()

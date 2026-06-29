"""Final pre-build audit — checks everything dpkg-buildpackage needs.
Run from DuckBotOS root: python3 scripts/audit-debian-packages.py
Run from cx-distro root:  python3 ../DuckBotOS/scripts/audit-debian-packages.py
Outputs PASS/FAIL per package + a summary table.
"""
import os, re, sys
from pathlib import Path

# Resolve relative to this script's location so it works anywhere
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT  = SCRIPT_DIR.parent
# cx-distro fork lives as a sibling to the DuckBotOS repo root
CX_DISTRO  = REPO_ROOT / "cx-distro"

# Audit target: prefer cx-distro (the build pipeline), fall back to DuckBotOS stubs
if (CX_DISTRO / "packages").is_dir():
    ROOT = str(CX_DISTRO / "packages")
    SOURCE = "cx-distro"
elif (REPO_ROOT / "packages").is_dir():
    ROOT = str(REPO_ROOT / "packages")
    SOURCE = "DuckBotOS"
else:
    ROOT = str(REPO_ROOT / "packages")  # fail with a useful error
    SOURCE = "DuckBotOS"

REQUIRED = ["debian/control", "debian/changelog", "debian/rules"]
RECOMMENDED_IF_SERVICE = ["debian/postinst"]
SERVICES_GLOB = "debian/*.service"

def main():
    failures = []
    print(f"{'PACKAGE':<35} {'CTRL':<5} {'CHANGELOG':<10} {'RULES':<6} {'POSTINST':<9} {'SERVICES':<10} {'GIT OK'}")
    print("-" * 90)
    for d in sorted(os.listdir(ROOT)):
        if not d.startswith("duckbotos-"):
            continue
        pkg = f"{ROOT}/{d}"
        if not os.path.isdir(pkg):
            continue
        has = {}
        for f in REQUIRED:
            has[f] = os.path.isfile(f"{pkg}/{f}")
        # postinst recommended if service files exist or systemctl referenced in postinst
        has_postinst = os.path.isfile(f"{pkg}/debian/postinst")
        has_services = sorted([os.path.basename(s) for s in (
            [os.path.join(f"{pkg}/debian/", f) for f in os.listdir(f"{pkg}/debian/") if f.endswith(".service")]
            if os.path.isdir(f"{pkg}/debian/") else []
        )])
        # Symbol for "would build successfully"
        ctrl_status = "✅" if has["debian/control"] else "❌"
        cl_status = "✅" if has["debian/changelog"] else "❌"
        rules_status = "✅" if has["debian/rules"] else "❌"
        pi_status = "✅" if has_postinst else "—"
        svc_status = str(len(has_services)) if has_services else "—"
        ok = all([has["debian/control"], has["debian/changelog"], has["debian/rules"]])
        marker = "✅" if ok else "❌"
        print(f"{d:<35} {ctrl_status:<5} {cl_status:<10} {rules_status:<6} {pi_status:<9} {svc_status:<10} {marker}")
        if not ok:
            failures.append(d)
    print()
    # Collision check (source packages generating same binary name)
    print("=" * 60)
    print("PACKAGE COLLISION CHECK")
    print("=" * 60)
    all_pkgs = {}
    for d in sorted(os.listdir(ROOT)):
        if not d.startswith("duckbotos-"):
            continue
        c_path = f"{ROOT}/{d}/debian/control"
        if not os.path.isfile(c_path):
            continue
        with open(c_path) as f:
            c = f.read()
        for pkg in re.findall(r'^Package:\s*(\S+)', c, re.M):
            all_pkgs.setdefault(pkg, []).append(d)
    collisions = [p for p, s in all_pkgs.items() if len(s) > 1]
    if collisions:
        print(f"❌ {len(collisions)} collisions:")
        for p in collisions:
            print(f"   {p}: {all_pkgs[p]}")
    else:
        print(f"✅ All {len(all_pkgs)} binary package names are unique across {sum(1 for d in os.listdir(ROOT) if d.startswith('duckbotos-'))} source packages")
    print()
    # Cross-reference Depends vs existing packages
    print("=" * 60)
    print("DEPENDS VALIDATION (each Depends: entry points to an existing binary package)")
    print("=" * 60)
    all_binary_names = set(all_pkgs.keys())
    # All the packages that provide actual services, NOT meta-packages
    concrete_pkgs = {n for n in all_binary_names}
    # Add base ubuntu-standard for "ubuntu-standard"
    depends_violations = []
    for d in sorted(os.listdir(ROOT)):
        if not d.startswith("duckbotos-"):
            continue
        c_path = f"{ROOT}/{d}/debian/control"
        if not os.path.isfile(c_path):
            continue
        with open(c_path) as f:
            c = f.read()
        for pkg_stanza in re.split(r'\nPackage: ', c)[1:]:
            pkg_name = pkg_stanza.split('\n', 1)[0].strip()
            deps_match = re.search(r'Depends:\s*(.+?)(?=\n[A-Z][a-z]+:|\Z)', pkg_stanza, re.S)
            if not deps_match:
                continue
            deps_raw = deps_match.group(1)
            # Split by comma, strip whitespace, extract package names
            for dep in re.findall(r'\n?\s*([\w.+-]+)(?:\s*\([^)]*\))?(?:,\s*[\w.+-]+)*', deps_raw):
                dep = dep.strip()
                if not dep or '${misc' in dep or dep.startswith('#'):
                    continue
                # Alternative deps: pkg1 | pkg2 | pkg3
                alts = [a.strip().split(' (')[0] for a in dep.split('|')]
                for alt in alts:
                    # Skip system pkgs we can't validate
                    if alt in concrete_pkgs:
                        continue  # our own package
                    if any(alt.startswith(p) for p in ('duckbotos', 'cx-')):
                        if alt not in concrete_pkgs:
                            depends_violations.append(f"{d}:{pkg_name} → Depends on missing package '{alt}'")
                    # else: external pkg (ubuntu-standard, nodejs, etc) — skip
    if depends_violations:
        print(f"❌ {len(depends_violations)} Depends violations:")
        for v in depends_violations:
            print(f"   {v}")
    else:
        print(f"✅ All internal Depends point to existing duckbotos/cx packages")
    print()

    print()
    print("=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print(f"Source audited: {SOURCE} ({ROOT})")
    print(f"Source packages audited: {sum(1 for d in os.listdir(ROOT) if d.startswith('duckbotos-'))}")
    print(f"Unique binary packages: {len(all_pkgs)}")
    print(f"Missing required files (deb-control/rules/changelog): {len(failures)}")
    print(f"Package collisions: {len(collisions)}")
    print(f"Depends violations: {len(depends_violations)}")
    if failures or collisions or depends_violations:
        print("❌ NOT BUILD-READY")
        sys.exit(1)
    print("✅ READY for dpkg-buildpackage")

main()

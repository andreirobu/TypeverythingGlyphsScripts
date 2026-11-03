
# MenuTitle: Find Flipped Corners
# -*- coding: utf-8 -*-

from GlyphsApp import *

font = Glyphs.font

if not font:
    raise Exception("Open a font first.")

Glyphs.clearLog()
Glyphs.showMacroWindow()

masters = font.masters

TOLERANCE = 0.0001

issues = []
affected_glyphs = []
read_errors = []


# -------------------------------------------------------
# Find the exact outline position of a node
# -------------------------------------------------------

def get_node_index(layer, origin_node):

    if origin_node is None:
        return None

    for path_index, path in enumerate(layer.paths):

        for node_index, node in enumerate(path.nodes):

            try:
                if node == origin_node:
                    return (path_index, node_index)
            except:
                pass

    return None


# -------------------------------------------------------
# Collect corner hints indexed by outline node
# -------------------------------------------------------

def get_corner_data(layer):

    corners = {}

    if layer is None:
        return corners

    for hint in layer.hints:

        if hint.type != CORNER:
            continue

        node_index = get_node_index(
            layer,
            hint.originNode
        )

        if node_index is None:
            continue

        scale = hint.scale

        corners[node_index] = {
            "name": hint.name,
            "x": float(scale.x),
            "y": float(scale.y)
        }

    return corners


# -------------------------------------------------------
# Compare values
# -------------------------------------------------------

def different(a, b):

    return abs(a - b) > TOLERANCE


# -------------------------------------------------------
# Scan all glyphs and masters
# -------------------------------------------------------

print("=" * 65)
print("CORNER VALUE CONSISTENCY CHECK")
print("=" * 65)

print("Font: %s" % font.familyName)
print("Reference master: %s" % masters[0].name)
print("Masters: %s" % ", ".join(m.name for m in masters))


for glyph in font.glyphs:

    master_data = {}
    glyph_error = False

    # Read corners from every master
    for master in masters:

        layer = glyph.layers[master.id]

        try:
            master_data[master.id] = get_corner_data(layer)

        except Exception as e:

            read_errors.append(
                "%s / %s: %s" %
                (glyph.name, master.name, str(e))
            )

            glyph_error = True

    if glyph_error:
        continue

    reference = masters[0]
    reference_data = master_data[reference.id]

    # All corner nodes found in any master
    all_nodes = set()

    for master in masters:
        all_nodes.update(
            master_data[master.id].keys()
        )

    glyph_issues = []

    # Compare each corresponding outline node
    for node_key in sorted(all_nodes):

        ref_corner = reference_data.get(node_key)

        for master in masters[1:]:

            current = master_data[master.id].get(node_key)

            # Missing corner in one master
            if ref_corner is None or current is None:

                glyph_issues.append({
                    "node": node_key,
                    "master": master.name,
                    "reference": ref_corner,
                    "current": current,
                    "missing": True
                })

                continue

            x_diff = different(
                ref_corner["x"],
                current["x"]
            )

            y_diff = different(
                ref_corner["y"],
                current["y"]
            )

            if x_diff or y_diff:

                glyph_issues.append({
                    "node": node_key,
                    "master": master.name,
                    "reference": ref_corner,
                    "current": current,
                    "x_diff": x_diff,
                    "y_diff": y_diff,
                    "missing": False
                })

    # ---------------------------------------------------
    # Report
    # ---------------------------------------------------

    if glyph_issues:

        affected_glyphs.append(glyph)

        print("\n[INCONSISTENT] %s" % glyph.name)
        print("-" * 55)

        for issue in glyph_issues:

            path_index, node_index = issue["node"]

            print(
                "\nContour %d / Node %d" %
                (path_index + 1, node_index + 1)
            )

            if issue["missing"]:

                if issue["reference"] is None:
                    print("  Missing in reference master")
                else:
                    print(
                        "  Missing corner in %s" %
                        issue["master"]
                    )

                continue

            ref = issue["reference"]
            cur = issue["current"]

            print(
                "  %s: X=%+.2f%% Y=%+.2f%%" %
                (
                    reference.name,
                    ref["x"] * 100,
                    ref["y"] * 100
                )
            )

            print(
                "  %s: X=%+.2f%% Y=%+.2f%%" %
                (
                    issue["master"],
                    cur["x"] * 100,
                    cur["y"] * 100
                )
            )

            if issue["x_diff"]:
                print("  !!! HORIZONTAL VALUE DIFFERENCE")

            if issue["y_diff"]:
                print("  !!! VERTICAL VALUE DIFFERENCE")

            issues.append(issue)


# -------------------------------------------------------
# Summary
# -------------------------------------------------------

print("\n" + "=" * 65)
print("SUMMARY")
print("=" * 65)

print("Affected glyphs: %d" % len(affected_glyphs))
print("Inconsistent corners: %d" % len(issues))
print("Read errors: %d" % len(read_errors))

if read_errors:

    print("\nREAD ERRORS:")

    for error in read_errors:
        print(error)


# -------------------------------------------------------
# Open affected glyphs
# -------------------------------------------------------

if affected_glyphs:

    tab_text = " ".join(
        "/" + glyph.name
        for glyph in affected_glyphs
    )

    font.newTab(tab_text)

    print("\nOpened affected glyphs.")

else:

    print("\nAll corner values are consistent.")

print("=" * 65)

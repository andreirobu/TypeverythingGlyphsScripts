# MenuTitle: Parallelize Segment (Disjoint Pair, H by default; ⇧=V, ⌘ flip)
# -*- coding: utf-8 -*-
from __future__ import division
import math
from GlyphsApp import *
from Foundation import NSPoint

# ---------- Utilities ----------

def is_oncurve(n):
    return isinstance(n, GSNode) and n.type != GSOFFCURVE

def selected_oncurves(layer):
    return [o for o in layer.selection if is_oncurve(o)]

def node_index_in_path(node):
    return node.parent.nodes.index(node)

def consecutive_pair_in_path(n1, n2):
    """Return ordered (a,b) if n1,n2 are consecutive on same path, else None."""
    if n1.parent != n2.parent:
        return None
    nodes = n1.parent.nodes
    i1, i2 = nodes.index(n1), nodes.index(n2)
    L = len(nodes)
    if (i1 + 1) % L == i2:
        return (n1, n2)
    if (i2 + 1) % L == i1:
        return (n2, n1)
    return None

def collect_selected_segments(layer):
    """Collect unique consecutive segments implied by the selection."""
    oncs = selected_oncurves(layer)
    segs, seen = [], set()
    N = len(oncs)
    for i in range(N):
        for j in range(i+1, N):
            pair = consecutive_pair_in_path(oncs[i], oncs[j])
            if pair:
                a, b = pair
                key = (id(a.parent),
                       min(node_index_in_path(a), node_index_in_path(b)),
                       max(node_index_in_path(a), node_index_in_path(b)))
                if key not in seen:
                    seen.add(key)
                    segs.append((a, b))
    return segs

def seg_nodes_set(seg):
    a, b = seg
    return {a, b}

def angle_between(a, b):
    return math.atan2(b.position.y - a.position.y, b.position.x - a.position.x)

def length_between(a, b):
    return math.hypot(b.position.x - a.position.x, b.position.y - a.position.y)

def rotate_point_around(p, origin, delta_rad):
    x = p.x - origin.x
    y = p.y - origin.y
    c, s = math.cos(delta_rad), math.sin(delta_rad)
    xr = x * c - y * s
    yr = x * s + y * c
    return NSPoint(xr + origin.x, yr + origin.y)

def forward_index_range(i_start, i_end, count):
    """Indices strictly between i_start and i_end when walking forward (wrapping)."""
    i = (i_start + 1) % count
    while i != i_end:
        yield i
        i = (i + 1) % count

def modifiers():
    """Return {'shift':bool,'cmd':bool} safely across AppKit versions."""
    try:
        from AppKit import NSEvent, NSEventModifierFlagShift, NSEventModifierFlagCommand
        flags = NSEvent.modifierFlags()
        return {"shift": bool(flags & NSEventModifierFlagShift), "cmd": bool(flags & NSEventModifierFlagCommand)}
    except Exception:
        try:
            from AppKit import NSEvent, NSShiftKeyMask, NSCommandKeyMask
            flags = NSEvent.modifierFlags()
            return {"shift": bool(flags & NSShiftKeyMask), "cmd": bool(flags & NSCommandKeyMask)}
        except Exception:
            return {"shift": False, "cmd": False}

# Ordering within a segment (A fixed, B moved)
def order_AB_horizontal(n1, n2):
    # A = left, B = right (tie on X → lower index first)
    x1, x2 = n1.position.x, n2.position.x
    if (x1 < x2) or (x1 == x2 and node_index_in_path(n1) < node_index_in_path(n2)):
        return n1, n2
    return n2, n1

def order_AB_vertical(n1, n2):
    # A = lower, B = upper (tie on Y → lower index first)
    y1, y2 = n1.position.y, n2.position.y
    if (y1 < y2) or (y1 == y2 and node_index_in_path(n1) < node_index_in_path(n2)):
        return n1, n2
    return n2, n1

# ---------- Pair choice (robust) ----------

def classify_orientation(angle_rad):
    """Return 'H' if more horizontal, 'V' if more vertical."""
    return 'H' if abs(math.cos(angle_rad)) >= abs(math.sin(angle_rad)) else 'V'

def find_disjoint_pairs(segs):
    """All pairs of segments that do NOT share nodes."""
    pairs = []
    for i in range(len(segs)):
        for j in range(i+1, len(segs)):
            if seg_nodes_set(segs[i]).isdisjoint(seg_nodes_set(segs[j])):
                pairs.append((segs[i], segs[j]))
    return pairs

def pick_pair(segs, prefer_vertical=False):
    """
    Choose best two segments to parallelize:
    1) Prefer disjoint pairs (ignores connecting segment, e.g., the L's vertical).
    2) Among disjoint pairs, prefer orientation (H default, ⇧→V).
    3) If multiple, pick the pair whose two angles are closest (most parallel).
    4) If no disjoint pair, fall back to any two with smallest angle difference.
    """
    want = 'V' if prefer_vertical else 'H'
    disjoint = find_disjoint_pairs(segs)

    def angle(seg):
        a, b = seg
        return angle_between(a, b)

    def angle_diff(a1, a2):
        d = abs((a1 - a2 + math.pi) % (2*math.pi) - math.pi)
        return d

    # 1+2: disjoint + desired orientation
    candidates = []
    for s1, s2 in disjoint:
        a1, a2 = angle(s1), angle(s2)
        ori1, ori2 = classify_orientation(a1), classify_orientation(a2)
        if ori1 == want and ori2 == want:
            candidates.append(((s1, s2), angle_diff(a1, a2)))

    if candidates:
        candidates.sort(key=lambda x: x[1])
        return candidates[0][0], want

    # 3: any disjoint pair with smallest angle difference
    if disjoint:
        best = min(disjoint, key=lambda p: angle_diff(angle(p[0]), angle(p[1])))
        # Decide orientation from first segment
        ori = classify_orientation(angle(best[0]))
        return best, ori

    # 4: fallback: pick any two segments closest in angle (even if sharing a node)
    if len(segs) >= 2:
        best = None
        bestd = 1e9
        for i in range(len(segs)):
            for j in range(i+1, len(segs)):
                a1, a2 = angle(segs[i]), angle(segs[j])
                d = angle_diff(a1, a2)
                if d < bestd:
                    best = (segs[i], segs[j])
                    bestd = d
        if best:
            ori = classify_orientation(angle(best[0]))
            return best, ori

    return None, None

# ---------- Main ----------

def main():
    font = Glyphs.font
    if not font or not font.selectedLayers:
        Message("Parallelize Segment", "No layer selected.", OKButton=None); return
    layer = font.selectedLayers[0]

    oncs = selected_oncurves(layer)
    if len(oncs) < 3:
        Message("Parallelize Segment", "Select at least 3 on-curve nodes that imply the two segments you want.", OKButton=None); return

    segs = collect_selected_segments(layer)
    if len(segs) < 2:
        Message("Parallelize Segment", "Not enough segments in selection.", OKButton=None); return

    mods = modifiers()
    (seg1, seg2), ori = pick_pair(segs, prefer_vertical=mods["shift"])
    if not seg1 or not seg2:
        Message("Parallelize Segment", "Could not determine two segments to parallelize. Try selecting only the relevant nodes.", OKButton=None); 
        return

    # Orientation-specific A/B ordering and source/target choice
    if ori == 'V':
        S1A, S1B = order_AB_vertical(*seg1)
        S2A, S2B = order_AB_vertical(*seg2)
        # source = lower midpoint-Y (⌘ flips)
        m1y = (S1A.position.y + S1B.position.y) * 0.5
        m2y = (S2A.position.y + S2B.position.y) * 0.5
        flip = mods["cmd"]
        if (m1y <= m2y and not flip) or (m1y > m2y and flip):
            srcA, srcB = S1A, S1B
            dstA, dstB = S2A, S2B
        else:
            srcA, srcB = S2A, S2B
            dstA, dstB = S1A, S1B
    else:
        # Default to horizontal behavior
        S1A, S1B = order_AB_horizontal(*seg1)
        S2A, S2B = order_AB_horizontal(*seg2)
        # source = leftmost midpoint-X (⌘ flips)
        m1x = (S1A.position.x + S1B.position.x) * 0.5
        m2x = (S2A.position.x + S2B.position.x) * 0.5
        flip = mods["cmd"]
        if (m1x <= m2x and not flip) or (m1x > m2x and flip):
            srcA, srcB = S1A, S1B
            dstA, dstB = S2A, S2B
        else:
            srcA, srcB = S2A, S2B
            dstA, dstB = S1A, S1B

    # Source angle
    theta = angle_between(srcA, srcB)

    # Destination: keep A′ fixed, move B′; preserve length
    L = length_between(dstA, dstB)
    if L == 0:
        Glyphs.showNotification("Parallelize Segment", "Target segment has zero length; nothing to do."); return

    # Orientation guard: keep A→B pointing the right way for the chosen orientation
    if ori == 'V':
        by_test = dstA.position.y + math.sin(theta) * L
        if by_test < dstA.position.y:
            theta = (theta + math.pi) % (2 * math.pi)
    else:
        bx_test = dstA.position.x + math.cos(theta) * L
        if bx_test < dstA.position.x:
            theta = (theta + math.pi) % (2 * math.pi)

    # Handle rotation delta
    current_angle = angle_between(dstA, dstB)
    delta = theta - current_angle

    # Rotate handles strictly between A′ and B′ around A′
    path = dstA.parent
    nodes = path.nodes
    iA = nodes.index(dstA)
    iB = nodes.index(dstB)

    doc = font.parent
    undo = doc.undoManager()

    font.disableUpdateInterface()
    undo.beginUndoGrouping()
    try:
        newBx = dstA.position.x + math.cos(theta) * L
        newBy = dstA.position.y + math.sin(theta) * L
        dstB.position = NSPoint(newBx, newBy)

        count = len(nodes)
        for idx in forward_index_range(iA, iB, count):
            nd = nodes[idx]
            if nd.type == GSOFFCURVE:
                nd.position = rotate_point_around(nd.position, dstA.position, delta)
    finally:
        undo.endUndoGrouping()
        font.enableUpdateInterface()

    deg = (math.degrees(theta) + 360.0) % 360.0
    src_txt = ("lower" if ori == 'V' else "leftmost")
    if mods["cmd"]:
        src_txt = ("upper" if ori == 'V' else "rightmost")
    pair_txt = "Vertical" if ori == 'V' else "Horizontal"
    Glyphs.showNotification("Parallelize Segment",
        f"{pair_txt} pair | Source: {src_txt} | Angle {deg:.2f}° | A fixed, B moved")

if __name__ == "__main__":
    main()

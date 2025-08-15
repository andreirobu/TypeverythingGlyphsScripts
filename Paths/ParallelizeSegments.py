# MenuTitle: Parallelize Segment (Disconnected-safe, H default; ⇧=V, ⌘ flip)
# -*- coding: utf-8 -*-
from __future__ import division
import math
from GlyphsApp import *
from Foundation import NSPoint

# ---------- Helpers ----------
def is_oncurve(n): return isinstance(n, GSNode) and n.type != GSOFFCURVE
def node_idx(n): return n.parent.nodes.index(n)

def selected_oncurves(layer):
    return [o for o in layer.selection if isinstance(o, GSNode) and is_oncurve(o)]

def iterate_segments_on_path(path):
    """Yield segments as (oncurve_start, oncurve_end, start_index, end_index)."""
    nodes = path.nodes
    # collect indices of on-curves in order, respecting wrap
    on_idx = [i for i, nd in enumerate(nodes) if nd.type != GSOFFCURVE]
    L = len(on_idx)
    if L < 2: return
    for k in range(L):
        iA = on_idx[k]
        iB = on_idx[(k + 1) % L]
        yield (nodes[iA], nodes[iB], iA, iB)

def collect_segments(layer):
    """
    Return list of segments implied by the selection across ALL paths:
    a segment is included iff BOTH its on-curve endpoints are selected.
    """
    sel = set(selected_oncurves(layer))
    segs = []
    for path in layer.paths:
        for a, b, iA, iB in iterate_segments_on_path(path):
            if a in sel and b in sel:
                segs.append((a, b))
    return segs

def seg_nodes_set(seg): a,b = seg; return {a,b}
def angle_between(a,b): return math.atan2(b.position.y-a.position.y, b.position.x-a.position.x)
def length_between(a,b): return math.hypot(b.position.x-a.position.x, b.position.y-a.position.y)

def rotate_point_around(p, origin, delta):
    x, y = p.x-origin.x, p.y-origin.y
    c, s = math.cos(delta), math.sin(delta)
    return NSPoint(x*c - y*s + origin.x, x*s + y*c + origin.y)

def forward_index_range(i_start, i_end, count):
    i = (i_start + 1) % count
    while i != i_end:
        yield i
        i = (i + 1) % count

def modifiers():
    try:
        from AppKit import NSEvent, NSEventModifierFlagShift, NSEventModifierFlagCommand
        f = NSEvent.modifierFlags()
        return {"shift": bool(f & NSEventModifierFlagShift), "cmd": bool(f & NSEventModifierFlagCommand)}
    except Exception:
        try:
            from AppKit import NSEvent, NSShiftKeyMask, NSCommandKeyMask
            f = NSEvent.modifierFlags()
            return {"shift": bool(f & NSShiftKeyMask), "cmd": bool(f & NSCommandKeyMask)}
        except Exception:
            return {"shift": False, "cmd": False}

# A/B ordering
def order_AB_horizontal(n1,n2):
    x1,x2 = n1.position.x, n2.position.x
    if (x1 < x2) or (x1 == x2 and node_idx(n1) < node_idx(n2)): return n1,n2
    return n2,n1

def order_AB_vertical(n1,n2):
    y1,y2 = n1.position.y, n2.position.y
    if (y1 < y2) or (y1 == y2 and node_idx(n1) < node_idx(n2)): return n1,n2
    return n2,n1

def classify_orientation(theta):
    # 'H' if more horizontal, else 'V'
    return 'H' if abs(math.cos(theta)) >= abs(math.sin(theta)) else 'V'

def find_disjoint_pairs(segs):
    pairs=[]
    for i in range(len(segs)):
        for j in range(i+1,len(segs)):
            if seg_nodes_set(segs[i]).isdisjoint(seg_nodes_set(segs[j])):
                pairs.append((segs[i],segs[j]))
    return pairs

def pick_pair(segs, prefer_vertical=False):
    """Pick best two segments: prefer disjoint; prefer requested orientation; else closest angles."""
    want = 'V' if prefer_vertical else 'H'
    def ang(seg): return angle_between(seg[0], seg[1])
    def angdiff(a1,a2): return abs((a1-a2+math.pi)%(2*math.pi)-math.pi)

    disjoint = find_disjoint_pairs(segs)
    # disjoint + desired orientation
    cands=[]
    for s1,s2 in disjoint:
        a1,a2 = ang(s1), ang(s2)
        if classify_orientation(a1)==want and classify_orientation(a2)==want:
            cands.append(((s1,s2), angdiff(a1,a2)))
    if cands:
        cands.sort(key=lambda x:x[1])
        return cands[0][0], want

    # any disjoint with smallest angle gap
    if disjoint:
        best = min(disjoint, key=lambda p: angdiff(ang(p[0]), ang(p[1])))
        return best, classify_orientation(ang(best[0]))

    # fallback: any two with smallest angle gap
    if len(segs)>=2:
        best=None; bestd=1e9
        for i in range(len(segs)):
            for j in range(i+1,len(segs)):
                a1,a2 = ang(segs[i]), ang(segs[j])
                d = angdiff(a1,a2)
                if d<bestd: best=(segs[i],segs[j]); bestd=d
        if best:
            return best, classify_orientation(ang(best[0]))
    return None, None

# ---------- Main ----------
def main():
    font = Glyphs.font
    if not font or not font.selectedLayers:
        Message("Parallelize Segment","No layer selected.",OKButton=None); return
    layer = font.selectedLayers[0]

    oncs = selected_oncurves(layer)
    if len(oncs) < 3:
        Message("Parallelize Segment","Select the endpoints of the two segments (≥3 on-curve nodes).",OKButton=None); return

    segs = collect_segments(layer)
    if len(segs) < 2:
        Message("Parallelize Segment","Couldn’t infer two segments from the selection.\nTip: select both endpoints of each segment.",OKButton=None); return

    mods = modifiers()
    picked, ori = pick_pair(segs, prefer_vertical=mods["shift"])
    if not picked:
        Message("Parallelize Segment","Ambiguous selection. Try selecting only the intended endpoints.",OKButton=None); return

    (s1a,s1b), (s2a,s2b) = picked

    # Orientation-specific ordering and source/target selection
    if ori=='V':
        S1A,S1B = order_AB_vertical(s1a,s1b)
        S2A,S2B = order_AB_vertical(s2a,s2b)
        m1y = 0.5*(S1A.position.y+S1B.position.y)
        m2y = 0.5*(S2A.position.y+S2B.position.y)
        flip = mods["cmd"]
        if (m1y <= m2y and not flip) or (m1y > m2y and flip):
            srcA,srcB = S1A,S1B; dstA,dstB = S2A,S2B
        else:
            srcA,srcB = S2A,S2B; dstA,dstB = S1A,S1B
    else:
        S1A,S1B = order_AB_horizontal(s1a,s1b)
        S2A,S2B = order_AB_horizontal(s2a,s2b)
        m1x = 0.5*(S1A.position.x+S1B.position.x)
        m2x = 0.5*(S2A.position.x+S2B.position.x)
        flip = mods["cmd"]
        if (m1x <= m2x and not flip) or (m1x > m2x and flip):
            srcA,srcB = S1A,S1B; dstA,dstB = S2A,S2B
        else:
            srcA,srcB = S2A,S2B; dstA,dstB = S1A,S1B

    theta = angle_between(srcA,srcB)
    L = length_between(dstA,dstB)
    if L == 0:
        Glyphs.showNotification("Parallelize Segment","Target segment has zero length."); return

    # Keep orientation consistent
    if ori=='V':
        if (dstA.position.y + math.sin(theta)*L) < dstA.position.y:
            theta = (theta + math.pi) % (2*math.pi)
    else:
        if (dstA.position.x + math.cos(theta)*L) < dstA.position.x:
            theta = (theta + math.pi) % (2*math.pi)

    current = angle_between(dstA,dstB)
    delta = theta - current

    path = dstA.parent
    nodes = path.nodes
    iA = nodes.index(dstA)
    iB = nodes.index(dstB)

    doc = font.parent
    undo = doc.undoManager()

    font.disableUpdateInterface()
    undo.beginUndoGrouping()
    try:
        newBx = dstA.position.x + math.cos(theta)*L
        newBy = dstA.position.y + math.sin(theta)*L
        dstB.position = NSPoint(newBx, newBy)

        count = len(nodes)
        for idx in forward_index_range(iA,iB,count):
            nd = nodes[idx]
            if nd.type == GSOFFCURVE:
                nd.position = rotate_point_around(nd.position, dstA.position, delta)
    finally:
        undo.endUndoGrouping()
        font.enableUpdateInterface()

    deg = (math.degrees(theta)+360.0)%360.0
    pair_txt = "Vertical" if ori=='V' else "Horizontal"
    src_txt = ("upper/right" if mods["cmd"] else "lower/left") if ori=='V' else ("rightmost" if mods["cmd"] else "leftmost")
    Glyphs.showNotification("Parallelize Segment", f"{pair_txt} pair | Source: {src_txt} | {deg:.2f}° | A fixed, B moved")

if __name__ == "__main__":
    main()

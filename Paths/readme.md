Parallelize Segment for Glyphs

A Glyphs script that aligns one segment to be perfectly parallel with another while preserving the target segment’s length and curve shape.

Features
Works with connected or disconnected segments.
Automatically ignores connecting segments (e.g., vertical stem of an “L”) and finds the two disjoint segments that match your chosen orientation.
Horizontal pair (top & bottom) by default, Vertical pair (left & right) with ⇧ Shift.
Source segment = leftmost (horizontal) or lowest (vertical); hold ⌘ Command to flip.
Keeps A point fixed and moves B only, rotating handles between them to keep curve shape intact.

Instructions
Select at least 3 on-curve nodes that include the endpoints of the two segments you want to parallelize.
Example: for top & bottom horizontals of an “L”, select all four outer endpoints (top-left, top-right, bottom-left, bottom-right).

Run the script:
Normal run → parallelize the horizontal pair.
Hold ⇧ Shift → parallelize the vertical pair.
Hold ⌘ Command → swap which segment is the source in the chosen pair.
The target segment’s angle will match the source segment’s, length unchanged, handles rotated accordingly.

--

Match Italics for Glyphs

A Glyphs script that aligns a selected segment to the font’s set italic angle, keeping one point fixed and preserving the segment’s length.

Features
Reads the Italic Angle from the current font’s Info panel.
Rotates the selected segment so it exactly matches that angle.
Keeps the first point in the segment fixed, moves the second point only.
Works with straight or curved segments (off-curve handles move accordingly).

Instructions
Select exactly two consecutive on-curve nodes forming the segment you want to adjust.
Run the script:
The segment will rotate to match the font’s italic angle.
Length remains unchanged; handles rotate to maintain curve shape.

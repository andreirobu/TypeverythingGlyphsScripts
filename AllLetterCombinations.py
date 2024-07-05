# MenuTitle: All Letter Combinations
# -*- coding: utf-8 -*-
# By Andrei Robu at Typeverything.com
__doc__="""
Generates all possible two-letter combinations from a selected group of letters and opens a new tab with the continuous string result.
"""

import GlyphsApp

# Function to generate combinations
def generate_combinations(letters):
    combinations = []
    for letter1 in letters:
        for letter2 in letters:
            combinations.append(letter1 + letter2)
    return combinations

# Get the current font and selected layers
Font = Glyphs.font
selectedLayers = Font.selectedLayers

if not selectedLayers:
    Glyphs.clearLog()
    Glyphs.showMacroWindow()
    print("No letters selected. Please select some letters to generate combinations.")
else:
    # Extract the selected glyphs
    selectedGlyphs = [layer.parent for layer in selectedLayers]
    letters = []
    
    # Debug: Print selected glyph names and unicodes
    Glyphs.clearLog()
    Glyphs.showMacroWindow()
    for glyph in selectedGlyphs:
        if glyph.unicode:
            letter = chr(int(glyph.unicode, 16))
            letters.append(letter)
            print(f"Glyph: {glyph.name}, Unicode: {glyph.unicode}, Character: {letter}")
        else:
            print(f"Glyph: {glyph.name} has no Unicode value and will be skipped.")
    
    # Generate combinations
    combinations = generate_combinations(letters)
    
    # Create a continuous string from the combinations
    continuous_string = ''.join(combinations)
    
    # Debug: Print the continuous string
    print("Continuous String:", continuous_string)
    
    # Open a new tab with the continuous string
    Font.newTab(continuous_string)

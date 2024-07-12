# MenuTitle: Match Italic Angle
# Select any bezier point or a handle and click on the script. It will move the handles or points around it to match the italic angle.
# Made by Andrei Robu at Typeverything.com
# -*- coding: utf-8 -*-
__doc__ = """
Aligns the handles of the selected point or aligns a handle and its associated point to the italic angle defined in the master settings.
"""

import math
from GlyphsApp import Glyphs, GSLayer, OFFCURVE, LINE, CURVE

def align_handles_to_italic_angle():
    font = Glyphs.font
    if not font:
        print("No font open!")
        return
    
    layer = font.selectedLayers[0]
    if not layer:
        print("No layer selected!")
        return
    
    master = layer.master
    italic_angle = master.italicAngle
    
    if italic_angle is None or italic_angle == 0:
        print("[ERROR] Italic angle not set for master %s: skipping %s %s." % (master.name, layer.parent.name, layer.name))
        return
    
    # Calculate the target angle in degrees (90 - italic_angle)
    target_angle = 90 - italic_angle
    
    # Get the selected nodes
    selected_nodes = [node for path in layer.paths for node in path.nodes if node.selected]
    
    if len(selected_nodes) not in [1, 2]:
        print("Please select exactly one on-curve point, one handle, or exactly two on-curve points to align.")
        return

    if len(selected_nodes) == 1:
        node = selected_nodes[0]

        if node.type == OFFCURVE:
            # Handle selected, align handle with its associated point
            handle = node
            if handle.prevNode and handle.prevNode.type != OFFCURVE:
                point = handle.prevNode
            elif handle.nextNode and handle.nextNode.type != OFFCURVE:
                point = handle.nextNode
            else:
                print("The selected handle does not have an associated on-curve point.")
                return
            
            dy = handle.position.y - point.position.y
            dx = dy * math.tan(math.radians(italic_angle))
            
            handle.position = (point.position.x + dx, handle.position.y)
            print("[SUCCESS] Aligned the handle in %s %s to the italic angle." % (layer.parent.name, master.name))

        elif node.type != OFFCURVE:
            fixed_node = node
            
            # Function to calculate the angle between two points
            def calculate_angle(x1, y1, x2, y2):
                dx = x2 - x1
                dy = y2 - y1
                return math.degrees(math.atan2(dy, dx))
            
            # Function to align a handle to the target angle
            def align_handle(handle, center_x, center_y, target_angle):
                handle_x = handle.position.x
                handle_y = handle.position.y
                
                delta_y = handle_y - center_y
                new_x = center_x + delta_y / math.tan(math.radians(target_angle))
                
                move_x = new_x - handle_x
                return move_x, handle_x, handle_y
            
            # Adjust the upper handle first
            if fixed_node.type == CURVE:
                upper_handle = None
                lower_handle = None
                
                if fixed_node.prevNode.position.y > fixed_node.position.y:
                    upper_handle = fixed_node.prevNode
                elif fixed_node.nextNode.position.y > fixed_node.position.y:
                    upper_handle = fixed_node.nextNode
                
                if fixed_node.prevNode.position.y < fixed_node.position.y:
                    lower_handle = fixed_node.prevNode
                elif fixed_node.nextNode.position.y < fixed_node.position.y:
                    lower_handle = fixed_node.nextNode
                
                move_x = 0
                upper_handle_x = 0
                upper_handle_y = 0
                if upper_handle and upper_handle.type == OFFCURVE:
                    move_x, upper_handle_x, upper_handle_y = align_handle(upper_handle, fixed_node.position.x, fixed_node.position.y, target_angle)
                
                lower_handle_x = 0
                lower_handle_y = 0
                if lower_handle and lower_handle.type == OFFCURVE:
                    lower_handle_x = lower_handle.position.x - move_x
                    lower_handle_y = lower_handle.position.y
                
                # Apply the movements simultaneously
                if upper_handle and upper_handle.type == OFFCURVE:
                    upper_handle.position = (upper_handle_x + move_x, upper_handle_y)
                if lower_handle and lower_handle.type == OFFCURVE:
                    lower_handle.position = (lower_handle_x, lower_handle_y)
            
            print("[SUCCESS] Aligned handles of the selected point in %s %s to the italic angle." % (layer.parent.name, master.name))

    elif len(selected_nodes) == 2:
        point1, point2 = selected_nodes
        if point1.nextNode == point2 or point1.prevNode == point2:
            # Calculate the vertical distance and the horizontal shift
            dy = abs(point2.position.y - point1.position.y)
            dx = dy * math.tan(math.radians(italic_angle))
            
            # Adjust the x-coordinate of the higher point
            if point2.position.y > point1.position.y:
                point2.position = (point1.position.x + dx, point2.position.y)
            else:
                point1.position = (point2.position.x + dx, point1.position.y)
                
            print("[SUCCESS] Aligned the selected line segment in %s %s to the italic angle." % (layer.parent.name, master.name))
        else:
            print("The selected points must form a straight line without any handles.")
        
if __name__ == "__main__":
    align_handles_to_italic_angle()

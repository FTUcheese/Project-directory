from solid import *
from solid.utils import *

def piston(radius=40, height=100, crown_height=20):
    crown = translate([0, 0, height])(cylinder(r=radius, h=crown_height))
    skirt = cylinder(r=radius*0.95, h=height)
    return union()(skirt, crown)

def connecting_rod(length=150, big_end_radius=30, small_end_radius=15):
    rod = hull()(translate([0, 0, 0])(cylinder(r=big_end_radius, h=20)),
                 translate([0, 0, length])(cylinder(r=small_end_radius, h=20)))
    return rod

def crankshaft(length=600, main_journal_radius=25, crank_journal_radius=20, crank_throw=50):
    main_journal = cylinder(r=main_journal_radius, h=length)
    counterweights = []
    for i in range(5):
        pos = i * (length / 5) + (length / 10)
        cw = translate([0, crank_throw, pos])(cylinder(r=crank_journal_radius, h=20))
        counterweights.append(cw)
    return union()(main_journal, *counterweights)

def cylinder_bank(angle=60, rows=1, cols=5, spacing=120, bore_radius=40, bore_height=100):
    bank = []
    for row in range(rows):
        for col in range(cols):
            x = col * spacing
            y = row * spacing
            piston_pos = translate([x, y, 0])(piston(bore_radius, bore_height))
            rod_pos = translate([x, y, -bore_height])(connecting_rod())
            bank.append(piston_pos)
            bank.append(rod_pos)
    return rotate([angle, 0, 0])(union()(bank))

def v10_engine():
    bank1 = cylinder_bank(angle=60)
    bank2 = mirror([0, 1, 0])(cylinder_bank(angle=60))
    crank = translate([0, 0, -200])(crankshaft())
    return union()(bank1, bank2, crank)

if __name__ == '__main__':
    scad_render_to_file(v10_engine(), 'v10_engine_detailed.scad')
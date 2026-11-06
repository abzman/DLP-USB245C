#!/usr/bin/env python3
"""Independent check: parse generated KiCad files, rebuild connectivity from geometry, compare to datasheets."""
import sys, json, re, os, glob

def tokenize(s):
    i, n = 0, len(s)
    while i < n:
        c = s[i]
        if c in " \t\r\n": i += 1
        elif c in "()": yield c; i += 1
        elif c == '"':
            j = i + 1; buf = []
            while s[j] != '"':
                if s[j] == "\\": j += 1
                buf.append(s[j]); j += 1
            yield ("S", "".join(buf)); i = j + 1
        else:
            j = i
            while j < n and s[j] not in ' \t\r\n()"': j += 1
            yield s[i:j]; i = j

def parse(s):
    stack = [[]]
    for t in tokenize(s):
        if t == "(": stack.append([])
        elif t == ")":
            x = stack.pop(); stack[-1].append(x)
        else:
            stack[-1].append(t[1] if isinstance(t, tuple) else t)
    assert len(stack) == 1, "unbalanced parens"
    assert len(stack[0]) == 1, "multiple top-level forms"
    return stack[0][0]

def kids(node, name):
    return [c for c in node if isinstance(c, list) and c and c[0] == name]

def kid(node, name):
    k = kids(node, name); return k[0] if k else None

d = sys.argv[1]
for path in glob.glob(os.path.join(d, "**", "*"), recursive=True):
    if path.endswith((".kicad_sch", ".kicad_pcb", ".kicad_sym", ".kicad_mod")) or path.endswith("lib-table"):
        parse(open(path).read())
print("syntax: all s-expression files parse")

sch = parse(open(os.path.join(d, "DLP-USB245C.kicad_sch")).read())
libs = {}
for s in kid(sch, "lib_symbols")[1:]:
    pins = []
    for sub in kids(s, "symbol"):
        for p in kids(sub, "pin"):
            at = kid(p, "at"); num = kid(p, "number")[1]
            pins.append((num, float(at[1]), float(at[2])))
    libs[s[1]] = pins

R = lambda v: round(v, 3)
labels = {}
for l in kids(sch, "label"):
    at = kid(l, "at"); labels.setdefault((R(float(at[1])), R(float(at[2]))), []).append(l[1])
ncs = {(R(float(kid(n, "at")[1])), R(float(kid(n, "at")[2]))) for n in kids(sch, "no_connect")}

nets = {}; problems = 0; refs = {}
for s in kids(sch, "symbol"):
    lid = kid(s, "lib_id")[1]; at = kid(s, "at")
    X, Y, rot = float(at[1]), float(at[2]), float(at[3])
    assert rot == 0
    ref = [p[2] for p in kids(s, "property") if p[1] == "Reference"][0]
    refs[ref] = lid
    for num, px, py in libs[lid]:
        pt = (R(X + px), R(Y - py))
        here = labels.get(pt, [])
        if pt in ncs and here:
            print("BOTH label and NC at", ref, num); problems += 1
        elif pt in ncs:
            nets.setdefault("<NC>", []).append(f"{ref}.{num}")
        elif len(here) == 1:
            nets.setdefault(here[0], []).append(f"{ref}.{num}")
        else:
            print("pin with", len(here), "labels:", ref, num, here); problems += 1
# every label/NC must sit on a pin
used = set()
for s in kids(sch, "symbol"):
    at = kid(s, "at"); X, Y = float(at[1]), float(at[2])
    for num, px, py in libs[kid(s, "lib_id")[1]]:
        used.add((R(X + px), R(Y - py)))
for pt in list(labels) + list(ncs):
    if pt not in used:
        print("dangling label/NC at", pt); problems += 1

exp = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "expected_nets.json")))["nets"]
for n, m in exp.items():
    if sorted(nets.get(n, [])) != sorted(f"{r}.{p}" for r, p in m):
        print("net mismatch", n); problems += 1

# ---- datasheet cross-checks (typed independently of generator) ----
# DLP-USB245M Table 1 (pin -> function), mapped to expected net
dlp = {1:"GND(BOARD ID low)",2:"GND",3:"RESET#",4:"RESETO#",5:"GND",6:"3V3",7:"GND",8:"SLEEP",
       9:"<NC>",10:"VCCIO",11:"EXTVCC",12:"PORTVCC",13:"RXF#",14:"TXE#",15:"WR",16:"RD#",
       17:"D7",18:"D6",19:"D5",20:"D4",21:"D3",22:"D2",23:"D1",24:"D0"}
# FT245R SSOP-28 datasheet pin table
ft = {1:"D0",2:"D4",3:"D2",4:"VCCIO",5:"D1",6:"D7",7:"GND",8:"<NC>",9:"D5",10:"D6",11:"D3",
      12:"SLEEP",13:"RD#",14:"WR",15:"USB_DP",16:"USB_DM",17:"3V3",18:"GND",19:"RESET#",20:"VCC",
      21:"GND",22:"TXE#",23:"RXF#",24:"<NC>",25:"GND",26:"GND",27:"<NC>",28:"<NC>"}
where = {m: n for n, ms in nets.items() for m in ms}
for pin, want in dlp.items():
    got = where.get(f"J1.{pin}"); want = want.split("(")[0]
    if got != want: print("J1 pin", pin, "is", got, "expected", want); problems += 1
for pin, want in ft.items():
    got = where.get(f"U1.{pin}")
    if got != want: print("U1 pin", pin, "is", got, "expected", want); problems += 1
# USBLC6: 1,6 = IO1 ; 3,4 = IO2 ; 2 GND ; 5 VBUS. MCP121 SOT-23: 1 RST 2 VDD 3 VSS
for pin, want in {1:"USB_DP",6:"USB_DP",3:"USB_DM",4:"USB_DM",2:"GND",5:"VBUS"}.items():
    if where.get(f"U2.{pin}") != want: print("U2", pin); problems += 1
for pin, want in {1:"RESETO#",2:"VCC",3:"GND"}.items():
    if where.get(f"U3.{pin}") != want: print("U3", pin); problems += 1

# ---- PCB: J1 footprint linked to schematic J1 symbol; pin geometry ----
pcb = parse(open(os.path.join(d, "DLP-USB245C.kicad_pcb")).read())
j1uuid = [kid(s, "uuid")[1] for s in kids(sch, "symbol")
          if [p[2] for p in kids(s, "property") if p[1] == "Reference"][0] == "J1"][0]
fpn = kids(pcb, "footprint")[0]
assert kid(fpn, "path")[1] == "/" + j1uuid, "J1 path link broken"
pads = {int(p[1]): (float(kid(p, "at")[1]), float(kid(p, "at")[2])) for p in kids(fpn, "pad")}
assert len(pads) == 24
assert pads[1] == (0, 0) and pads[12] == (0, 27.94) and pads[13] == (15.24, 27.94) and pads[24] == (15.24, 0)
assert all(abs(pads[n][1] - pads[n+1][1]) - 2.54 < 1e-6 for n in range(1, 12))
edge = kids(pcb, "gr_rect")[0]
x0, y0 = map(float, kid(edge, "start")[1:]); x1, y1 = map(float, kid(edge, "end")[1:])
fx, fy = map(float, kid(fpn, "at")[1:3])
print(f"board {x1-x0:.2f} x {y1-y0:.2f} mm; pad-to-edge (center) {fx-x0:.2f} / {x1-(fx+15.24):.2f} mm")
print("nets:", len([n for n in nets if n != '<NC>']), "| NC pins:", len(nets.get('<NC>', [])), "| parts:", len(refs))
print("PROBLEMS:", problems)
sys.exit(1 if problems else 0)

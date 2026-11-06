#!/usr/bin/env python3
"""Generate the DLP-USB245C KiCad 8 project (FT245RNL + USB-C, DLP-USB245M pin-compatible)."""
import os, sys, uuid, json, csv, datetime

PROJ = "DLP-USB245C"
LIB = "DLP245C"
OUT = sys.argv[1] if len(sys.argv) > 1 else "out"
os.makedirs(os.path.join(OUT, LIB + ".pretty"), exist_ok=True)

def U():
    return str(uuid.uuid4())

def q(s):
    return '"' + str(s).replace('\\', '\\\\').replace('"', '\\"') + '"'

def f(v):
    s = f"{v:.4f}".rstrip('0').rstrip('.')
    return "0" if s in ("-0", "") else s

FONT = "(effects (font (size 1.27 1.27)))"
FONT_H = "(effects (font (size 1.27 1.27)) hide)"
G = 2.54

# ---------------------------------------------------------------- symbols
# pin: (number, name, etype, side 'L'/'R', y)
SYMS = {}

def sym(name, ref, pins, half_w, half_h, show_names=True, descr="", extra_graphics=""):
    SYMS[name] = dict(ref=ref, pins=pins, hw=half_w, hh=half_h, names=show_names,
                      descr=descr, gfx=extra_graphics)

def side_list(left, right, top_y):
    """left/right: lists of (num,name,type) top->bottom, None = gap."""
    pins = []
    for side, lst in (("L", left), ("R", right)):
        y = top_y
        for p in lst:
            if p is not None:
                pins.append((p[0], p[1], p[2], side, y))
            y -= G
    return pins

# FT245RNL, SSOP-28 (pin numbers per FT245R datasheet, identical for FT245RN)
ft_left = [("20","VCC","passive"),("4","VCCIO","passive"),("17","3V3OUT","power_out"),
           ("19","~{RESET}","input"),("15","USBDP","bidirectional"),("16","USBDM","bidirectional"),
           ("27","OSCI","input"),("28","OSCO","output"),("26","TEST","input"),
           ("25","AGND","passive"),("7","GND","passive"),("18","GND","passive"),
           ("21","GND","passive"),("8","NC","no_connect")]
ft_right = [("1","D0","bidirectional"),("5","D1","bidirectional"),("3","D2","bidirectional"),
            ("11","D3","bidirectional"),("2","D4","bidirectional"),("9","D5","bidirectional"),
            ("10","D6","bidirectional"),("6","D7","bidirectional"),("13","~{RD}","input"),
            ("14","WR","input"),("22","~{TXE}","output"),("23","~{RXF}","bidirectional"),
            ("12","~{PWREN}","output"),("24","NC","no_connect")]
sym("FT245RNL", "U", side_list(ft_left, ft_right, 6.5*G), 10.16, 7.5*G,
    descr="FTDI FT245RNL USB full-speed to 8-bit parallel FIFO, SSOP-28")

# DLP-USB245M 24-pin module edge (DIP-style numbering)
mod_left = [(str(i), n, "passive") for i, n in enumerate(
    ["BOARD_ID","GND","~{RESET}","~{RESETO}","GND","3V3OUT","GND","SLEEP",
     "SND/WUP","VCC-IO","EXTVCC","PORTVCC"], start=1)]
mod_right_bottom_up = ["~{RXF}","~{TXE}","WR","~{RD}","D7","D6","D5","D4","D3","D2","D1","D0"]
mod_right = [(str(13+i), n, "passive") for i, n in enumerate(mod_right_bottom_up)][::-1]
sym("DLP_USB245M_Module", "J", side_list(mod_left, mod_right, 5.5*G), 7.62, 6.5*G,
    descr="DLP-USB245M compatible 24-pin 0.6in DIP module pins")

# USB-C receptacle, USB 2.0, 16 pin (numbering as KiCad Connector:USB_C_Receptacle_USB2.0_16P)
usbc_r = [("A4","VBUS","passive"),("A9","VBUS","passive"),("B4","VBUS","passive"),("B9","VBUS","passive"),
          ("A5","CC1","bidirectional"),("B5","CC2","bidirectional"),
          ("A6","D+","bidirectional"),("B6","D+","bidirectional"),
          ("A7","D-","bidirectional"),("B7","D-","bidirectional"),
          ("A8","SBU1","bidirectional"),("B8","SBU2","bidirectional"),
          ("A1","GND","passive"),("A12","GND","passive"),("B1","GND","passive"),("B12","GND","passive"),
          ("S1","SHIELD","passive")]
sym("USB_C_Receptacle_USB2.0_16P", "J", side_list([], usbc_r, 8*G), 7.62, 9*G,
    descr="USB 2.0 Type-C receptacle, 16 pin")

# USBLC6-2SC6 ESD, SOT-23-6
sym("USBLC6-2SC6", "U", side_list(
    [("1","I/O1","passive"),("3","I/O2","passive"),("2","GND","passive")],
    [("6","I/O1","passive"),("4","I/O2","passive"),("5","VBUS","passive")], G), 7.62, 2*G,
    descr="ST USBLC6-2SC6 USB ESD protection, SOT-23-6")

# MCP121T-450E/TT open-drain supervisor, SOT-23-3 (1=RST 2=VDD 3=VSS)
sym("MCP121-450", "U", side_list(
    [("2","VDD","passive"),("3","VSS","passive")],
    [("1","~{RST}","open_collector")], G/2*1), 7.62, 1.5*G,
    descr="Microchip MCP121T-450E/TT 4.38V open-drain reset supervisor, 120ms, SOT-23-3")
# fix: put pins on integer grid
SYMS["MCP121-450"]["pins"] = [("2","VDD","passive","L",G/2+G/2),("3","VSS","passive","L",-G/2-G/2+0),
                              ("1","~{RST}","open_collector","R",G)]
SYMS["MCP121-450"]["pins"] = [("2","VDD","passive","L",G),("3","VSS","passive","L",-G),
                              ("1","~{RST}","open_collector","R",G)]

# 2-pin horizontal parts
two = [("1","~","passive","L",0),("2","~","passive","R",0)]
sym("R", "R", two, 2.54, 1.016, show_names=False, descr="Resistor")
sym("C", "C", two, 2.54, 1.524, show_names=False, descr="Capacitor")
sym("FerriteBead", "FB", two, 2.54, 1.016, show_names=False, descr="Ferrite bead")
sym("Polyfuse", "F", two, 2.54, 1.016, show_names=False, descr="Resettable fuse (PTC)")
sym("SolderJumper_2_Open", "JP", two, 2.54, 1.524, show_names=False, descr="Solder jumper, open by default")

PIN_X = {}  # name -> abs x of pin endpoint
def pin_end_local(sname, p):
    s = SYMS[sname]
    plen = 2.54
    x = -(s["hw"] + plen) if p[3] == "L" else (s["hw"] + plen)
    return x, p[4]

def lib_symbol_sexpr(sname, prefix):
    s = SYMS[sname]
    full = (prefix + ":" if prefix else "") + sname
    out = [f"(symbol {q(full)}"]
    if s["names"]:
        out.append("(pin_names (offset 1.016))")
    else:
        out.append("(pin_names (offset 0) hide) (pin_numbers hide)")
    out.append("(exclude_from_sim no) (in_bom yes) (on_board yes)")
    out.append(f'(property "Reference" {q(s["ref"])} (at 0 {f(s["hh"]+1.27)} 0) {FONT})')
    out.append(f'(property "Value" {q(sname)} (at 0 {f(-s["hh"]-1.27)} 0) {FONT})')
    out.append(f'(property "Footprint" "" (at 0 0 0) {FONT_H})')
    out.append(f'(property "Datasheet" "" (at 0 0 0) {FONT_H})')
    out.append(f'(property "Description" {q(s["descr"])} (at 0 0 0) {FONT_H})')
    out.append(f'(symbol {q(sname + "_0_1")} (rectangle (start {f(-s["hw"])} {f(s["hh"])}) '
               f'(end {f(s["hw"])} {f(-s["hh"])}) (stroke (width 0.254) (type default)) '
               f'(fill (type background))))')
    pins = []
    for p in s["pins"]:
        x, y = pin_end_local(sname, p)
        ang = 0 if p[3] == "L" else 180
        pins.append(f'(pin {p[2]} line (at {f(x)} {f(y)} {ang}) (length 2.54) '
                    f'(name {q(p[1])} {FONT}) (number {q(p[0])} {FONT}))')
    out.append(f'(symbol {q(sname + "_1_1")} ' + " ".join(pins) + ")")
    out.append(")")
    return "\n".join(out)

# ---------------------------------------------------------------- parts & nets
FP = {
    "FT245RNL": "Package_SO:SSOP-28_5.3x10.2mm_P0.65mm",
    "DLP_USB245M_Module": f"{LIB}:DIP24_Module_W15.24mm",
    "USB_C_Receptacle_USB2.0_16P": "Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal",
    "USBLC6-2SC6": "Package_TO_SOT_SMD:SOT-23-6",
    "MCP121-450": "Package_TO_SOT_SMD:SOT-23",
    "R": "Resistor_SMD:R_0603_1608Metric",
    "C": "Capacitor_SMD:C_0603_1608Metric",
    "FerriteBead": "Inductor_SMD:L_0603_1608Metric",
    "Polyfuse": "Fuse:Fuse_1206_3216Metric",
    "SolderJumper_2_Open": "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm",
}

# (ref, symbol, value, x, y, {pin: net or None(=NC)}, mpn, dnp, note)
NC = None
PARTS = [
 ("U1","FT245RNL","FT245RNL",127.0,93.98,
   {"20":"VCC","4":"VCCIO","17":"3V3","19":"RESET#","15":"USB_DP","16":"USB_DM",
    "27":NC,"28":NC,"26":"GND","25":"GND","7":"GND","18":"GND","21":"GND","8":NC,
    "1":"D0","5":"D1","3":"D2","11":"D3","2":"D4","9":"D5","10":"D6","6":"D7",
    "13":"RD#","14":"WR","22":"TXE#","23":"RXF#","12":"SLEEP","24":NC},
   "FTDI FT245RNL-REEL / FT245RNL-TUBE", False, "USB FIFO; internal EEPROM, oscillator and USB resistors"),
 ("J1","DLP_USB245M_Module","DLP-USB245M pins",218.44,93.98,
   {"1":"GND","2":"GND","3":"RESET#","4":"RESETO#","5":"GND","6":"3V3","7":"GND","8":"SLEEP",
    "9":NC,"10":"VCCIO","11":"EXTVCC","12":"PORTVCC","13":"RXF#","14":"TXE#","15":"WR","16":"RD#",
    "17":"D7","18":"D6","19":"D5","20":"D4","21":"D3","22":"D2","23":"D1","24":"D0"},
   "2x Samtec TS-112-T-A or generic 1x12 2.54mm male header (or turned-pin)", False,
   "Pin 1 BOARD ID tied low (= 245 variant). Pin 9 SND/WUP not available on FT245R"),
 ("J2","USB_C_Receptacle_USB2.0_16P","USB-C",43.18,73.66,
   {"A4":"VBUS","A9":"VBUS","B4":"VBUS","B9":"VBUS","A5":"CC1","B5":"CC2",
    "A6":"USB_DP","B6":"USB_DP","A7":"USB_DM","B7":"USB_DM","A8":NC,"B8":NC,
    "A1":"GND","A12":"GND","B1":"GND","B12":"GND","S1":"GND"},
   "GCT USB4105-GF-A", False, "USB 2.0 Type-C receptacle, 16P"),
 ("U2","USBLC6-2SC6","USBLC6-2SC6",43.18,121.92,
   {"1":"USB_DP","6":"USB_DP","3":"USB_DM","4":"USB_DM","2":"GND","5":"VBUS"},
   "STMicroelectronics USBLC6-2SC6", False, "ESD protection on D+/D-"),
 ("R1","R","5.1k",38.1,139.7,{"1":"CC1","2":"GND"},"5.1k 1% 0603",False,"CC1 Rd pull-down (UFP)"),
 ("R2","R","5.1k",38.1,147.32,{"1":"CC2","2":"GND"},"5.1k 1% 0603",False,"CC2 Rd pull-down (UFP)"),
 ("F1","Polyfuse","500mA PTC",38.1,157.48,{"1":"VBUS","2":"PORTVCC"},
   "Bourns MF-MSMF050-2 (or equiv. 1206 PTC, 0.5A hold)",False,"VBUS protection"),
 ("C7","C","4.7u",38.1,165.1,{"1":"PORTVCC","2":"GND"},"4.7uF 10V X5R 0603",False,"VBUS bulk (keep total <10uF)"),
 ("FB1","FerriteBead","600R@100MHz",101.6,152.4,{"1":"EXTVCC","2":"VCC"},
   "Murata BLM18PG601SN1D (or equiv.)",False,"Supply filter to FT245 VCC"),
 ("C1","C","1u",101.6,160.02,{"1":"VCC","2":"GND"},"1uF 10V X5R 0603",False,"VCC decoupling"),
 ("C2","C","100n",101.6,167.64,{"1":"VCC","2":"GND"},"100nF 16V X7R 0603",False,"VCC decoupling, at pin 20"),
 ("C3","C","100n",134.62,152.4,{"1":"VCCIO","2":"GND"},"100nF 16V X7R 0603",False,"VCCIO decoupling, at pin 4"),
 ("C4","C","100n",134.62,160.02,{"1":"3V3","2":"GND"},"100nF 16V X7R 0603",False,"3V3OUT decoupling (required)"),
 ("C5","C","47p",134.62,167.64,{"1":"USB_DP","2":"GND"},"47pF C0G 0603",True,"Optional EMI cap per FTDI ref, DNP"),
 ("C6","C","47p",134.62,175.26,{"1":"USB_DM","2":"GND"},"47pF C0G 0603",True,"Optional EMI cap per FTDI ref, DNP"),
 ("R5","R","10k",167.64,152.4,{"1":"SLEEP","2":"VCCIO"},"10k 0603",False,"PWREN# pull-up to VCCIO"),
 ("R3","R","10k",167.64,160.02,{"1":"RESETO#","2":"3V3"},"10k 0603",False,"RESETO# pull-up to 3.3V"),
 ("U3","MCP121-450","MCP121T-450E/TT",167.64,172.72,{"2":"VCC","3":"GND","1":"RESETO#"},
   "Microchip MCP121T-450E/TT",False,"Emulates RESETO#: low until VCC>4.38V +120ms, then 3.3V via R3"),
 ("JP1","SolderJumper_2_Open","PORTVCC-EXTVCC",208.28,152.4,{"1":"PORTVCC","2":"EXTVCC"},
   "PCB solder jumper",False,"Close for USB bus-powered without external strap"),
 ("JP2","SolderJumper_2_Open","EXTVCC-VCCIO",208.28,160.02,{"1":"EXTVCC","2":"VCCIO"},
   "PCB solder jumper",False,"Close for 5V I/O without external strap"),
]

# ---------------------------------------------------------------- schematic
ROOT = U()
J1_UUID = None
items = []
labels = []
ncs = []
NETS = {}

def place(ref, sname, value, X, Y, conn, dnp):
    global J1_UUID
    s = SYMS[sname]
    su = U()
    if ref == "J1":
        J1_UUID = su
    o = [f'(symbol (lib_id {q(LIB + ":" + sname)}) (at {f(X)} {f(Y)} 0) (unit 1)',
         f'(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp {"yes" if dnp else "no"})',
         f'(uuid {q(su)})',
         f'(property "Reference" {q(ref)} (at {f(X)} {f(Y - s["hh"] - 1.27)} 0) {FONT})',
         f'(property "Value" {q(value)} (at {f(X)} {f(Y + s["hh"] + 1.27)} 0) {FONT})',
         f'(property "Footprint" {q(FP[sname])} (at {f(X)} {f(Y)} 0) {FONT_H})',
         f'(property "Datasheet" "" (at {f(X)} {f(Y)} 0) {FONT_H})',
         f'(property "Description" {q(s["descr"])} (at {f(X)} {f(Y)} 0) {FONT_H})']
    for p in s["pins"]:
        o.append(f'(pin {q(p[0])} (uuid {q(U())}))')
    o.append(f'(instances (project {q(PROJ)} (path {q("/" + ROOT)} (reference {q(ref)}) (unit 1))))')
    o.append(")")
    items.append("\n".join(o))
    pinnums = {p[0] for p in s["pins"]}
    assert pinnums == set(conn.keys()), (ref, pinnums ^ set(conn.keys()))
    for p in s["pins"]:
        lx, ly = pin_end_local(sname, p)
        x, y = X + lx, Y - ly
        net = conn[p[0]]
        if net is None:
            ncs.append(f'(no_connect (at {f(x)} {f(y)}) (uuid {q(U())}))')
        else:
            NETS.setdefault(net, []).append((ref, p[0]))
            if p[3] == "L":
                labels.append(f'(label {q(net)} (at {f(x)} {f(y)} 180) (fields_autoplaced yes) '
                              f'(effects (font (size 1.27 1.27)) (justify right bottom)) (uuid {q(U())}))')
            else:
                labels.append(f'(label {q(net)} (at {f(x)} {f(y)} 0) (fields_autoplaced yes) '
                              f'(effects (font (size 1.27 1.27)) (justify left bottom)) (uuid {q(U())}))')

for (ref, sname, value, X, Y, conn, mpn, dnp, note) in PARTS:
    place(ref, sname, value, X, Y, conn, dnp)

for net, members in NETS.items():
    assert len(members) >= 2, f"net {net} has only one member: {members}"

notes = [
 (20.32, 20.32, "DLP-USB245C - USB-C, FT245RNL based, pin-compatible replacement for DLP-USB245M (24-pin, 0.6in DIP)"),
 (20.32, 25.4, "Connectivity is by net label: identical label names are the same net."),
 (20.32, 185.42, "NOTES:"),
 (20.32, 190.5, "1. J1 pin 9 (SND/WUP) has no FT245R equivalent; left unconnected. Remote wake on FT245R = strobe RXF# low >=20ms while suspended."),
 (20.32, 194.31, "2. J1 pin 4 RESETO# emulated by U3 (low until VCC>4.38V +120ms, then pulled to 3V3). Not driven by RESET# like the FT245BM."),
 (20.32, 198.12, "3. JP1/JP2 default OPEN = identical behaviour to original (user straps PORTVCC/EXTVCC/VCC-IO externally)."),
 (20.32, 201.93, "4. FT245R power pins modelled as passive to keep ERC free of PWR_FLAG noise. TEST and AGND tied to GND, OSCI/OSCO NC."),
 (20.32, 205.74, "5. Program FT245RNL EEPROM with FT_PROG: description string 'DLP-USB245M' if host software opens by description."),
]
for x, y, t in notes:
    items.append(f'(text {q(t)} (exclude_from_sim no) (at {f(x)} {f(y)} 0) '
                 f'(effects (font (size 1.27 1.27)) (justify left bottom)) (uuid {q(U())}))')

today = datetime.date.today().isoformat()
sch = [f'(kicad_sch (version 20231120) (generator "eeschema") (generator_version "8.0")',
       f'(uuid {q(ROOT)})', '(paper "A4")',
       f'(title_block (title "DLP-USB245C USB-C FIFO module") (date {q(today)}) (rev "0.1") '
       f'(comment 1 "Pin-compatible with DLP-USB245M (FT245BM/BL), based on FTDI FT245RNL") '
       f'(comment 2 "Open hardware community replacement - verify before fabrication"))',
       "(lib_symbols"]
for n in SYMS:
    sch.append(lib_symbol_sexpr(n, LIB))
sch.append(")")
sch += items + labels + ncs
sch.append('(sheet_instances (path "/" (page "1")))')
sch.append(")")
open(os.path.join(OUT, PROJ + ".kicad_sch"), "w").write("\n".join(sch) + "\n")

# symbol library
lib = ['(kicad_symbol_lib (version 20231120) (generator "kicad_symbol_editor") (generator_version "8.0")']
for n in SYMS:
    lib.append(lib_symbol_sexpr(n, None))
lib.append(")")
open(os.path.join(OUT, LIB + ".kicad_sym"), "w").write("\n".join(lib) + "\n")

# ---------------------------------------------------------------- footprint (24-pin module edge)
PITCH = 2.54
ROW = 15.24
def dip_pad_pos(n):
    if n <= 12:
        return 0.0, (n - 1) * PITCH
    return ROW, (24 - n) * PITCH

def fp_body(in_board):
    o = []
    for n in range(1, 25):
        x, y = dip_pad_pos(n)
        shape = "rect" if n == 1 else "circle"
        o.append(f'(pad {q(n)} thru_hole {shape} (at {f(x)} {f(y)}) (size 1.7 1.7) (drill 1.0) '
                 f'(layers "*.Cu" "*.Mask") (remove_unused_layers no) (uuid {q(U())}))')
    # silk pin-1 marker and outline of pin field
    o.append(f'(fp_line (start -1.2 -1.6) (end 1.2 -1.6) (stroke (width 0.15) (type solid)) (layer "F.SilkS") (uuid {q(U())}))')
    o.append(f'(fp_rect (start -1.1 -1.1) (end {f(ROW+1.1)} {f(11*PITCH+1.1)}) (stroke (width 0.1) (type solid)) (fill none) (layer "F.Fab") (uuid {q(U())}))')
    o.append(f'(fp_rect (start -1.15 -1.15) (end {f(ROW+1.15)} {f(11*PITCH+1.15)}) (stroke (width 0.05) (type solid)) (fill none) (layer "F.CrtYd") (uuid {q(U())}))')
    return o

fp = ['(footprint "DIP24_Module_W15.24mm" (version 20240108) (generator "pcbnew") (generator_version "8.0")',
      '(layer "F.Cu")',
      '(descr "DLP-USB245M module pins: 24 pins, 2.54mm pitch, 15.24mm (0.6in) row spacing, 1.0mm drill for square header pins")',
      '(tags "DIP 24 module DLP-USB245M")',
      f'(property "Reference" "REF**" (at {f(ROW/2)} -3) (layer "F.SilkS") (uuid {q(U())}) (effects (font (size 1 1) (thickness 0.15))))',
      f'(property "Value" "DIP24_Module_W15.24mm" (at {f(ROW/2)} {f(11*PITCH+3)}) (layer "F.Fab") (uuid {q(U())}) (effects (font (size 1 1) (thickness 0.15))))',
      '(attr through_hole)'] + fp_body(False) + [")"]
open(os.path.join(OUT, LIB + ".pretty", "DIP24_Module_W15.24mm.kicad_mod"), "w").write("\n".join(fp) + "\n")

# ---------------------------------------------------------------- PCB
BW, BL = 17.78, 38.10          # 0.70in x 1.50in, per DLP-USB245M outline (verify!)
P1X, P1Y = 100.0, 80.0         # pin 1 position
bx0 = P1X - (BW - ROW) / 2
by0 = P1Y - 2.54
pcb = ['(kicad_pcb (version 20240108) (generator "pcbnew") (generator_version "8.0")',
       '(general (thickness 1.6) (legacy_teardrops no))', '(paper "A4")',
       f'(title_block (title "DLP-USB245C") (date {q(today)}) (rev "0.1"))',
       '(layers (0 "F.Cu" signal) (31 "B.Cu" signal) (32 "B.Adhes" user "B.Adhesive") (33 "F.Adhes" user "F.Adhesive") '
       '(34 "B.Paste" user) (35 "F.Paste" user) (36 "B.SilkS" user "B.Silkscreen") (37 "F.SilkS" user "F.Silkscreen") '
       '(38 "B.Mask" user) (39 "F.Mask" user) (40 "Dwgs.User" user "User.Drawings") (41 "Cmts.User" user "User.Comments") '
       '(42 "Eco1.User" user "User.Eco1") (43 "Eco2.User" user "User.Eco2") (44 "Edge.Cuts" user) (45 "Margin" user) '
       '(46 "B.CrtYd" user "B.Courtyard") (47 "F.CrtYd" user "F.Courtyard") (48 "B.Fab" user) (49 "F.Fab" user))',
       '(setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no))',
       '(net 0 "")',
       f'(footprint "{LIB}:DIP24_Module_W15.24mm" (layer "F.Cu") (uuid {q(U())}) (at {f(P1X)} {f(P1Y)})',
       f'(property "Reference" "J1" (at {f(ROW/2)} 30.5 0) (layer "F.SilkS") (uuid {q(U())}) (effects (font (size 0.8 0.8) (thickness 0.12))))',
       f'(property "Value" "DLP-USB245M pins" (at {f(ROW/2)} 12 0) (layer "F.Fab") (uuid {q(U())}) (effects (font (size 1 1) (thickness 0.15))))',
       f'(path {q("/" + J1_UUID)}) (sheetname "Root") (sheetfile {q(PROJ + ".kicad_sch")})',
       '(attr through_hole)'] + fp_body(True) + [")",
       f'(gr_rect (start {f(bx0)} {f(by0)}) (end {f(bx0+BW)} {f(by0+BL)}) (stroke (width 0.1) (type default)) (fill none) (layer "Edge.Cuts") (uuid {q(U())}))',
       f'(gr_text "DLP-USB245C" (at {f(P1X+ROW/2)} {f(P1Y+4)} 90) (layer "F.SilkS") (uuid {q(U())}) (effects (font (size 1 1) (thickness 0.15))))',
       f'(gr_text "USB-C edge" (at {f(P1X+ROW/2)} {f(by0+BL-1)} 0) (layer "Cmts.User") (uuid {q(U())}) (effects (font (size 0.8 0.8) (thickness 0.1))))',
       ")"]
open(os.path.join(OUT, PROJ + ".kicad_pcb"), "w").write("\n".join(pcb) + "\n")

# ---------------------------------------------------------------- project & lib tables
pro = {"meta": {"filename": PROJ + ".kicad_pro", "version": 1},
       "board": {"design_settings": {"rules": {"min_clearance": 0.15, "min_track_width": 0.15,
                 "min_via_diameter": 0.5, "min_through_hole_diameter": 0.3}}},
       "net_settings": {"classes": [{"name": "Default", "clearance": 0.15, "track_width": 0.2,
                         "via_diameter": 0.6, "via_drill": 0.3,
                         "diff_pair_width": 0.2, "diff_pair_gap": 0.2}], "meta": {"version": 3}},
       "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
       "sheets": [[ROOT, "Root"]], "text_variables": {}}
json.dump(pro, open(os.path.join(OUT, PROJ + ".kicad_pro"), "w"), indent=2)
open(os.path.join(OUT, "sym-lib-table"), "w").write(
    f'(sym_lib_table (version 7)\n  (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.kicad_sym")(options "")(descr "DLP-USB245C project symbols"))\n)\n')
open(os.path.join(OUT, "fp-lib-table"), "w").write(
    f'(fp_lib_table (version 7)\n  (lib (name "{LIB}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIB}.pretty")(options "")(descr "DLP-USB245C project footprints"))\n)\n')

# ---------------------------------------------------------------- BOM & netlist
with open(os.path.join(OUT, "BOM.csv"), "w", newline="") as fh:
    w = csv.writer(fh)
    w.writerow(["Ref", "Value", "Footprint", "Manufacturer part (suggested)", "Populate", "Note"])
    for (ref, sname, value, X, Y, conn, mpn, dnp, note) in PARTS:
        w.writerow([ref, value, FP[sname], mpn, "DNP" if dnp else "Yes", note])
with open(os.path.join(OUT, "netlist_check.txt"), "w") as fh:
    for net in sorted(NETS):
        fh.write(f"{net:10s} " + " ".join(f"{r}.{p}" for r, p in sorted(NETS[net])) + "\n")
json.dump({"nets": NETS}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "expected_nets.json"), "w"))
print("ok", len(PARTS), "parts", len(NETS), "nets")

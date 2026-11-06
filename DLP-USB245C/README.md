# DLP-USB245C

A USB-C, FT245RNL-based module that fits the 24-pin, 0.6" DIP footprint of the DLP-USB245M (FT245BM/BL). Revision 0.1 is a draft: schematic done, PCB outline and pins placed, nothing routed yet.

## Contents
| File | What it is |
|---|---|
| `DLP-USB245C.kicad_pro` | Project file (KiCad 8 or newer) |
| `DLP-USB245C.kicad_sch` | Schematic. Parts connect through net labels: labels with the same name are the same net. |
| `DLP-USB245C.kicad_pcb` | 2-layer board, 17.78 × 38.10 mm. The 24 module pins are already placed and linked to J1. |
| `DLP245C.kicad_sym`, `DLP245C.pretty/` | Project symbols, plus the module-pin footprint (1.0 mm drill) |
| `sym-lib-table`, `fp-lib-table` | Point KiCad at the project libraries |
| `BOM.csv` | Parts list with suggested manufacturer part numbers. DNP marks parts left unpopulated. |
| `netlist_check.txt` | Every net with its members, for review |

## Finishing the board
1. Open the `.kicad_pro` file and run ERC in the schematic.
2. In the PCB editor, run **Tools → Update PCB from Schematic (F8)**. This pulls the rest of the footprints from KiCad's standard libraries, and J1 stays where it is.
3. Place the parts. USB-C (J2) goes on the edge at the pin 12/13 end. The FT245RNL fits between the pin rows on the top side, and the passives can go on the bottom.
4. Route D+/D- as a 90 Ω differential pair, add a GND pour on both layers, then run DRC.

## Pin mapping (module pin → FT245RNL)
| Module pin | Signal | Connection |
|---|---|---|
| 1 | BOARD ID | GND (low means the 245 variant) |
| 2, 5, 7 | GND | GND |
| 3 | RESET# | U1 pin 19 |
| 4 | RESETO# | U3 MCP121 open-drain output, with R3 pull-up to 3V3 (see note 2) |
| 6 | 3V3OUT | U1 pin 17 (up to 50 mA) |
| 8 | SLEEP | U1 pin 12 PWREN#, with R5 10k pull-up to VCCIO |
| 9 | SND/WUP | **Not connected** (see note 1) |
| 10 | VCC-IO | U1 pin 4 (1.8 to 5.25 V) |
| 11 | EXTVCC | Through FB1 to U1 pin 20 VCC |
| 12 | PORTVCC | USB-C VBUS through F1 (500 mA PTC) |
| 13–16 | RXF#, TXE#, WR, RD# | U1 pins 23, 22, 14, 13 |
| 17–24 | D7…D0 | U1 pins 6, 10, 9, 2, 11, 3, 5, 1 |

## Differences from the original
1. **SND/WUP (pin 9):** the FT245R has no SI/WU pin, so the send-immediate function is not available. For remote wake, the FT245R uses RXF#: strobe it low for at least 20 ms while the bus is suspended.
2. **RESETO# (pin 4):** this is emulated by U3. It stays low until VCC rises above 4.38 V, then releases 120 ms later and is pulled up to 3.3 V. Unlike the FT245BM, the RESET# input does not drive it.
3. **Buffers:** the FIFO sizes differ from the FT245BM. Code that only uses the TXE#/RXF# handshake is unaffected.
4. **Jumpers:** JP1 (PORTVCC↔EXTVCC) and JP2 (EXTVCC↔VCC-IO) are open by default, so the board behaves exactly like the original. Close them to run a bus-powered 5 V setup without wiring straps on the host board.
5. **USB identity:** the default VID/PID is 0403:6001, the same as the FT245BM. If host software opens the device by description, set the description string with FT_PROG.

## Check before fabrication
- None of these files has been opened in KiCad yet. If anything fails to load, re-save from KiCad.
- Check that the stock footprint names in the BOM exist in your KiCad version. In particular, check that the GCT USB4105 footprint's pad names match the symbol pins A1…B12 and S1.
- The 17.78 × 38.10 mm (0.70" × 1.50") outline comes from DLP's *preliminary* drawing. Measure a real module with calipers, including which end the USB jack sits on.
- Read FTDI's "Migrating from FT2xxR to FT2xxRN" app note and the RN errata.

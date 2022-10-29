#!/usr/env python3

import colorsys

data = [
"00048000000d0e0b3b230000000000000032000090",
"00058000000d0e0b3ba13c646400000000000000e0",
"00068000000d0e0b3ba13c643400000000000000b0",
"00078000000d0e0b3ba13c64180000000000000094",
"00088000000d0e0b3ba13c6400000000000000007c",
"00098000000d0e0b3ba13c646400000000000000e0",
"000a8000000d0e0b3ba100646400000000000000a4",
"000b8000000d0e0b3ba1786464000000000000001c"
]

for line in data:
    hue = line[20:22]
    sat = line[22:24]
    bri = line[24:26]
    #print("Hue: " + hue + " Sat: " + sat + " Bri: " + bri)
    # Convert to decimal
    hued = int(hue, 16)
    hued = hued * 2
    satd = int(sat, 16)
    brid = int(bri, 16)
    #print("Hued: " + str(hued) + " Satd: " + str(satd) + " Brid: " + str(brid))
    #print(str(hued)+','+str(satd)+','+str(brid))
    # Convert to RGB
    
    rgb = colorsys.hsv_to_rgb(hued/360.0, satd/100.0,brid/100.0)
    #print("RGB: " + str(rgb))
    rgb = [int(x*255) for x in rgb]
    print("RGB: " + str(rgb))
    #print(rgb)



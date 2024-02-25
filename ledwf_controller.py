#!/bin/env python3

# A very basic bit of Python to let us play with the LEDnetWF devices a bit more easily.
# This is a means to an end and is not intended to be a complete solution.

from operator import contains
import sys
import colorsys
import simplepyble
import time


SERVICE_UUID = "0000ffff-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID  = "0000ff02-0000-1000-8000-00805f9b34fb"
WRITE_UUID   = "0000ff01-0000-1000-8000-00805f9b34fb"
COUNTER      = 0
PIXEL_COUNT  = 48 # TODO: where does this come from?  We must be able to read it from the device


# The control "packets" vary in size and content depending on the command.  The first two bytes
# seem to be a counter that increments with each packet.  The last two bytes are a checksum.
# However, the counter and checksum are seemingly ignored by the device, so you don't need to worry
# about them.  However, I am keeping a packet counter in this script just in case it makes a difference.
# There is a common "header" that is used for all packets. This is 80 00 00 and comes after the counter.

# checksum is the last byte of the packet
# general data area here ----------------------------------------V
# 0b seems to be for colour and mode stuff, 0a is "other" -------v
# length of packet from here to the end including checksum ---V (fun fact, copilot worked this out for me)
# one less than the length above ? ------------------------v  |  |
# standard header --------------------------------v--v--v  |  |  |
# counter ----------------------------------v--v  |  |  |  |  |  |
INITIAL_PACKET         = bytearray.fromhex("00 01 80 00 00 04 05 0a 81 8a 8b 96")
INITIAL_PACKET_2       = bytearray.fromhex("00 02 80 00 00 0c 0d 0b 10 14 16 0b 05 0d 36 36 06 00 0f d8")
UNKNOWN_STATE_CHANGE   = bytearray.fromhex("00 45 80 00 00 05 06 0a 22 2a 2b 0f 86")
UNKNOWN_STATE_CHANGE_2 = bytearray.fromhex("00 46 80 00 00 05 06 0a 11 1a 1b 0f 55")
ON_PACKET              = bytearray.fromhex("00 04 80 00 00 0d 0e 0b 3b 23 00 00 00 00 00 00 00 32 00 00 90")
OFF_PACKET             = bytearray.fromhex("00 5b 80 00 00 0d 0e 0b 3b 24 00 00 00 00 00 00 00 32 00 00 91")


# == Simple colour handling ==
# checksum ---------------------------------------------------------------------------------------------v
# White temperature and brightness ------------------------------------------------v--v                 |
# HSV colour data --------------------------------------------------------v--v--v  |  |                 |
# ?                      ----------------------------------------v        |     |  |  |                 |
# length of packet from here to the end including checksum ---V  |        |     |  |  |                 |
# length of packet from here without the checksum? --------v  |  |        |     |  |  |                 |
# standard header --------------------------------v--v--v  |  |  |        |     |  |  |                 |
# counter ----------------------------------v--v  |  |  |  |  |  |        |     |  |  |                 |
HSV_PACKET             = bytearray.fromhex('00 05 80 00 00 0d 0e 0b 3b a1 00 64 64 00 00 00 00 00 00 00 00') # 10, 11, 12
WHITE_PACKET           = bytearray.fromhex("00 10 80 00 00 0d 0e 0b 3b b1 00 00 00 1b 36 00 00 00 00 00 3d") # 13 & 14 

# == Symphony Modes / effects ==

# Brightness 1 - 100 ---------------------------------------------v
# Speed 1 - 100 -----------------------------------------------v  |
# effect number (1 - 113) ----------------------------------v  |  |
# ? --------------------------------------------------v--v  |  |  |
# length of packets from here to the end ----------v  |  |  |  |  |
# length of packets minus 1 --------------------v  |  |  |  |  |  |
# Standard header ---------------------v--v--v  |  |  |  |  |  |  |
# counter -----------------------v--v  |  |  |  |  |  |  |  |  |  |
MODE_PACKET = bytearray.fromhex("00 06 80 00 00 04 05 0b 38 01 01 64")

# == Smear mode ==
# checksum? ----------------------------------------------------------------------------------------------------------------------v
# direction 0 or 1 for mode "stream" 2-----------------------------------------------------------------------------------------v  |
# Brightness 0% - 100% -----------------------------------------------------------------------------------------------------v  |  |
# Speed 0% - 100% ------------------------------------------------------------------------------------------------------ v  |  |  |
# Mode. 1 = static, 2 = stream (check direction also) 3 = strobe  4 = jump  ------------------------------------------v  |  |  |  |
# pixel by pixel RGB data 3 bytes * 48 pixels = 144 bytes ------------------------------v---------------------------v |  |  |  |  |
# Length of packet from next byte to the end ----------------------------------v        |                           | |  |  |  |  |
# Length of the packet without the checksum? -------------------------------v  |        |                           | |  |  |  |  |
# more fixed header stuff -----------------------------------------v--v--v  |  |        |                           | |  |  |  |  |
# counter ---------------------------------------------------v--v  |  |  |  |  |        |                           | |  |  |  |  |
#                                                            |  |  |  |  |  |  |        |                           | |  |  |  |  |
#                                                            00 10 80 00 00 96 97 0b 59 000000 ...[deleted]... 000000 02 64 64 00 23


# Response data
# checksum - checksum is add all the bytes except the checksum AND 0xFF ----------v
# I thought this might be LED count, but maybe not ----------------------------v  |
# unknown data ----------------------------------------------------------v--v  |  |
# white temperature --------------------------------------------------v  |  |  |  |
# blue ------------------------------------------------------------v  |  |  |  |  |
# green --------------------------------------------------------v  |  |  |  |  |  |
# red -------------------------------------------------------v  |  |  |  |  |  |  |
# brightness ---------------------------------------------v  |  |  |  |  |  |  |  |
# guess mode ------------------------------------------v  |  |  |  |  |  |  |  |  |
# unknown ------------------------------------------v  |  |  |  |  |  |  |  |  |  |
# off = 24, on = 23 -----------------------------v  |  |  |  |  |  |  |  |  |  |  |
# fixed -----------------------------------v--v  |  |  |  |  |  |  |  |  |  |  |  |
#                                          81 1D 24 24 02 00 64 32 FF 00 02 00 30 AF
#                                          81 1D 23 61 0F 31 64 32 FF 64 02 00 30 8D
#                                          81 1D 23 61 0F 31 64 32 FF 00 02 00 30 29
#                                          81 1D 23 61 F0 00 FF 00 00 00 02 00 30 43
#                                          81 1D 23 61 F0 00 00 FF 00 00 02 00 30 43
#                                          81 1D 23 61 F0 00 00 00 FF 00 02 00 30 43
#                                          81 1D 23 25 01 00 64 32 FF 00 02 00 30 AE
#                                          81 1D 23 25 02 00 64 32 FF 00 02 00 30 AF
#                                          81 1D 23 25 03 00 64 32 FF 00 02 00 30 B0
#                                          81 1D 23 25 04 00 64 32 FF 00 02 00 30 B1
#                                          81 1D 23 25 05 00 64 32 FF 00 02 00 30 B2

def logger(message):
    print(message)

def get_counter():
    global COUNTER
    COUNTER += 1
    return COUNTER

def prepare_packet(packet):
    # Could add the 80 00 00 header here too
    # For now this just adds the counter to the first two
    # bytes of the packet.  As we have seen this doesn't seem to be 
    # necessary though.  So we could skip this step.
    count = get_counter()
    packet[0] = 0xFF00 & count
    packet[1] = 0x00FF & count
    return packet

def send_prepared_packet(peripheral, packet):
    peripheral.write_request(SERVICE_UUID, WRITE_UUID, bytes(packet))

def send_initial_packet(peripheral):
    # This doesnt seem to make any difference, but it does generate a notification
    # which we might be able to use to find the current status
    initial_packet = INITIAL_PACKET
    initial_packet = prepare_packet(initial_packet)
    peripheral.write_request(SERVICE_UUID, WRITE_UUID, bytes(initial_packet))

def send_initial_packet2(peripheral):
    # This doesnt seem to make any difference, but it does generate a notification
    # which we might be able to use to find the current status
    initial_packet = INITIAL_PACKET_2
    initial_packet = prepare_packet(initial_packet)
    peripheral.write_request(SERVICE_UUID, WRITE_UUID, bytes(initial_packet))

def set_white(peripheral, temperature, brightness):
    "Set colour temperature (0-100% warm to cool) and brightness (0-100%)"
    # Pass in the peripheral object and the colour quality
    # Colour temperature is from 0 warm to 100 cool
    # Brightness is from 0 to 100
    if brightness > 100: brightness = 100
    if temperature > 100: temperature = 100
    print(f"Setting white temperature to {temperature}% and {brightness}% brightness")
    white_packet = WHITE_PACKET
    white_packet[13] = temperature
    white_packet[14] = brightness
    peripheral.write_request(SERVICE_UUID, WRITE_UUID, bytes(white_packet))

def rgb_to_hsv(r,g,b):
    h, s, v = colorsys.rgb_to_hsv(r/255.0,g/255.0,b/255.0)
    h, s, v = int(h*360), int(s*100), int(v*100)
    h = int(h/2)
    return [h,s,v]

def set_rgb(peripheral, r, g, b):
    logger(f"Setting RGB colour: {r}, {g}, {b}")
    hsv = rgb_to_hsv(r,g,b)
    hsv_packet = prepare_packet(HSV_PACKET)
    hsv_packet[10] = hsv[0]
    hsv_packet[11] = hsv[1]
    hsv_packet[12] = hsv[2]
    peripheral.write_request(SERVICE_UUID, WRITE_UUID, bytes(hsv_packet))  

def set_power(peripheral, power):
    if power:
        packet = prepare_packet(ON_PACKET)
    else:
        packet = prepare_packet(OFF_PACKET)
    peripheral.write_request(SERVICE_UUID, WRITE_UUID, bytes(packet))

def build_smear_packet():
    # Might be useful to make this a class, so you can fiddle the mode without rebuilding the whole packet?
    "Builds an empty smear packet.  Still needs to be filled with the colour data and mode/speed/brightness"
    global PIXEL_COUNT
    smear_packet = bytearray.fromhex("00 00")
    count = get_counter()
    smear_packet[0] = (0xFF00 & count)
    smear_packet[1] = (0x00FF & count)
    smear_packet.extend([0x80, 0x00, 0x00])
    smear_packet.extend([0x96, 0x97]) # this is the length stuff, which for smear packets on my device is 48 pixels plus the other bits. 
    smear_packet.extend([0x0b, 0x59]) # not sure what this is yet
    for i in range(PIXEL_COUNT):
        smear_packet.extend([0x00, 0x00, 0x00]) # this is the rgb colour data.
    smear_packet.extend([0x01, 0x64, 0x64, 0x00, 0x23])
    return smear_packet

def test_smear_pattern(packet):
    "Pass in a built packet, and we will add a colour gradient and make is spin medium speed"
    global PIXEL_COUNT
    mode_byte       = 153
    speed_byte      = 154
    brightness_byte = 155
    direction_byte  = 156
    start_byte = 9
    h = 1
    colour_divisions = int(360 / PIXEL_COUNT)
    for i in range(PIXEL_COUNT):
        rgb = colorsys.hsv_to_rgb(h/360.0, 1, 1)
        packet[start_byte]   = int(rgb[0] * 255)
        packet[start_byte+1] = int(rgb[1] * 255)
        packet[start_byte+2] = int(rgb[2] * 255)
        start_byte += 3
        h += colour_divisions
    packet[mode_byte] = 2
    packet[speed_byte] = 50
    packet[brightness_byte] = 100
    packet[direction_byte] = 1
    #print(f"Sending smear packet: {packet.hex()}")
    return packet

def set_mode(peripheral, mode, speed, brightness):
    "Modes are numbered 1 to 113."
    mode_packet = MODE_PACKET
    count = get_counter()
    mode_packet[0]  = (0xFF00 & count)
    mode_packet[1]  = (0x00FF & count)
    mode_packet[9]  = mode
    mode_packet[10] = speed
    mode_packet[11] = brightness
    peripheral.write_request(SERVICE_UUID, WRITE_UUID, bytes(mode_packet))

def connect_to_device(mac_addr):
    print("Connecting to device" + mac_addr)
    lednetwf_device = Peripheral(mac_addr)
    services = lednetwf_device.getServices()
    for service in services:
        print(service)
        characteristics = service.getCharacteristics()  
        for characteristic in characteristics:
            print(characteristic)
        descriptors = service.getDescriptors()
        for descriptor in descriptors:
            print(descriptor)
    return lednetwf_device

def find_devices():
    lednetwfs = {}
    scanner = Scanner().withDelegate(ScanDelegate())
    devices = scanner.scan(10.0)
    for dev in devices:
        for (adtype, desc, value) in dev.getScanData():
            if desc == "Complete Local Name" and value.startswith("LEDnetWF"):
                    print("Found device: %s (%s), RSSI=%d dB" % (dev.addr, value, dev.rssi))
                    lednetwfs[dev.addr] = dev.rssi

    if len(lednetwfs) > 0:
        lednetwfs = dict(sorted(lednetwfs.items(), key=lambda item: item[1], reverse=True))
        print("\n\n")
        for key, value in lednetwfs.items():
            print(f"Device: {key}, RSSI: {value}")
    else:
        print("No devices found")

def response_decode(response):
    print("Got a response")
    #print(f"Response: {response.hex()}")
    response_str = response.decode("utf-8", errors="ignore")
    last_quote = response_str.rfind('"')
    if last_quote > 0:
        first_quote = response_str.rfind('"', 0, last_quote)
        if first_quote > 0:
            payload = response_str[first_quote+1:last_quote]
        else:
            return None
    else:
        return None
    
    print(f"Payload: {payload}")
    response = bytearray.fromhex(payload)
    power = response[2]
    if power == 0x23:
        print("Power: ON")
    elif power == 0x24:
        print("Power: OFF")

    mode = response[4]

    if mode == 0xF0:
        # RGB mode
        r,g,b = response[6], response[7], response[8]
        print(f"RGB: {r}, {g}, {b}")
    elif mode == 0x0F:
        # White mode
        temp, brightness = response[9], response[5]
        print(f"White Temperature: {temp}, Brightness: {brightness}")
    elif mode > 0x0 and mode < 0x72:
        # Symphony modes
        print(f"Symphony Mode: {mode}")
        brightness = response[6]
        speed = response[7]
        print(f"Speed: {speed}, Brightness: {brightness}")
    else:
        print(f"Mode: {mode}")
        print(f"Payload: {payload}")
        response = bytearray.fromhex(payload)


adapters = simplepyble.Adapter.get_adapters()
adapter = adapters[0] # We are assuming you only have one BT adapter for now
print("Using adapter: " + adapter.address())

if len(sys.argv) > 1 and sys.argv[1] == "--scan":
    adapter.set_callback_on_scan_start(lambda: print("Scan started"))
    adapter.set_callback_on_scan_stop(lambda: print("Scan stopped"))
    adapter.set_callback_on_scan_found(lambda peripheral: print(f"Found {peripheral.identifier()} [{peripheral.address()}]"))
    adapter.scan_for(5000)
    peripherals = adapter.scan_get_results()
    print("The following LEDnet WF devices  were found:")
    for peripheral in peripherals:
        if peripheral.identifier().startswith("LEDnetWF"):
            print(f"\tMAC address: {peripheral.address()}, RSSI: {peripheral.rssi()}")
            manufacturer_data = peripheral.manufacturer_data()
            for manufacturer_id, value in manufacturer_data.items():
                print(f"\t\tManufacturer ID: {manufacturer_id}")
                print(f"\t\tManufacturer data: {value}")
                print(' '.join(format(x, '02x') for x in value))

elif len(sys.argv) > 1 and sys.argv[1] == "--connect":
    # There are no examples of how to instantiate a peripheral object from a mac address
    # it probably can be done, but I can't work it out from the source, so for now
    # just use scan to find it by name
    print("Scanning for devices")
    adapter.scan_for(5000)
    peripherals = adapter.scan_get_results()
    for peripheral in peripherals:
        if peripheral.identifier().startswith("LEDnetWF"):
            # this will do
            peripheral.connect()
            try:
                #services = peripheral.services()
                # for service in services:
                #     print(f"Service: {service.uuid()}")
                #     for characteristic in service.characteristics():
                #         print(f"\tCharacteristic: {characteristic.uuid()}")
                #         for descriptor in characteristic.descriptors():
                #             print(f"\t\tDescriptor: {descriptor.uuid()}")
                peripheral.notify(SERVICE_UUID, NOTIFY_UUID, response_decode)
                #send_initial_packet(peripheral)
                #send_initial_packet2(peripheral)
                print("Turning on")
                set_power(peripheral, True)
                time.sleep(2)
                # Use to debug response packets
                # while True:
                #     time.sleep(1)
                set_white(peripheral, 100, 50)
                time.sleep(5)
                set_white(peripheral, 75, 50)
                time.sleep(5)
                set_white(peripheral, 50, 50)
                time.sleep(5)

                for m in range(5):
                    m += 1
                    print(f"Setting mode: {m}")
                    set_mode(peripheral, m, 50, 100)
                    time.sleep(5)
                
                p = build_smear_packet()
                p = test_smear_pattern(p)
                send_prepared_packet(peripheral, p)
                time.sleep(10)

                print("Turning off")
                set_power(peripheral, False)
                time.sleep(2)
            finally:
                peripheral.disconnect()
else:
    print("Pass in either --scan or --connect")















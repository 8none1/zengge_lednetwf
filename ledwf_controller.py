#!/bin/env python3

# A very basic bit of Python to let us play with the LEDnetWF devices a bit more easily.
# This is a means to an end and is not intended to be a complete solution.

from operator import contains
import sys
import colorsys
import simplepyble
import time


SERVICE_UUID = "0000ffff-0000-1000-8000-00805f9b34fb"
NOTIFY_UUID =  "0000ff02-0000-1000-8000-00805f9b34fb"
WRITE_UUID =   "0000ff01-0000-1000-8000-00805f9b34fb"
COUNTER = 0

INITIAL_PACKET         = bytearray.fromhex("00 01 80 00 00 04 05 0a 81 8a 8b 96")
INITIAL_PACKET_2       = bytearray.fromhex("00 02 80 00 00 0c 0d 0b 10 14 16 0b 05 0d 36 36 06 00 0f d8")
UNKNOWN_STATE_CHANGE   = bytearray.fromhex("00 45 80 00 00 05 06 0a 22 2a 2b 0f 86")
UNKNOWN_STATE_CHANGE_2 = bytearray.fromhex("00 46 80 00 00 05 06 0a 11 1a 1b 0f 55")
# There is possible a different white on/off packet
ON_PACKET              = bytearray.fromhex("00 04 80 00 00 0d 0e 0b 3b 23 00 00 00 00 00 00 00 32 00 00 90")
OFF_PACKET             = bytearray.fromhex("00 5b 80 00 00 0d 0e 0b 3b 24 00 00 00 00 00 00 00 32 00 00 91")
# White bytes                                                                XX XX - bytes 11 & 12 0x00 to 0x64
WHITE_PACKET           = bytearray.fromhex("00 10 80 00 00 0d 0e 0b 3b b1 00 00 00 1b 36 00 00 00 00 00 3d")
# HSV bytes                                                               XX XX XX -  10, 11, 12 0x00 to 0x64
HSV_PACKET             = bytearray.fromhex('00 05 80 00 00 0d 0e 0b 3b a1 00 64 64 00 00 00 00 00 00 00 00')





def logger(message):
    print(message)

def get_counter():
    global COUNTER
    COUNTER += 1
    return COUNTER

def prepare_packet(packet):
    # Could add the 80 00 00 header here too
    count = get_counter()
    packet[0] = 0xFF00 & count
    packet[1] = 0x00FF & count
    return packet

def set_white(periph, ww, cw):
    # Pass in the peripheral object and the white values
    # the white values are percentages for warm white and cool white
    if ww > 100:
        ww = 100
    if cw > 100:
        cw = 100
    global WHITE_PACKET
    WHITE_PACKET[13] = ww
    WHITE_PACKET[14] = cw
    #periph.writeCharacteristic(WRITE_UUID, WHITE_PACKET)

def rgb_to_hsv(r,g,b):
    h, s, v = colorsys.rgb_to_hsv(r/255.0,g/255.0,b/255.0)
    h, s, v = int(h*360), int(s*100), int(v*100)
    h = int(h/2)
    print(h,s,v)
    return [h,s,v]

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

if len(sys.argv) > 1 and sys.argv[1] == "--connect":
    # There are no examples of how to instantiate a peripheral object from a mac address
    # if probably can be done, but I cant work it out from the source, so for now
    # just use scan to find it by name
    adapter.scan_for(5000)
    peripherals = adapter.scan_get_results()
    for peripheral in peripherals:
        if peripheral.identifier().startswith("LEDnetWF"):
            # this will do
            peripheral.connect()
            try:
                services = peripheral.services()
                for service in services:
                    print(f"Service: {service.uuid()}")
                    for characteristic in service.characteristics():
                        print(f"\tCharacteristic: {characteristic.uuid()}")
                        for descriptor in characteristic.descriptors():
                            print(f"\t\tDescriptor: {descriptor.uuid()}")
                peripheral.notify(SERVICE_UUID, NOTIFY_UUID, lambda data: print(f"Received data: {data}"))
                initial_packet_write = INITIAL_PACKET
                initial_packet_write = prepare_packet(initial_packet_write)
                # This doesnt seem to make any difference, but it does generate a notification
                # which we might be able to use to find the current status
                peripheral.write_request(SERVICE_UUID, WRITE_UUID, bytes(initial_packet_write))
                time.sleep(5)
                print("Turning on")
                on_packet_write = ON_PACKET
                on_packet_write = prepare_packet(on_packet_write)
                peripheral.write_request(SERVICE_UUID, WRITE_UUID, bytes(on_packet_write))
                time.sleep(5)
                # print("Switching to RGB mode")
                # unknown_state_packet_write = UNKNOWN_STATE_CHANGE
                # unknown_state_packet_write = prepare_packet(unknown_state_packet_write)
                # peripheral.write_request(SERVICE_UUID, WRITE_UUID, bytes(unknown_state_packet_write))
                # #time.sleep(5)
                # unknown_state_packet_write = UNKNOWN_STATE_CHANGE_2
                # unknown_state_packet_write = prepare_packet(unknown_state_packet_write)
                # peripheral.write_request(SERVICE_UUID, WRITE_UUID, bytes(unknown_state_packet_write))
                # time.sleep(5)

                

                hsv_packet_write = prepare_packet(HSV_PACKET)
                hsv = rgb_to_hsv(255,0,0)
                hsv_packet_write[10]  = hsv[0]
                hsv_packet_write[11]  = hsv[1]
                hsv_packet_write[12] = hsv[2]
                print("Setting colour: red")
                peripheral.write_request(SERVICE_UUID, WRITE_UUID, bytes(hsv_packet_write))
                time.sleep(5)
                hsv = rgb_to_hsv(0,255,0)
                hsv_packet_write[10]  = hsv[0]
                hsv_packet_write[11]  = hsv[1]
                hsv_packet_write[12] = hsv[2]
                print("Setting colour: green")
                peripheral.write_request(SERVICE_UUID, WRITE_UUID, bytes(hsv_packet_write))
                time.sleep(5)
                hsv = rgb_to_hsv(0,0,255)
                hsv_packet_write[10]  = hsv[0]
                hsv_packet_write[11]  = hsv[1]
                hsv_packet_write[12] = hsv[2]
                print("Setting colour: blue")
                peripheral.write_request(SERVICE_UUID, WRITE_UUID, bytes(hsv_packet_write))                
                time.sleep(5)
                print("Turning off")
                off_packet_write = OFF_PACKET
                off_packet_write = prepare_packet(off_packet_write)
                peripheral.write_request(SERVICE_UUID, WRITE_UUID, bytes(off_packet_write))

            finally:
                peripheral.disconnect()

            














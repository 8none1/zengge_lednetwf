# Zengge LEDnet WF Bluetooth LE reverse engineering

Might also be known as:
 - YBCRG-RGBWW 
 - Magic Hue
 - Bluetooth full colors selfie ring light


## Background
I bought one of these neat looking RGB WW ring lamp things off [Ali Express](https://www.aliexpress.com/item/1005004712536400.html?spm=a2g0o.order_list.0.0.21ef1802Yiov0S):

![image](https://user-images.githubusercontent.com/6552931/198835721-98a37067-6197-4116-9572-551e1f78e7a5.png)


It has a Bluetooth LE controller and I want to be able to control it myself from code, not from within the app.  It also has an mini remote control which seems to be RF not IR, despite looking like an IR.
The app is called "Zengge" but also seems to be branded Magic Hue in a few places.

I'm going to try and reverse engineer the BLE protocol and see if I can make it work.  It is probably worth trying to decompile the Android app as well and see if any insights can be gained there.  The option of last resort is to replace the entire controller with something more friendly, like WLED on an ESP8266.

![image](https://user-images.githubusercontent.com/6552931/198889989-ac594279-b3c5-47e6-ad61-4ea750f723b1.png)


If you're interested in helping out, please get in touch.  If you know of someone who has already worked this out let me know.

# Latest news
## 2022-11-06
Most of the features are now supported.  With the decoded protocols you can:
 - Set single static colours
 - Select from any of the built in modes and alter the speed and brightness
 - Create your own pixel by pixel patterns, called "smear" in the app.

Here's a demo of stepping through those features:


https://user-images.githubusercontent.com/6552931/200186465-590ff263-4d1e-49c9-acda-37d8344e04e2.mp4



There are still some things that need doing:
 - How does it describe the number of LEDs it has? (I have some theories already about this, just need to test them).  Theory tested, it was wrong.  I think they need you to tell them.

## 2022-11-05
I can command this thing from Python!

## 2022-11-04
It turns out that once you've connected to the device, set the MTU and enabled notifications then the packet counter and checksum ARE COMPLETELY IGNORED.  Yup.  
You can read the whole horrific story in the scratch notes file.  A very rough, unfinished, and at this point abandoned attempt to reverse engineering the protocol exists in the file `encoder.py`.  It rather looks like we don't need any of that at the moment. Tomorrow I will craft some bash scripts to really shake down what we can do with this discovery.

# Process

I used HCI logging from the debug menu in Android to capture the packets going from the app to the device.  I then copied those to my main machine using `adb pull sdcard/btsnoop_hci.log <local filename>`.  There are many logs captured in the `btsnoop_logs` directory if you want to have a look.
I also decompiled the Zengee app in to Smali code and made an attempt to reverse engineer the "encryption" and checksum routines.  However, I abandoned this work when I discovered that you don't need to concern yourself with things like making sure the checksums are correct, because the device doesn't care.

Some tips for doing this sort of HCI log reverse engineering:
 - Walking through the app pressing each button multiple times makes it much easier to spot where you moved on from one feature to the next.
 - Keep the number of multiple presses the same throughout your logging.  I pressed each thing five times.
 - Wireshark can import the log files directly
 - Setting a Wireshark filter of `(btatt or btgatt) && btatt.opcode.method==0x12` allows you to filter only writes from Android to the device.
 - Open a packet up in the bottom pane, clicking through to Bluetooth Attribute Protocol -> Value, right click and choose "Apply as column".  This will allow you to see the bytes being sent to the device
 - Export write packets to a new file (or overwrite): Select all, export specified packets, export as `pcapng` Selected packets only.
 - Install `tshark` and: `tshark -r <filename.pcapng -T fields -e btatt.value`
 - That will dump out only the bytes with all the other BT headers removed.  Much easier than copy and pasting from Wireshark
 - Assume that the original developers of the protocol were in a rush. If it seems the obvious way to do something, it probably is.
 - Try using some simple replay tests using `gatttool` to send the bytes you found with tshark.  Can you make it do things by just sending the same packet again?  e.g. switch the device to green and send a red packet, does it work?  If so, then things like packet counters are likely ignored.  Do this early, you will save a lot of time if you don't have to reversed engineer encryption and checksums.


Ok, on to the actual information.

# Protocol

## Header
These are common to all payloads.
 - The first two bytes (0,1) are a counter which increments after every write.  I haven't seen the counter roll over to use byte zero yet, but I assume it does.
 - The next three bytes (2,3,4) are static `0x80 0x00 0x00`
 - The next two bytes (5,6) refer to how long the rest of the payload is. Byte 6 represents the number of bytes to the end of the payload including the last checksum byte.  Byte 5 is one less that this, I assume this means the length without the checksum.
 - The last byte is, I assume, a checksum.  The calculation for which is explored in the scratch notes file, and the `encoder.py` Python script (unfinished).  The validity of this checksum is seemingly ignored by the device.

## Power control
Example bytes `ON`:  `00 04 80 00 00 0d 0e 0b 3b 23 00 00 00 00 00 00 00 32 00 00 90`

Example bytes `OFF`: `00 5b 80 00 00 0d 0e 0b 3b 24 00 00 00 00 00 00 00 32 00 00 91`


```
# checksum is the last byte of the packet --------------------------------------------------------------v
# unknown ----------------------------------------------------------------v---------------------------v |
# on = 0x23 off = 0x24 ------------------------------------------------v  |                           | |
# unknown -------------- ----------------------------------------v--v  |  |                           | |
# length of packet from here to the end including checksum ---v  |  |  |  |                           | |
# one less than the length ------- ------------------------v  |  |  |  |  |                           | |
# standard header --------------------------------v--v--v  |  |  |  |  |  |                           | |
# counter ----------------------------------v--v  |  |  |  |  |  |  |  |  |                           | |
                                            00 04 80 00 00 0d 0e 0b 3b 23 00 00 00 00 00 00 00 32 00 00 90
```

## RGB colour handling
The device expects basic static colour information in HSV format.  The value for the Hue element is divided by two to fit in to a single byte.  Saturation and Value are percentages from 0 to 100 (0x64).
White colours are represented by colour temperature percentage from 0x0 to 0x64 from warm to cool.  Warm (0x0) is only the warm white LED, cool (0x64) is only the white LED and then a mixture between the two.  Brightness is a percentage.

I assume that HSV colours and white colours are mutually exclusive, but I haven't tried to do both at the same time.

```
# checksum ---------------------------------------------------------------------------------------------v
# White temperature and brightness ------------------------------------------------v--v                 |
# HSV colour data --------------------------------------------------------v--v--v  |  |                 |
# ?                      ----------------------------------------v        |     |  |  |                 |
# length of packet from here to the end including checksum ---v  |        |     |  |  |                 |
# length of packet from here without the checksum? --------v  |  |        |     |  |  |                 |
# standard header --------------------------------v--v--v  |  |  |        |     |  |  |                 |
# counter ----------------------------------v--v  |  |  |  |  |  |        |     |  |  |                 |
                                            00 05 80 00 00 0d 0e 0b 3b a1 00 64 64 00 00 00 00 00 00 00 00   # bytes 10, 11, 12
                                            00 10 80 00 00 0d 0e 0b 3b b1 00 00 00 1b 36 00 00 00 00 00 3d   # bytes 13 & 14 
```

## Symphony
This is what the app calls modes / effects.  There are a number (113 in the app) of effects.  They are be numbered serially from 0x01 to 0x71.  These packets do not have a checksum it seems, and they use a different format to the RGB and white colour setting payloads.  Nevertheless they are fairly easy to understand. They take the form of:

```
# Brightness 1 - 0x64 --------------------------------------------v
# Speed 1 - 0x64 ----------------------------------------------v  |
# effect number (1 - 0x71 ----------------------------------v  |  |
# ? --------------------------------------------------v--v  |  |  |
# length of packets from here to the end ----------v  |  |  |  |  |
# length of packets minus 1 --------------------v  |  |  |  |  |  |
# Standard header ---------------------v--v--v  |  |  |  |  |  |  |
# counter -----------------------v--v  |  |  |  |  |  |  |  |  |  |
                                 00 06 80 00 00 04 05 0b 38 01 01 64
```

## Smear
This is what the apps calls custom patterns and effects.
It allows you to draw your own patterns on the device.  My device has 48 LEDs and so the message has 48 RRGGBB entries.  There are also some modes.  
The packets are 170 bytes long for a 48 LED device.

```
# checksum  ----------------------------------------------------------------------------------------------------------------------v
# direction 0 or 1 for mode "stream" (2) --------------------------------------------------------------------------------------v  |
# Brightness 0% - 100% -----------------------------------------------------------------------------------------------------v  |  |
# Speed 0% - 100% ------------------------------------------------------------------------------------------------------ v  |  |  |
# Mode. 1 = static, 2 = stream (check direction also) 3 = strobe  4 = jump  ------------------------------------------v  |  |  |  |
# pixel by pixel RGB data 3 bytes * 48 pixels = 144 bytes ------------------------------v---------------------------v |  |  |  |  |
# ? ------------------------------------------------------------------------------v---v |                           | |  |  |  |  |
# Length of packet from next byte to the end ----------------------------------v  |   | |                           | |  |  |  |  |
# Length of the packet without the checksum? -------------------------------v  |  |   | |                           | |  |  |  |  |
# more fixed header stuff -----------------------------------------v--v--v  |  |  |   | |                           | |  |  |  |  |
# counter ---------------------------------------------------v--v  |  |  |  |  |  |   | |                           | |  |  |  |  |
#                                                            |  |  |  |  |  |  |  |   | |                           | |  |  |  |  |
#                                                            00 10 80 00 00 96 97 0b 59 000000 ...[deleted]... 000000 02 64 64 00 23
```

## Response data

Once you have enabled notifications (which you seem to have to do in order for it to accept commands) you will receive a message on every state change.  The format of that message is 8 bytes of some kind of header, followed by a hex encoded string which resembles a JSON object.  If you convert who whole hex string to text it looks like this:
```
€��34
{"code":0,"payload":"811D24610F313232FF640200305C"}
```

The header includes a counter, and some other numbers which I haven't worked out.

The payload in the JSON object reflects what is currently going on with the device. I haven't worked it all out yet, but it can be largely understood as:
```
# checksum? ----------------------------------------------------------------------v
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
```



# Tools

There is a Python3 script which uses the new, and so far very good, [SimpleBLE](https://github.com/OpenBluetoothToolbox/SimpleBLE) library to connect to a 48 LED device and cycle through a few colours and modes.  This is more of a proof-of-concept than code to be used to control your device.  That said, patches are welcome.

I will create a new project very similar to my [NimBLE Triones](https://github.com/8none1/nimble_triones) code to interface between LEDnetWF devices and MQTT using an ESP32. This will allow for easy integration with Node RED and Home Assistant.

It'd be great if these devices could get included in [led-ble](https://github.com/Bluetooth-Devices/led-ble) to give native support to Home Assistant.  However that library depends on Bleak which uses asyncio in Python and try as I might, I can't make sense of it.  So help is welcomed on this front.

If you are able to make use of this information in your own projects, please let me know and I can link to them from here.

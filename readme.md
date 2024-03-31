# Zengge LEDnet WF Bluetooth LE reverse engineering

Might also be known as:
 - Zengge LEDnetWF
 - YBCRG-RGBWW 
 - Magic Hue
 - Bluetooth full colors selfie ring light

There are other ZENGGE devices with similar names. For example, there are small black USB Bluetooth LED controllers bundled with light strips, which can be used with any WS2812B lights with 3-pin connector. They show up as "LEDnetWF0200A3" plus the last six digits of their MAC. While the app uses different commands than those below, they will still accept some of them (namely on/off, HSL colors and symphony, but with only 100 effects).

## Home Assistant Integration

Check out @raulgbcr project to add support for these lights to Home Assistant:  https://github.com/raulgbcr/lednetwf_ble

We've got a pretty decent integration going, and it's getting updated fairly regularly.  Contributions very welcome.

## Background

I bought one of these neat looking RGB WW ring lamp things off [Ali Express](https://www.aliexpress.com/item/1005004712536400.html?spm=a2g0o.order_list.0.0.21ef1802Yiov0S):

![image](https://user-images.githubusercontent.com/6552931/198835721-98a37067-6197-4116-9572-551e1f78e7a5.png)


It has a Bluetooth LE controller and I want to be able to control it myself from code, not from within the app.  It also has an mini remote control which seems to be RF not IR, despite looking like an IR.
The app is called "Zengge" but also seems to be branded Magic Hue in a few places.

I'm going to try and reverse engineer the BLE protocol and see if I can make it work.  It is probably worth trying to decompile the Android app as well and see if any insights can be gained there.  The option of last resort is to replace the entire controller with something more friendly, like WLED on an ESP8266.

![image](https://user-images.githubusercontent.com/6552931/198889989-ac594279-b3c5-47e6-ad61-4ea750f723b1.png)

If you're interested in helping out, please get in touch.  If you know of someone who has already worked this out let me know.

# Latest news

## 2024-03-31

I got a new version of this controller which has a later firmware version.  There are some small changes in the protocol between these versions, and I'm working them out.  This also requires support for changing the LED colour ordering, chip type, number of LEDs etc.  This has been worked out and decoded below.

Also I have spent some time looking at the advertising packets which they send.  This contains information about the power state, current colour etc without any kind of pairing required.  The data is just broadcast.  I'm working on integrating this in to the Home Assistant integration as well.

In summary, this is still an active project and contributions are welcome both here to document the protocol and on the Home Assistant integration listed above.

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

I used HCI logging from the debug menu in Android to capture the packets going from the app to the device. It must be enabled before enabling Bluetooth.  I then copied those to my main machine using `adb pull sdcard/btsnoop_hci.log <local filename>`.  There are many logs captured in the `btsnoop_logs` directory if you want to have a look. Depending on your phone, there might be easier ways to retrieve the log. For example, Xiaomi users can just dial `*#*#284#*#*` to make copies of the two most recent logs spawn in the user-accessible files (the exact location depends on the device).
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
These are common to all payloads and many (if not all) Zengge devices.
 - The first byte is used for per-command flags. 0x40 means that the command is fragmented due to length. The flag is set for every fragment. You need at least 56 to 57 LEDs (depending on the device) for this to happen. As this ring light only has 48 LEDs, commands will never need to be fragmented.
 - After this comes the counter which increments after every command (so it's the same for all fragments of one command). It starts at 1 and can roll over. It is generally ignored but used to tell which fragments belong together.
 - The next byte is per-fragment flags. 0x80 means that this is the last (or only) fragment.
 - This is the fragment counter. It starts with 0 for the first or only fragment of a command.
 - Now comes the only word (big endian) in this header. It contains to the total payload of all fragments' length, not counting the following byte and the checksum. This word is only present in the first or only fragment.
 - The next byte represents the number of bytes to the end of the payload including the last checksum byte. For single-fragment commands, this is therefore one more than the previous word.
 - Except for some initialisation commands, the next byte is always 0x0b. It is only present in the first or only fragment.
 - The last byte is a checksum. It is simply the sum of all bytes after the header, not counting the checksum itself. It is generally ignored. Some commands even omit it.
This means that the header (without the checksum) of the first fragment is 8 bytes long, but only 5 for follow-up fragments.

## Power control
Example bytes `ON`:  `00 04 80 00 00 0d 0e 0b 3b 23 00 00 00 00 00 00 00 32 00 00 90`

Example bytes `OFF`: `00 5b 80 00 00 0d 0e 0b 3b 24 00 00 00 00 00 00 00 32 00 00 91`


```
# checksum is the last byte of the packet seems to be sum of bytes from the `3b` not inc. checksum -----v
# unknown -------------------------------------------------------------------------------v------------v |
# Likely to be colour information per HSV/WW packets ---------------------v-----------v  |            | |
# on = 0x23 off = 0x24 ------------------------------------------------v  |           |  |            | |
# unknown -------------- ----------------------------------------v--v  |  |           |  |            | |
# length of packet from here to the end including checksum ---v  |  |  |  |           |  |            | |
# one less than the length ------- ------------------------v  |  |  |  |  |           |  |            | |
# standard header --------------------------------v--v--v  |  |  |  |  |  |           |  |            | |
# counter ----------------------------------v--v  |  |  |  |  |  |  |  |  |           |  |            | |
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
# effect number (1 - 0x71) ---------------------------------v  |  |
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

## LED settings

You can configure the number of LEDs on your strip via the number of segments and the number of LEDs in a segment.  You can configure the type of LEDs in use and the protocol used to talk to them (e.g. colour ordering).  There are some sample Wireshark captures in the `led_settings` file in the `bt_snoop` directory.

```text
checksum? -----------------------------------------------------v
f0 ---------------------------------------------------------v  |
Number of segments --------------------------------------v  |  |
Num LEDs ---------------------------------------------v  |  |  |
Colour ordering -----------------------------------v  |  |  |  |
LED type (0x0-0x0b) ----------------------------v  |  |  |  |  |
Number of segments --------------------------v  |  |  |  |  |  |
Num LEDs (16 bit number?) -------------v--v  |  |  |  |  |  |  |
Some kind of instruction? ------v----v |  |  |  |  |  |  |  |  |
length of packet? ---------v--v |    | |  |  |  |  |  |  |  |  |
header -------------v----v |  | |    | |  |  |  |  |  |  |  |  |
counter -------v--v |    | |  | |    | |  |  |  |  |  |  |  |  |
               0022 800000 0b0c 0b6200 64 00 03 01 00 64 03 f0 21
                                  |--------------------------|
                                     checksum source && 0xFF
```
I think the checksum is the sum of these bytes & 0xff.  Bytes 9->18.

## Response data

Once you have enabled notifications (which you seem to have to do in order for it to accept commands) you will receive a message on every state change.  The format of that message is 8 bytes of some kind of header, followed by a hex encoded string which resembles a JSON object.  If you convert the whole hex string to text it looks like this:
```
€��34 {"code":0,"payload":"811D24610F313232FF640200305C"}
```

The header includes a counter, and some other numbers which I haven't worked out.

The payload in the JSON object reflects what is currently going on with the device. I haven't worked it all out yet, but it can be largely understood as:
```
# checksum SUM of all the bytes except checksum AND 0xFF -------------------------v
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
# Device type / firmware minor version -------v  |  |  |  |  |  |  |  |  |  |  |  |
# fixed -----------------------------------v  |  |  |  |  |  |  |  |  |  |  |  |  |
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

Thanks to [bdraco](https://github.com/8none1/zengge_lednetwf/issues/1) for pointing me at the flux_led code which has the exact same status packets.

### LED Strip settings response

There seem to be differences between firmware versions and/or device types.

To request a notification containing the settings of the LED controller you can send:
`00 35 80 00 00 04 05 0a 81 8a 8b 96`

The LED strip should send you a JSON payload which tells you about it's settings.  Settings include the number of LEDs, the LED type (WS2812b etc), the colour order (RGB, GBR, etc).  I can be decoded as:

### LED strips

 ```text
 checksum (sum AND 0xff) ---------------------------------------------------------||
 num segs music mode ----------------------------------------------------------|| ||
 num leds music mode -------------------------------------------------------|| || ||
 colour order 0x00 - 0x05 -----------------------------------------------|| || || ||
 chip type 0x01-0x0b -------------------------------------------------|| || || || ||
 light bar segments -----------------------------------------------|| || || || || ||
 0 -------------------------------------------------------------|| || || || || || ||
 num leds lightbar mode ----------------------------------||-|| || || || || || || ||
 header --------------------------------------------|---| || || || || || || || || ||
      04 79 80 00 00 2d 2e 0a  {"code":0,"payload":"00 63 00 35 00 01 0B 02 35 01 DC"}
 ```

#### LED ring light / circle

Hm, ignore this bit for now.  I made a mistake somewhere...

```text
colour order --------------------||
led type 1 to 6 --------------|| ||
num leds ------------------|| || ||
header --------------|---| || || ||
{"code":0,"payload":"63 00 1C 01 02 82"}
{"code":0,"payload":"63 00 1C 01 02 82"}
{"code":0,"payload":"63 00 1C 06 02 87"}
{"code":0,"payload":"63 00 1C 01 02 82"}
{"code":0,"payload":"63 00 1C 01 00 80"}
{"code":0,"payload":"63 00 1C 01 05 85"}
```

TODO: Work out how to tell which device is which.

## Advertising Data

It turns out that these devices provide some information via the advertising data before they are connected.  I'm still trying to decode all of this information but it's likely this is how to tell one device type from another.

### Ring

```text
Off:              btle.scan_responce_data == 1e ff 02 5a 53 05 08 65 f0 0c da 81 00 1d 0f 02 01 01 24 61 0f 1d 32 51 00 32 02 00 1c 00 00
On White:         btle.scan_responce_data == 1e ff 02 5a 53 05 08 65 f0 0c da 81 00 1d 0f 02 01 01 23 61 0f 64 32 51 00 32 02 00 1c 00 00
On Red ?          btle.scan_responce_data == 1e ff 02 5a 53 05 08 65 f0 0c da 81 00 1d 0f 02 01 01 23 61 f0 00 ff 00 00 00 02 00 1c 00 00
On Green:         btle.scan_responce_data == 1e ff 02 5a 53 05 08 65 f0 0c da 81 00 1d 0f 02 01 01 23 61 f0 00 00 ff 00 00 02 00 1c 00 00
On Blue:          btle.scan_responce_data == 1e ff 02 5a 53 05 08 65 f0 0c da 81 00 1d 0f 02 01 01 23 61 f0 00 00 00 ff 00 02 00 1c 00 00
Some effect mode: btle.scan_responce_data == 1e ff 02 5a 53 05 08 65 f0 0c da 81 00 1d 0f 02 01 01 23 25 1d 00 32 51 ff 00 02 00 1c 00 00
Same but off:     btle.scan_responce_data == 1e ff 02 5a 53 05 08 65 f0 0c da 81 00 1d 0f 02 01 01 24 25 20 00 32 51 ff 00 02 00 1c 00 00
```
### Strip

```text
                                                         0  1  2  3  4  5  6  7  8  9  10 11 12 13 14 15 16 17 18 19 20 21 22 23 24 25 26
Music Mode:       btle.scan_responce_data == 1e ff 00 5a 56 05 08 65 f0 62 b0 5b 00 a3 2d 03 01 02 23 62 01 64 ff 00 00 00 03 00 36 00 00
Off:              btle.scan_responce_data == 1e ff 00 5a 56 05 08 65 f0 62 b0 5b 00 a3 2d 03 01 02 24 62 01 64 ff 00 00 00 03 00 36 00 00
Fixed Red:        btle.scan_responce_data == 1e ff 00 5a 56 05 08 65 f0 62 b0 5b 00 a3 2d 03 01 02 23 61 01 32 ff 00 00 00 03 00 36 00 00
Fixed Green:      btle.scan_responce_data == 1e ff 00 5a 56 05 08 65 f0 62 b0 5b 00 a3 2d 03 01 02 23 61 01 32 00 ff 00 00 03 00 36 00 00
Fixed Blue:       btle.scan_responce_data == 1e ff 00 5a 56 05 08 65 f0 62 b0 5b 00 a3 2d 03 01 02 23 61 01 32 00 00 ff 00 03 00 36 00 00
eir_ad.entry.length -------------------------^^ || || || ||    || || || || || || || || ||          || || || || || || || ||       ||
eir_ad.entry.type ------------------------------^^ || || ||    |               | || || ||          || || |   | |      | ||       ||
eir_ad.entry.company_id ---------------------------^^-^^ ||    |               | || || ||          || || |   | |      | ||       ||
Firmware version or similar -----------------------------^^----+---------------+-^^-^^-^^          || || |   | |      | ||       ||
MAC address  --------------------------------------------------|^^^^^^^^^^^^^^^|                   || || |   | |      | ||       ||
On/Off  -------------------------------------------------------------------------------------------^^ || |   | |      | ||       ||
Mode? ------------------------------------------------------------------------------------------------^^ |   | |      | ||       ||
White brightness ----------------------------------------------------------------------------------------^^^^^ |      | ||       ||
RGB -----------------------------------------------------------------------------------------------------------^^^^^^^^ ||       ||
White colour temp ------------------------------------------------------------------------------------------------------^^       ||
LED count -----------------------------------------------------------------------------------------------------------------------^^
```

# Tools

There is a Python3 script which uses the new, and so far very good, [SimpleBLE](https://github.com/OpenBluetoothToolbox/SimpleBLE) library to connect to a 48 LED device and cycle through a few colours and modes.  This is more of a proof-of-concept than code to be used to control your device.  That said, patches are welcome.

I will create a new project very similar to my [NimBLE Triones](https://github.com/8none1/nimble_triones) code to interface between LEDnetWF devices and MQTT using an ESP32. This will allow for easy integration with Node RED and Home Assistant.

It'd be great if these devices could get included in [led-ble](https://github.com/Bluetooth-Devices/led-ble) to give native support to Home Assistant.  However that library depends on Bleak which uses asyncio in Python and try as I might, I can't make sense of it.  So help is welcomed on this front.

If you are able to make use of this information in your own projects, please let me know and I can link to them from here.

## Other projects that might be of interest

- [iDotMatrix](https://github.com/8none1/idotmatrix)
- [Zengge LEDnet WF](https://github.com/8none1/zengge_lednetwf)
- [iDealLED](https://github.com/8none1/idealLED)
- [BJ_LED](https://github.com/8none1/bj_led)
- [ELK BLEDOB](https://github.com/8none1/elk-bledob)
- [HiLighting LED](https://github.com/8none1/hilighting_homeassistant)
- [BLELED LED Lamp](https://github.com/8none1/ledble-ledlamp)

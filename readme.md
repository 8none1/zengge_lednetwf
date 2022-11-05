# Zengge LEDnet WF Bluetooth LE reverse engineering attempt

Might also be known as:
 - YBCRG-RGBWW 
 - Magic Hue
 - Bluetooth full colors selfie ring light


## Background
I bought one of these neat looking RGB WW ring lamp things off [Ali Express](https://www.aliexpress.com/item/1005004712536400.html?spm=a2g0o.order_list.0.0.21ef1802Yiov0S):

![image](https://user-images.githubusercontent.com/6552931/198835721-98a37067-6197-4116-9572-551e1f78e7a5.png)


It has a Bluetooth LE controller and I want to be able to control it myself from code, not from within the app.  It also has an mini remote control which seems to be RF not IR, despite looking like an IR.
The app is called "Zengge" but also seems to be branded Magic Hue in a few places.

I'm going to try and reverse engineer the BLE protocol and see if I can make it work.  It is probably worth trying to decompile the Android app as well and see if any insights can be gained there.  The final idea I have is to simply replace the entire controller with something more friendly, like WLED.

![image](https://user-images.githubusercontent.com/6552931/198889989-ac594279-b3c5-47e6-ad61-4ea750f723b1.png)


If you're interested in helping out, please get in touch.  If you know of someone who has already worked this out let me know.


## Current Status

I think all the basic commands are worked out.  I need to make sense of the notifications.
I will build an initial Python script to test everything works.


[vid.mp4.webm](https://user-images.githubusercontent.com/6552931/200139193-8668e011-3e02-4f38-b48c-0a247f3dc47d.webm)




## Process

I'm going to start by using HCI debugging in Android to capture the packets from the app to the device, then I will use Wireshark to view them.  As I see patterns I will write them down here.
You can tell Wireshark to filter out only BLE ATT write commands with this filter: `btatt.opcode.method==0x12`
I should be able to test basic assumptions with `gatttool` on Linux.  Eventually I would like to write a Python script or an MQTT bridge in C++ on an ESP32.

## Initial Investigation

In the file `add on_off_hci.log` I opened the app and switched the main power on and off 5 times.
That results in payloads that look like:

```
0000   02 02 00 1c 00 18 00 04 00 12 17 00 00 04 80 00   ................
0010   00 0d 0e 0b 3b 24 00 00 00 00 00 00 00 32 00 00   ....;$.......2..
0020   91                                                .
```

and

```
0000   02 02 00 1c 00 18 00 04 00 12 17 00 00 05 80 00   ................
0010   00 0d 0e 0b 3b 23 00 00 00 00 00 00 00 32 00 00   ....;#.......2..
0020   90                                                .
```

repeated 5 times.  So I assume that these mean "on" and "off".

I will keep on in this manner until I understand more.

Have a look at the [scratch notes file](https://github.com/8none1/zengge_lednetwf/blob/main/scratchnotes.md) to see where I've got to.

# Example Packets (arbitary grouping of bytes for my benefit)
- On       `0004 800000 0d0e0b3b 23 000000 0000 0000 32 0000 90`
- RGB      `0007 800000 0d0e0b3b a1 3c6464 0000 0000 00 0000 e0`
- White    `000c 800000 0d0e0b3b b1 000000 642e 0000 00 0000 7e`
- Symphony `0012 800000 04 05 0b 38 01 64 64`
- Smear    `020200a500a1000 400121700 0007 800000 96970b59 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 0000ff 000000 000000 000000 0000ff 0000ff 0000ff 01333200 92`

# Secondary Investigation
## Counter - bytes 0 & 1
The first two bytes of the written value are a counter of some kind.  It increments by 1 each time a command is sent and seems to reset each time the app opens.  So a per session counter?  Should be easy to implement and test.

## Some kind of padding - bytes 2 to 4
The next 3 bytes are (so far) common to all packets and are `0x80 0x00 0x00`.

## Power on/off
 - 2 byte counter
 - Bytes 2 -> 8 : `0x80 0x00 0x00 0x0d 0x0e 0x0b 0x3b` 
 - Power on: Byte 9 is set to `0x23` Power off is `0x24` 
 - Bytes 10 - 16 are `0x00`
 - Byte 17 is set to `0x32`
 - Bytes 18 & 19 `0x00`
 - Byte 20 is checksum(?)

## Colour handling
### RGB
The colour handling is set in bytes 10,11,12.  It is encoded in HSV format, and the first byte, `hue`, is actually hue/2 to fit in one byte.
Also byte 9 is set to 0xa1.
### White
The white LEDs are set in bytes 13 & 14.  Bytes 14 is a scale from 0 to 100 representing white colour temperature and byte 15 is brightness from 0 to 100%.
Also byte 10 is set to 0xb1.

## Symphony
This is what the app calls effects.  There are a number (113 in the app) of effects.  They are be numbered serially from 0x01 to 0x71.  These packets do not have a checksum it seems, and they use a different format to the RGB and white colour setting commands.  Nevertheless they are fairly easy to understand. They take the form of:

`cnt  header --fixed- e  s  b`
`0009 800000 04050b38 71 64 64`

We see the usual counter, then a fixed chunk which is different to the colour commands, but consistent in the effect commands - so some kind of fixed mode setting, then `e` is the effect number, `s` is the speed (1-100) and `b` is brightness (0-100).

## Smear
This allows you to draw your own patterns on the device.  The message has 48 RRGGBB entries, and my device has 48 LEDs (according to the app), so that's pretty straight forward.  There are also some modes.  As always there is a whole lot of other stuff to work out which seems to be just fixed values.

- The packets are 170 bytes long
- There is a 12 byte header of some sort.  Seems fixed.
- Then there is the counter.  I'm reasonably sure this is a two byte counter
- Then there is a three byte "80 00 00" which we've seen elsewhere
- Then four bytes which stay the same
- Then 48 bytes of RRGGBB. Pixel zero is where the wire enters the metal circle and then with the stand on the left they go clockwise 
- Then there are 5 bytes:
  - mode (1 stream one way, 2 stream the other, 3 strobe, 4 jump)
  - Speed (1 - 100%)
  - Brightness (1-100%)
  - ?
  - ?  checksum perhaps?


## Checksum
The last byte appears to be a checksum, but I haven't worked out how to calculate it yet.
Update: turns out you don't need to.


# Latest news
It turns out that once you've connected to the device, set the MTU and enabled notifications then the packet counter and checksum ARE COMPLETELY IGNORED.  Yup.  
You can read the whole horrific story in the scratch notes file.  A very rough, unfinished, and at this point abandoned attempt to reverse engineering the protocol exists in the file `encoder.py`.  It rather looks like we don't need any of that at the moment. Tomorrow I will craft some bash scripts to really shake down what we can do with this discovery.

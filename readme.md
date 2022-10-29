# Zengge LEDnet WF reverse engineering attempt


## Background
I bought one of these neat looking RGB WW ring lamp things off [Ali Express](https://www.aliexpress.com/item/1005004712536400.html?spm=a2g0o.order_list.0.0.21ef1802Yiov0S):

![image](https://user-images.githubusercontent.com/6552931/198835721-98a37067-6197-4116-9572-551e1f78e7a5.png)


I has a Bluetooth LE controller and I want to be able to control myself from code, not from within the app.

I'm going to try and reverse engineer the BLE protocol and see if I can make it work.

If you're interested in helping out, please get in touch.  If you know of someone who has already worked this out let me know.

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

Have a look at the scratch notes file to see where I've got to.


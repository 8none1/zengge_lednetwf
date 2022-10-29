# Scratch notes


## Basic info & connection params stuff
- Device name advertised as: `LEDneWF02001D0CDC48`
- Wireshark says it's a `JMZengge`
- UUID: FF00
  - 0xFF22 - read/write without response notify
  - 0xFF11 - write without response
- UUID: FFFF
  - 0xFF02 - Read notify
  - 0xFF01 - write

Based on previous escapades in BLE I assume you have to enable notifications by writing to one of the notification endpoints on FFFF.

Not sure if this is relevant:
MTU: 200 bytes
Command length: 8
Min interval: 16 (20 msec)
Max interval: 24 (30 msec)
Timeout multiplier: 600 (6 sec)

## Initial conversation

### Probably enabling a notification

We sent:
```
0000   02 02 00 09 00 05 00 04 00 12 15 00 01 00         ..............
```
 - Write Request 0x12
 - Handle: 0x0015
   - Service UUIDL 0xffff
   - Characteristic: 0xff02
   - UUID: 0x2902

We received:
```
0000   02 02 20 05 00 01 00 04 00 13                     .. .......
```
 - Write response: 0x13
 - Handle: 0x0015
   - Service: 0xffff
   - Char: 0xff02
   - UUID: 0x2902

Characteristic Configuration Client: 0x0001, Notification


### Next write request (perhaps some kind of set up)

We sent:
```
0000   02 02 00 13 00 0f 00 04 00 12 17 00 00 01 80 00   ................
0010   00 04 05 0a 81 8a 8b 96                           ........
```
 - Write request 0x12
 - Handle: 0x0017
   - Service: 0xffff
   - UUID: 0xff01

Value is hex:  `00 01 80 00 00 04 05 0a 81 8a 8b 96`

which results in us being sent this over multiple frames:

```
0000   3e 00 04 00 1b 14 00 04 43 80 00 00 33 34 0a 7b   >.......C...34.{
0010   22 63 6f 64 65 22 3a 30 2c 22 70 61 79 6c 6f 61   "code":0,"payloa
0020   64 22 3a 22 38 31 31 44 32 33 32 35 30 45 30 30   d":"811D23250E00
0030   33 32 33 32 46 46 30 30 30 32 30 30 33 30 38 39   3232FF0002003089
0040   22 7d                                             "}
```

`>C34 {"code":0,"payload":"811D23250E003232FF0002003089"}`

`04 43 80 00 00 33 34 0a 7b 22 63 6f 64 65 22 3a 30 2c 22 70 61 79 6c 6f 61 64 22 3a 22 38 31 31 44 32 33 32 35 30 45 30 30 33 32 33 32 46 46 30 30 30 32 30 30 33 30 38 39 22 7d`
`    C           3  4 sp  {  "  c  o  d  e  "  :  0  ,  "  p  a  y  l  o  a  d  "  :  "  8  1  1  D  2  3  2  5  0  E  0  0  3  2  3  2  F  F  0  0  0  2  0  0  3  0  8  9  "  }`

I would guess that this is an 8 byte header?


We then send:
```
0000   02 02 00 1b 00 17 00 04 00 12 17 00 00 02 80 00   ................
0010   00 0c 0d 0b 10 14 16 0a 1d 0e 20 00 06 00 0f a4   .......... .....
```
 - Write request 0x12
   - Handle: 0x0017
   - Service: 0xffff
   - UUID: 0xff01

Value in hex: `00 02 80 00 00 0c 0d 0b 10 14 16 0a 1d 0e 20 00 06 00 0f a4`

We received a write response.

Then we send (to the same service and UUID):
Value in hex: `00 03 80 00 00 0c 0d 0b 10 14 16 0a 1d 0e 20 00 06 00 0f a4`

We received a write response and then

In summary, these are the three payloads we sent:
 - `00 01 80 00 00 04 05 0a 81 8a 8b 96`
 - `00 02 80 00 00 0c 0d 0b 10 14 16 0a 1d 0e 20 00 06 00 0f a4`
 - `00 03 80 00 00 0c 0d 0b 10 14 16 0a 1d 0e 20 00 06 00 0f a4`

### Toggling the light on and off from the app

I think the first "on" request looks like this:

- Service: 0xffff
- UUID: 0xff01
Payload: `02 02 00 1c 00 18 00 04 00 12 17 00 00 04 80 00 00 0d 0e 0b 3b 24 00 00 00 00 00 00 00 32 00 00 91`

which results in receiving this:
`3e 00 04 00 1b 14 00 04 44 80 00 00 33 34 0c     7b22636f6465223a302c227061796c6f6164223a2238313144323432353045303033323332464630303032303033303841227d`
`>D34                                            {"code":0,"payload":"811D24250E003232FF000200308A"}`

The I think the first "off" request looks like this:
- Service: 0xffff
- UUID: 0xff01
Payload: `02 02 00 1c 00 18 00 04 00 12 17 00 00 05 80 00 00 0d 0e 0b 3b 23 00 00 00 00 00 00 00 32 00 00 90`
and we receive:
`3e 00 04 00 1b 14 00 04 45 80 00 00 33 34 0c  7b22636f6465223a302c227061796c6f6164223a2238313144323332353045303033323332464630303032303033303839227d`
`>E34                                         {"code":0,"payload":"811D23250E003232FF0002003089"}`

If I look at just on the on/off messages I sent they look like this:

`02 02 00 1c 00 18 00 04 00 12 17 00 00 04 80 00 00 0d 0e 0b 3b 24 00 00 00 00 00 00 00 32 00 00 91`
`02 02 00 1c 00 18 00 04 00 12 17 00 00 05 80 00 00 0d 0e 0b 3b 23 00 00 00 00 00 00 00 32 00 00 90`
`02 02 00 1c 00 18 00 04 00 12 17 00 00 06 80 00 00 0d 0e 0b 3b 24 00 00 00 00 00 00 00 32 00 00 91`
`02 02 00 1c 00 18 00 04 00 12 17 00 00 07 80 00 00 0d 0e 0b 3b 23 00 00 00 00 00 00 00 32 00 00 90`
`02 02 00 1c 00 18 00 04 00 12 17 00 00 08 80 00 00 0d 0e 0b 3b 24 00 00 00 00 00 00 00 32 00 00 91`
`02 02 00 1c 00 18 00 04 00 12 17 00 00 09 80 00 00 0d 0e 0b 3b 23 00 00 00 00 00 00 00 32 00 00 90`
`02 02 00 1c 00 18 00 04 00 12 17 00 00 0a 80 00 00 0d 0e 0b 3b 24 00 00 00 00 00 00 00 32 00 00 91`
`02 02 00 1c 00 18 00 04 00 12 17 00 00 0b 80 00 00 0d 0e 0b 3b 23 00 00 00 00 00 00 00 32 00 00 90`
`02 02 00 1c 00 18 00 04 00 12 17 00 00 0c 80 00 00 0d 0e 0b 3b 24 00 00 00 00 00 00 00 32 00 00 91`
`02 02 00 1c 00 18 00 04 00 12 17 00 00 0d 80 00 00 0d 0e 0b 3b 23 00 00 00 00 00 00 00 32 00 00 90`
`02 02 00 1c 00 18 00 04 00 12 17 00 00 0e 80 00 00 0d 0e 0b 3b 24 00 00 00 00 00 00 00 32 00 00 91`

`counter? ------------------------------^`
`on/off command? -----------------------------------------------^`
`checksum? --------------------------------------------------------------------------------------^`


# Response data

A combination of 8 bytes of hex, then a JSON like string.

8 bytes format of:

```
seems fixed -----------------------------------------------------v------v
the same 80 00 00 we see elsewhere ---------------------v------v |      |
counter ---------------------------------------------v  |      | |      |
                                                     |  |      | |      |
                                                 `04 5e 80 00 00 33 34 0a`
                                                 `04 60 80 00 00 33 34 0c`
                                                 `04 61 80 00 00 33 34 0c`
                                                 `04 62 80 00 00 33 34 0c`
                                                 `04 63 80 00 00 33 34 0c`
```

In summary: nothing very interesting

The JSON payload looks like:

```
0x30 = 48 decimal which is how many leds this thing has (makes no diff) -----v
blue ------------------------------------------------------------v           |
green --------------------------------------------------------v  |           |
red -------------------------------------------------------v  |  |           |
guess mode ------------------------------------------v     |  |  |           |
guess off = 24, on = 23 -----------------------v     |     |  |  |           |
fixed -----------------------------------v--v  |     |     |  |  |           |
                                         81 1D 24 24 02 00 64 32 FF 00 02 00 30 AF
                                         81 1D 23 61 0F 31 64 32 FF 64 02 00 30 8D
                                         81 1D 23 61 0F 31 64 32 FF 00 02 00 30 29
                                         81 1D 23 61 F0 00 FF 00 00 00 02 00 30 43
                                         81 1D 23 61 F0 00 00 FF 00 00 02 00 30 43
                                         81 1D 23 61 F0 00 00 00 FF 00 02 00 30 43
                                         81 1D 23 25 01 00 64 32 FF 00 02 00 30 AE
                                         81 1D 23 25 02 00 64 32 FF 00 02 00 30 AF
                                         81 1D 23 25 03 00 64 32 FF 00 02 00 30 B0
                                         81 1D 23 25 04 00 64 32 FF 00 02 00 30 B1
                                         81 1D 23 25 05 00 64 32 FF 00 02 00 30 B2
```

{"code":0,"payload":"81 1D 24 24 02 00 64 32 FF 00 02 00 30 AF"}'.
{"code":0,"payload":"811D232402006432FF00020030AE"}'.


Setting white temperature to 100% and 50% brightness
{"code":0,"payload":"811D23610F316432FF640200308D"}'.



Setting white temperature to 0% and 50% brightness
{"code":0,"payload":"811D23610F316432FF0002003029"}'.


Setting RGB colour: 255, 0, 0
{"code":0,"payload":"811D2361F000FF00000002003043"}'.



Setting RGB colour: 0, 255, 0
{"code":0,"payload":"811D2361F00000FF000002003043"}'.

Setting RGB colour: 0, 0, 255
{"code":0,"payload":"811D2361F0000000FF0002003043"}'.

Setting mode: 1
{"code":0,"payload":"811D232501006432FF00020030AE"}'.


Setting mode: 2
{"code":0,"payload":"811D232502006432FF00020030AF"}'.

Setting mode: 3
{"code":0,"payload":"811D232503006432FF00020030B0"}'.


Setting mode: 4
{"code":0,"payload":"811D232504006432FF00020030B1"}'.

Setting mode: 5
{"code":0,"payload":"811D232505006432FF00020030B2"}'.

Setting mode: 6
{"code":0,"payload":"811D232506006432FF00020030B3"}'.

Setting mode: 7
{"code":0,"payload":"811D232507006432FF00020030B4"}'.

Setting mode: 8
{"code":0,"payload":"811D232508006432FF00020030B5"}'.

Setting mode: 9
{"code":0,"payload":"811D232509006432FF00020030B6"}'.
Setting mode: 10
{"code":0,"payload":"811D23250A006432FF00020030B7"}'
{"code":0,"payload":"811D232402006432FF00020030AE"}'



## White


81 1D 23 61 0F 31 64 32 FF 64 02 00 30 8D - Setting white temperature to 100% and 50% brightness
81 1D 23 61 0F 31 64 32 FF 00 02 00 30 29 - Setting white temperature to 0% and 50% brightness


temperature ---------------v        
mode -                     |        
white br ------v           |        
mode--------v  |           |        
            |  |           |        
81 1D 23 61 0F 31 64 32 FF 64 02 00 30 8D - Setting white temperature to 100% and 50% brightness
81 1D 23 61 0F 31 64 32 FF 4B 02 00 30 74 - Setting white temperature to 75% and 50% brightness
81 1D 23 61 0F 31 64 32 FF 32 02 00 30 5B - Setting white temperature to 50% and 50% brightness
81 1D 23 61 0F 31 64 32 FF 19 02 00 30 42 - Setting white temperature to 25% and 50% brightness
81 1D 23 61 0F 31 64 32 FF 32 02 00 30 5B - Setting white temperature to 50% and 50% brightness
81 1D 23 61 0F 31 64 32 FF 4B 02 00 30 74 - Setting white temperature to 75% and 50% brightness
81 1D 23 61 0F 31 64 32 FF 64 02 00 30 8D - Setting white temperature to 100% and 50% brightness
81 1D 23 61 0F 00 64 32 FF 64 02 00 30 5C - Setting white temperature to 100% and 1% brightness
81 1D 23 61 0F 18 64 32 FF 64 02 00 30 74 - Setting white temperature to 100% and 25% brightness
81 1D 23 61 0F 31 64 32 FF 64 02 00 30 8D - Setting white temperature to 100% and 50% brightness
81 1D 23 61 0F 4A 64 32 FF 64 02 00 30 A6 - Setting white temperature to 100% and 75% brightness
81 1D 23 61 0F 64 64 32 FF 64 02 00 30 C0 - Setting white temperature to 100% and 100% brightness


## Symphony



                           b  s
Payload: 81 1D 23 25 02 00 64 32 FF 00 02 00 30 AF Mode: 2
Payload: 81 1D 23 25 03 00 64 32 FF 00 02 00 30 B0 mode: 3
Payload: 81 1D 23 25 04 00 64 32 FF 00 02 00 30 B1 Mode: 4
Payload: 81 1D 23 25 05 00 64 32 FF 00 02 00 30 B2 Mode: 5
Payload: 81 1D 23 25 06 00 64 32 FF 00 02 00 30 B3 Mode: 6
Payload: 81 1D 23 25 07 00 64 32 FF 00 02 00 30 B4 Mode: 7 
Payload: 81 1D 23 25 08 00 64 32 FF 00 02 00 30 B5 Mode: 8 
Payload: 81 1D 23 25 09 00 64 32 FF 00 02 00 30 B6 Mode: 9
Payload: 81 1D 23 25 0A 00 64 32 FF 00 02 00 30 B7 Mode: 10 


# Small vs big ring


small first packet:  811D2425FF00323200000200307C 

  big 81 1D 23 61 0F 31 32 32 FF 64 02 00 30 5B
040180000033340a


small 81 1D 24 24 02 00 64 32 FF 00 02 00 30 AF

sml   04 02 80 00 00 33 34 0a
bigm  04 01 80 00 00 33 34 0a

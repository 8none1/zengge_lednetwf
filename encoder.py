#!usr/env python3

PACKET_COUNTER = 0

SPECIAL_SECRET_ARRAY = [
    0x11,
    0x22,
    0x4,
    0x8,
    -0x67,
    0x4,
    0x24,
    0x16,
    0x4,
    -0x56,
    -0x45,
    -0x34,
    -0x10,
    0x60,
    0x61,
    -0x33,
    -0x31,
    -0x80,
    0x35,
    0x2a
]

def get_packet_counter():
    global PACKET_COUNTER
    PACKET_COUNTER += 1
    return PACKET_COUNTER

def encrypt1(incoming_array, rand_num, thing1, thing2):
    for i,item in enumerate(incoming_array):
        incoming_array[i] = item ^ rand_num
    return incoming_array

def encrypt2(incoming_array, startpos, length):
    for i,item in enumerate(incoming_array, start=startpos):
        incoming_array[i] = item ^ SPECIAL_SECRET_ARRAY[startpos - i]
        # I think this is trying to read from the start of SPECIAL_SECRET_ARRAY and then move 
        # through the array on each loop, but the smali and the decompliled Java both seem to 
        # subtract the wrong way around and end up with negative numbers.
        # e.g. 
        #  bArr[i] = (byte) (bArr[i] ^ args[i - startpos]);
        # where args = SPECIAL_SECRET_ARRAY and i is the loop counter

def to_crc(incoming_array):
    sum = 0
    limit = len(incoming_array-2) # might need to be -1?
    for index, item in incoming_array:
        sum += item
        if index == limit: break
    sum = sum & 0xffff
    return sum

def reversal(incoming_array):
    v0 = 2
    v1 = len(incoming_array)
    v1 = v1 - 1
    while (v0 <= v1):
        v1 = incoming_array[v0]
        v2 = v0 + 1
        v3 = incoming_array[v2]
        incoming_array[v0] = v3
        incoming_array[v2] = v1
        v0 = v2 + 1
    return incoming_array
 

def encoder( p0, p1, p2, incoming_array):
    # p0 = byte
    # p1 = byte
    # p2 = int
    count = 1
    v0 = 9
    v1 = 0
    # v2 is a copy of the 9 element array passed in incoming_array
    if len(incoming_array) is not 0: (# could check type here as well)
        alen = len(incoming_array)
        if alen > v0:
            if alen > v0:
                print("Array to long")
                return False

        header = [0x5a, 0x71, 0x0, 0x11, 0x0, p1, get_packet_counter(), p2, 0x0, 0x0]

        new_array = [None] * 26 # should be sized? 0x1a

        # I think this is saying of the int passed in we only
        # want the first two bytes
        # If we sent in 0xac000000 we would get 0xac00 (the last byte would always be 0x00)
        # This could be our 0x8000000 thing?  If the top bit of 32 bit number is set, and
        # then shifted 16 bits to the right, we get 0x8000
        v5 = p2 & 0xff0000 # p2 is an int
        v5 = v5 >> 0x10
        new_array[7] = v5
        # Could this be dealing with a large number and spreading it across two bytes?
        v5 = p2 & 0xff00 
        v5 = v5 >> 0x8
        new_array[8] = v5
        p2 = p2 & 0xff
        new_array[9] = p2
        new_array[10] = 0
        new_array[11] = 0
        new_array[12] = p0
        # invoke-static {p3, v1, v3, p0, v0}, Ljava/lang/System;->arraycopy(Ljava/lang/Object;ILjava/lang/Object;II)V
        #               {src, srcPos, dest, destPos, length}
        # invoke-static {new_array, 0, new_array_2, 13, len(new_array)}, array copy 
        start_pos = 13
        for each in incoming_array:
            new_array[start_pos] = each
            start_pos += 1
        rand_int = random.randint()
        rand_int = rand_int & 0xff
        new_array2[23] = rand_int # 0x17
        new_array = encrypt1(new_array, rand_int, 0xa, 0x16)
        new_array = encrypt2(new_array, 0x4, 0x17)
        crc_result = to_crc(new_array)
        first_crc = 0xff00 & crc
        first_crc = first_crc >> 0x8
        first_crc = first_crc & 0xff
        new_array2[0x18] = first_crc # d 24
        second_crc = crc_result & 0xff
        new_array2[0x19] = second_crc #25
        new_array2 = reversal(new_array2)
        print(new_array2)


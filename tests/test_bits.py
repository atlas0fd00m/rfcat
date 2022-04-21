import unittest
import rflib.bits as rfbits

class BitsTest(unittest.TestCase):
    def test_bits(self):
        # test correctbytes
        rfbits.correctbytes(24)



        self.assertEqual(
                rfbits.genBitArray(b'asdfasdfasdfaf', 20,23),
                ([0x0, 0x1, 0x0, 0x0, 0x0, 0x0, 0x0, 0x0], 0.6666666666666666)
                )

        self.assertEqual(
                rfbits.strBitReverse(b'asdf'),
                b'f&\xce\x86'
                )

        self.assertEqual(
                rfbits.strXorMSB(b'asdfasdfadfasfdsa', 0x1234, 2),
                b'sGvRsGvRsPtUaRvGs4'
                )

        self.assertEqual(
                rfbits.bitReverse(0x45, 16),
                0xa200
                )

        self.assertEqual(
                rfbits.shiftString(b'asdfasdf', 1),
                b'\xc2\xe6\xc8\xcc\xc2\xe6\xc8\xcc'
                )

        self.assertEqual(
                rfbits.shiftString(b'asdfasdf', 0),
                b'asdfasdf'
                )

        self.assertEqual(
                rfbits.shiftString(b'asdfasdf', 7),
                b'\xb9\xb230\xb9\xb23\x00'
                )

        self.assertEqual(
                rfbits.shiftString(b'asdfasdf', 8),
                b'sdfasdf\x00'
                )

        self.assertEqual(
                rfbits.whitenData(b'asdfasdfasdfasdf'),
                b'\x9fn\x81\xf4e?9\nx\xda\xab\x0e4\x87\xc7'
                )


        '''
        128:def getNextByte_feedbackRegister7bitsLSB():
        158:def findSyncWord(byts, sensitivity=4, minpreamble=2):
        218:def findSyncWordDoubled(byts):
        292:def visBits(data):
        297:def getBit(data, bit):
        305:def detectRepeatPatterns(data, size=64, minEntropy=.07):
        373:def bitSectString(string, startbit, endbit):
        419:def genBitArray(string, startbit, endbit):
        470:def reprBitArray(bitAry, width=194):
        498:def invertBits(data):
        525:def diff_manchester_decode(data, align=False):
        579:def biphase_mark_coding_encode(data):
        605:def manchester_decode(data, hilo=1):
        633:def manchester_encode(data, hilo=1):
        655:def findManchesterData(data, hilo=1):
        666:def findManchester(data, minbytes=10):
        '''

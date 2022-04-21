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

        self.assertEqual(   # this tests getNextByte_feedbackRegister7bitsLSB too
                rfbits.whitenData(b'asdfasdfasdfasdf'),
                b'\x9fn\x81\xf4e?9\nx\xda\xab\x0e4\x87\xc7'
                )

        byts = b'\x0a\xaa\xaa\xaa\x34\x35\x34\x36sdfasdfasdfasdfasdfasdfasdfasdfasdfasdf\xaa\xaa\xaa\xaa45\xc6\xdfasdfasdf'
        self.assertEqual(
                rfbits.findSyncWord(byts, sensitivity=4, minpreamble=2),
                [0xd0d4,
                 0x686a,
                 0x3435,
                 0x1a1a,
                 0x8d0d,
                 0x4686,
                 0xa343,
                 0x51a1,
                 0xd0d7,
                 0x686b]
                )

        self.assertEqual(
            rfbits.findSyncWordDoubled(b'\x0a\xaa\xaa\xaa\x34\x35\x34\x35sdfasdfasdfasdfasdfasdfasdfasdfasdfasdf\xaa\xaa\xaa\xaa45\xc6\xdfasdfasdf'),
            [0x34353435]
            )

        self.assertEqual(
                rfbits.genBitArray(b'\x0a\xaa\xaa\xaa\x34\x35\x34\x35sdfasdfasdfasdfasdfasdfa', 3, 16),
                ([0x0,
                  0x1,
                  0x0,
                  0x1,
                  0x0,
                  0x1,
                  0x0,
                  0x1,
                  0x0,
                  0x1,
                  0x0,
                  0x1,
                  0x0,
                  0x0,
                  0x0,
                  0x0],
                 1.0)
                )

        self.assertEqual(
                rfbits.reprBitArray(rfbits.genBitArray(b'\x0a\xaa\xaa\xaa\x34\x35\x34\x35sdfasdfasdfasdfasdfasdfasdfasdfasdfasdf\xaa\xaa\xaa\xaa45\xc6\xdfasdfasdf', 45, 122)[0]),
                b'/-\\  /-\\     /--\\   /\\          /---\\  /-\\  /-\\  /-----\\     /---\\  /---\\     /-\\       /---\\    /---\\     /---\\          /\\   /-----\\     /---\\  /---\\     /\\       /---\\     /---\\     /\\       \n   ||   |   |    | |  |        |     ||   ||   ||       |   |     ||     |   |   |     |     |  |     |   |     |        |  | |       |   |     ||     |   |  |     |     |   |     |   |  |      \n   \\/   \\---/    \\-/  \\--------/     \\/   \\/   \\/       \\---/     \\/     \\---/   \\-----/     \\--/     \\---/     \\--------/  \\-/       \\---/     \\/     \\---/  \\-----/     \\---/     \\---/  \\------'
                )

        self.assertEqual(
                rfbits.invertBits(b'\x0a\xaa\xaa\xaa'),
                b'\xf5UUU'
                )

        self.assertEqual(
                rfbits.detectRepeatPatterns(b'asdfasdfasdfasdfasdfasdfasdfasdf'),
                [(0x0, 0x80, 0x80, 0xc2e6c8ccc2e6c8cc)]
                )

        '''
        305:def detectRepeatPatterns(data, size=64, minEntropy=.07):
        525:def diff_manchester_decode(data, align=False):
        579:def biphase_mark_coding_encode(data):
        605:def manchester_decode(data, hilo=1):
        633:def manchester_encode(data, hilo=1):
        655:def findManchesterData(data, hilo=1):
        666:def findManchester(data, minbytes=10):
        '''

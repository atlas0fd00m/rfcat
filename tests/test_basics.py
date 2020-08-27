import unittest

class RfCatBasicTests(unittest.TestCase):

    def test_importing(self):
        import rflib
        devs = rflib.getRfCatDevices()
        self.assertEqual(type(devs), list, "rflib.getRfCatDevices() doesn't return a list!: %r" % devs)
        import rflib.chipcon_nic
        import rflib.chipcon_usb
        import rflib.chipcondefs
        import rflib.bits
        import rflib.ccspecan
        import rflib.intelhex
        import rflib.rflib_defs


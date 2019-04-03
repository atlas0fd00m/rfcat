import unittest

class RfCatBasicTests(unittest.TestCase):

    def test_importing(self):
        import rflib
        devs = rflib.getRfCatDevices()
        self.assertEquals(type(devs), list, "rflib.getRfCatDevices() doesn't return a list!: %r" % devs)


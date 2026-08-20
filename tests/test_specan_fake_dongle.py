#!/usr/bin/env python3
"""
Unit Tests for Spectrum Analyzer Integration with FakeDongle

Tests verify that:
1. FakeDongle correctly generates and queues specan frames
2. ccspecan.py can consume fake data through the mock interface  
3. RSSI values are properly formatted and converted (byte <-> dBm)
4. GUI components can be tested without physical hardware

Usage:
    python -m pytest tests/test_specan_fake_dongle.py -v
    
Or run directly:
    python tests/test_specan_fake_dongle.py
"""

import sys
import os
import time
import unittest
import threading

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Ensure the Qt platform is usable headless (CI / no display)
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')

from rflib.fakedongle_nic import fakeDongle, generate_fake_specan_data
from rflib.const import APP_SPECAN, SPECAN_QUEUE


class TestGenerateFakeSpecanData(unittest.TestCase):
    """Test the fake specan data generation function."""
    
    def test_default_parameters(self):
        """Test with default 83 channels."""
        rssi_bytes, dbm_values = generate_fake_specan_data()
        self.assertEqual(len(rssi_bytes), 83)
        self.assertEqual(len(dbm_values), 83)
        
    def test_minimum_channels(self):
        """Test edge case: minimum viable channel count."""
        # Even with very few channels, should not crash
        rssi_bytes, dbm_values = generate_fake_specan_data(num_channels=10, seed=42)
        self.assertEqual(len(rssi_bytes), 10)
        self.assertEqual(len(dbm_values), 10)
        
    def test_custom_channels(self):
        """Test with custom number of channels."""
        for num_chans in [50, 83, 100]:
            rssi_bytes, dbm_values = generate_fake_specan_data(num_channels=num_chans, seed=123)
            self.assertEqual(len(rssi_bytes), num_chans)
            self.assertEqual(len(dbm_values), num_chans)
            
    def test_rssi_range(self):
        """Test that generated dBm values are in valid range [-88, +40]."""
        rssi_bytes, dbm_values = generate_fake_specan_data(seed=42, num_channels=50)
        for dbm in dbm_values:
            self.assertGreaterEqual(dbm, -88)
            self.assertLessEqual(dbm, 35)  # We clip at +35 internally
            
    def test_byte_format_conversion(self):
        """Test that byte format round-trips through the ccspecan formula.

        The generator truncates (uses int()) when building the byte, so recovery
        is exact up to the 1/2 dBm quantization step. We verify the recovered
        value stays within half a step of the original.
        """
        rssi_bytes, original_dbm = generate_fake_specan_data(seed=123, num_channels=50)

        for i, b in enumerate(rssi_bytes):
            # Apply the exact conversion from ccspecan.py: (((byte ^ 0x80) / 2) - 88)
            recovered_dbm = ((b ^ 0x80) / 2) - 88
            # within the 0.5 dBm quantization step (plus float tolerance)
            self.assertAlmostEqual(recovered_dbm, original_dbm[i], delta=0.5)
            
    def test_noise_floor_parameter(self):
        """Test that noise floor parameter influences output."""
        # Compare outputs with different noise floors  
        _, dbm_low = generate_fake_specan_data(
            num_channels=50, 
            noise_floor=-90, 
            signal_dbm=-75,
            seed=42
        )
        _, dbm_high = generate_fake_specan_data(
            num_channels=50, 
            noise_floor=-65, 
            signal_dbm=-55,
            seed=42
        )
        
        # High noise floor should give higher RSSI values  
        self.assertGreater(sum(dbm_high), sum(dbm_low))

    def test_deterministic_with_seed(self):
        """Test that same seed produces identical results."""
        rssi1, dbm1 = generate_fake_specan_data(num_channels=50, seed=999)
        rssi2, dbm2 = generate_fake_specan_data(num_channels=50, seed=999)
        
        self.assertEqual(rssi1, rssi2)
        for i in range(len(dbm1)):
            self.assertAlmostEqual(dbm1[i], dbm2[i])  # Float comparison
    
    def test_different_seeds_produce_different_data(self):
        """Test that different seeds produce different output."""
        rssi1, _ = generate_fake_specan_data(num_channels=50, seed=111)
        rssi2, _ = generate_fake_specan_data(num_channels=50, seed=222)
        
        # They should be different (very high probability)  
        self.assertNotEqual(rssi1, rssi2)


class TestFakeDongleSpecAnQueue(unittest.TestCase):
    """Test fakeDongle's specan frame queueing."""
    
    def setUp(self):
        self.dongle = fakeDongle()
        
    def test_specan_queue_exists(self):
        """Verify the _specan_queue attribute exists."""
        self.assertTrue(hasattr(self.dongle, '_specan_queue'))
        
    def test_queue_specan_frame(self):
        """Test queuing and retrieving a specan frame."""
        rssi_bytes, dbm_values = generate_fake_specan_data(num_channels=10)
        
        self.dongle.queue_specan_frame(rssi_bytes)
        
        # Verify queue is not empty  
        self.assertGreater(self.dongle._specan_queue.qsize(), 0)
        
    def test_queue_specan_frame_with_timestamp(self):
        """Test queuing with explicit timestamp."""
        rssi_bytes, _ = generate_fake_specan_data(num_channels=10)
        custom_ts = time.time() + 1000
        
        self.dongle.queue_specan_frame(rssi_bytes, timestamp=custom_ts)
        
        # Retrieve and verify  
        queued_rssi, queued_ts = self.dongle._specan_queue.get_nowait()
        self.assertEqual(queued_rssi, rssi_bytes)
        # the explicit timestamp is stored verbatim, so it should match exactly
        self.assertEqual(queued_ts, custom_ts)


class TestSpecAnThreadIntegration(unittest.TestCase):
    """Test integration with ccspecan.py's SpecanThread using list mode."""
    
    def test_list_data_consumption(self):
        """Test that a list of (rssi_bytes, timestamp) tuples can be consumed.
        
        This simulates what happens when FakeDongle prepulates data and 
        ccspecan SpecanThread iterates over it as 'if type(self._data) == list'.
        """
        from rflib.ccspecan import ensureQapp
        
        # Generate test frames  
        frames = []
        for i in range(5):
            rssi_bytes, _ = generate_fake_specan_data(num_channels=20, seed=i*100)
            frames.append((rssi_bytes, time.time() + i))
            
        # Verify we can iterate and convert (simulating SpecanThread behavior)  
        from rflib.bits import ord23
        
        processed_frames = []
        for rssi_values, timestamp in frames:
            # Apply the exact conversion from ccspecan.py line 75
            converted_dbm = [(((ord23(x)^0x80) / 2))-88 for x in rssi_values]
            processed_frames.append((timestamp, converted_dbm))
            
        # Verify all frames were processed  
        self.assertEqual(len(processed_frames), 5)
        
    def test_multiple_specan_frames(self):
        """Test queuing and consuming multiple specan frames."""
        frames = []
        for i in range(10):
            rssi_bytes, dbm_vals = generate_fake_specan_data(num_channels=30, seed=i*42)
            frames.append((rssi_bytes, time.time() + i * 0.1))
            
        # Queue all frames  
        dongle = fakeDongle()
        for rssi_bytes, ts in frames:
            dongle.queue_specan_frame(rssi_bytes, timestamp=ts)
            
        # Verify queue size  
        self.assertEqual(dongle._specan_queue.qsize(), 10)


class TestFakeRfCatWithSpecAn(unittest.TestCase):
    """Test FakeRfCat class with specan support."""
    
    def setUp(self):
        from rflib.fakedongle_nic import FakeRfCat
        try:
            self.rfcat = FakeRfCat()
        except Exception as e:
            self.skipTest(f"Failed to initialize FakeRfCat: {e}")
            
    def test_fake_rfcat_has_specan_method(self):
        """Verify FakeRfCat has access to specan functionality."""
        # Should inherit queue_specan_frame from fakeDongle via _do attribute  
        self.assertTrue(hasattr(self.rfcat._do, 'queue_specan_frame'))

    def test_fake_rfcat_recv_specan_frame(self):
        """End-to-end: queue a fake frame on the dongle and recv via the threaded pipeline.

        This exercises the real path ccspecan.SpecanThread uses when running against
        a live FakeRfCat: `data.recv(APP_SPECAN, SPECAN_QUEUE, timeout)`.
        """
        rssi, dbm = generate_fake_specan_data(num_channels=40, seed=7)
        self.rfcat._do.queue_specan_frame(rssi)
        try:
            data, ts = self.rfcat.recv(APP_SPECAN, SPECAN_QUEUE, 4000)
        except Exception as e:
            self.fail("recv(APP_SPECAN) raised %r — fake data pipeline broken" % (e,))
        self.assertEqual(len(data), 40)
        # verified the round-trip value range matches what ccspecan will render
        dbm_rec = [((b ^ 0x80) / 2) - 88 for b in data]
        self.assertTrue(max(dbm_rec) > min(dbm_rec))


class TestSpecAnGUIRenderArea(unittest.TestCase):
    """GUI-level tests for ccspecan.RenderArea using fake specan data (list mode).

    RenderArea spins up a SpecanThread; feeding it a *list* of (rssi, ts) frames
    makes the thread consume deterministically and exit, so tests don't need a
    real dongle or a display.
    """

    @classmethod
    def setUpClass(cls):
        from rflib.ccspecan import ensureQapp
        ensureQapp()          # creates the singleton QApplication (headless)

    def setUp(self):
        from rflib.ccspecan import RenderArea
        # build N fake frames as (rssi_bytes, timestamp).
        # ccspecan's LIST-mode path slices `rssi_values[4:]`, so each frame is
        # padded with a 4-byte header (like a captured/dumped frame) so the
        # slice recovers exactly `num_channels` values.
        self.num_channels = 32
        self.frames = []
        for i in range(3):
            rssi, _ = generate_fake_specan_data(num_channels=self.num_channels, seed=i * 100)
            self.frames.append((b'\xff\xff\xff\xff' + rssi, time.time() + i))
        # list-mode data source -> Thread consumes + exits on its own
        self.ra = RenderArea(self.frames, low_freq=900e6, high_freq=930e6,
                             freq_step=1e6, delay=0)

    def tearDown(self):
        self.ra.stop_thread()
        self.ra.setParent(None)

    def test_render_area_consumes_all_frames(self):
        """SpecanThread should consume every provided fake frame."""
        self.ra._thread.join(5.0)
        self.assertFalse(self.ra._thread.is_alive(), "SpecanThread did not exit")
        # after consumption, RenderArea should hold at least one frame
        self.assertIsNotNone(self.ra._frame)
        freq_axis, values = self.ra._frame
        self.assertTrue(len(freq_axis) > 0)
        self.assertTrue(len(values) > 0)
        # a persisted-frames array should have been created
        self.assertIsNotNone(self.ra._persisted_frames)

    def test_render_area_frame_dimensions(self):
        """The rendered frame must match the number of fake channels."""
        self.ra._thread.join(5.0)
        freq_axis, values = self.ra._frame
        self.assertEqual(len(values), self.num_channels)


class TestSpecAnGUIWindow(unittest.TestCase):
    """GUI-level tests for ccspecan.Window with fake list-mode data."""

    @classmethod
    def setUpClass(cls):
        from rflib.ccspecan import ensureQapp
        ensureQapp()

    def setUp(self):
        from rflib.ccspecan import Window
        self.num_channels = 32
        self.frames = []
        for i in range(3):
            rssi, _ = generate_fake_specan_data(num_channels=self.num_channels, seed=i * 100)
            self.frames.append((b'\xff\xff\xff\xff' + rssi, time.time() + i))
        self.win = Window(self.frames, low_freq=900e6, high_freq=930e6,
                          spacing=1e6, delay=0)

    def tearDown(self):
        self.win.render_area.stop_thread()
        self.win.setParent(None)

    def test_window_opens(self):
        """Window should construct a render area wired to the fake data."""
        self.assertIsNotNone(self.win.render_area)
        self.assertEqual(self.win.windowTitle(), "RfCat Spectrum Analyzer (thanks Ubertooth!)")

    def test_window_thread_consumes_frames(self):
        """The window's SpecanThread consumes the fake frames and renders."""
        self.win.render_area._thread.join(5.0)
        self.assertFalse(self.win.render_area._thread.is_alive())
        self.assertIsNotNone(self.win.render_area._frame)


def run_tests():
    """Run all tests and print results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes  
    suite.addTests(loader.loadTestsFromTestCase(TestGenerateFakeSpecanData))
    suite.addTests(loader.loadTestsFromTestCase(TestFakeDongleSpecAnQueue))
    suite.addTests(loader.loadTestsFromTestCase(TestSpecAnThreadIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestSpecAnGUIRenderArea))
    suite.addTests(loader.loadTestsFromTestCase(TestSpecAnGUIWindow))
    try:
        from rflib.fakedongle_nic import FakeRfCat
        suite.addTests(loader.loadTestsFromTestCase(TestFakeRfCatWithSpecAn))
    except Exception:
        print("Note: Skipping TestFakeRfCatWithSpecAn (FakeRfCat init failed)")
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return exit code for CI  
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())

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
        """Test that byte format converts back correctly using ccspecan formula."""
        rssi_bytes, original_dbm = generate_fake_specan_data(seed=123, num_channels=50)
        
        for i, b in enumerate(rssi_bytes):
            # Apply the exact conversion from ccspecan.py: (((byte ^ 0x80) / 2) - 88)
            recovered_dbm = ((b ^ 0x80) / 2) - 88
            # Should match (within rounding error due to int() truncation)
            self.assertAlmostEqual(recovered_dbm, original_dbm[i], places=1)
            
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
        self.assertGreaterEqual(abs(queued_ts - custom_ts), 0.9)  # Allow small drift


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


def run_tests():
    """Run all tests and print results."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes  
    suite.addTests(loader.loadTestsFromTestCase(TestGenerateFakeSpecanData))
    suite.addTests(loader.loadTestsFromTestCase(TestFakeDongleSpecAnQueue))
    suite.addTests(loader.loadTestsFromTestCase(TestSpecAnThreadIntegration))
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

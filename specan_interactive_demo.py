#!/usr/bin/env python3
"""
Interactive Spectrum Analyzer Demo with FakeDongle

Usage:
    python specan_interactive_demo.py
    
This script will:
- Use FakeDongle instead of physical hardware  
- Generate fake RSSI data and queue it to the specan buffer
- Open a GUI window showing the spectrum in real-time
- Continuously generate new frames every ~100ms

Controls in GUI:
- Mouse click: Set marker X position  
- Middle mouse click: Clear markers
"""

import sys
import time
import threading
import random

# Mock headless environment if no display
if 'DISPLAY' not in __import__('os').environ and not hasattr(__import__('sys'), 'argv'):
    print("Note: Running without display - GUI may not appear")

try:
    from rflib.fakedongle_nic import FakeRfCat, generate_fake_specan_data
    from rflib.ccspecan import Window
except Exception as e:  
    print(f"Error importing modules: {e}")
    sys.exit(1)

def specan_generator(dongle, interval=0.1):
    """Background thread that generates and queues fake specan frames."""
    print(f"[Generator] Starting with {interval}s interval...")
    
    frame_count = 0
    while True:
        try:
            # Generate new data with slight variation each time
            noise_floor = -75 + random.uniform(-2, 2)
            signal_strength = -50 + random.uniform(-3, 3)
            
            rssi_bytes, dbm_values = generate_fake_specan_data(
                num_channels=83, 
                noise_floor=noise_floor,
                signal_dbm=signal_strength,
                seed=int(time.time() * 1000)  # Pseudo-random but reproducible per second
            )
            
            frame_count += 1
            
            # Optionally print status every 50 frames
            if frame_count % 50 == 0:
                avg_dbm = sum(dbm_values) / len(dbm_values)
                peak_dbm = max(dbm_values)
                print(f"[Generator] Frame {frame_count}: avg={avg_dbm:.1f}dBm, peak={peak_dbm:.1f}dBm")
            
            # Queue the frame (ccspecan will consume it)  
            dongle.queue_specan_frame(rssi_bytes)
            
        except Exception as e:
            print(f"[Generator] Error: {e}")
        
        time.sleep(interval)

def main():
    print("=" * 50)
    print("Interactive Spectrum Analyzer Demo (FakeDongle)")
    print("=" * 50)
    
    # Initialize FakeRfCat instead of real hardware  
    print("\n[1/4] Initializing FakeDongle...")
    try:
        fake_cat = FakeRfCat()
        print(f"      Done! Fake dongle ready.")
    except Exception as e:
        print(f"      ERROR: Failed to initialize FakeDongle: {e}")
        sys.exit(1)
    
    # Start generator thread  
    print("[2/4] Starting fake data generator...")
    gen_thread = threading.Thread(
        target=specan_generator, 
        kwargs={'dongle': fake_cat._do, 'interval': 0.1},
        daemon=True
    )
    gen_thread.start()
    
    # Give generator time to queue a few frames  
    print("[3/4] Pre-filling specan buffer...")
    time.sleep(0.5)
    
    # Launch the GUI window (this blocks until window is closed)
    print("[4/4] Opening spectrum analyzer GUI window...")
    print("      Press Ctrl+C to quit")
    print()
    
    try:
        Window(d=fake_cat, 
               low_freq=2.400e9, 
               high_freq=2.483e9,  # 2.4GHz ISM band  
               freq_step=1e6)       # 1MHz resolution
    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
    except Exception as e:
        print(f"\nGUI Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

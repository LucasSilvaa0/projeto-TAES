import unittest
import time
import random

class TestFlakyExample(unittest.TestCase):
    def setUp(self):
        self.shared_value = 0
    
    def test_race_condition(self):
        self.shared_value += 1
        time.sleep(random.random())  # Flaky!
        self.assertEqual(self.shared_value, 1)
    
    def test_timing_dependent(self):
        start = time.time()
        time.sleep(0.1)  # Depende de timing
        end = time.time()
        self.assertLess(end - start, 0.2)

import unittest

# The problematic lambda from production_worker.py
sanitize_buggy = lambda t: t.replace('\x00', '') if t else None

# The fixed lambda
sanitize_fixed = lambda t: t.replace('\x00', '') if t is not None else None

class TestSanitize(unittest.TestCase):
    def test_buggy_behavior(self):
        """Verify that the bug exists: empty string becomes None."""
        self.assertIsNone(sanitize_buggy(""))
        self.assertEqual(sanitize_buggy("hello"), "hello")
        self.assertIsNone(sanitize_buggy(None))

    def test_fixed_behavior(self):
        """Verify the fix: empty string remains empty string."""
        self.assertEqual(sanitize_fixed(""), "")
        self.assertEqual(sanitize_fixed("hello"), "hello")
        self.assertIsNone(sanitize_fixed(None))
        self.assertEqual(sanitize_fixed("\x00hello"), "hello")

if __name__ == '__main__':
    unittest.main()

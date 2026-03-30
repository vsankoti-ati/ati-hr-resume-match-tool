#!/usr/bin/env python3
"""
Test script for PII masking functionality
"""
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.pii_masker import mask_pii_in_text

def test_pii_masking():
    """Test PII masking with sample text"""

    # Sample resume text with PII
    sample_text = """
    John Smith
    Email: john.smith@email.com
    Phone: (555) 123-4567
    Address: 123 Main Street, Anytown, CA 90210

    Professional Summary:
    I am John Smith, a software engineer with 5 years of experience.
    You can reach me at john.smith@email.com or call (555) 123-4567.
    My SSN is 123-45-6789 and I live at 123 Main Street.

    Education:
    Bachelor of Science in Computer Science
    University of California, Berkeley (2015-2019)

    Work Experience:
    Software Engineer at Tech Corp
    January 2020 - Present
    Contact: jane.doe@techcorp.com
    """

    print("=== PII Masking Test ===")
    print("\nOriginal Text:")
    print(sample_text)

    print("\n" + "="*50)

    # Test with regex fallback first (doesn't require Presidio)
    print("\nTesting with regex method:")
    try:
        masked_text, stats = mask_pii_in_text(sample_text, method="regex")
        print(f"Masked Text:\n{masked_text}")
        print(f"\nPII Statistics: {stats}")
    except Exception as e:
        print(f"Regex failed: {e}")

    print("\n" + "="*50)

    # Test with Presidio (may fail if not installed)
    print("\nTesting with Presidio method:")
    try:
        masked_text, stats = mask_pii_in_text(sample_text, method="presidio")
        print(f"Masked Text:\n{masked_text}")
        print(f"\nPII Statistics: {stats}")
    except Exception as e:
        print(f"Presidio failed (expected if not installed): {e}")
        print("This is normal - Presidio requires additional setup")

if __name__ == "__main__":
    test_pii_masking()
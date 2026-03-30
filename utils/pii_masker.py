"""
PII Masking Module
Handles detection and masking of personally identifiable information in text
"""
import logging
import re
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PIIMasker:
    """Handles PII detection and masking in text documents"""

    def __init__(self):
        """Initialize PII masker with regex patterns"""
        # Comprehensive regex patterns for PII detection
        self.pii_patterns = {
            'EMAIL_ADDRESS': [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Standard email
                r'\b[A-Za-z0-9._%+-]+\s*@\s*[A-Za-z0-9.-]+\s*\.\s*[A-Z|a-z]{2,}\b',  # Email with spaces
            ],
            'PHONE_NUMBER': [
                r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b',  # US phone
                r'\b\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',  # International phone
                r'\b\d{3}[-.\s]\d{3}[-.\s]\d{4}\b',  # Simple US format
            ],
            'US_SSN': [
                r'\b\d{3}[-]?\d{2}[-]?\d{4}\b',  # Social Security Number
            ],
            'CREDIT_CARD': [
                r'\b\d{4}[-.\s]?\d{4}[-.\s]?\d{4}[-.\s]?\d{4}\b',  # Credit card numbers
                r'\b\d{4}[-.\s]?\d{6}[-.\s]?\d{5}\b',  # Alternative formats
            ],
            'IP_ADDRESS': [
                r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b',  # IPv4 addresses
            ],
            'US_DRIVER_LICENSE': [
                r'\b[A-Z]\d{7,8}\b',  # California style
                r'\b\d{2}[-.\s]?\d{3}[-.\s]?\d{4}\b',  # Other formats
            ],
            'URL': [
                r'\bhttps?://[^\s<>"{}|\\^`[\]]+\b',  # HTTP/HTTPS URLs
                r'\bwww\.[^\s<>"{}|\\^`[\]]+\b',  # WWW URLs
            ],
        }

        # Name patterns (more conservative to avoid false positives)
        self.name_patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # First Last
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # First Middle Last
        ]

        # Address patterns
        self.address_patterns = [
            r'\b\d+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Place|Pl|Court|Ct|Circle|Cir)\b',
            r'\b\d+\s+[A-Z][a-z]+\s+[A-Z][a-z]+\s+(Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Place|Pl|Court|Ct|Circle|Cir)\b',
        ]

        # Date patterns
        self.date_patterns = [
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or DD/MM/YYYY
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',  # YYYY/MM/DD
            r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}\b',
        ]

        logger.info("PII Masker initialized with regex patterns")

    def mask_pii(self, text: str) -> Tuple[str, Dict[str, int]]:
        """
        Mask PII in the given text using comprehensive regex patterns

        Args:
            text: Input text to mask

        Returns:
            Tuple of (masked_text, masking_stats)
        """
        if not text:
            return text, {}

        masking_stats = {}
        masked_text = text

        # Mask structured PII first (emails, phones, SSN, etc.)
        for pii_type, patterns in self.pii_patterns.items():
            count = 0
            for pattern in patterns:
                matches = re.findall(pattern, masked_text, re.IGNORECASE)
                if matches:
                    masked_text = re.sub(pattern, f'[{pii_type}]', masked_text, flags=re.IGNORECASE)
                    count += len(matches)
            if count > 0:
                masking_stats[pii_type] = count

        # Mask addresses
        address_count = 0
        for pattern in self.address_patterns:
            matches = re.findall(pattern, masked_text, re.IGNORECASE)
            if matches:
                masked_text = re.sub(pattern, '[LOCATION]', masked_text, flags=re.IGNORECASE)
                address_count += len(matches)
        if address_count > 0:
            masking_stats['LOCATION'] = address_count

        # Mask dates
        date_count = 0
        for pattern in self.date_patterns:
            matches = re.findall(pattern, masked_text, re.IGNORECASE)
            if matches:
                masked_text = re.sub(pattern, '[DATE]', masked_text, flags=re.IGNORECASE)
                date_count += len(matches)
        if date_count > 0:
            masking_stats['DATE_TIME'] = date_count

        # Mask names (only if we find multiple potential names to avoid false positives)
        name_count = 0
        potential_names = []
        for pattern in self.name_patterns:
            matches = re.findall(pattern, masked_text)
            potential_names.extend(matches)

        # Only mask names if we find more than 2 (to reduce false positives)
        if len(potential_names) > 2:
            for pattern in self.name_patterns:
                matches = re.findall(pattern, masked_text)
                if matches:
                    masked_text = re.sub(pattern, '[PERSON]', masked_text)
                    name_count += len(matches)

        if name_count > 0:
            masking_stats['PERSON'] = name_count

        if masking_stats:
            logger.info(f"Masked {sum(masking_stats.values())} PII instances: {masking_stats}")

        return masked_text, masking_stats

    def mask_pii_preserving_structure(self, text: str) -> Tuple[str, Dict[str, int]]:
        """
        Mask PII while preserving document structure and readability
        Uses more specific placeholders for better context preservation
        """
        if not text:
            return text, {}

        masking_stats = {}
        masked_text = text

        # Use more descriptive placeholders
        placeholder_map = {
            'EMAIL_ADDRESS': '[EMAIL_ADDRESS]',
            'PHONE_NUMBER': '[PHONE_NUMBER]',
            'US_SSN': '[SOCIAL_SECURITY_NUMBER]',
            'CREDIT_CARD': '[CREDIT_CARD_NUMBER]',
            'IP_ADDRESS': '[IP_ADDRESS]',
            'US_DRIVER_LICENSE': '[DRIVER_LICENSE_NUMBER]',
            'URL': '[WEBSITE_URL]',
            'LOCATION': '[ADDRESS]',
            'DATE_TIME': '[DATE]',
            'PERSON': '[PERSON_NAME]'
        }

        # Apply masking with descriptive placeholders
        for pii_type, patterns in self.pii_patterns.items():
            count = 0
            placeholder = placeholder_map.get(pii_type, f'[{pii_type}]')
            for pattern in patterns:
                matches = re.findall(pattern, masked_text, re.IGNORECASE)
                if matches:
                    masked_text = re.sub(pattern, placeholder, masked_text, flags=re.IGNORECASE)
                    count += len(matches)
            if count > 0:
                masking_stats[pii_type] = count

        # Mask addresses and dates with descriptive placeholders
        address_matches = re.findall(r'|'.join(self.address_patterns), masked_text, re.IGNORECASE)
        if address_matches:
            for pattern in self.address_patterns:
                masked_text = re.sub(pattern, '[ADDRESS]', masked_text, flags=re.IGNORECASE)
            masking_stats['LOCATION'] = len(address_matches)

        date_matches = re.findall(r'|'.join(self.date_patterns), masked_text, re.IGNORECASE)
        if date_matches:
            for pattern in self.date_patterns:
                masked_text = re.sub(pattern, '[DATE]', masked_text, flags=re.IGNORECASE)
            masking_stats['DATE_TIME'] = len(date_matches)

        # Conservative name masking
        name_count = 0
        potential_names = []
        for pattern in self.name_patterns:
            matches = re.findall(pattern, masked_text)
            potential_names.extend(matches)

        if len(potential_names) > 2:
            for pattern in self.name_patterns:
                matches = re.findall(pattern, masked_text)
                if matches:
                    masked_text = re.sub(pattern, '[PERSON_NAME]', masked_text)
                    name_count += len(matches)

        if name_count > 0:
            masking_stats['PERSON'] = name_count

        if masking_stats:
            logger.info(f"Structure-preserving masking: {sum(masking_stats.values())} PII instances masked")

        return masked_text, masking_stats

    @staticmethod
    def simple_regex_mask(text: str) -> Tuple[str, Dict[str, int]]:
        """
        Simple regex-based PII masking as fallback

        Args:
            text: Input text to mask

        Returns:
            Tuple of (masked_text, masking_stats)
        """
        if not text:
            return text, {}

        masking_stats = {}

        # Email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = re.findall(email_pattern, text)
        text = re.sub(email_pattern, '[EMAIL]', text)
        masking_stats['EMAIL_ADDRESS'] = len(emails)

        # Phone numbers
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})\b'
        phones = re.findall(phone_pattern, text)
        text = re.sub(phone_pattern, '[PHONE]', text)
        masking_stats['PHONE_NUMBER'] = len(phones)

        # Social Security Numbers
        ssn_pattern = r'\b\d{3}[-]?\d{2}[-]?\d{4}\b'
        ssns = re.findall(ssn_pattern, text)
        text = re.sub(ssn_pattern, '[SSN]', text)
        masking_stats['US_SSN'] = len(ssns)

        return text, masking_stats


def mask_pii_in_text(text: str, method: str = "comprehensive") -> Tuple[str, Dict[str, int]]:
    """
    Convenience function to mask PII in text

    Args:
        text: Input text to mask
        method: Masking method ("comprehensive", "structure_preserving", or "simple")

    Returns:
        Tuple of (masked_text, masking_stats)
    """
    if method == "comprehensive":
        try:
            masker = PIIMasker()
            return masker.mask_pii(text)
        except Exception as e:
            logger.warning(f"Comprehensive masking failed, falling back to simple: {str(e)}")
            return PIIMasker.simple_regex_mask(text)
    elif method == "structure_preserving":
        try:
            masker = PIIMasker()
            return masker.mask_pii_preserving_structure(text)
        except Exception as e:
            logger.warning(f"Structure-preserving masking failed, falling back to simple: {str(e)}")
            return PIIMasker.simple_regex_mask(text)
    else:
        return PIIMasker.simple_regex_mask(text)
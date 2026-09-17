"""Entity extraction service for message verification.

Extracts phone numbers, URLs, sender IDs, institution names, and other entities
from SMS messages, screenshots, and other text inputs.
"""

import re
from dataclasses import dataclass, field
from typing import ClassVar


@dataclass
class ExtractedEntities:
    """Structured extracted entities from message text."""
    sender: str | None = None
    phone_numbers: list[str] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    short_codes: list[str] = field(default_factory=list)
    ussd_codes: list[str] = field(default_factory=list)
    institution_names: list[str] = field(default_factory=list)
    email_addresses: list[str] = field(default_factory=list)


class EntityExtractor:
    """Extracts verification-relevant entities from message text."""
    
    # Malawi country code and common patterns
    MALAWI_COUNTRY_CODE = "+265"
    COMMON_TELCO_PREFIXES: ClassVar[list[str]] = ["88", "99", "91"]
    
    # Known institution name patterns (case-insensitive)
    KNOWN_INSTITUTIONS: ClassVar[list[str]] = [
        "standard bank",
        "tnm",
        "airtel",
        "airtel money",
        "mpamba",
        "reserve bank",
        "rbm",
        "national bank",
        "fdh bank",
        "opportunity bank",
        "nbs bank",
        "ecobank",
        "finley",
        "macra",
        "malawi communications regulatory authority",
        "malawi police",
        "malawi government",
        "pusepa",
        "public service pensioners association",
        "ministry of finance",
        "mra",
        "malawi revenue authority",
        "escom",
        "water board",
        "city council",
        "university",
        "college",
    ]
    
    @staticmethod
    def extract_phone_numbers(text: str) -> list[str]:
        """Extract phone numbers from text.
        
        Handles formats:
        - +265 XXX XXX XXX
        - 0XXX XXX XXX
        - XXX XXX XXX
        """
        patterns = [
            r'\+265\s*\d{3}\s*\d{3}\s*\d{3}',  # +265 format
            r'0\d{2}\s*\d{3}\s*\d{3}',  # 0XXX format
            r'\d{3}\s*\d{3}\s*\d{3}',  # XXX XXX XXX format
        ]
        
        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            numbers.extend([m.replace(' ', '') for m in matches])
        
        return list(set(numbers))  # Remove duplicates
    
    @staticmethod
    def extract_urls(text: str) -> list[str]:
        """Extract URLs from text."""
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+|www\.[^\s<>"{}|\\^`\[\]]+'
        urls = re.findall(url_pattern, text, re.IGNORECASE)
        return list(set(urls))
    
    @staticmethod
    def extract_short_codes(text: str) -> list[str]:
        """Extract short codes (e.g., 212, 543, 888)."""
        # Match 2-4 digit numbers that could be short codes
        short_code_pattern = r'\b\d{2,4}\b'
        potential_codes = re.findall(short_code_pattern, text)
        
        # Filter out numbers that are likely part of phone numbers
        filtered_codes = []
        for code in potential_codes:
            # Exclude if part of a longer phone number pattern
            if not re.search(rf'\+265.*{code}|0\d{{2}}.*{code}', text):
                filtered_codes.append(code)
        
        return list(set(filtered_codes))
    
    @staticmethod
    def extract_ussd_codes(text: str) -> list[str]:
        """Extract USSD codes (e.g., *212#, *123#)."""
        ussd_pattern = r'\*\d{3,4}#'
        ussd_codes = re.findall(ussd_pattern, text)
        return list(set(ussd_codes))
    
    @staticmethod
    def extract_email_addresses(text: str) -> list[str]:
        """Extract email addresses."""
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, text)
        return list(set(emails))
    
    @staticmethod
    def extract_sender_id(text: str) -> str | None:
        """Extract SMS sender ID from message text.
        
        Looks for patterns like:
        - "From: [Sender]"
        - "Sender: [Sender]"
        - "[Sender]" at the start
        """
        # Try to extract from common patterns
        patterns = [
            r'from\s*[:]\s*([a-zA-Z0-9\s]+?)(?:\n|$)',
            r'sender\s*[:]\s*([a-zA-Z0-9\s]+?)(?:\n|$)',
            r'^([a-zA-Z0-9\s]{3,20})\s*[:\n]',  # First line before colon or newline
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                sender = match.group(1).strip()
                # Filter out common non-sender words
                if sender.lower() not in ['message', 'sms', 'text', 'from', 'sender']:
                    return sender[:50]  # Limit length
        
        return None
    
    @staticmethod
    def extract_institution_names(text: str) -> list[str]:
        """Extract known institution names from text."""
        found_institutions = []
        text_lower = text.lower()
        
        for institution in EntityExtractor.KNOWN_INSTITUTIONS:
            if institution in text_lower:
                found_institutions.append(institution.title())
        
        return list(set(found_institutions))
    
    @classmethod
    def extract_all(cls, text: str) -> ExtractedEntities:
        """Extract all entities from message text."""
        return ExtractedEntities(
            sender=cls.extract_sender_id(text),
            phone_numbers=cls.extract_phone_numbers(text),
            urls=cls.extract_urls(text),
            short_codes=cls.extract_short_codes(text),
            ussd_codes=cls.extract_ussd_codes(text),
            institution_names=cls.extract_institution_names(text),
            email_addresses=cls.extract_email_addresses(text),
        )
    
    @classmethod
    def extract_with_gemini(cls, text: str) -> ExtractedEntities:
        """Extract entities using Gemini AI for more sophisticated extraction.
        
        This is a placeholder for when Gemini integration is needed for
        more complex entity extraction that regex cannot handle reliably.
        """
        # For now, use regex-based extraction
        # TODO: Integrate Gemini for more sophisticated extraction
        return cls.extract_all(text)


def extract_entities_from_text(text: str, use_ai: bool = False) -> dict:
    """Main entry point for entity extraction.
    
    Args:
        text: The message text to extract entities from
        use_ai: Whether to use AI-enhanced extraction (future feature)
    
    Returns:
        Dictionary with extracted entities
    """
    if use_ai:
        entities = EntityExtractor.extract_with_gemini(text)
    else:
        entities = EntityExtractor.extract_all(text)
    
    return {
        "sender": entities.sender,
        "phone_numbers": entities.phone_numbers,
        "urls": entities.urls,
        "short_codes": entities.short_codes,
        "ussd_codes": entities.ussd_codes,
        "institution_names": entities.institution_names,
        "email_addresses": entities.email_addresses,
    }

"""Official channel verification service.

Verifies whether extracted phone numbers, sender IDs, short codes, and other channels
are officially associated with registered institutions.
"""

from dataclasses import dataclass, field
from typing import Any

from sqlalchemy.orm import Session

from app.models.institution import Institution


@dataclass
class ChannelVerificationResult:
    """Result of channel verification."""
    sender_verified: bool = False
    channel_verified: bool = False
    matched_institution: str | None = None
    matched_channels: list[str] = field(default_factory=list)
    verification_details: dict[str, Any] = field(default_factory=dict)


class ChannelVerifier:
    """Verifies official channels against institution registry."""
    
    @staticmethod
    def normalize_phone_number(phone: str) -> str:
        """Normalize phone number for comparison."""
        # Remove spaces, dashes, parentheses
        normalized = phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
        
        # Ensure Malawi country code
        if normalized.startswith('0'):
            normalized = '+265' + normalized[1:]
        elif not normalized.startswith('+'):
            normalized = '+265' + normalized
        
        return normalized
    
    @staticmethod
    def normalize_sender_id(sender: str) -> str:
        """Normalize sender ID for comparison."""
        return sender.strip().upper()
    
    @staticmethod
    def normalize_short_code(code: str) -> str:
        """Normalize short code for comparison."""
        return code.strip()
    
    @staticmethod
    def normalize_ussd_code(code: str) -> str:
        """Normalize USSD code for comparison."""
        return code.strip().upper()
    
    @classmethod
    def verify_phone_number(cls, phone: str, institution: Institution) -> bool:
        """Check if phone number matches institution's official numbers."""
        if not institution.official_phone_numbers or not isinstance(institution.official_phone_numbers, list):
            return False
        
        normalized_phone = cls.normalize_phone_number(phone)
        official_numbers: list[str] = institution.official_phone_numbers
        
        for official_num in official_numbers:
            normalized_official = cls.normalize_phone_number(official_num)
            if normalized_phone == normalized_official:
                return True
        
        return False
    
    @classmethod
    def verify_sender_id(cls, sender: str, institution: Institution) -> bool:
        """Check if sender ID matches institution's official sender IDs."""
        if not institution.official_sms_sender_ids or not isinstance(institution.official_sms_sender_ids, list):
            return False
        
        normalized_sender = cls.normalize_sender_id(sender)
        official_senders: list[str] = institution.official_sms_sender_ids
        
        for official_sender in official_senders:
            normalized_official = cls.normalize_sender_id(official_sender)
            if normalized_sender == normalized_official:
                return True
        
        return False
    
    @classmethod
    def verify_short_code(cls, code: str, institution: Institution) -> bool:
        """Check if short code matches institution's official short codes."""
        if not institution.official_short_codes or not isinstance(institution.official_short_codes, list):
            return False
        
        normalized_code = cls.normalize_short_code(code)
        official_codes: list[str] = institution.official_short_codes
        
        return normalized_code in official_codes
    
    @classmethod
    def verify_ussd_code(cls, code: str, institution: Institution) -> bool:
        """Check if USSD code matches institution's official USSD codes."""
        if not institution.official_ussd_codes or not isinstance(institution.official_ussd_codes, list):
            return False
        
        normalized_code = cls.normalize_ussd_code(code)
        official_codes: list[str] = institution.official_ussd_codes
        
        return normalized_code in official_codes
    
    @classmethod
    def verify_url_domain(cls, url: str, institution: Institution) -> bool:
        """Check if URL domain matches institution's official domains."""
        if not institution.official_email_domains or not isinstance(institution.official_email_domains, list):
            return False
        
        # Extract domain from URL
        from urllib.parse import urlparse
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check against official domains
            official_domains: list[str] = institution.official_email_domains
            for official_domain in official_domains:
                if official_domain.lower() in domain:
                    return True
        except Exception as exc:
            import logging
            logging.getLogger(__name__).debug("URL parse error in channel verification: %s", exc)
        
        return False
    
    @classmethod
    def verify_institution_by_name(
        cls, 
        institution_names: list[str], 
        db: Session
    ) -> list[Institution]:
        """Find institutions by name."""
        if not institution_names:
            return []
        
        matched_institutions = []
        
        for name in institution_names:
            # Case-insensitive search
            institutions = db.query(Institution).filter(
                Institution.name.ilike(f"%{name}%")
            ).all()
            matched_institutions.extend(institutions)
        
        return matched_institutions
    
    @classmethod
    def verify_channels(
        cls,
        extracted_entities: dict,
        db: Session
    ) -> ChannelVerificationResult:
        """Verify all extracted channels against institution registry."""
        result = ChannelVerificationResult()
        
        # Get institution names from extracted entities
        institution_names = extracted_entities.get('institution_names', [])
        
        if not institution_names:
            # No institution detected, cannot verify
            result.verification_details['reason'] = 'No institution detected in message'
            return result
        
        # Find matching institutions
        matched_institutions = cls.verify_institution_by_name(institution_names, db)
        
        if not matched_institutions:
            result.verification_details['reason'] = 'No matching institution found in registry'
            return result
        
        # Check each matched institution
        for institution in matched_institutions:
            institution_name = str(institution.name)
            matched_channels = []
            
            # Verify phone numbers
            phone_numbers = extracted_entities.get('phone_numbers', [])
            for phone in phone_numbers:
                if cls.verify_phone_number(phone, institution):
                    matched_channels.append(f'Phone: {phone}')
                    result.channel_verified = True
            
            # Verify sender ID
            sender = extracted_entities.get('sender')
            if sender and cls.verify_sender_id(sender, institution):
                matched_channels.append(f'Sender ID: {sender}')
                result.sender_verified = True
            
            # Verify short codes
            short_codes = extracted_entities.get('short_codes', [])
            for code in short_codes:
                if cls.verify_short_code(code, institution):
                    matched_channels.append(f'Short Code: {code}')
                    result.channel_verified = True
            
            # Verify USSD codes
            ussd_codes = extracted_entities.get('ussd_codes', [])
            for code in ussd_codes:
                if cls.verify_ussd_code(code, institution):
                    matched_channels.append(f'USSD: {code}')
                    result.channel_verified = True
            
            # Verify URLs
            urls = extracted_entities.get('urls', [])
            for url in urls:
                if cls.verify_url_domain(url, institution):
                    matched_channels.append(f'URL: {url}')
                    result.channel_verified = True
            
            # If any channel matched, record the institution
            if matched_channels:
                result.matched_institution = institution_name
                result.matched_channels.extend(matched_channels)
                result.verification_details['matched_institution'] = institution_name
                result.verification_details['matched_channels'] = matched_channels
                result.verification_details['institution_sector'] = institution.sector
                result.verification_details['institution_website'] = institution.website_url
                break  # Use first match
        
        result.verification_details['institutions_checked'] = [i.name for i in matched_institutions]
        
        return result


def verify_official_channels(extracted_entities: dict, db: Session) -> dict:
    """Main entry point for channel verification.
    
    Args:
        extracted_entities: Dictionary of entities from entity extraction
        db: Database session
    
    Returns:
        Dictionary with verification results
    """
    verifier = ChannelVerifier()
    result = verifier.verify_channels(extracted_entities, db)
    
    return {
        'sender_verified': result.sender_verified,
        'channel_verified': result.channel_verified,
        'matched_institution': result.matched_institution,
        'matched_channels': result.matched_channels,
        'verification_details': result.verification_details,
    }

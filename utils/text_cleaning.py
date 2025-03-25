"""
Text Cleaning Module

This module provides utilities for cleaning and normalizing text extracted from OCR.
"""

import re
import unicodedata


def clean_text(text: str) -> str:
    """Clean OCR-extracted text by removing noise and normalizing.
    
    Args:
        text: Raw text from OCR
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""

    # Remove excess whitespace
    text = ' '.join(text.split())

    # Normalize line breaks
    # text = re.sub(r'\r\n', '\n', text)
    # text = re.sub(r'\r', '\n', text)

    # Normalize multiple line breaks
    # text = re.sub(r'\n{3,}', '\n\n', text)

    # Fix common OCR errors
    text = fix_common_ocr_errors(text)

    # Replace problematic characters
    text = text.replace('•', '-')

    # Remove non-printable characters
    text = ''.join(c for c in text if c.isprintable() or c == '\n')

    return text


def normalize_text(text: str) -> str:
    """Normalize text by removing accents and converting to lowercase.
    
    Args:
        text: Text to normalize
        
    Returns:
        Normalized text
    """
    # Convert to lowercase
    text = text.lower()

    # Remove accents
    text = ''.join(c for c in unicodedata.normalize('NFD', text)
                   if unicodedata.category(c) != 'Mn')

    return text


def fix_common_ocr_errors(text: str) -> str:
    """Fix common OCR errors in menu text.
    
    Args:
        text: Text with potential OCR errors
        
    Returns:
        Text with fixed common errors
    """
    # Fix price format errors
    text = re.sub(r'(\d+)[\s,.-]+(\d{2})(?=\s*€|\s*EUR|\s*euros|\s*\$)',
                  r'\1.\2', text)

    # Fix common OCR misrecognitions
    replacements = {
        'O': '0',  # Letter O to number 0 in price contexts
        'l': '1',  # Lowercase L to number 1 in price contexts
        'I': '1',  # Uppercase I to number 1 in price contexts
    }

    # Only replace in contexts that look like prices
    for pattern in [
            r'([^\d])([OlI])(\d)', r'(\d)([OlI])([^\d])', r'(\d)([OlI])(\d)'
    ]:
        for pattern in [
                r'([^\d])([OlI])(\d)', r'(\d)([OlI])([^\d])',
                r'(\d)([OlI])(\d)'
        ]:
            for old, new in replacements.items():
                text = re.sub(pattern, lambda m: m.group(1) + new + m.group(3),
                              text)

    # Common food word corrections in Spanish
    common_corrections = {
        'ensaiada': 'ensalada',
        'hamburgesa': 'hamburguesa',
        'cale': 'café',
        'cervesa': 'cerveza',
        'patata5': 'patatas',
        'tor+illa': 'tortilla',
        'tapa5': 'tapas',
        'pollo5': 'pollos',
    }

    for wrong, right in common_corrections.items():
        text = re.sub(r'\b' + wrong + r'\b', right, text, flags=re.IGNORECASE)

    return text

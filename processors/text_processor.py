"""
Text Processor Module

This module handles the processing of extracted text to identify menu items,
categories, and prices using pattern recognition and NLP techniques.
"""

import re
import logging
from typing import List, Dict, Any, Optional, Tuple
import string
from difflib import SequenceMatcher

from models.menu_item import MenuItem, MenuCategory
from utils.text_cleaning import clean_text, normalize_text

logger = logging.getLogger(__name__)

class TextProcessor:
    """Class to process OCR-extracted text and identify menu components."""
    
    def __init__(self):
        """Initialize the text processor."""
        # Common words that indicate a category in Spanish menus
        self.category_indicators = [
            'entrantes', 'aperitivos', 'primeros', 'segundos', 'postres',
            'bebidas', 'vinos', 'cervezas', 'refrescos', 'cafés', 'especialidades',
            'platos', 'menú', 'combo', 'principal', 'ensaladas', 'sopas',
            'carnes', 'pescados', 'mariscos', 'vegetariano', 'vegano',
            'hamburguesas', 'pizzas', 'pastas', 'arroces', 'tapas', 'raciones',
            'desayunos', 'almuerzos', 'cenas', 'sugerencias', 'recomendaciones'
        ]
        
        # Spanish words to ignore when identifying items (stop words)
        self.stopwords = [
            'con', 'y', 'de', 'del', 'la', 'el', 'los', 'las', 'un', 'una', 'unos', 'unas',
            'en', 'para', 'por', 'a', 'al', 'o', 'u', 'sin', 'sobre', 'desde'
        ]
        
        # Regular expressions for finding prices
        # Match patterns like: $10.99, 10,99€, 10.99 €, 10,99 €, etc.
        self.price_patterns = [
            r'(\d+[\.,]\d+)\s*€',  # 10.99 €, 10,99€
            r'€\s*(\d+[\.,]\d+)',  # € 10.99, €10,99
            r'(\d+[\.,]\d+)\s*EUR',  # 10.99 EUR
            r'(\d+[\.,]\d+)\s*euros',  # 10.99 euros
            r'(\d+)\s*€',  # 10 €, 10€
            r'€\s*(\d+)',  # € 10, €10
            r'\$\s*(\d+[\.,]\d+)',  # $10.99
            r'(\d+[\.,]\d+)\$',  # 10.99$
            r'\$\s*(\d+)',  # $10
            r'(\d+)\$',  # 10$
            r'(\d+)[-,]\s*(\d+)[\s€]'  # 10-50€, 10,50€
        ]
    
    def process_text(self, text: str) -> List[MenuCategory]:
        """Process text to identify menu items and categories.
        
        Args:
            text: Extracted text from OCR
            
        Returns:
            List of MenuCategory objects containing menu items
        """
        logger.debug("Processing extracted text")
        
        # Clean and normalize text
        clean = clean_text(text)
        
        # Split into lines and process each line
        lines = clean.split('\n')
        lines = [line.strip() for line in lines if line.strip()]
        
        # Identify potential category headers and menu items
        categories = self._identify_categories(lines)
        
        # If no categories were found, create a default one
        if not categories:
            categories = [MenuCategory("Menu Items", [])]
            current_category = categories[0]
            
            # Process all lines as potential menu items
            for line in lines:
                item = self._process_menu_item_line(line)
                if item:
                    current_category.items.append(item)
        
        # Filter out empty categories
        categories = [cat for cat in categories if cat.items]
        
        # Log the results
        for category in categories:
            logger.debug(f"Category: {category.name} with {len(category.items)} items")
            
        return categories
    
    def _identify_categories(self, lines: List[str]) -> List[MenuCategory]:
        """Identify category headers and associated menu items.
        
        Args:
            lines: List of text lines
            
        Returns:
            List of MenuCategory objects
        """
        categories = []
        current_category = None
        
        for i, line in enumerate(lines):
            # Normalize for comparison
            normalized_line = normalize_text(line.lower())
            
            # Check if line is a category header
            is_category = False
            
            # Check for uppercase lines (common for category headers)
            if line.isupper() and len(line) > 3:
                is_category = True
            
            # Check for lines containing category indicator words
            for indicator in self.category_indicators:
                if indicator in normalized_line:
                    is_category = True
                    break
                    
            # Check for short lines followed by longer lines (likely headers)
            if (len(line.split()) <= 3 and len(line) < 20 and i < len(lines) - 1 and 
                len(lines[i + 1]) > len(line) and ':' not in line):
                is_category = True
            
            # Line with only one word and not a price
            if len(line.split()) == 1 and len(line) > 3 and not self._extract_price(line):
                is_category = True
            
            # If we identified a category
            if is_category:
                # Clean the category name
                category_name = line.strip()
                # Remove trailing colons and dots
                category_name = re.sub(r'[:\.]+$', '', category_name)
                
                # Create a new category
                current_category = MenuCategory(category_name, [])
                categories.append(current_category)
            
            # If line is not a category and we have a current category
            elif current_category is not None:
                # Process the line as a potential menu item
                item = self._process_menu_item_line(line)
                if item:
                    current_category.items.append(item)
        
        return categories
    
    def _process_menu_item_line(self, line: str) -> Optional[MenuItem]:
        """Process a line of text as a potential menu item.
        
        Args:
            line: Text line to process
            
        Returns:
            MenuItem object or None if not a valid item
        """
        # Skip very short lines
        if len(line) < 3:
            return None
        
        # Extract the price first as it's the most reliable indicator
        price_match, price_value = self._extract_price(line)
        
        # If we found a price, extract the name from the rest of the line
        if price_match:
            # Remove the price part from the line
            name_part = line.replace(price_match, '').strip()
            # Clean trailing and leading punctuation
            name_part = re.sub(r'^[^\w]+|[^\w]+$', '', name_part)
            
            # If name part is too short after removing price, it's probably not a valid item
            if len(name_part) < 3:
                return None
                
            return MenuItem(
                name=name_part,
                price=price_value,
                description=None  # No detailed description in this line
            )
        
        # If no price was found, check if it's a description line for the previous item
        # or if it's a menu item without a price
        
        # Line is too long to be just a name - likely contains name and description
        if len(line) > 30 and ':' in line:
            parts = line.split(':', 1)
            return MenuItem(
                name=parts[0].strip(),
                price=None,  # No price found
                description=parts[1].strip() if len(parts) > 1 else None
            )
        
        # Otherwise, treat the whole line as an item name without a price
        return MenuItem(
            name=line.strip(),
            price=None,
            description=None
        )
    
    def _extract_price(self, text: str) -> Tuple[Optional[str], Optional[float]]:
        """Extract price information from text.
        
        Args:
            text: Text to extract price from
            
        Returns:
            Tuple of (matched text, price value) or (None, None) if no price found
        """
        for pattern in self.price_patterns:
            matches = re.search(pattern, text)
            if matches:
                try:
                    # Get the full matched text
                    full_match = matches.group(0)
                    
                    # Extract numerical value
                    if len(matches.groups()) == 1:
                        # Simple single number pattern
                        price_str = matches.group(1)
                        # Convert comma to dot for float parsing
                        price_str = price_str.replace(',', '.')
                        price_value = float(price_str)
                    elif len(matches.groups()) == 2:
                        # Pattern with two number groups (like 10-50)
                        price_str = matches.group(1) + '.' + matches.group(2)
                        price_value = float(price_str)
                    else:
                        continue
                    
                    return full_match, price_value
                    
                except (ValueError, IndexError):
                    continue
        
        return None, None

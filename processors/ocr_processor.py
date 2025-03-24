"""
OCR Processor Module

This module handles the extraction of text from images using OCR technology (Tesseract).
"""

import os
import logging
from pathlib import Path
from typing import Optional

import pytesseract
from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)

class OCRProcessor:
    """Class to handle OCR processing of images."""
    
    def __init__(self, language: str = 'spa'):
        """Initialize OCR processor.
        
        Args:
            language: Language code for Tesseract OCR (default: 'spa' for Spanish)
        """
        self.language = language
        self.custom_config = f'--oem 3 --psm 6 -l {language}'
        
        # Check if Tesseract is installed
        try:
            pytesseract.get_tesseract_version()
        except Exception as e:
            logger.error(f"Tesseract not properly installed or configured: {str(e)}")
            logger.error("Make sure Tesseract is installed and properly configured.")
    
    def extract_text(self, image_path: str, preprocess: bool = True) -> str:
        """Extract text from an image using OCR.
        
        Args:
            image_path: Path to the image file
            preprocess: Whether to preprocess the image before OCR
            
        Returns:
            Extracted text string
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image file not found: {image_path}")
            
            # Open the image
            image = Image.open(image_path)
            
            # Preprocess image if requested
            if preprocess:
                image = self._preprocess_image(image)
            
            # Extract text using Tesseract
            text = pytesseract.image_to_string(image, config=self.custom_config)
            
            logger.debug(f"Extracted {len(text)} characters from {os.path.basename(image_path)}")
            return text
            
        except Exception as e:
            logger.error(f"Error extracting text from {image_path}: {str(e)}")
            return ""
    
    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        """Preprocess image to improve OCR accuracy.
        
        Args:
            image: PIL Image object
            
        Returns:
            Preprocessed PIL Image object
        """
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(2.0)
        
        # Apply slight blur to reduce noise
        image = image.filter(ImageFilter.GaussianBlur(radius=0.5))
        
        # Apply thresholding to make text more distinct
        threshold = 150
        image = image.point(lambda p: 255 if p > threshold else 0)
        
        return image
    
    def extract_text_from_regions(self, image_path: str, regions: list) -> dict:
        """Extract text from specific regions of an image.
        
        Args:
            image_path: Path to the image file
            regions: List of tuples (name, (left, top, right, bottom))
            
        Returns:
            Dictionary mapping region names to extracted text
        """
        try:
            image = Image.open(image_path)
            results = {}
            
            for name, (left, top, right, bottom) in regions:
                # Crop to region
                region_img = image.crop((left, top, right, bottom))
                
                # Preprocess and extract text
                region_img = self._preprocess_image(region_img)
                text = pytesseract.image_to_string(region_img, config=self.custom_config)
                
                results[name] = text.strip()
                
            return results
            
        except Exception as e:
            logger.error(f"Error processing regions in {image_path}: {str(e)}")
            return {}

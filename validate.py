#!/usr/bin/python3

import argparse
import qrcode
from PIL import Image, ImageEnhance
import pytesseract
import cv2
import numpy as np
from pyzbar.pyzbar import decode
from eth_keys import keys
from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey as BtcPrivateKey
import binascii
import re
import sys
import os

class KeyValidator:
    def __init__(self):
        setup('mainnet')
        
    def process_merged_image(self, image_path):
        """Read and preprocess the merged image"""
        try:
            img = cv2.imread(image_path)
            if img is None:
                raise ValueError(f"Could not read image: {image_path}")
            
            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Enhance contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            gray = clahe.apply(gray)
            
            # Threshold
            _, threshold = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
            
            return img, threshold
            
        except Exception as e:
            print(f"Error processing image: {str(e)}")
            return None, None

    def extract_qr_codes(self, img, threshold):
        """Extract and sort QR codes from image"""
        try:
            # Find QR codes
            qr_codes = decode(threshold)
            
            # Sort QR codes by vertical position first, then horizontal
            sorted_qr_codes = sorted(qr_codes, key=lambda qr: (qr.rect.top, qr.rect.left))
            
            # Group QR codes into pairs
            pairs = []
            current_pair = []
            current_y = None
            
            for qr in sorted_qr_codes:
                if current_y is None:
                    current_y = qr.rect.top
                
                # If we're significantly far from the last y position, it's a new pair
                if abs(qr.rect.top - current_y) > 100:
                    if current_pair:
                        current_pair.sort(key=lambda qr: qr.rect.left)
                        pairs.append(current_pair)
                        current_pair = []
                    current_y = qr.rect.top
                
                current_pair.append(qr)
                
                # If we have 2 QR codes in current pair, add it to pairs
                if len(current_pair) == 2:
                    current_pair.sort(key=lambda qr: qr.rect.left)
                    pairs.append(current_pair)
                    current_pair = []
                    current_y = None
            
            # Add any remaining pair
            if current_pair:
                current_pair.sort(key=lambda qr: qr.rect.left)
                pairs.append(current_pair)
            
            return pairs
            
        except Exception as e:
            print(f"Error extracting QR codes: {str(e)}")
            return []

    def decode_qr_pair(self, pair):
        """Decode a pair of QR codes into private key and address"""
        try:
            # First (left) QR should be private key, second (right) should be address
            private_key = pair[0].data.decode('utf-8')
            address = pair[1].data.decode('utf-8')
            
            return {
                'private_key': private_key,
                'address': address,
                'position': {
                    'private_key_x': pair[0].rect.left,
                    'address_x': pair[1].rect.left,
                    'y': pair[0].rect.top
                }
            }
            
        except Exception as e:
            print(f"Error decoding QR pair: {str(e)}")
            return None
    def extract_text_from_region(self, img, y_start, y_end, qr_positions):
        """Extract text from a specific region of the image, excluding QR codes"""
        try:
            # Extract the region we're interested in
            region = img[y_start:y_end, :]
            
            # Create mask (white background)
            mask = np.ones(region.shape[:2], dtype=np.uint8) * 255
            
            # Mask out QR codes with padding
            padding = 30
            for qr_pos in qr_positions:
                x = qr_pos.rect.left
                y = qr_pos.rect.top - y_start  # Adjust y position relative to region
                w = qr_pos.rect.width
                h = qr_pos.rect.height
                
                # Only mask if QR code is in this region
                if 0 <= y < region.shape[0]:
                    x1 = max(0, x - padding)
                    y1 = max(0, y - padding)
                    x2 = min(region.shape[1], x + w + padding)
                    y2 = min(region.shape[0], y + h + padding)
                    mask[y1:y2, x1:x2] = 0
            
            # Apply mask
            masked_region = cv2.bitwise_and(region, region, mask=mask)
            
            # Convert to PIL
            region_pil = Image.fromarray(cv2.cvtColor(masked_region, cv2.COLOR_BGR2RGB))
            
            # Convert to grayscale
            region_pil = region_pil.convert('L')
            
            # Enhance contrast
            enhancer = ImageEnhance.Contrast(region_pil)
            region_pil = enhancer.enhance(2.0)
            
            # Enhance sharpness
            enhancer = ImageEnhance.Sharpness(region_pil)
            region_pil = enhancer.enhance(1.5)
            
            # Add white background where masked
            bg = Image.new('L', region_pil.size, 255)
            region_pil = Image.composite(region_pil, bg, Image.fromarray(mask))
            
            # OCR with custom configuration
            custom_config = r'--oem 3 --psm 6 -c preserve_interword_spaces=1'
            text = pytesseract.image_to_string(region_pil, config=custom_config)
            
            return text.strip()
            
        except Exception as e:
            print(f"Error extracting text from region: {str(e)}")
            return ""
        
    def validate_btc_key_pair(self, private_key, address):
        """Validate Bitcoin key pair"""
        try:
            print(f"\nValidating BTC pair:")
            print(f"Private Key (WIF): {private_key}")
            print(f"Address: {address}")
            
            btc_private_key = BtcPrivateKey.from_wif(private_key)
            btc_public_key = btc_private_key.get_public_key()
            generated_address = btc_public_key.get_address().to_string()
            
            matches = generated_address == address
            if not matches:
                print(f"Address mismatch:")
                print(f"Generated: {generated_address}")
                print(f"Expected:  {address}")
            return matches
            
        except Exception as e:
            print(f"Error validating BTC pair: {str(e)}")
            return False

    def validate_eth_key_pair(self, private_key, address):
        """Validate Ethereum key pair"""
        try:
            private_key = private_key.lower().replace('0x', '')
            address = address.lower().replace('0x', '')
            
            private_key_bytes = binascii.unhexlify(private_key)
            eth_private_key = keys.PrivateKey(private_key_bytes)
            eth_public_key = eth_private_key.public_key
            generated_address = eth_public_key.to_address().lower().replace('0x', '')
            
            matches = generated_address == address.lower()
            if not matches:
                print(f"Address mismatch:")
                print(f"Generated: {generated_address}")
                print(f"Expected:  {address}")
            return matches
            
        except Exception as e:
            print(f"Error validating ETH pair: {str(e)}")
            return False

    def validate_image(self, image_path, crypto_type):
        """Validate all key pairs in the image using both QR codes and text"""
        try:
            print(f"\nValidating {crypto_type.upper()} key pairs from: {image_path}")
            print("-" * 60)
            
            # Process image
            img, threshold = self.process_merged_image(image_path)
            if img is None or threshold is None:
                return False
            
            # Extract QR codes
            qr_pairs = self.extract_qr_codes(img, threshold)
            
            if not qr_pairs:
                print("No QR code pairs found in image")
                return False
            
            # Validate each pair
            results = []
            for idx, pair in enumerate(qr_pairs, 1):
                print(f"\nValidating Key Pair {idx}:")
                print("-" * 30)
                
                # Decode QR codes
                key_data_qr = self.decode_qr_pair(pair)
                if not key_data_qr:
                    print(f"❌ Failed to decode QR pair {idx}")
                    continue
                
                # Calculate text region based on QR positions
                qr_top = min(pair[0].rect.top, pair[1].rect.top)
                qr_bottom = max(pair[0].rect.top + pair[0].rect.height,
                              pair[1].rect.top + pair[1].rect.height)
                qr_height = qr_bottom - qr_top
                
                # Extend region to capture text
                y_start = max(0, qr_top - qr_height//2)  # Start above QRs
                y_end = min(img.shape[0], qr_bottom + qr_height//2)  # End below QRs
                
                # Extract text with QR masking
                raw_text = self.extract_text_from_region(img, y_start, y_end, pair)
                print("\nText Extracted from Image (excluding QR codes):")
                print("-" * 50)
                print(raw_text)
                print("-" * 50)
                
                # Print QR code content for comparison
                print(f"\nQR Code Contents:")
                print(f"Left QR (Private Key): {key_data_qr['private_key']}")
                print(f"Right QR (Address): {key_data_qr['address']}")
                
                # Validate the key pair
                if crypto_type == 'btc':
                    is_valid = self.validate_btc_key_pair(
                        key_data_qr['private_key'],
                        key_data_qr['address']
                    )
                else:
                    is_valid = self.validate_eth_key_pair(
                        key_data_qr['private_key'],
                        key_data_qr['address']
                    )
                
                print(f"\nCryptographic Validation: {'✅ Valid' if is_valid else '❌ Invalid'}")
                results.append(is_valid)
            
            return all(results)
            
        except Exception as e:
            print(f"Error during validation: {str(e)}")
            return False

def main():
    parser = argparse.ArgumentParser(description='Validate cryptocurrency key pair images')
    parser.add_argument('--image', required=True, help='Path to the image file')
    parser.add_argument('--type', choices=['btc', 'eth'], required=True,
                      help='Specify cryptocurrency type: btc or eth')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image):
        print(f"Error: Image file not found: {args.image}")
        sys.exit(1)
        
    validator = KeyValidator()
    is_valid = validator.validate_image(args.image, args.type)
    
    print(f"\nFinal Result: {'✅ All key pairs are valid' if is_valid else '❌ Validation failed'}")
    sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main()

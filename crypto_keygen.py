#!/usr/bin/python3

import argparse
from eth_keys import keys
from bitcoinutils.setup import setup
from bitcoinutils.keys import PrivateKey as BtcPrivateKey
import secrets
import binascii
import sys
import qrcode
import os
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime

def validate_private_key(private_key_input, crypto_type):
    """Validate and normalize private key input"""
    try:
        # Handle WIF format for BTC
        if crypto_type == 'btc' and len(private_key_input) in [51, 52]:
            setup('mainnet')
            priv_key = BtcPrivateKey.from_wif(private_key_input)
            return priv_key.to_hex()[2:]  # Convert to hex format without '0x' prefix
        
        # Handle hex format
        if private_key_input.startswith('0x'):
            private_key_input = private_key_input[2:]
        
        # Validate hex string
        int(private_key_input, 16)
        if len(private_key_input) != 64:
            raise ValueError("Private key must be 32 bytes (64 hex characters)")
        
        return private_key_input
    except Exception as e:
        raise ValueError(f"Invalid private key format: {str(e)}")

def generate_private_key():
    """Generate a random private key"""
    private_key_bytes = secrets.token_bytes(32)
    return binascii.hexlify(private_key_bytes).decode('ascii')

def get_eth_address(private_key_hex):
    """Generate Ethereum address from private key"""
    private_key_bytes = binascii.unhexlify(private_key_hex)
    eth_private_key = keys.PrivateKey(private_key_bytes)
    eth_public_key = eth_private_key.public_key
    return {
        'private_key': private_key_hex,
        'public_key': eth_public_key.to_hex()[2:],  # Remove '0x' prefix
        'address': eth_public_key.to_address().lower()
    }

def get_btc_address(private_key_hex):
    """Generate Bitcoin address from private key"""
    setup('mainnet')
    private_key_int = int(private_key_hex, 16)
    btc_private_key = BtcPrivateKey(secret_exponent=private_key_int)
    btc_public_key = btc_private_key.get_public_key()
    
    return {
        'private_key': btc_private_key.to_wif(),
        'private_key_hex': private_key_hex,
        'public_key': btc_public_key.to_hex(),
        'address': btc_public_key.get_address().to_string()
    }

def get_output_directory():
    current_date = datetime.now().strftime("%Y%m%d")
    dir_name = f"keys_{current_date}"
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    return dir_name

def save_to_file(result, crypto_type):
    """Save key details to text file"""
    output_dir = get_output_directory()
    address_prefix = result['address']
    filename = f"keys_{crypto_type.lower()}_{address_prefix}.txt"
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        if crypto_type.lower() == 'btc':
            f.write(f"Private Key (WIF): {result['private_key']}\n")
            f.write(f"Private Key (HEX): {result['private_key_hex']}\n")
        else:
            f.write(f"Private Key: {result['private_key']}\n")
        f.write(f"Public Key: {result['public_key']}\n")
        f.write(f"Address: {result['address']}\n")
    
    return filepath

def get_logo(crypto_type):
    btc_logo = '''<?xml version="1.0" encoding="UTF-8"?>
<svg viewBox="0 0 64 64">
    <circle cx="32" cy="32" r="32" fill="#F7931A"/>
    <path d="M44.4 25.9c.6-4-2.4-6.2-6.6-7.6l1.3-5.4-3.3-.8-1.3 5.2c-.9-.2-1.7-.4-2.6-.6l1.3-5.2-3.3-.8-1.3 5.4c-.7-.2-1.4-.3-2.1-.5l0 0-4.5-1.1-.9 3.5s2.4.6 2.4.6c1.3.3 1.6 1.2 1.5 1.9l-1.5 6.2c.1 0 .2.1.4.1-.1 0-.2-.1-.4-.1l-2.2 8.7c-.2.4-.6 1.1-1.6.8 0 0-2.4-.6-2.4-.6l-1.6 3.7 4.3 1.1c.8.2 1.6.4 2.3.6l-1.4 5.5 3.3.8 1.3-5.4c.9.2 1.8.5 2.6.7l-1.3 5.3 3.3.8 1.4-5.5c5.6 1.1 9.9.6 11.7-4.4 1.4-4.1-.1-6.4-3-7.9 2.1-.5 3.7-1.9 4.1-4.8zm-7.4 10.4c-1 4.1-7.9 1.9-10.1 1.3l1.8-7.2c2.2.6 9.4 1.7 8.3 5.9zm1-10.6c-.9 3.7-6.6 1.8-8.4 1.4l1.6-6.6c1.8.4 7.7 1.2 6.8 5.2z" fill="white"/>
</svg>'''

    eth_logo = '''<?xml version="1.0" encoding="UTF-8"?>
<svg viewBox="0 0 64 64">
    <circle cx="32" cy="32" r="32" fill="#627EEA"/>
    <path d="M32 8l-.3.9v31.8l.3.3 14.8-8.7L32 8z" fill="#FFFFFF" fill-opacity="0.6"/>
    <path d="M32 8L17.2 32.3l14.8 8.7V8z" fill="#FFFFFF"/>
    <path d="M32 44.8l-.2.2v11.3l.2.6 14.8-20.8L32 44.8z" fill="#FFFFFF" fill-opacity="0.6"/>
    <path d="M32 56.9v-12.1l-14.8-8.7L32 56.9z" fill="#FFFFFF"/>
</svg>'''

    return btc_logo if crypto_type.lower() == 'btc' else eth_logo

def svg_to_png(svg_content, size=60):
    try:
        import cairosvg
        import io
        png_data = cairosvg.svg2png(bytestring=svg_content.encode(), output_width=size, output_height=size)
        return Image.open(io.BytesIO(png_data))
    except ImportError:
        # Fallback to simple circle if cairosvg is not available
        img = Image.new('RGB', (size, size), 'white')
        draw = ImageDraw.Draw(img)
        draw.ellipse([0, 0, size, size], fill='blue')
        return img

def create_qr_code(data, crypto_type):
    """Create a QR code with logo overlay"""
    # For BTC, use WIF format in QR if it's a private key
    if crypto_type.lower() == 'btc' and isinstance(data, dict):
        qr_data = data.get('private_key', data)
    else:
        qr_data = data
        
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=5,
        border=4,
    )
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_image = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    
    # Get and convert logo
    svg_content = get_logo(crypto_type)
    logo = svg_to_png(svg_content)
    
    # Calculate logo size and position
    logo_size = qr_image.size[0] // 4
    logo = logo.resize((logo_size, logo_size))
    
    pos = ((qr_image.size[0] - logo_size) // 2,
           (qr_image.size[1] - logo_size) // 2)
    
    qr_image.paste(logo, pos, logo)
    return qr_image

def create_combined_image(result, crypto_type):
    """Create a single image with both QR codes and addresses"""
    qr_private = create_qr_code(result['private_key'], crypto_type)
    qr_address = create_qr_code(result['address'], crypto_type)
    
    qr_width = max(qr_private.size[0], qr_address.size[0])
    qr_private = qr_private.resize((qr_width, qr_width))
    qr_address = qr_address.resize((qr_width, qr_width))
    
    padding = 60
    extra_width = 750
    text_height = 100
    text_padding = 30
    
    total_width = (qr_width * 2) + (padding * 3) + extra_width
    total_height = qr_width + text_height + padding
    combined = Image.new('RGB', (total_width, total_height), 'white')
    
    left_qr_x = padding
    right_qr_x = qr_width + (padding * 2) + extra_width
    combined.paste(qr_private, (left_qr_x, padding))
    combined.paste(qr_address, (right_qr_x, padding))
    
    draw = ImageDraw.Draw(combined)
    try:
        font = ImageFont.truetype("DejaVuSans.ttf", 20)
        title_font = ImageFont.truetype("DejaVuSans.ttf", 24)
    except:
        font = ImageFont.load_default()
        title_font = ImageFont.load_default()

    title = f"{crypto_type.upper()} Keys"
    title_width = draw.textlength(title, font=title_font)
    title_x = (total_width - title_width) // 2
    draw.text((title_x, padding // 2), title, font=title_font, fill='black')

    private_key = result['private_key']
    chunk_size = len(private_key) // 2
    private_key_lines = [
        private_key[i:i + chunk_size]
        for i in range(0, len(private_key), chunk_size)
    ]

    text_y = qr_width + padding - 10
    left_x = left_qr_x
    right_x = right_qr_x

    draw.text((left_x, text_y), "Private Key:", font=font, fill='black')
    for i, line in enumerate(private_key_lines):
        y_pos = text_y + 25 + (i * 25)
        draw.text((left_x, y_pos), line, font=font, fill='black')

    draw.text((right_x - 250, text_y), "Address:", font=font, fill='black')
    draw.text((right_x - 250, text_y + 25), result['address'], font=font, fill='black')

    output_dir = get_output_directory()
    address_prefix = result['address']
    filename = f"keys_{crypto_type.lower()}_{address_prefix}.png"
    filepath = os.path.join(output_dir, filename)
    combined.save(filepath)
    
    return filepath

def create_merged_image(image_files):
    """Merge multiple QR code images into one"""
    images = [Image.open(f) for f in image_files]
    single_height = images[0].size[1]
    single_width = images[0].size[0]
    
    merged = Image.new('RGB', (single_width, single_height * len(images)), 'white')
    
    for idx, img in enumerate(images):
        merged.paste(img, (0, idx * single_height))
    
    output_dir = get_output_directory()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filepath = os.path.join(output_dir, f'merged_keys_{timestamp}.png')
    merged.save(filepath)
    
    return filepath

def generate_multiple_keys(count, crypto_type, decode_key=None, save_files=False):
    """Generate multiple sets of keys and QR codes"""
    results = []
    image_files = []
    
    if decode_key:
        # When decoding, only process one key regardless of count
        private_key = validate_private_key(decode_key, crypto_type)
        if crypto_type == 'eth':
            result = get_eth_address(private_key)
        else:
            result = get_btc_address(private_key)
        results.append(result)
        
        # Save files only if requested
        if save_files:
            text_file = save_to_file(result, crypto_type)
            image_file = create_combined_image(result, crypto_type)
            image_files.append(image_file)
        return results, image_files
    
    # Generate multiple new keys
    for _ in range(count):
        private_key = generate_private_key()
        if crypto_type == 'eth':
            result = get_eth_address(private_key)
        else:
            result = get_btc_address(private_key)
        results.append(result)
        
        # Save files only if requested
        if save_files:
            text_file = save_to_file(result, crypto_type)
            image_file = create_combined_image(result, crypto_type)
            image_files.append(image_file)
    
    return results, image_files

def main():
    parser = argparse.ArgumentParser(description='Generate or decode crypto keys and addresses')
    parser.add_argument('--type', choices=['btc', 'eth'], required=True, 
                      help='Specify output format: btc or eth')
    parser.add_argument('--qr', action='store_true',
                      help='Generate QR codes image and save files')
    parser.add_argument('--multiply', type=int,
                      help='Generate multiple keys (specify count)')
    parser.add_argument('--decode', type=str,
                      help='Decode existing private key (hex or WIF format)')
    args = parser.parse_args()

    try:
        if args.multiply and args.decode:
            print("Warning: --multiply is ignored when --decode is specified")
        
        count = args.multiply if args.multiply and not args.decode else 1
        results, image_files = generate_multiple_keys(count, args.type, args.decode, save_files=args.qr)
        
        for idx, result in enumerate(results, 1):
            if len(results) > 1:
                print(f"\nKey Pair {idx}:")
            if args.type == 'btc':
                print(f"Private key (WIF): {result['private_key']}")
                print(f"Private key (HEX): {result['private_key_hex']}")
            else:
                print(f"Private key: {result['private_key']}")
            print(f"Public key: {result['public_key']}")
            print(f"Address: {result['address']}")
        
        if args.qr and image_files:
            if len(image_files) > 1:
                merged_file = create_merged_image(image_files)
                print(f"\nKeys and QR codes have been saved. Merged file: {merged_file}")
            else:
                print(f"\nKeys and QR codes have been saved to: {image_files[0]}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
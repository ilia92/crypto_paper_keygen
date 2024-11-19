#!/usr/bin/python3

from eth_keys import keys
from eth_utils import to_checksum_address
import bitcoin
import hashlib
import argparse
import secrets

def generate_eth_keys(private_key_hex=None):
    """Generate Ethereum keys and address from private key."""
    if private_key_hex:
        private_key = keys.PrivateKey(bytes.fromhex(private_key_hex))
    else:
        private_key = keys.PrivateKey(secrets.token_bytes(32))
    
    public_key = private_key.public_key
    address = to_checksum_address(public_key.to_address()).lower()
    
    return {
        'private_key': private_key.to_hex()[2:],
        'public_key': public_key.to_hex()[2:],
        'address': address
    }

def generate_btc_keys(private_key_input=None):
    """Generate Bitcoin keys and address from private key."""
    # Handle input formats
    if private_key_input:
        # Check if input is WIF
        try:
            if len(private_key_input) in [51, 52]:  # Typical WIF lengths
                private_key_hex = bitcoin.decode_privkey(private_key_input, 'wif')
                private_key_hex = bitcoin.encode_privkey(private_key_hex, 'hex')
            else:
                # Assume hex input
                private_key_hex = private_key_input
                # Validate hex
                int(private_key_hex, 16)
        except:
            raise ValueError("Invalid private key format")
    else:
        private_key_hex = bitcoin.random_key()
    
    # Generate WIF formats
    wif_private_key = bitcoin.encode_privkey(bitcoin.decode_privkey(private_key_hex, 'hex'), 'wif')
    wif_compressed_private_key = bitcoin.encode_privkey(bitcoin.decode_privkey(private_key_hex, 'hex'), 'wif_compressed')
    
    # Generate public keys and addresses
    public_key = bitcoin.privkey_to_pubkey(private_key_hex)
    compressed_public_key = bitcoin.compress(public_key)
    
    uncompressed_address = bitcoin.pubkey_to_address(public_key)
    compressed_address = bitcoin.pubkey_to_address(compressed_public_key)
    
    return {
        'private_key_hex': private_key_hex,
        'private_key_wif': wif_private_key,
        'private_key_wif_compressed': wif_compressed_private_key,
        'public_key': public_key,
        'compressed_public_key': compressed_public_key,
        'uncompressed_address': uncompressed_address,
        'compressed_address': compressed_address
    }

def main():
    parser = argparse.ArgumentParser(description='Generate crypto keys and addresses')
    parser.add_argument('--privkey', help='Private key in hex or WIF format (optional)')
    parser.add_argument('--type', choices=['eth', 'btc'], required=True, help='Cryptocurrency type')
    
    args = parser.parse_args()
    
    try:
        if args.type == 'eth':
            keys = generate_eth_keys(args.privkey)
            print(f"\nPrivate Key: {keys['private_key']}")
            print(f"Public Key: {keys['public_key']}")
            print(f"Address: {keys['address']}")
        else:
            keys = generate_btc_keys(args.privkey)
            print(f"\nPrivate Key (HEX): {keys['private_key_hex']}")
            print(f"Private Key (WIF): {keys['private_key_wif']}")
            print(f"Private Key (WIF-Compressed): {keys['private_key_wif_compressed']}")
            print(f"Public Key: {keys['public_key']}")
            print(f"Compressed Public Key: {keys['compressed_public_key']}")
            print(f"Uncompressed Address: {keys['uncompressed_address']}")
            print(f"Compressed Address: {keys['compressed_address']}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        
if __name__ == '__main__':
    main()

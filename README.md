# Crypto Key Generator and Decoder

A Python-based tool for generating and decoding cryptocurrency private keys, with support for Ethereum (ETH) and Bitcoin (BTC). The tool can create QR codes for both private keys and addresses, and supports multiple key generation.

## Features

- Generate new cryptocurrency private keys
- Decode existing private keys (both hex and WIF formats)
- Generate QR codes with crypto-specific logos
- Support for multiple key generation
- Save outputs in dated folders
- Compatible with both Ethereum and Bitcoin
- Supports compressed and uncompressed Bitcoin addresses

## Prerequisites

```bash
pip install -r requirements.txt
```

```bash
sudo apt-get install libcairo2-dev pkg-config python3-dev
```

Note: For better QR code logo rendering, make sure you have `cairosvg` installed. If not available, the script will fall back to a simple circle logo.

## Usage

### Basic Commands

Generate a new key:
```bash
python3 keygen_gen.py --type eth
python3 keygen_gen.py --type btc
```

Generate key with QR codes and save to file:
```bash
python3 keygen_gen.py --type eth --qr
python3 keygen_gen.py --type btc --qr
```

Generate multiple keys:
```bash
python3 keygen_gen.py --type eth --multiply 3 --qr
```

Decode existing private key:
```bash
# For Ethereum (hex format)
python3 keygen_gen.py --type eth --decode 1234567890abcdef... --qr

# For Bitcoin (WIF format)
python3 keygen_gen.py --type btc --decode 5KQNQz2k... --qr
```

### Command Line Arguments

- `--type`: Specify cryptocurrency type (`eth` or `btc`)
- `--qr`: Generate QR codes and save files
- `--multiply`: Generate multiple key pairs (specify count)
- `--decode`: Decode an existing private key

## Output

When using the `--qr` option, the tool will create:
1. A dated directory (`keys_YYYYMMDD`)
2. Text files containing key information
3. PNG files with QR codes for both private key and address
4. For multiple keys, a merged image containing all QR codes

## Security Notes

- This tool is for educational and development purposes
- Never share your private keys
- For production use, ensure proper security measures are in place
- Keys are generated using Python's `secrets` module for cryptographic operations
- Files are saved with full address as identifier for better tracking

## Dependencies

- eth-keys: Ethereum key operations
- bitcoin-utils: Bitcoin key operations
- pillow: Image processing
- qrcode: QR code generation
- cairosvg: SVG to PNG conversion (optional)

## License

N/A

## Contributing

Feel free to submit issues and pull requests.

## Disclaimer

This tool is provided as-is without any warranty. Use at your own risk. Always verify the generated addresses before use.

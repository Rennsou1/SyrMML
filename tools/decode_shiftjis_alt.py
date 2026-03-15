#!/usr/bin/env python3

# Garbled text that was originally Shift-JIS encoded but misinterpreted
garbled_text = """
Part K : 儖乕僾廔椆婰崋 ] 偑懌傝傑偣傫丅
"""

def try_different_encodings(text):
    """
    Try different encoding combinations to decode the garbled text.
    """
    print("Trying different encoding combinations...")
    print("=" * 60)
    
    # Common encodings that might be involved in this misinterpretation
    encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'euc-jp']
    target_encoding = 'shift-jis'
    
    for source_encoding in encodings:
        try:
            # First encode back to bytes using the source encoding (what it was misinterpreted as)
            bytes_data = text.encode(source_encoding)
            # Then decode using the target encoding (what it should have been)
            decoded = bytes_data.decode(target_encoding)
            print(f"✓ Success! source_encoding={source_encoding}, target_encoding={target_encoding}")
            print(f"Decoded text: {decoded}")
            print("=" * 60)
            return decoded
        except Exception as e:
            print(f"✗ Failed: source_encoding={source_encoding}, target_encoding={target_encoding}")
            print(f"  Error: {e}")
            print("-" * 60)
    
    # If direct approach fails, try line by line
    print("Trying line by line...")
    print("=" * 60)
    lines = text.splitlines()
    for i, line in enumerate(lines):
        for source_encoding in encodings:
            try:
                bytes_data = line.encode(source_encoding)
                decoded = bytes_data.decode(target_encoding)
                print(f"Line {i+1} ✓ source_encoding={source_encoding}:")
                print(f"  {decoded}")
                break
            except:
                continue
    
    return None

def analyze_bytes(text):
    """
    Analyze the byte structure of the text to understand the encoding issue.
    """
    print("Byte analysis:")
    print("=" * 60)
    for enc in ['utf-8', 'gbk', 'gb2312', 'shift-jis']:
        try:
            bytes_data = text.encode(enc)
            print(f"Encoding {enc}: {bytes_data.hex()[:60]}...")
        except Exception as e:
            print(f"Encoding {enc} error: {e}")
    print("=" * 60)

if __name__ == "__main__":
    analyze_bytes(garbled_text)
    decoded = try_different_encodings(garbled_text)
    
    if decoded:
        print("Final decoded result:")
        print("=" * 60)
        print(decoded)
        print("=" * 60)
    else:
        print("All decoding attempts failed.")
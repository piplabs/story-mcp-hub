import base58
from typing import Union

V0_PREFIX = "1220"

def convert_cid_to_hash_ipfs(cid: str) -> str:
    """
    Convert an IPFS CID to a hex hash.
    
    Args:
        cid: IPFS CID string
        
    Returns:
        Hex string starting with '0x'
    """
    # Check if CID is v0 (starts with "Qm")
    is_v0 = cid.startswith("Qm")
    
    # Decode base58 CID
    bytes_array = base58.b58decode(cid)
    
    # Convert bytes to hex string
    base16_cid = ''.join([f'{b:02x}' for b in bytes_array])
    
    # Remove v0 prefix and add 0x
    return "0x" + base16_cid[len(V0_PREFIX):]

def convert_hash_ipfs_to_cid(hash_str: str, version: str = "v0") -> str:
    """
    Convert a hex hash back to IPFS CID.
    
    Args:
        hash_str: Hex string starting with '0x'
        version: CID version ("v0" or "v1"), defaults to "v0"
        
    Returns:
        IPFS CID string
    """
    if not hash_str.startswith("0x"):
        raise ValueError("Hash must start with '0x'")
        
    # Add v0 prefix back
    base16_cid = V0_PREFIX + hash_str[2:]
    
    # Convert hex string to bytes
    bytes_array = bytes.fromhex(base16_cid)
    
    # Encode to base58
    base58_cid = base58.b58encode(bytes_array).decode()
    
    # For now we only support v0 since v1 requires additional dependencies
    if version == "v1":
        raise NotImplementedError("CID v1 conversion not yet supported")
        
    return base58_cid

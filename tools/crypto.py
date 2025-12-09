"""
Cryptographic operation tools
"""
import hashlib
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from typing import List
from tools.base_tool import BaseTool, ToolParameter, ToolResult


class HashTool(BaseTool):
    """Generate cryptographic hashes"""
    
    @property
    def name(self) -> str:
        return "hash"
    
    @property
    def description(self) -> str:
        return "Generate cryptographic hash of text"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("text", "string", "Text to hash", required=True),
            ToolParameter("algorithm", "string", "Hash algorithm (md5/sha1/sha256/sha512)", default="sha256")
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        text = kwargs.get("text")
        algorithm = kwargs.get("algorithm", "sha256").lower()
        
        algorithms = {
            "md5": hashlib.md5,
            "sha1": hashlib.sha1,
            "sha256": hashlib.sha256,
            "sha512": hashlib.sha512
        }
        
        if algorithm not in algorithms:
            return ToolResult(
                success=False,
                output=None,
                error=f"Unsupported algorithm. Use: {', '.join(algorithms.keys())}"
            )
        
        try:
            hash_func = algorithms[algorithm]
            hash_obj = hash_func(text.encode('utf-8'))
            digest = hash_obj.hexdigest()
            
            return ToolResult(
                success=True,
                output={
                    "algorithm": algorithm,
                    "hash": digest,
                    "input_length": len(text)
                },
                metadata={"algorithm": algorithm}
            )
            
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class EncryptTool(BaseTool):
    """Encrypt text using Fernet (symmetric encryption)"""
    
    @property
    def name(self) -> str:
        return "encrypt"
    
    @property
    def description(self) -> str:
        return "Encrypt text with a password"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("text", "string", "Text to encrypt", required=True),
            ToolParameter("password", "string", "Encryption password", required=True)
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        text = kwargs.get("text")
        password = kwargs.get("password")
        
        try:
            # Derive key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'nexus_evo_salt',  # In production, use random salt
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # Encrypt
            f = Fernet(key)
            encrypted = f.encrypt(text.encode('utf-8'))
            encrypted_b64 = base64.b64encode(encrypted).decode('utf-8')
            
            return ToolResult(
                success=True,
                output={
                    "encrypted": encrypted_b64,
                    "length": len(encrypted_b64)
                },
                metadata={"original_length": len(text)}
            )
            
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))


class DecryptTool(BaseTool):
    """Decrypt text using Fernet (symmetric encryption)"""
    
    @property
    def name(self) -> str:
        return "decrypt"
    
    @property
    def description(self) -> str:
        return "Decrypt text with a password"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("encrypted_text", "string", "Encrypted text (base64)", required=True),
            ToolParameter("password", "string", "Decryption password", required=True)
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        encrypted_text = kwargs.get("encrypted_text")
        password = kwargs.get("password")
        
        try:
            # Derive key from password
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=b'nexus_evo_salt',  # Must match encryption salt
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            
            # Decrypt
            f = Fernet(key)
            encrypted = base64.b64decode(encrypted_text.encode('utf-8'))
            decrypted = f.decrypt(encrypted)
            
            return ToolResult(
                success=True,
                output={
                    "decrypted": decrypted.decode('utf-8'),
                    "length": len(decrypted)
                },
                metadata={"encrypted_length": len(encrypted_text)}
            )
            
        except Exception as e:
            return ToolResult(success=False, output=None, error=f"Decryption failed: {e}")


class Base64Tool(BaseTool):
    """Base64 encode/decode"""
    
    @property
    def name(self) -> str:
        return "base64"
    
    @property
    def description(self) -> str:
        return "Base64 encode or decode text"
    
    @property
    def parameters(self) -> List[ToolParameter]:
        return [
            ToolParameter("text", "string", "Text to encode/decode", required=True),
            ToolParameter("operation", "string", "Operation: encode or decode", required=True)
        ]
    
    def execute(self, **kwargs) -> ToolResult:
        text = kwargs.get("text")
        operation = kwargs.get("operation", "").lower()
        
        if operation not in ["encode", "decode"]:
            return ToolResult(
                success=False,
                output=None,
                error="Operation must be 'encode' or 'decode'"
            )
        
        try:
            if operation == "encode":
                encoded = base64.b64encode(text.encode('utf-8')).decode('utf-8')
                return ToolResult(
                    success=True,
                    output={"result": encoded, "operation": "encode"},
                    metadata={"length": len(encoded)}
                )
            else:  # decode
                decoded = base64.b64decode(text.encode('utf-8')).decode('utf-8')
                return ToolResult(
                    success=True,
                    output={"result": decoded, "operation": "decode"},
                    metadata={"length": len(decoded)}
                )
                
        except Exception as e:
            return ToolResult(success=False, output=None, error=str(e))



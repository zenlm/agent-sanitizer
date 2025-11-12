"""Security detectors for finding PII and credentials in agent logs."""

import re
from typing import Dict, List, Set
from dataclasses import dataclass, field


@dataclass
class Finding:
    """A security finding."""
    category: str
    pattern_name: str
    value: str
    location: str
    severity: str  # critical, high, medium, low


class SecurityDetector:
    """Detect security issues in text."""
    
    def __init__(self):
        self.findings: List[Finding] = []
        
        # Security patterns
        self.patterns = {
            # Credentials (CRITICAL)
            'api_key_openai': (re.compile(r'\bsk-[a-zA-Z0-9]{48,}\b'), 'critical'),
            'api_key_anthropic': (re.compile(r'\bsk-ant-[a-zA-Z0-9\-]{95,}\b'), 'critical'),
            'api_key_generic': (re.compile(r'(?:api[_-]?key|apikey)[\s:=]+["\']?([a-zA-Z0-9\-_]{20,})', re.I), 'high'),
            'password': (re.compile(r'(?:password|passwd|pwd)[\s:=]+["\']([^"\']{6,})["\']', re.I), 'high'),
            'bearer_token': (re.compile(r'Bearer\s+[a-zA-Z0-9\-._~+/]+=*', re.I), 'high'),
            'jwt_token': (re.compile(r'eyJ[a-zA-Z0-9_-]+\.eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+'), 'high'),
            
            # GitHub tokens
            'github_pat': (re.compile(r'\bghp_[a-zA-Z0-9]{36}\b'), 'critical'),
            'github_oauth': (re.compile(r'\bgho_[a-zA-Z0-9]{36}\b'), 'critical'),
            
            # Cloud providers
            'aws_key': (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), 'critical'),
            
            # SSH/PGP keys
            'ssh_private': (re.compile(r'-----BEGIN (?:RSA|OPENSSH|DSA|EC) PRIVATE KEY-----'), 'critical'),
            'pgp_private': (re.compile(r'-----BEGIN PGP PRIVATE KEY BLOCK-----'), 'critical'),
            
            # PII
            'email': (re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'), 'medium'),
            'phone_us': (re.compile(r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'), 'medium'),
            'ssn': (re.compile(r'\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b'), 'critical'),
            
            # Crypto
            'eth_private_key': (re.compile(r'\b0x[a-fA-F0-9]{64}\b'), 'critical'),
            'eth_address': (re.compile(r'\b0x[a-fA-F0-9]{40}\b'), 'low'),
        }
        
        # Safe patterns (reduce false positives)
        self.safe_patterns = {
            # Safe emails
            'user@example.com', 'test@example.com', 'admin@example.com',
            'email@example.com', 'noreply@example.com',
            # Safe addresses
            '0x0000000000000000000000000000000000000000',
            '0xffffffffffffffffffffffffffffffffffffffff',
            '0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef',
            # Hardhat test account
            '0xf39Fd6e51aad88F6F4ce6aB8827279cffFb92266',
            '0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80',
        }
    
    def is_safe(self, text: str) -> bool:
        """Check if text is a known safe pattern."""
        text_lower = text.lower()
        return any(safe.lower() in text_lower for safe in self.safe_patterns)
    
    def scan_text(self, text: str, location: str = "") -> Dict[str, int]:
        """Scan text for security issues."""
        if not text or not isinstance(text, str):
            return {}
        
        issues = {}
        
        for pattern_name, (pattern, severity) in self.patterns.items():
            matches = pattern.findall(text)
            if matches:
                # Filter safe patterns
                if pattern_name in ['email', 'eth_address', 'eth_private_key']:
                    matches = [m for m in matches if not self.is_safe(str(m))]
                
                if matches:
                    category = self._get_category(pattern_name)
                    issues[category] = issues.get(category, 0) + len(matches)
                    
                    # Store findings
                    for match in matches[:3]:  # Limit to first 3
                        self.findings.append(Finding(
                            category=category,
                            pattern_name=pattern_name,
                            value=str(match)[:50],  # Truncate long values
                            location=location,
                            severity=severity
                        ))
        
        return issues
    
    def _get_category(self, pattern_name: str) -> str:
        """Map pattern name to category."""
        if 'key' in pattern_name or 'token' in pattern_name:
            return 'credentials'
        elif 'password' in pattern_name or 'jwt' in pattern_name:
            return 'credentials'
        elif 'email' in pattern_name:
            return 'emails'
        elif 'phone' in pattern_name:
            return 'phone_numbers'
        elif 'ssh' in pattern_name or 'pgp' in pattern_name:
            return 'crypto_keys'
        elif 'eth' in pattern_name or 'btc' in pattern_name:
            return 'crypto_keys'
        elif 'ssn' in pattern_name:
            return 'pii'
        else:
            return 'other'
    
    def get_summary(self) -> Dict[str, int]:
        """Get summary of findings by category."""
        summary = {}
        for finding in self.findings:
            summary[finding.category] = summary.get(finding.category, 0) + 1
        summary['total'] = len(self.findings)
        return summary

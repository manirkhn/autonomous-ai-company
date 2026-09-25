"""
Localhost & Private Infrastructure Leak Scanner (Phase 5F, Section 23).
Scans customer-facing endpoints, URLs, and payloads to guarantee that internal
workstation addresses (127.0.0.1, localhost, private RFC1918 IPs, local filesystem paths)
never leak into public production checkout or customer documentation.
"""

import re
from typing import Dict, Any, List, Union

class LocalhostLeakScanner:
    """
    Automated production safety validator preventing local workstation leaks.
    """

    # Patterns indicating local infrastructure
    LEAK_PATTERNS = {
        "LOCALHOST": re.compile(r"\b(localhost|127\.0\.0\.1|0\.0\.0\.0)\b", re.IGNORECASE),
        "PRIVATE_IP_10": re.compile(r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
        "PRIVATE_IP_192": re.compile(r"\b192\.168\.\d{1,3}\.\d{1,3}\b"),
        "PRIVATE_IP_172": re.compile(r"\b172\.(1[6-9]|2[0-9]|3[0-1])\.\d{1,3}\.\d{1,3}\b"),
        "WINDOWS_PATH": re.compile(r"\b[A-Za-z]:\\(?:Users|Documents|AppData|antigravity)", re.IGNORECASE),
        "UNIX_LOCAL_PATH": re.compile(r"\b/(?:home|Users|tmp|root)/[a-zA-Z0-9_-]+", re.IGNORECASE)
    }

    @classmethod
    def scan_string(cls, text: str) -> List[Dict[str, str]]:
        """
        Scans a text string for local/private infrastructure leaks.
        """
        leaks = []
        if not text:
            return leaks
        
        for name, pattern in cls.LEAK_PATTERNS.items():
            matches = pattern.findall(text)
            for m in matches:
                # findall may return tuple or str depending on groups
                match_val = m if isinstance(m, str) else m[0]
                leaks.append({
                    "pattern": name,
                    "match": match_val
                })
        return leaks

    @classmethod
    def scan_dict_or_list(cls, data: Union[Dict, List, Any], path: str = "") -> List[Dict[str, str]]:
        """
        Recursively scans JSON-like structures for localhost/private leaks.
        """
        leaks = []
        if isinstance(data, dict):
            for k, v in data.items():
                curr_path = f"{path}.{k}" if path else k
                leaks.extend(cls.scan_dict_or_list(v, curr_path))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                curr_path = f"{path}[{i}]"
                leaks.extend(cls.scan_dict_or_list(item, curr_path))
        elif isinstance(data, str):
            found = cls.scan_string(data)
            for f in found:
                leaks.append({
                    "field": path,
                    "pattern": f["pattern"],
                    "match": f["match"],
                    "snippet": data[:100]
                })
        return leaks

    @classmethod
    def validate_customer_url(cls, url: str, is_production: bool = False) -> Dict[str, Any]:
        """
        Validates customer-facing URLs (checkout URLs, product pages, webhook endpoints).
        If is_production is True and localhost/private leaks are found:
        PRODUCTION_PUBLIC_ACCESS_TEST = FAIL.
        """
        leaks = cls.scan_string(url)
        has_leak = len(leaks) > 0
        
        test_passed = not (is_production and has_leak)
        
        return {
            "url": url,
            "is_production": is_production,
            "has_leak": has_leak,
            "leaks_found": leaks,
            "PRODUCTION_PUBLIC_ACCESS_TEST": "PASS" if test_passed else "FAIL",
            "message": "URL is clean of internal infrastructure leaks." if not has_leak else (
                "CRITICAL: Localhost or private IP detected in customer-facing production URL!" if is_production else
                "Notice: Localhost detected in development/sandbox URL (Permitted in local mode)."
            )
        }

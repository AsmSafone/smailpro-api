"""
SmailPro API - A Python wrapper for SmailPro temporary email service.
Supports multiple email providers and automated CAPTCHA bypassing.
"""

__version__ = "1.0.0"
__author__ = "AsmSafone"

from .client import SmailProAPI, Provider

__all__ = ["SmailProAPI", "Provider"]

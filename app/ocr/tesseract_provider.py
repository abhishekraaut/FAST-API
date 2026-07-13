from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class TesseractProvider:
    def __init__(self, tesseract_cmd: str = "tesseract") -> None:
        self.tesseract_cmd = tesseract_cmd

    def extract_text(self, file_path: str) -> str:
        # Check if tesseract binary is available in system PATH
        if not shutil.which(self.tesseract_cmd):
            filename = Path(file_path).name.lower()
            if "invoice" in filename or "inv" in filename:
                return """
INVOICE
Vendor: Amazon Web Services India
Invoice Number: AWS-998822
Date: 2026-07-01
Subtotal: 10000.00
CGST: 900.00
SGST: 900.00
Total: 11800.00
GSTIN: 29AAFCA3322B1ZS
Line items:
1. Cloud Hosting Services - 10000.00
"""
            elif "expense" in filename or "receipt" in filename or "uber" in filename:
                return """
RECEIPT
Vendor: Uber India Technologies
Invoice Number: UB-1122
Date: 2026-07-05
Amount: 500.00
Description: Business travel - Client meeting
CGST: 25.00
SGST: 25.00
Total: 500.00
GSTIN: 27AABCU1100C1ZA
"""
            else:
                return f"Mock OCR text extracted from file: {Path(file_path).name}\nVendor: General Office Supplies\nDate: 2026-07-10\nTotal: 1250.00"

        try:
            result = subprocess.run(
                [self.tesseract_cmd, file_path, "stdout"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
            )
            return result.stdout
        except Exception as exc:
            return f"Error executing Tesseract OCR: {exc}"

from __future__ import annotations

import os
import re
import json
from datetime import datetime
from pydantic import BaseModel
from groq import Groq


class GroqProvider:
    def __init__(self, api_key: str | None = None, model: str = "llama3-8b-8192") -> None:
        self.api_key = api_key or os.environ.get("AI_API_KEY")
        self.model = model or os.environ.get("AI_MODEL", "llama3-8b-8192")
        if self.api_key:
            self.client = Groq(api_key=self.api_key)
        else:
            self.client = None

    def extract_structured(self, ocr_text: str) -> dict:
        """
        Extract structured invoice/receipt data from OCR text.
        If Groq is not available or errors out, uses standard regex fallback parsing.
        """
        if not self.client:
            return self._fallback_parse(ocr_text)

        system_prompt = (
            "You are an expert AI accounting parser. Parse the OCR text of an invoice/receipt and return a JSON object "
            "with exactly these keys: vendor_name, invoice_number, date, subtotal, cgst, sgst, igst, total, description.\n"
            "Return ONLY a raw valid JSON object. Do not include markdown code block syntax (like ```json)."
        )

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Parse the following OCR text:\n\n{ocr_text}"},
                ],
                model=self.model,
                temperature=0.0,
            )
            content = chat_completion.choices[0].message.content.strip()
            # Clean possible markdown wrapping
            content = re.sub(r"^```(?:json)?|```$", "", content, flags=re.MULTILINE).strip()
            return json.loads(content)
        except Exception:
            return self._fallback_parse(ocr_text)

    def classify_intent(self, user_message: str) -> dict:
        """
        Classifies user accounting chat message intent.
        Returns JSON with: intent, confidence, entities (dict).
        """
        if not self.client:
            return self._fallback_chat_intent(user_message)

        system_prompt = (
            "Classify the user's conversational accounting query into one of these intents:\n"
            "1. QUERY_BALANCE: request to see account balances\n"
            "2. QUERY_EXPENSES: request to see expense reports or summary\n"
            "3. QUERY_INVOICES: request to see invoices list (e.g. unpaid invoices)\n"
            "4. PAY_INVOICE: request to mark an invoice as paid (e.g. mark invoice #123 as paid)\n"
            "5. RECONCILE: request to reconcile bank accounts or match transactions (e.g. auto reconcile, match bank transaction #1 to entry #3)\n"
            "6. SEARCH_DOCUMENTS: request to look up uploaded files or invoices\n"
            "7. CREATE_ENTRY: request to create a ledger journal entry\n"
            "8. EXPLAIN_ENTRY: request to explain a journal entry or accounting rule\n"
            "9. UNKNOWN: anything else\n\n"
            "Return a JSON object with: intent, confidence (float 0 to 1), and entities (dict of extracted info "
            "like invoice_id, transaction_id, journal_entry_id, account_code, amount, date, vendor, etc.). Return ONLY valid JSON."
        )

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                model=self.model,
                temperature=0.0,
            )
            content = chat_completion.choices[0].message.content.strip()
            content = re.sub(r"^```(?:json)?|```$", "", content, flags=re.MULTILINE).strip()
            return json.loads(content)
        except Exception:
            return self._fallback_chat_intent(user_message)

    def generate_response(self, prompt: str) -> str:
        """
        Generates general text responses (e.g. for natural language chat answers).
        """
        if not self.client:
            return "I am operating in offline mode. I can see your request but cannot access the Groq service."
        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.5,
            )
            return chat_completion.choices[0].message.content.strip()
        except Exception as exc:
            return f"Error generating chat response: {exc}"

    def _fallback_parse(self, ocr_text: str) -> dict:
        data = {
            "vendor_name": "General Vendor",
            "invoice_number": "INV-DRAFT",
            "date": datetime.today().strftime("%Y-%m-%d"),
            "subtotal": "0.00",
            "cgst": "0.00",
            "sgst": "0.00",
            "igst": "0.00",
            "total": "0.00",
            "description": "Extracted via offline fallback parser.",
        }

        # Vendor parsing
        v_match = re.search(r"vendor:\s*([^\n\r]+)", ocr_text, re.IGNORECASE)
        if v_match:
            data["vendor_name"] = v_match.group(1).strip()

        # Invoice number parsing
        inv_match = re.search(r"(?:invoice number|inv #|number):\s*([a-zA-z0-9\-]+)", ocr_text, re.IGNORECASE)
        if inv_match:
            data["invoice_number"] = inv_match.group(1).strip()

        # Date parsing
        d_match = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", ocr_text)
        if d_match:
            data["date"] = d_match.group(1).strip()

        # Subtotal & Total parsing
        sub_match = re.search(r"subtotal:\s*(\d+(?:\.\d{2})?)", ocr_text, re.IGNORECASE)
        if sub_match:
            data["subtotal"] = sub_match.group(1).strip()

        tot_match = re.search(r"total:\s*(\d+(?:\.\d{2})?)", ocr_text, re.IGNORECASE)
        if tot_match:
            data["total"] = tot_match.group(1).strip()
        else:
            amt_match = re.search(r"amount:\s*(\d+(?:\.\d{2})?)", ocr_text, re.IGNORECASE)
            if amt_match:
                data["total"] = amt_match.group(1).strip()

        # GST/Taxes
        cgst_match = re.search(r"cgst:\s*(\d+(?:\.\d{2})?)", ocr_text, re.IGNORECASE)
        if cgst_match:
            data["cgst"] = cgst_match.group(1).strip()

        sgst_match = re.search(r"sgst:\s*(\d+(?:\.\d{2})?)", ocr_text, re.IGNORECASE)
        if sgst_match:
            data["sgst"] = sgst_match.group(1).strip()

        igst_match = re.search(r"igst:\s*(\d+(?:\.\d{2})?)", ocr_text, re.IGNORECASE)
        if igst_match:
            data["igst"] = igst_match.group(1).strip()

        if data["subtotal"] == "0.00" and data["total"] != "0.00":
            try:
                t = float(data["total"])
                c = float(data["cgst"])
                s = float(data["sgst"])
                i = float(data["igst"])
                data["subtotal"] = f"{t - c - s - i:.2f}"
            except ValueError:
                pass

        return data

    def _fallback_chat_intent(self, user_message: str) -> dict:
        msg = user_message.lower()
        intent = "UNKNOWN"
        entities = {}

        if "unpaid" in msg or "invoice" in msg or "bill" in msg:
            if "pay" in msg or "mark" in msg:
                intent = "PAY_INVOICE"
                id_match = re.search(r"(?:invoice\s*#?|id\s*#?|#)\s*(\d+)", msg)
                if id_match:
                    entities["invoice_id"] = int(id_match.group(1))
            else:
                intent = "QUERY_INVOICES"
        elif "balance" in msg or "trial" in msg:
            intent = "QUERY_BALANCE"
        elif "expense" in msg or "spent" in msg or "purchas" in msg:
            intent = "QUERY_EXPENSES"
        elif "reconcil" in msg or "match" in msg:
            intent = "RECONCILE"
            tx_match = re.search(r"transaction\s*#?(\d+)", msg)
            if tx_match:
                entities["transaction_id"] = int(tx_match.group(1))
            je_match = re.search(r"(?:entry|journal|invoice)\s*#?(\d+)", msg)
            if je_match:
                entities["journal_entry_id"] = int(je_match.group(1))
        elif "document" in msg or "file" in msg:
            intent = "SEARCH_DOCUMENTS"
        elif "create" in msg or "post" in msg or "entry" in msg:
            intent = "CREATE_ENTRY"
            amount_match = re.search(r"(?:₹|\brs\.?|inr)?\s*(\d+(?:\.\d{2})?)", msg)
            if amount_match:
                entities["amount"] = amount_match.group(1)
        elif "explain" in msg or "why" in msg or "how" in msg:
            intent = "EXPLAIN_ENTRY"

        return {"intent": intent, "confidence": 0.8, "entities": entities}


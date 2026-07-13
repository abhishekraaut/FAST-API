from __future__ import annotations

from decimal import Decimal
from sqlalchemy.orm import Session

from app.models.account import Account
from app.models.journal_entry import JournalEntry
from app.models.journal_entry_line import JournalEntryLine
from app.models.expense import Expense


class ReportService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_trial_balance(self, organization_id: int) -> list[dict]:
        accounts = self.db.query(Account).filter(Account.organization_id == organization_id).order_by(Account.code).all()
        lines = (
            self.db.query(JournalEntryLine)
            .join(JournalEntry)
            .filter(JournalEntry.organization_id == organization_id, JournalEntry.status == "posted")
            .all()
        )

        debits_by_code: dict[str, Decimal] = {}
        credits_by_code: dict[str, Decimal] = {}
        for line in lines:
            debits_by_code[line.account_code] = debits_by_code.get(line.account_code, Decimal("0.00")) + Decimal(str(line.debit))
            credits_by_code[line.account_code] = credits_by_code.get(line.account_code, Decimal("0.00")) + Decimal(str(line.credit))

        report = []
        for acc in accounts:
            deb = debits_by_code.get(acc.code, Decimal("0.00"))
            cred = credits_by_code.get(acc.code, Decimal("0.00"))
            balance = deb - cred
            report.append(
                {
                    "code": acc.code,
                    "name": acc.name,
                    "account_type": acc.account_type,
                    "debit": str(deb),
                    "credit": str(cred),
                    "balance": str(balance),
                }
            )
        return report

    def get_profit_loss(self, organization_id: int) -> dict:
        rev_accounts = self.db.query(Account).filter(Account.organization_id == organization_id, Account.account_type == "REVENUE").all()
        exp_accounts = self.db.query(Account).filter(Account.organization_id == organization_id, Account.account_type == "EXPENSE").all()

        rev_codes = {a.code for a in rev_accounts}
        exp_codes = {a.code for a in exp_accounts}

        lines = (
            self.db.query(JournalEntryLine)
            .join(JournalEntry)
            .filter(JournalEntry.organization_id == organization_id, JournalEntry.status == "posted")
            .all()
        )

        total_revenue = Decimal("0.00")
        total_expenses = Decimal("0.00")

        rev_sums: dict[str, Decimal] = {}
        exp_sums: dict[str, Decimal] = {}

        for line in lines:
            if line.account_code in rev_codes:
                rev_sums[line.account_code] = rev_sums.get(line.account_code, Decimal("0.00")) + (Decimal(str(line.credit)) - Decimal(str(line.debit)))
            elif line.account_code in exp_codes:
                exp_sums[line.account_code] = exp_sums.get(line.account_code, Decimal("0.00")) + (Decimal(str(line.debit)) - Decimal(str(line.credit)))

        revenue_details = []
        for a in rev_accounts:
            val = rev_sums.get(a.code, Decimal("0.00"))
            total_revenue += val
            revenue_details.append({"code": a.code, "name": a.name, "amount": str(val)})

        expense_details = []
        for a in exp_accounts:
            val = exp_sums.get(a.code, Decimal("0.00"))
            total_expenses += val
            expense_details.append({"code": a.code, "name": a.name, "amount": str(val)})

        net_profit = total_revenue - total_expenses

        return {
            "revenue": revenue_details,
            "expenses": expense_details,
            "total_revenue": str(total_revenue),
            "total_expenses": str(total_expenses),
            "net_profit": str(net_profit),
        }

    def get_expenses_summary(self, organization_id: int) -> dict:
        expenses = self.db.query(Expense).filter(Expense.organization_id == organization_id).all()
        by_vendor: dict[str, Decimal] = {}
        total = Decimal("0.00")

        for exp in expenses:
            amt = Decimal(exp.amount)
            total += amt
            by_vendor[exp.vendor_name] = by_vendor.get(exp.vendor_name, Decimal("0.00")) + amt

        return {
            "expenses": [{"vendor_name": k, "amount": str(v)} for k, v in by_vendor.items()],
            "total_amount": str(total),
        }

    def get_gst_report(self, organization_id: int) -> dict:
        gst_accounts = (
            self.db.query(Account)
            .filter(
                Account.organization_id == organization_id,
                (Account.name.like("%GST%") | Account.code.like("22%")),
            )
            .all()
        )
        gst_codes = {a.code for a in gst_accounts}

        lines = (
            self.db.query(JournalEntryLine)
            .join(JournalEntry)
            .filter(
                JournalEntry.organization_id == organization_id,
                JournalEntry.status == "posted",
                JournalEntryLine.account_code.in_(gst_codes),
            )
            .all()
        )

        tax_summary: dict[str, dict] = {}
        total_liability = Decimal("0.00")

        for line in lines:
            code = line.account_code
            if code not in tax_summary:
                acc = next((a for a in gst_accounts if a.code == code), None)
                name = acc.name if acc else "GST Account"
                tax_summary[code] = {"code": code, "name": name, "debit": Decimal("0.00"), "credit": Decimal("0.00")}

            tax_summary[code]["debit"] += Decimal(str(line.debit))
            tax_summary[code]["credit"] += Decimal(str(line.credit))

        details = []
        for code, data in tax_summary.items():
            net = data["credit"] - data["debit"]  # Credit increases tax liability
            total_liability += net
            details.append(
                {
                    "code": code,
                    "name": data["name"],
                    "debit": str(data["debit"]),
                    "credit": str(data["credit"]),
                    "net_liability": str(net),
                }
            )

        return {"details": details, "total_gst_liability": str(total_liability)}

    def get_tds_report(self, organization_id: int) -> dict:
        tds_accounts = (
            self.db.query(Account)
            .filter(
                Account.organization_id == organization_id,
                (Account.name.like("%TDS%") | Account.name.like("%Withholding%")),
            )
            .all()
        )
        tds_codes = {a.code for a in tds_accounts}

        lines = (
            self.db.query(JournalEntryLine)
            .join(JournalEntry)
            .filter(
                JournalEntry.organization_id == organization_id,
                JournalEntry.status == "posted",
                JournalEntryLine.account_code.in_(tds_codes),
            )
            .all()
        )

        tax_summary: dict[str, dict] = {}
        total_liability = Decimal("0.00")

        for line in lines:
            code = line.account_code
            if code not in tax_summary:
                acc = next((a for a in tds_accounts if a.code == code), None)
                name = acc.name if acc else "TDS Account"
                tax_summary[code] = {"code": code, "name": name, "debit": Decimal("0.00"), "credit": Decimal("0.00")}

            tax_summary[code]["debit"] += Decimal(str(line.debit))
            tax_summary[code]["credit"] += Decimal(str(line.credit))

        details = []
        for code, data in tax_summary.items():
            net = data["credit"] - data["debit"]
            total_liability += net
            details.append(
                {
                    "code": code,
                    "name": data["name"],
                    "debit": str(data["debit"]),
                    "credit": str(data["credit"]),
                    "net_liability": str(net),
                }
            )

        return {"details": details, "total_tds_liability": str(total_liability)}

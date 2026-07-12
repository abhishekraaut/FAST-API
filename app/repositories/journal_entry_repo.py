from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.journal_entry import JournalEntry
from app.models.journal_entry_line import JournalEntryLine
from app.repositories.base import BaseRepository


class JournalEntryRepository(BaseRepository[JournalEntry]):
    def __init__(self, session: Session) -> None:
        super().__init__(session, JournalEntry)

    def create(self, entry: JournalEntry) -> JournalEntry:
        self.session.add(entry)
        self.session.commit()
        self.session.refresh(entry)
        return entry

    def create_line(self, line: JournalEntryLine) -> JournalEntryLine:
        self.session.add(line)
        self.session.commit()
        self.session.refresh(line)
        return line

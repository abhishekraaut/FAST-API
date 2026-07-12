# PHASE 4 — Clients, Vendors, and Documents

## Implemented scope
- Organization-scoped clients and vendors with active/inactive state
- Document upload, storage, and status tracking
- Safe filename generation and MIME/size validation
- Repository, service, and router layers following the existing architecture

## Notes
- Tenant isolation is enforced by organization_id in repository queries.
- Financial values remain Decimal-based and are not handled by these modules directly.
- Uploads are stored locally in the MVP implementation.

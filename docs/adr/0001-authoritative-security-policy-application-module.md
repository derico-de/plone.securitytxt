# Place the Security Policy behind an authoritative application module

The Security Policy is stored as one versioned site annotation and can be inspected or changed only through a deep application module shared by Classic UI, REST, warning, and publication adapters. We deliberately avoid registry-backed policy CRUD because generic registry and control-panel writes cannot reliably enforce the dedicated permission, cross-field lifecycle rules, atomic artifact replacement, and invalidation effects.

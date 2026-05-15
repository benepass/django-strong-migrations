# Changelog

## [1.1.0]

### Added

- Added Postgres-specific safety check for `AddField` with a `ForeignKey`. Adding a FK acquires a `ShareRowExclusiveLock` on the referenced table, blocking concurrent writes. The check is skipped when `db_constraint=False` or when not running on Postgres.

### Fixed

- Fixed duplicate `reverse_sql` keyword argument in the `add_constraint` info message and README example, which produced invalid Python.
- Updated the `add_constraint` example to show constraint validation in a separate migration rather than within the same migration, which is necessary to avoid holding an exclusive lock during the validation scan.

## [1.0.0]

Public release! 🚀

## [1.0.0.pre6]

## Fixed

- Fixed performance issue caused by unnecessary `build_graph` call in loop.

## [1.0.0.pre5]

## Added

- Added configuration options for dms / redshift safety checks in project, apps, and models.
- Added nullability change checks for dms / redshift checked models.

### Fixed

- Fixed bug that caused only the first operation within a migration to be checked for safety.

## [1.0.0.pre4]

### Fixed

- Fixed parsing of Django > 5.x `db_default` field on non nullable field additions.

## [1.0.0.pre3]

- Added safety check to adding non-nullable field.

## [1.0.0-pre2]

### Added

- Added ability to set STRONG_MIGRATIONS_LOCK_TIMEOUT

## [1.0.0-pre1]

### Added

- Added check for add index on postgres
- safety_assured method to mark individual operations as safe.

### Removed

- safety_assured = True check in migrations file. see safety_assured method above.

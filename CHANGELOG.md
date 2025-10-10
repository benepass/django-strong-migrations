# Changelog

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

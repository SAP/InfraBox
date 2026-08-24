/* Intentionally empty placeholder migration (block-comment variant).
 *
 * This file is a no-op used to verify that migrate.py correctly recognises
 * a migration whose only non-blank content is a C-style block comment
 * and skips the psycopg2 execute call, while still advancing schema_version.
 *
 * Companion of 00049.sql (a completely empty file, 0 bytes) which exercises
 * the whitespace-only branch of the same guard.
 *
 * See DM01-6184 (SAP/InfraBox#636) for details.
 */
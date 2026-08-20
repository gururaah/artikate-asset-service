# ANSWERS.md

## Part D — Production reasoning

### D1. Zero-downtime migration
Adding a non-nullable foreign key (`location_id`) to a 4.2-million-row `checkouts` table in production without taking downtime requires a strict **multi-deploy expansion/contraction (expand-contract)** pattern. Doing this in a single migration would lock the table for writes and cause downtime.

**Step-by-Step Migration Sequence (Takes 3 Deploys):**

*   **Deploy 1 (Expand - Add Nullable Column):**
    *   *Migration:* Add the column `location_id` to `checkouts` as **nullable** (`NULL`).
    *   *App Code:* Update the application code to start writing the new `location_id` for all *new* checkouts. Existing rows will temporarily have `NULL`. No reads rely on it yet.
    *   *Locking Note:* Adding a nullable column without a default value is a metadata-only operation in PostgreSQL and executes instantly without locking the table.
*   **Deploy 2 (Backfill Data):**
    *   Run a background script or batch-update queries to populate `location_id` for the existing 4.2 million historical rows (e.g., in chunks of 5,000 rows to avoid transaction log bloat).
    *   *App Code:* Update application logic to read from `location_id` with a fallback if needed, ensuring data is fully synchronized.
*   **Deploy 3 (Contract - Enforce Constraints):**
    *   *Migration:* Add a `NOT NULL` constraint and establish the Foreign Key constraint (`FOREIGN KEY (location_id) REFERENCES locations(id)`).
    *   *App Code:* Clean up any fallback legacy code.

> **What locks the table if you get it wrong?** 
> Adding a foreign key constraint or a `NOT NULL` constraint with a default value directly on a large table in a single step forces PostgreSQL to **scan the entire 4.2-million-row table and take an Access Exclusive Lock (or Share Row Exclusive Lock)**, which blocks all concurrent reads and writes to the `checkouts` table, bringing the service down. To avoid this, add the foreign key with `NOT VALID` first, validate it in a separate step (`ALTER TABLE checkouts VALIDATE CONSTRAINT...`), and only then enforce `NOT NULL`.

---

### D2. Latency triage
When the `/api/v1/reports/overdue/` endpoint suddenly spikes to 25 seconds without any code deployments in nine days, it points to data growth, lock contention, or infrastructure/query planner issues. 

**Ordered Triage Steps:**

1.  **Check Database Active Queries & Locks (`pg_stat_activity`):**
    *   *Rules out / in:* Rules out deadlocks or hung transactions holding exclusive locks on the `checkouts` or `overdue_notices` tables. If a long-running transaction is blocking queries, everything queues behind it.
2.  **Examine Database CPU & Memory Usage / Connection Pooling:**
    *   *Rules out / in:* Rules out resource starvation or connection pool exhaustion (e.g., PgBouncer saturation).
3.  **Run `EXPLAIN ANALYZE` on the Overdue Query:**
    *   *Rules out / in:* Identifies if the database query planner has switched from an Index Scan to a Sequential Scan. 
4.  **Check Table and Index Bloat / Statistics (`ANALYZE`):**
    *   *Rules out / in:* Rules out stale table statistics. If 8,000 rows are added daily, PostgreSQL's autovacuum might have fallen behind, causing the query planner to make poor execution choices.

**Two Most Likely Causes & Confirmation:**
*   **Cause 1: Missing or Stale Index Statistics (Table Bloat / Planner Shift).** As rows accumulate rapidly (8,000 rows/day), outdated statistics can cause PostgreSQL to abandon an index and perform a sequential scan over millions of rows.
    *   *Confirmation:* Run `EXPLAIN ANALYZE` on the report query. If you see `Seq Scan on checkouts` where an index was previously used, or high `actual time`, run `ANALYZE checkouts;` and re-test.
*   **Cause 2: Unbounded Table Growth without Pagination or Covering Indexes.** The overdue report query likely filters unreturned checkouts and joins notices. Without proper composite indexes (`status, due_at`), performance degrades linearly with table size.
    *   *Confirmation:* Check query execution time against a subset or check `pg_stat_statements` to verify execution cost and buffer hits.

---

### D3. CI/CD and safety
A robust GitHub Actions pipeline ensures code quality and safe database deployments.

**Pipeline Structure:**

*   **On Pull Request:**
    *   Run linters (`flake8`, `black`, or `ruff`).
    *   Run the full pytest test suite against an ephemeral PostgreSQL service container using SQLite/Postgres.
    *   Check for breaking migration changes.
*   **On Merge to `main` (Staging / Build):**
    *   Build Docker images and push to the container registry (e.g., AWS ECR or Docker Hub).
*   **Production Deploy Gates & Migration Strategy:**
    *   *Rule of thumb:* **Never couple code deployment directly with destructive database migrations.**
    *   *Sequence:* 
        1. Run backward-compatible database migrations (`alembic upgrade head`) as an automated pre-deployment step or a separate secure job.
        2. Deploy the new container instances with the backward-compatible app code.
    *   *Rollback Story:* If a deployment fails or introduces a bug, code rollback is straightforward (deploy the previous Docker image tag). However, **database schema rollbacks are risky**. Therefore, all migrations must be written to be **backward-compatible** (e.g., adding a column in one release, dropping it in a subsequent release) so that if the app is rolled back, the previous version of the code continues to function seamlessly with the newly migrated schema.
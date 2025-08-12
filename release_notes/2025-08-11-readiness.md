# Release Readiness Report – 2025-08-11

On branch main
Your branch is up to date with 'origin/main'.

Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   docker-compose.prod.yml

no changes added to commit (use "git add" and/or "git commit -a")

OCI runtime exec failed: exec failed: unable to start container process: exec: "pytest": executable file not found in $PATH: unknown

CONTAINER ID   NAME                    CPU %     MEM USAGE / LIMIT     MEM %     NET I/O           BLOCK I/O        PIDS
8fb03381c011   thecommons2nd-web-1     0.89%     311MiB / 7.654GiB     3.97%     24.9kB / 31.9kB   61.4kB / 4.1kB   9
8dd13382dbe5   thecommons2nd-db-1      2.84%     30.81MiB / 7.654GiB   0.39%     75.8kB / 55.1kB   3.6MB / 614kB    10
e0e9b731e64d   thecommons2nd-redis-1   2.32%     9.578MiB / 7.654GiB   0.12%     17.7kB / 8.67kB   20.5kB / 0B      6

-rw-r--r--@ 1 kaarlehurtig  staff    12K Aug 11 15:51 backups/prod-20250811/database_backup.sql

                                           List of relations
 Schema |       Name       | Type  |  Owner   | Persistence | Access method |    Size    | Description 
--------+------------------+-------+----------+-------------+---------------+------------+-------------
 public | activitylog      | table | postgres | permanent   | heap          | 8192 bytes | 
 public | alembic_version  | table | postgres | permanent   | heap          | 8192 bytes | 
 public | delegation_stats | table | postgres | permanent   | heap          | 8192 bytes | 
 public | delegations      | table | postgres | permanent   | heap          | 0 bytes    | 
 public | options          | table | postgres | permanent   | heap          | 8192 bytes | 
 public | polls            | table | postgres | permanent   | heap          | 8192 bytes | 
 public | users            | table | postgres | permanent   | heap          | 8192 bytes | 
 public | votes            | table | postgres | permanent   | heap          | 8192 bytes | 
(8 rows)


=== 5. Security Review Notes ===
n

=== 6. First User Onboarding Plan ===
not relevant yet

No frontend container detected – API-only interaction

=== 8. Deployment Target ===
    ports:
Deployment Target: not yet

=== Release Readiness Checklist Complete ===

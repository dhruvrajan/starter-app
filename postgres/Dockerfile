# Pull pgvector extension files from the official image — no apt-get needed.
FROM pgvector/pgvector:pg17 AS pgvector

FROM apache/age:release_PG17_1.6.0

COPY --from=pgvector \
    /usr/lib/postgresql/17/lib/vector.so \
    /usr/lib/postgresql/17/lib/

COPY --from=pgvector \
    /usr/share/postgresql/17/extension/vector.control \
    /usr/share/postgresql/17/extension/

# vector--*.sql covers all version migration scripts
COPY --from=pgvector \
    /usr/share/postgresql/17/extension/ \
    /tmp/pgvector-ext/

RUN find /tmp/pgvector-ext -name 'vector--*.sql' \
        -exec cp {} /usr/share/postgresql/17/extension/ \; \
    && rm -rf /tmp/pgvector-ext

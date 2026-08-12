# syntax=docker/dockerfile:1

ARG UBUNTU_VERSION=24.04
ARG MONGO_LEGACY_RUNTIME_UBUNTU_VERSION=20.04

FROM ubuntu:${MONGO_LEGACY_RUNTIME_UBUNTU_VERSION} AS mongo-legacy-runtime

ARG DEBIAN_FRONTEND=noninteractive

RUN set -eux; \
    apt-get update; \
    apt-get install --yes --no-install-recommends libssl1.1; \
    install --directory /opt/mongo-legacy/lib; \
    cp -L /usr/lib/*/libcrypto.so.1.1 /usr/lib/*/libssl.so.1.1 /opt/mongo-legacy/lib/; \
    rm -rf /var/lib/apt/lists/*

FROM ubuntu:${UBUNTU_VERSION} AS vendor-assets

ARG DEBIAN_FRONTEND=noninteractive
ARG TARGETARCH
ARG MONGO_LEGACY_VERSION=4.4.31
ARG ORACLE_INSTANTCLIENT_VERSION=19.31.0.0.0dbru
ARG SQLCL_DOWNLOAD_URL=https://download.oracle.com/otn_software/java/sqldeveloper/sqlcl-latest.zip
ARG SQLCL_SHA256=""

RUN set -eux; \
    apt-get update; \
    apt-get install --yes --no-install-recommends \
        ca-certificates \
        curl \
        gnupg \
        unzip; \
    case "${TARGETARCH}" in \
        amd64) \
            mongo_legacy_arch=x86_64; \
            mongo_legacy_sha256=ebf18f73caa0633c6c280fe4f5c91dbdf8bdcef88572452708c59abd44b44462; \
            oracle_arch=x64; \
            oracle_release=1931000v2; \
            oracle_basic_cksum=1873896064; \
            oracle_basic_size=77596277; \
            oracle_sqlplus_cksum=3118300284; \
            oracle_sqlplus_size=919945; \
            oracle_tools_cksum=4025744786; \
            oracle_tools_size=1166552 \
            ;; \
        arm64) \
            mongo_legacy_arch=aarch64; \
            mongo_legacy_sha256=06ea0cb32d4547a2d2ae2ca044be0cec0ffe50f559d81ed639dfef468959feab; \
            oracle_arch=arm64; \
            oracle_release=1931000; \
            oracle_basic_cksum=399177817; \
            oracle_basic_size=75238916; \
            oracle_sqlplus_cksum=2225550773; \
            oracle_sqlplus_size=905168; \
            oracle_tools_cksum=3685519323; \
            oracle_tools_size=1303557 \
            ;; \
        *) echo "Unsupported Oracle Instant Client architecture: ${TARGETARCH}" >&2; exit 1 ;; \
    esac; \
    mongo_legacy_archive="mongodb-linux-${mongo_legacy_arch}-ubuntu2004-${MONGO_LEGACY_VERSION}"; \
    curl --fail --location --show-error --silent \
        "https://fastdl.mongodb.org/linux/${mongo_legacy_archive}.tgz" \
        --output /tmp/mongo-legacy.tgz; \
    echo "${mongo_legacy_sha256}  /tmp/mongo-legacy.tgz" | sha256sum --check --strict -; \
    install --directory /opt/mongo-legacy/bin; \
    tar --extract --gzip --file /tmp/mongo-legacy.tgz \
        --strip-components=2 \
        --directory /opt/mongo-legacy/bin \
        "${mongo_legacy_archive}/bin/mongo"; \
    chmod 0755 /opt/mongo-legacy/bin/mongo; \
    oracle_download_base="https://download.oracle.com/otn_software/linux/instantclient/${oracle_release}"; \
    curl --fail --location --show-error --silent \
        "${oracle_download_base}/instantclient-basic-linux.${oracle_arch}-${ORACLE_INSTANTCLIENT_VERSION}.zip" \
        --output /tmp/oracle-basic.zip; \
    set -- $(cksum /tmp/oracle-basic.zip); \
    test "$1" = "${oracle_basic_cksum}"; \
    test "$2" = "${oracle_basic_size}"; \
    curl --fail --location --show-error --silent \
        "${oracle_download_base}/instantclient-sqlplus-linux.${oracle_arch}-${ORACLE_INSTANTCLIENT_VERSION}.zip" \
        --output /tmp/oracle-sqlplus.zip; \
    set -- $(cksum /tmp/oracle-sqlplus.zip); \
    test "$1" = "${oracle_sqlplus_cksum}"; \
    test "$2" = "${oracle_sqlplus_size}"; \
    curl --fail --location --show-error --silent \
        "${oracle_download_base}/instantclient-tools-linux.${oracle_arch}-${ORACLE_INSTANTCLIENT_VERSION}.zip" \
        --output /tmp/oracle-tools.zip; \
    set -- $(cksum /tmp/oracle-tools.zip); \
    test "$1" = "${oracle_tools_cksum}"; \
    test "$2" = "${oracle_tools_size}"; \
    install --directory /opt/oracle; \
    unzip -qo /tmp/oracle-basic.zip -d /opt/oracle; \
    unzip -qo /tmp/oracle-sqlplus.zip -d /opt/oracle; \
    unzip -qo /tmp/oracle-tools.zip -d /opt/oracle; \
    chmod -R a+rX /opt/oracle; \
    test -x /opt/oracle/instantclient_19_31/sqlplus; \
    test -x /opt/oracle/instantclient_19_31/expdp; \
    test -x /opt/oracle/instantclient_19_31/impdp; \
    test -x /opt/oracle/instantclient_19_31/sqlldr; \
    test -e /opt/oracle/instantclient_19_31/libclntsh.so; \
    ln -s /opt/oracle/instantclient_19_31 /opt/oracle/instantclient; \
    curl --fail --location --show-error --silent \
        "${SQLCL_DOWNLOAD_URL}" \
        --output /tmp/sqlcl.zip; \
    if [ -n "${SQLCL_SHA256}" ]; then \
        echo "${SQLCL_SHA256}  /tmp/sqlcl.zip" | sha256sum --check --strict -; \
    fi; \
    unzip -q /tmp/sqlcl.zip -d /opt; \
    chmod -R a+rX /opt/sqlcl; \
    test -x /opt/sqlcl/bin/sql; \
    curl --fail --location --show-error --silent \
        https://pgp.mongodb.com/server-8.0.asc \
        --output /tmp/mongodb-server.asc; \
    gpg --batch --yes \
        --dearmor \
        --output /tmp/mongodb-server-8.0.gpg \
        /tmp/mongodb-server.asc; \
    curl --fail --location --show-error --silent \
        https://www.postgresql.org/media/keys/ACCC4CF8.asc \
        --output /tmp/postgresql.asc; \
    gpg --batch --yes \
        --dearmor \
        --output /tmp/postgresql.gpg \
        /tmp/postgresql.asc; \
    curl --fail --location --show-error --silent \
        https://packages.microsoft.com/config/ubuntu/24.04/packages-microsoft-prod.deb \
        --output /tmp/packages-microsoft-prod.deb; \
    test -s /tmp/packages-microsoft-prod.deb

COPY --from=mongo-legacy-runtime /opt/mongo-legacy/lib /opt/mongo-legacy/lib

FROM ubuntu:${UBUNTU_VERSION}

ARG DEBIAN_FRONTEND=noninteractive
ARG TARGETARCH

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8 \
    LD_LIBRARY_PATH=/opt/oracle/instantclient \
    PATH="/opt/oracle/instantclient:/opt/mssql-tools18/bin:/opt/sqlcl/bin:${PATH}"

COPY --from=vendor-assets /tmp/mongodb-server-8.0.gpg /usr/share/keyrings/mongodb-server-8.0.gpg
COPY --from=vendor-assets /tmp/postgresql.gpg /usr/share/keyrings/postgresql.gpg
COPY --from=vendor-assets /tmp/packages-microsoft-prod.deb /tmp/packages-microsoft-prod.deb

RUN set -eux; \
    apt-get update; \
    apt-get install --yes --no-install-recommends ca-certificates; \
    dpkg --install /tmp/packages-microsoft-prod.deb; \
    rm /tmp/packages-microsoft-prod.deb; \
    arch="$(dpkg --print-architecture)"; \
    case "${arch}" in \
        amd64|arm64) ;; \
        *) echo "Unsupported architecture for database client repositories: ${arch}" >&2; exit 1 ;; \
    esac; \
    echo "deb [arch=${arch} signed-by=/usr/share/keyrings/mongodb-server-8.0.gpg] https://repo.mongodb.org/apt/ubuntu noble/mongodb-org/8.0 multiverse" \
        > /etc/apt/sources.list.d/mongodb-org-8.0.list; \
    echo "deb [arch=${arch} signed-by=/usr/share/keyrings/postgresql.gpg] https://apt.postgresql.org/pub/repos/apt noble-pgdg main" \
        > /etc/apt/sources.list.d/postgresql.list; \
    apt-get update; \
    apt-get install --yes --no-install-recommends \
        bash \
        libaio1t64 \
        libcurl4 \
        libnsl2 \
        mysql-client \
        mysql-server-core-8.0 \
        mongodb-database-tools \
        mongodb-mongosh \
        openjdk-17-jre-headless \
        postgresql-client-18 \
        redis-tools; \
    ACCEPT_EULA=Y apt-get install --yes --no-install-recommends mssql-tools18; \
    if [ "${TARGETARCH}" = amd64 ]; then \
        ACCEPT_EULA=Y apt-get install --yes --no-install-recommends mssql-tools; \
    fi; \
    rm -rf /var/lib/apt/lists/*

COPY --from=vendor-assets /opt/oracle /opt/oracle
COPY --from=vendor-assets /opt/sqlcl /opt/sqlcl
COPY --from=vendor-assets /opt/mongo-legacy /opt/mongo-legacy

COPY --chmod=0755 <<'EOF' /usr/local/bin/mongo-legacy
#!/bin/sh
set -eu

export LD_LIBRARY_PATH="/opt/mongo-legacy/lib${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}"
exec /opt/mongo-legacy/bin/mongo "$@"
EOF

COPY --chmod=0755 <<'EOF' /usr/local/bin/mongo-connect
#!/bin/sh
set -eu

usage() {
    cat <<'HELP'
Usage: mongo-connect [selector] [client arguments]

Selectors (must be first):
  --server-version VERSION  Use mongo-legacy for MongoDB 3.4; mongosh otherwise.
  --legacy                  Force mongo-legacy.
  --modern                  Force mongosh.

MONGO_SERVER_VERSION can be used instead of --server-version.
HELP
}

client=modern
server_version="${MONGO_SERVER_VERSION:-}"

case "${1:-}" in
    --server-version)
        if [ "$#" -lt 2 ]; then
            echo "mongo-connect: --server-version requires a value" >&2
            exit 2
        fi
        server_version="$2"
        shift 2
        ;;
    --server-version=*)
        server_version="${1#*=}"
        shift
        ;;
    --legacy)
        client=legacy
        shift
        ;;
    --modern)
        client=modern
        server_version=""
        shift
        ;;
    --help|-h)
        usage
        exit 0
        ;;
esac

case "${server_version}" in
    3.4|3.4.*) client=legacy ;;
esac

if [ "${client}" = legacy ]; then
    exec mongo-legacy "$@"
fi

exec mongosh "$@"
EOF

RUN set -eux; \
    libaio_t64="$(find /usr/lib -name libaio.so.1t64 -print -quit)"; \
    test -n "${libaio_t64}"; \
    ln -s "${libaio_t64}" /opt/oracle/instantclient/libaio.so.1; \
    echo /opt/oracle/instantclient > /etc/ld.so.conf.d/oracle-instantclient.conf; \
    ldconfig; \
    ln -s /opt/sqlcl/bin/sql /usr/local/bin/sql; \
    if [ -x /opt/mssql-tools/bin/sqlcmd ]; then \
        ln -s /opt/mssql-tools/bin/sqlcmd /usr/local/bin/sqlcmd17; \
        ln -s /opt/mssql-tools/bin/bcp /usr/local/bin/bcp17; \
    fi; \
    usermod --login agent --home /home/agent --move-home ubuntu; \
    groupmod --new-name agent ubuntu; \
    usermod --groups '' agent; \
    install --directory --owner=agent --group=agent /workspace

USER agent
WORKDIR /workspace

RUN set -eux; \
    sql -version; \
    sqlplus -v; \
    expdp -help >/dev/null; \
    impdp -help >/dev/null; \
    sqlldr -help >/dev/null; \
    test -e /opt/oracle/instantclient/libclntsh.so; \
    psql --version; \
    mysql --version; \
    mysqlbinlog --version; \
    mongosh --version; \
    mongodump --version; \
    mongorestore --version; \
    mongoexport --version; \
    mongo-legacy --version; \
    mongo-connect --server-version 3.4 --version; \
    mongo-connect --modern --version; \
    redis-cli --version; \
    sqlcmd -? >/dev/null; \
    bcp -v; \
    if command -v sqlcmd17 >/dev/null; then \
        sqlcmd17 -? >/dev/null; \
        bcp17 -v; \
    fi

CMD ["bash"]

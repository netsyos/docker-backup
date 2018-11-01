FROM alpine:3.4
RUN apk add --update bash openssh-client wget curl lftp gzip postgresql-client mysql-client && rm -rf /var/cache/apk/*
COPY mysql_dump.sh /
COPY mysql_import.sh /
ENTRYPOINT ["/mysql_dump.sh"]
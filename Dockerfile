FROM alpine:latest
RUN apk add --update bash openssh-client wget curl lftp gzip postgresql-client mysql-client && rm -rf /var/cache/apk/*
ADD scripts /scripts
RUN chmod +x /scripts/*
ENTRYPOINT ["/scripts/mysql_dump.sh"]
FROM alpine:latest
RUN apk add --update coreutils bash openssh-client wget curl lftp gzip postgresql-client mysql-client python
RUN rm -rf /var/cache/apk/*
RUN pip
ADD scripts /scripts
RUN chmod +x /scripts/*
ENTRYPOINT ["tail", "-f" ,"/dev/null"]
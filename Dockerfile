FROM alpine:latest
RUN apk add --update coreutils bash openssh-client wget curl lftp gzip postgresql-client mysql-client python3 py-pip
RUN rm -rf /var/cache/apk/*
RUN pip install --upgrade google-api-python-client oauth2client
RUN pip install --upgrade google-auth google-auth-oauthlib google-auth-httplib2
RUN pip install --upgrade flask request pip slackclient
ADD scripts /scripts
RUN chmod +x /scripts/*
ENTRYPOINT ["tail", "-f" ,"/dev/null"]
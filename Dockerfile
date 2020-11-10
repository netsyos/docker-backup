FROM alpine:latest
RUN apk update \
    && apk add --no-cache gcc git python3-dev musl-dev linux-headers \
    libc-dev  rsync zsh \
    findutils wget util-linux grep libxml2-dev libxslt-dev \
    bzip2 tar coreutils bash openssh-client wget curl lftp gzip postgresql-client mysql-client python3 py-pip

RUN rm -rf /var/cache/apk/*
RUN pip3 install --upgrade pip 
RUN pip3 install --upgrade google-api-python-client oauth2client
RUN pip3 install --upgrade google-auth google-auth-oauthlib google-auth-httplib2
RUN pip3 install --upgrade flask 
RUN pip3 install --upgrade requests
RUN pip3 install --upgrade slackclient 
ADD scripts /scripts
RUN chmod +x /scripts/*
ADD entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
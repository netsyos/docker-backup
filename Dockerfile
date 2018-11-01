FROM alpine:3.4
RUN apk add --update mysql-client bash openssh-client && rm -rf /var/cache/apk/*
COPY dump.sh /
COPY import.sh /
ENTRYPOINT ["/dump.sh"]

# Use baseimage-docker's init system.
CMD ["/sbin/my_init"]

# ...put your own build instructions here...
RUN apt-get update

RUN apt-get -y install sudo acl strace dialog net-tools lynx nano vim wget curl htop unzip

ADD init/00_init.sh /etc/my_init.d/00_init.sh
RUN chmod +x /etc/my_init.d/00_init.sh

# Clean up APT when done.
#RUN apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

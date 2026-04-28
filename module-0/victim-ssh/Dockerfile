FROM debian:12-slim

RUN apt update && apt install -y openssh-server sudo && \
    mkdir /var/run/sshd && \
    useradd -m -s /bin/bash alice && echo "alice:summer2025" | chpasswd && \
    useradd -m -s /bin/bash bob && echo "bob:P@ssw0rd!" | chpasswd && \
    useradd -m -s /bin/bash carol && echo "carol:carolina123" | chpasswd && \
    echo "root:toor" | chpasswd && \
    sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/' /etc/ssh/sshd_config && \
    echo 'flag{m0dulo_zer0_ssh_brute_was_easy}' > /home/alice/.flag && \
    chown alice:alice /home/alice/.flag && chmod 600 /home/alice/.flag

EXPOSE 22
CMD ["/usr/sbin/sshd", "-D"]

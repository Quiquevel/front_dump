FROM registry.global.ccc.srvb.bo.paas.cloudcenter.corp/shuttle-san/python:3.11.1
# Create app directory as working directory
WORKDIR /app

ENV TZ=Europe/Madrid

RUN set -x && \
    export GIT_SSL_NO_VERIFY="true" && \
    export http_proxy=http://proxyapp.cloudcenter.corp:8080 && \
    export https_proxy=http://proxyapp.cloudcenter.corp:8080 && \
    export no_proxy=.cloudcenter.corp && \
    apt-get update && \
    apt-get install -y python3-dev build-essential && \
    rm -rf /var/lib/apt/lists/* && \
    groupadd -g 1000060000 userpython && \
    useradd -u 1000 -g userpython -d /home/userpython -s /bin/bash userpython && \
    mkdir -p /home/userpython && \
    chown -R userpython:userpython /app && \
    chown -R userpython:userpython /home/userpython

COPY requirements.txt /

RUN export GIT_SSL_NO_VERIFY="true" && \
    export http_proxy=http://proxyapp.cloudcenter.corp:8080 && \
    export https_proxy=http://proxyapp.cloudcenter.corp:8080 && \
    export no_proxy=.cloudcenter.corp && \
    pip install --proxy ${https_proxy} --no-cache-dir --trusted-host files.pythonhosted.org \
    --trusted-host pypi.org --trusted-host pypi.python.org --trusted-host github.alm.europe.cloudcenter.corp \
    -r /requirements.txt && \
    apt-get update && \
    apt-get install -y curl && \
    apt-get install -y rsync && \
    rm -rf /var/lib/apt/lists/* && \
    curl -LO https://mirror.openshift.com/pub/openshift-v4/clients/oc/latest/linux/oc.tar.gz && \
    tar -xf oc.tar.gz -C /usr/local/bin && \
    rm oc.tar.gz

# Copy code from root repo to the working directory
COPY /app/ /app/

# Switch to non-root user
USER userpython

#Giving executable permission
USER 1000
EXPOSE 8080
ENTRYPOINT ["streamlit", "run"]
CMD ["main.py", "--server.port", "8080", "--server.baseUrlPath", "shuttledump","--theme.backgroundColor","#eff6f9"]
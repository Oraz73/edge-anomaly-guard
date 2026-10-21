# Jenkins server for EdgeGuard: Jenkins LTS + Docker CLI + plugins + configuration as code.
FROM jenkins/jenkins:lts-jdk21

USER root
# Docker CLI (the Docker engine itself runs on the host; we use its socket).
RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates curl gnupg \
    && install -m 0755 -d /etc/apt/keyrings \
    && curl -fsSL https://download.docker.com/linux/debian/gpg -o /etc/apt/keyrings/docker.asc \
    && chmod a+r /etc/apt/keyrings/docker.asc \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/debian $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
       > /etc/apt/sources.list.d/docker.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends docker-ce-cli docker-buildx-plugin \
    && rm -rf /var/lib/apt/lists/*

USER jenkins
COPY --chown=jenkins:jenkins plugins.txt /usr/share/jenkins/ref/plugins.txt
RUN jenkins-plugin-cli --plugin-file /usr/share/jenkins/ref/plugins.txt

# Jenkins Configuration as Code: admin user and the "edgeguard" pipeline job.
COPY --chown=jenkins:jenkins casc.yaml /var/jenkins_conf/jenkins.yaml
ENV CASC_JENKINS_CONFIG=/var/jenkins_conf/jenkins.yaml \
    JAVA_OPTS="-Djenkins.install.runSetupWizard=false"

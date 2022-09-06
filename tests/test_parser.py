import pytest

from src.dokter.parser import DockerfileParser


@pytest.mark.parametrize(
    "raw,image,alias,version",
    [
        ("FROM python3.8", "python3.8", None, None),
        ("FROM python3.8 AS build", "python3.8", "build", None),
        ("FROM python:3.8.9", "python", None, "3.8.9"),
        ("FROM ruby:latest", "ruby", None, "latest"),
        ("FROM ruby:latest as build", "ruby", "build", "latest"),
    ]
)
def test_froms(raw, image, alias, version):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.froms) == 1
    from_details = dfp.froms[0]["instruction_details"]
    assert from_details["image"] == image
    assert from_details.get("version") == version
    assert from_details.get("alias") == alias


@pytest.mark.parametrize(
    "raw,comment",
    [
        ("#This is a comment", "This is a comment"),
        ("# This is also a comment", "This is also a comment")
    ]
)
def test_comments(raw, comment):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.comments) == 1
    assert dfp.comments[0]["instruction"] == "COMMENT"
    assert dfp.comments[0]["instruction_details"].get("comment") == comment


@pytest.mark.parametrize(
    "raw,user,group",
    [
        ("USER root", "root", None),
        ("USER 1000:1234", "1000", "1234")
    ]
)
def test_users(raw, user, group):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.users) == 1
    assert dfp.users[0]["instruction"] == "USER"
    assert dfp.users[0]["instruction_details"].get("user") == user
    assert dfp.users[0]["instruction_details"].get("group") == group


@pytest.mark.parametrize(
    "raw,chown,source,parsed_source_files,target",
    [
        ("COPY . .", None, ["."], ["./__init__.py", "./integration", "./integration/test_dokter.py", "./test_analyzer.py", "./test_parser.py"], "."),
        ("COPY --chown=me:me . /app", "me:me", ["."], ["./__init__.py", "./integration", "./integration/test_dokter.py", "./test_analyzer.py", "./test_parser.py"], "/app"),
        ("COPY ../requirements.txt .", None, ["../requirements.txt"], ["../requirements.txt"], "."),
        ("COPY ../requirements.txt ../README.md .", None, ["../requirements.txt", "../README.md"], ["../README.md", "../requirements.txt", ], "."),
        ("COPY --chown=me:me ../requirements.txt ../README.md .", "me:me", ["../requirements.txt", "../README.md"], ["../README.md", "../requirements.txt", ], "."),
        ("COPY --chown=1000:1234 ../tests /app/app", "1000:1234", ["../tests"], ["../tests/__init__.py", "../tests/integration", "../tests/integration/test_dokter.py", "../tests/test_analyzer.py", "../tests/test_parser.py"], "/app/app"),
        ("COPY ../src/dokter .", None, ["../src/dokter"], ["../src/dokter/__init__.py", "../src/dokter/analyzer.py", "../src/dokter/main.py", "../src/dokter/parser.py", "../src/dokter/shellcheck.py"], "."),
    ]
)
def test_copies(raw, chown, source, parsed_source_files, target):
    dfp = DockerfileParser(raw_text=raw, dockerignore="../.dockerignore")
    assert len(dfp.copies) == 1
    assert dfp.copies[0]["instruction"] == "COPY"
    assert dfp.copies[0]["instruction_details"].get("chown") == chown
    assert dfp.copies[0]["instruction_details"].get("source") == source
    assert dfp.copies[0]["instruction_details"].get("parsed_source_files") == parsed_source_files
    assert dfp.copies[0]["instruction_details"].get("target") == target


@pytest.mark.parametrize(
    "raw,chown,source,parsed_source_files,target",
    [
        ("ADD . .", None, ["."], ["./__init__.py", "./integration", "./integration/test_dokter.py", "./test_analyzer.py", "./test_parser.py"], "."),
        ("ADD --chown=me:me . /app", "me:me", ["."], ["./__init__.py", "./integration", "./integration/test_dokter.py", "./test_analyzer.py", "./test_parser.py"],
         "/app"),
        ("ADD ../requirements.txt .", None, ["../requirements.txt"], ["../requirements.txt"], "."),
        ("ADD --chown=1000:1234 ../tests /app/app", "1000:1234", ["../tests"],
         ["../tests/__init__.py", "../tests/integration", "../tests/integration/test_dokter.py", "../tests/test_analyzer.py", "../tests/test_parser.py"], "/app/app"),
        ("ADD ../src/dokter .", None, ["../src/dokter"],
         ["../src/dokter/__init__.py", "../src/dokter/analyzer.py", "../src/dokter/main.py", "../src/dokter/parser.py", "../src/dokter/shellcheck.py"],
         "."),
        ("ADD http://ipv4.download.thinkbroadband.com/5MB.zip /small_file.mp3", None, ["http://ipv4.download.thinkbroadband.com/5MB.zip"], [], "/small_file.mp3")
    ]
)
def test_adds(raw, chown, source, parsed_source_files, target):
    dfp = DockerfileParser(raw_text=raw, dockerignore="../.dockerignore")
    assert len(dfp.adds) == 1
    assert dfp.adds[0]["instruction"] == "ADD"
    assert dfp.adds[0]["instruction_details"].get("chown") == chown
    assert dfp.adds[0]["instruction_details"].get("source") == source
    assert dfp.adds[0]["instruction_details"].get("parsed_source_files") == parsed_source_files
    assert dfp.adds[0]["instruction_details"].get("target") == target


def test_instructions():
    dfp = DockerfileParser(dockerfile="../fixtures/Dockerfile")
    assert len(dfp.instructions) == 27
    instructions = ['FROM', 'ARG', 'ARG', 'ENV', 'LABEL', 'LABEL', 'LABEL', 'COPY', 'COPY', 'COPY', 'ENV', 'ENV',
                    'COMMENT', 'RUN', 'RUN', 'SHELL', 'EXPOSE', 'EXPOSE', 'ADD', 'USER', 'WORKDIR', 'ENTRYPOINT',
                    'ONBUILD', 'HEALTHCHECK', 'STOPSIGNAL', 'STOPSIGNAL', 'CMD']
    assert dfp.instructions == instructions


@pytest.mark.parametrize(
    "raw,argument,default_value",
    [
        ("ARG version", "version", None),
        ("ARG api_key=secret", "api_key", "secret")
    ]
)
def test_args(raw, argument, default_value):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.args) == 1
    assert dfp.args[0]["instruction"] == "ARG"
    assert dfp.args[0]["instruction_details"].get("argument") == argument
    assert dfp.args[0]["instruction_details"].get("default_value") == default_value


@pytest.mark.parametrize(
    "raw,envs,environment_variables",
    [
        ("ENV VERSION=$version", 1, [("VERSION", "$version")]),
        ("ENV DEBIAN_FRONTEND=noninteractive", 1, [("DEBIAN_FRONTEND", "noninteractive")]),
        ("ENV VERSION=$version DEBIAN_FRONTEND=noninteractive", 2, [("VERSION", "$version"), ("DEBIAN_FRONTEND", "noninteractive")])
    ]
)
def test_envs(raw, envs, environment_variables):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.envs) == 1
    for i in range(envs):
        assert dfp.envs[0]["instruction"] == "ENV"
        assert dfp.envs[0]["instruction_details"][i].get("env") == environment_variables[i][0]
        assert dfp.envs[0]["instruction_details"][i].get("default_value") == environment_variables[i][1]


@pytest.mark.parametrize(
    "raw,labels",
    [
        ("LABEL maintainer='me'", [("maintainer", "me")]),
        ('LABEL maintainer="me"', [("maintainer", "me")]),
        ('LABEL maintainer=me', [("maintainer", "me")]),
        ("LABEL maintainer='me' version='0.1.1'", [("maintainer", 'me'), ('version', '0.1.1')])
    ]
)
def test_labels(raw, labels):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.labels) == 1
    for i in range(len(labels)):
        assert dfp.labels[0]["instruction"] == "LABEL"
        assert dfp.labels[0]["instruction_details"][i].get("label") == labels[i][0]
        assert dfp.labels[0]["instruction_details"][i].get("default_value") == labels[i][1]


@pytest.mark.parametrize(
    "raw,executable,arguments,docker_syntax",
    [
        ("RUN apt-get install curl && git", "apt-get", "install curl && git", None),
        ("""RUN apt-get \\
                install curl && \\
                git""", "apt-get", "\\install curl && \\git", None),
        ("RUN --mount=type=cache,target=/cache npx encore production", "npx", "encore production",
         "--mount=type=cache,target=/cache"),
        ("RUN --security=insecure cat /proc/self/status | grep CapEff", "cat", "/proc/self/status | grep CapEff",
         "--security=insecure"),
        ("RUN --network=none pip install --find-links wheels mypackage", "pip", "install --find-links wheels mypackage",
         "--network=none")
    ]
)
def test_runs(raw, executable, arguments, docker_syntax):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.runs) == 1
    assert dfp.runs[0]["instruction"] == "RUN"
    assert dfp.runs[0]["instruction_details"].get("executable") == executable
    assert dfp.runs[0]["instruction_details"].get("arguments") == arguments
    assert dfp.runs[0]["instruction_details"].get("docker_syntax") == docker_syntax


@pytest.mark.parametrize(
    "raw,executable,arguments",
    [
        ("ENTRYPOINT ['python', 'main.py', '--all']", "python", ['main.py', '--all']),
        ("ENTRYPOINT ['python']", "python", []),
        ("ENTRYPOINT []", None, []),
        ("ENTRYPOINT python", "python", []),
        ("ENTRYPOINT --network=none python", "python", [])
    ]
)
def test_entrypoints(raw, executable, arguments):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.entrypoints) == 1
    assert dfp.entrypoints[0]["instruction"] == "ENTRYPOINT"
    assert dfp.entrypoints[0]["instruction_details"].get("executable") == executable
    assert dfp.entrypoints[0]["instruction_details"].get("arguments") == arguments


@pytest.mark.parametrize(
    "raw,executable,arguments",
    [
        ("SHELL ['powershell', '-command']", "powershell", ['-command']),
        ("SHELL powershell", "powershell", [])
    ]
)
def test_shells(raw, executable, arguments):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.shells) == 1
    assert dfp.shells[0]["instruction"] == "SHELL"
    assert dfp.shells[0]["instruction_details"].get("executable") == executable
    assert dfp.shells[0]["instruction_details"].get("arguments") == arguments


@pytest.mark.parametrize(
    "raw,port,protocol",
    [
        ("EXPOSE 8000", "8000", None),
        ("EXPOSE 8001/tdp", "8001", "tdp")
    ]
)
def test_exposes(raw, port, protocol):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.exposes) == 1
    assert dfp.exposes[0]["instruction"] == "EXPOSE"
    assert dfp.exposes[0]["instruction_details"].get("port") == port
    assert dfp.exposes[0]["instruction_details"].get("protocol") == protocol


@pytest.mark.parametrize(
    "raw,workdir",
    [
        ("WORKDIR /app", "/app"),
        ("WORKDIR app", "app"),
        ("WORKDIR /app/src", "/app/src")
    ]
)
def test_workdirs(raw, workdir):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.workdirs) == 1
    assert dfp.workdirs[0]["instruction_details"].get("workdir") == workdir


@pytest.mark.parametrize(
    "raw,stopsignal",
    [
        ("STOPSIGNAL 1337", '1337'),
        ("STOPSIGNAL '1338'", "'1338'"),
        ("STOPSIGNAL whoops", "whoops")
    ]
)
def test_stopsignals(raw, stopsignal):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.stopsignals) == 1
    assert dfp.stopsignals[0]["instruction_details"].get("stopsignal") == stopsignal


@pytest.mark.parametrize(
    "raw,volume",
    [
        ("VOLUME /myvol", "/myvol"),
        ("VOLUME /myvol /secondvol", "/myvol /secondvol"),
        ("VOLUME ['/myvol']", "['/myvol']"),
    ]
)
def test_volumes(raw, volume):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.volumes) == 1
    assert dfp.volumes[0]["instruction_details"].get("volume") == volume


@pytest.mark.parametrize(
    "raw,sub_instruction,executable,arguments,options",
    [
        ("HEALTHCHECK CMD cat --force /tmp.txt", "CMD", "cat", "--force /tmp.txt", {}),
        ("HEALTHCHECK ['CMD', 'cat', '/tmp.txt']", "CMD", 'cat', ['/tmp.txt'], {}),
        ("HEALTHCHECK NONE", "NONE", None, [], {}),
        ("HEALTHCHECK --interval=30s ['CMD', 'cat', '--force', '/tmp.txt']", "CMD", 'cat', ['--force', '/tmp.txt'], {"interval": "30s"}),
        ("HEALTHCHECK --interval=30s --start-period=1m ['CMD', 'cat', '/tmp.txt']", "CMD", 'cat', ['/tmp.txt'],
         {"interval": "30s", "start-period": "1m"}),
        ("HEALTHCHECK --interval=30s --start-period=1m CMD cat /tmp.txt", "CMD", 'cat', '/tmp.txt',
         {"interval": "30s", "start-period": "1m"})
    ]
)
def test_healthchecks(raw, sub_instruction, executable, arguments, options):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.healthchecks) == 1
    assert dfp.healthchecks[0]["instruction_details"].get("sub_instruction") == sub_instruction
    assert dfp.healthchecks[0]["instruction_details"].get("executable") == executable
    assert dfp.healthchecks[0]["instruction_details"].get("arguments") == arguments
    assert dfp.healthchecks[0]["instruction_details"].get("options") == options


@pytest.mark.parametrize(
    "raw,sub_instruction,executable,arguments",
    [
        ("ONBUILD RUN /usr/local/bin/python-build --dir /app/src", "RUN", "/usr/local/bin/python-build",
         "--dir /app/src"),
        ("ONBUILD ['RUN', '/usr/local/bin/python-build', '--dir', '/app/src']", "RUN", '/usr/local/bin/python-build',
         ['--dir', '/app/src'])
    ]
)
def test_onbuilds(raw, sub_instruction, executable, arguments):
    dfp = DockerfileParser(raw_text=raw)
    assert len(dfp.onbuilds) == 1
    assert dfp.onbuilds[0]["instruction_details"].get("sub_instruction") == sub_instruction
    assert dfp.onbuilds[0]["instruction_details"].get("executable") == executable
    assert dfp.onbuilds[0]["instruction_details"].get("arguments") == arguments


@pytest.mark.parametrize(
    "dockerfile,expected",
    [
        ("../fixtures/ansible.Dockerfile", [{'line_number': {'start': 1, 'end': 1}, 'instruction': 'COMMENT', 'instruction_details': {'comment': '+++++++++++++++++++++++++++++++++++++++'}, '_raw': 'COMMENT +++++++++++++++++++++++++++++++++++++++', 'formatted': '#+++++++++++++++++++++++++++++++++++++++\n'}, {'line_number': {'start': 2, 'end': 2}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'Dockerfile for webdevops/ansible:ubuntu-16.04'}, '_raw': 'COMMENT  Dockerfile for webdevops/ansible:ubuntu-16.04', 'formatted': '# Dockerfile for webdevops/ansible:ubuntu-16.04\n'}, {'line_number': {'start': 3, 'end': 3}, 'instruction': 'COMMENT', 'instruction_details': {'comment': '-- automatically generated  --'}, '_raw': 'COMMENT     -- automatically generated  --', 'formatted': '#    -- automatically generated  --\n'}, {'line_number': {'start': 4, 'end': 4}, 'instruction': 'COMMENT', 'instruction_details': {'comment': '+++++++++++++++++++++++++++++++++++++++'}, '_raw': 'COMMENT +++++++++++++++++++++++++++++++++++++++', 'formatted': '#+++++++++++++++++++++++++++++++++++++++\n'}, {'line_number': {'start': 6, 'end': 6}, 'instruction': 'FROM', 'instruction_details': {'image': 'webdevops/bootstrap', 'version': 'ubuntu-16.04'}, '_raw': 'FROM webdevops/bootstrap:ubuntu-16.04', 'formatted': 'FROM webdevops/bootstrap:ubuntu-16.04\n'}, {'line_number': {'start': 8, 'end': 32}, 'instruction': 'RUN', 'instruction_details': {'executable': 'set', 'arguments': '-x \\&& apt-install \\python-minimal \\python-setuptools \\python-pip \\python-paramiko \\python-jinja2 \\python-dev \\libffi-dev \\libssl-dev \\build-essential \\openssh-client \\&& pip install --upgrade pip \\&& hash -r \\&& pip install --no-cache-dir ansible \\&& chmod 750 /usr/local/bin/ansible* \\&& apt-get purge -y -f --force-yes \\python-dev \\build-essential \\libssl-dev \\libffi-dev \\&& docker-run-bootstrap \\&& docker-image-cleanup'}, '_raw': 'RUN set -x \\&& apt-install \\python-minimal \\python-setuptools \\python-pip \\python-paramiko \\python-jinja2 \\python-dev \\libffi-dev \\libssl-dev \\build-essential \\openssh-client \\&& pip install --upgrade pip \\&& hash -r \\&& pip install --no-cache-dir ansible \\&& chmod 750 /usr/local/bin/ansible* \\&& apt-get purge -y -f --force-yes \\python-dev \\build-essential \\libssl-dev \\libffi-dev \\&& docker-run-bootstrap \\&& docker-image-cleanup', 'formatted': 'RUN set -x \\\n\t&& apt-install \\\n\tpython-minimal \\\n\tpython-setuptools \\\n\tpython-pip \\\n\tpython-paramiko \\\n\tpython-jinja2 \\\n\tpython-dev \\\n\tlibffi-dev \\\n\tlibssl-dev \\\n\tbuild-essential \\\n\topenssh-client \\\n\t&& pip install --upgrade pip \\\n\t&& hash -r \\\n\t&& pip install --no-cache-dir ansible \\\n\t&& chmod 750 /usr/local/bin/ansible* \\\n\t&& apt-get purge -y -f --force-yes \\\n\tpython-dev \\\n\tbuild-essential \\\n\tlibssl-dev \\\n\tlibffi-dev \\\n\t&& docker-run-bootstrap \\\n\t&& docker-image-cleanup\n'}]),
        ("../fixtures/kafka.Dockerfile", [{'line_number': {'start': 1, 'end': 1}, 'instruction': 'FROM', 'instruction_details': {'image': 'openjdk', 'version': '11-jre-slim'}, '_raw': 'FROM openjdk:11-jre-slim', 'formatted': 'FROM openjdk:11-jre-slim\n'}, {'line_number': {'start': 3, 'end': 3}, 'instruction': 'ARG', 'instruction_details': {'argument': 'kafka_version', 'default_value': '2.8.1'}, '_raw': 'ARG kafka_version=2.8.1', 'formatted': 'ARG kafka_version=2.8.1\n'}, {'line_number': {'start': 4, 'end': 4}, 'instruction': 'ARG', 'instruction_details': {'argument': 'scala_version', 'default_value': '2.13'}, '_raw': 'ARG scala_version=2.13', 'formatted': 'ARG scala_version=2.13\n'}, {'line_number': {'start': 5, 'end': 5}, 'instruction': 'ARG', 'instruction_details': {'argument': 'vcs_ref', 'default_value': 'unspecified'}, '_raw': 'ARG vcs_ref=unspecified', 'formatted': 'ARG vcs_ref=unspecified\n'}, {'line_number': {'start': 6, 'end': 6}, 'instruction': 'ARG', 'instruction_details': {'argument': 'build_date', 'default_value': 'unspecified'}, '_raw': 'ARG build_date=unspecified', 'formatted': 'ARG build_date=unspecified\n'}, {'line_number': {'start': 8, 'end': 15}, 'instruction': 'LABEL', 'instruction_details': [{'label': 'org.label-schema.name', 'default_value': 'kafka'}, {'label': '\\org.label-schema.description', 'default_value': 'Apache'}, {'label': 'Kafka"'}, {'label': '\\org.label-schema.build-date', 'default_value': '${build_date}'}, {'label': '\\org.label-schema.vcs-url', 'default_value': 'https://github.com/wurstmeister/kafka-docker'}, {'label': '\\org.label-schema.vcs-ref', 'default_value': '${vcs_ref}'}, {'label': '\\org.label-schema.version', 'default_value': '${scala_version}_${kafka_version}'}, {'label': '\\org.label-schema.schema-version', 'default_value': '1.0'}, {'label': '\\maintainer', 'default_value': 'wurstmeister'}], '_raw': 'LABEL org.label-schema.name="kafka" \\org.label-schema.description="Apache Kafka" \\org.label-schema.build-date="${build_date}" \\org.label-schema.vcs-url="https://github.com/wurstmeister/kafka-docker" \\org.label-schema.vcs-ref="${vcs_ref}" \\org.label-schema.version="${scala_version}_${kafka_version}" \\org.label-schema.schema-version="1.0" \\maintainer="wurstmeister"', 'formatted': 'LABEL org.label-schema.name="kafka" \\\n\torg.label-schema.description="Apache Kafka" \\\n\torg.label-schema.build-date="${build_date}" \\\n\torg.label-schema.vcs-url="https://github.com/wurstmeister/kafka-docker" \\\n\torg.label-schema.vcs-ref="${vcs_ref}" \\\n\torg.label-schema.version="${scala_version}_${kafka_version}" \\\n\torg.label-schema.schema-version="1.0" \\\n\tmaintainer="wurstmeister"\n'}, {'line_number': {'start': 17, 'end': 19}, 'instruction': 'ENV', 'instruction_details': [{'env': 'KAFKA_VERSION', 'default_value': '$kafka_version'}, {'env': '\\SCALA_VERSION', 'default_value': '$scala_version'}, {'env': '\\KAFKA_HOME', 'default_value': '/opt/kafka'}], '_raw': 'ENV KAFKA_VERSION=$kafka_version \\SCALA_VERSION=$scala_version \\KAFKA_HOME=/opt/kafka', 'formatted': 'ENV KAFKA_VERSION=$kafka_version \\\n\tSCALA_VERSION=$scala_version \\\n\tKAFKA_HOME=/opt/kafka\n'}, {'line_number': {'start': 21, 'end': 21}, 'instruction': 'ENV', 'instruction_details': [{'env': 'PATH', 'default_value': '${PATH}:${KAFKA_HOME}/bin'}], '_raw': 'ENV PATH=${PATH}:${KAFKA_HOME}/bin', 'formatted': 'ENV PATH=${PATH}:${KAFKA_HOME}/bin\n'}, {'line_number': {'start': 23, 'end': 23}, 'instruction': 'COPY', 'instruction_details': {'source': ['download-kafka.sh', 'start-kafka.sh', 'broker-list.sh', 'create-topics.sh', 'versions.sh'], 'parsed_source_files': [], 'target': '/tmp2/'}, '_raw': 'COPY download-kafka.sh start-kafka.sh broker-list.sh create-topics.sh versions.sh /tmp2/', 'formatted': 'COPY download-kafka.sh start-kafka.sh broker-list.sh create-topics.sh versions.sh /tmp2/\n'}, {'line_number': {'start': 25, 'end': 53}, 'instruction': 'RUN', 'instruction_details': {'executable': 'set', 'arguments': '-eux ; \\apt-get update ; \\apt-get upgrade -s ; \\apt-get install -y --no-install-recommends jq net-tools curl wget ; \\apt-get install -y --no-install-recommends gnupg lsb-release ; \\curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg ; \\echo \\"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \\$(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null ; \\apt-get update ; \\apt-get install -y --no-install-recommends docker-ce-cli ; \\apt remove -y gnupg lsb-release ; \\apt clean ; \\apt autoremove -y ; \\apt -f install ; \\apt-get install -y --no-install-recommends netcat ; \\chmod a+x /tmp2/*.sh ; \\mv /tmp2/start-kafka.sh /tmp2/broker-list.sh /tmp2/create-topics.sh /tmp2/versions.sh /usr/bin ; \\sync ; \\/tmp2/download-kafka.sh ; \\tar xfz /tmp2/kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz -C /opt ; \\rm /tmp2/kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz ; \\ln -s /opt/kafka_${SCALA_VERSION}-${KAFKA_VERSION} ${KAFKA_HOME} ; \\rm -rf /tmp2 ; \\rm -rf /var/lib/apt/lists/*'}, '_raw': 'RUN set -eux ; \\apt-get update ; \\apt-get upgrade -s ; \\apt-get install -y --no-install-recommends jq net-tools curl wget ; \\apt-get install -y --no-install-recommends gnupg lsb-release ; \\curl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg ; \\echo \\"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \\$(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null ; \\apt-get update ; \\apt-get install -y --no-install-recommends docker-ce-cli ; \\apt remove -y gnupg lsb-release ; \\apt clean ; \\apt autoremove -y ; \\apt -f install ; \\apt-get install -y --no-install-recommends netcat ; \\chmod a+x /tmp2/*.sh ; \\mv /tmp2/start-kafka.sh /tmp2/broker-list.sh /tmp2/create-topics.sh /tmp2/versions.sh /usr/bin ; \\sync ; \\/tmp2/download-kafka.sh ; \\tar xfz /tmp2/kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz -C /opt ; \\rm /tmp2/kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz ; \\ln -s /opt/kafka_${SCALA_VERSION}-${KAFKA_VERSION} ${KAFKA_HOME} ; \\rm -rf /tmp2 ; \\rm -rf /var/lib/apt/lists/*', 'formatted': 'RUN set -eux ; \\\n\tapt-get update ; \\\n\tapt-get upgrade -s ; \\\n\tapt-get install -y --no-install-recommends jq net-tools curl wget ; \\\n\tapt-get install -y --no-install-recommends gnupg lsb-release ; \\\n\tcurl -fsSL https://download.docker.com/linux/debian/gpg | gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg ; \\\n\techo \\\n\t"deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/debian \\\n\t$(lsb_release -cs) stable" | tee /etc/apt/sources.list.d/docker.list > /dev/null ; \\\n\tapt-get update ; \\\n\tapt-get install -y --no-install-recommends docker-ce-cli ; \\\n\tapt remove -y gnupg lsb-release ; \\\n\tapt clean ; \\\n\tapt autoremove -y ; \\\n\tapt -f install ; \\\n\tapt-get install -y --no-install-recommends netcat ; \\\n\tchmod a+x /tmp2/*.sh ; \\\n\tmv /tmp2/start-kafka.sh /tmp2/broker-list.sh /tmp2/create-topics.sh /tmp2/versions.sh /usr/bin ; \\\n\tsync ; \\\n\t/tmp2/download-kafka.sh ; \\\n\ttar xfz /tmp2/kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz -C /opt ; \\\n\trm /tmp2/kafka_${SCALA_VERSION}-${KAFKA_VERSION}.tgz ; \\\n\tln -s /opt/kafka_${SCALA_VERSION}-${KAFKA_VERSION} ${KAFKA_HOME} ; \\\n\trm -rf /tmp2 ; \\\n\trm -rf /var/lib/apt/lists/*\n'}, {'line_number': {'start': 55, 'end': 55}, 'instruction': 'COPY', 'instruction_details': {'source': ['overrides'], 'parsed_source_files': [], 'target': '/opt/overrides'}, '_raw': 'COPY overrides /opt/overrides', 'formatted': 'COPY overrides /opt/overrides\n'}, {'line_number': {'start': 57, 'end': 57}, 'instruction': 'VOLUME', 'instruction_details': {'volume': '["/kafka"]'}, '_raw': 'VOLUME ["/kafka"]', 'formatted': 'VOLUME ["/kafka"]\n'}, {'line_number': {'start': 59, 'end': 59}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'Use "exec" form so that it runs as PID 1 (useful for graceful shutdown)'}, '_raw': 'COMMENT  Use "exec" form so that it runs as PID 1 (useful for graceful shutdown)', 'formatted': '# Use "exec" form so that it runs as PID 1 (useful for graceful shutdown)\n'}, {'line_number': {'start': 60, 'end': 60}, 'instruction': 'CMD', 'instruction_details': {'executable': 'start-kafka.sh', 'arguments': []}, '_raw': 'CMD ["start-kafka.sh"]', 'formatted': 'CMD ["start-kafka.sh"]\n'}]),
        ("../fixtures/mailgun.Dockerfile", [{'line_number': {'start': 1, 'end': 1}, 'instruction': 'FROM', 'instruction_details': {'image': 'r.j3ss.co/curl'}, '_raw': 'FROM r.j3ss.co/curl', 'formatted': 'FROM r.j3ss.co/curl\n'}, {'line_number': {'start': 2, 'end': 2}, 'instruction': 'LABEL', 'instruction_details': [{'label': 'maintainer', 'default_value': 'Jessie Frazelle <jess@linux.com>'}], '_raw': 'LABEL maintainer "Jessie Frazelle <jess@linux.com>"', 'formatted': 'LABEL maintainer "Jessie Frazelle <jess@linux.com>"\n'}, {'line_number': {'start': 4, 'end': 5}, 'instruction': 'RUN', 'instruction_details': {'executable': 'apk', 'arguments': 'add --no-cache \\bash'}, '_raw': 'RUN apk add --no-cache \\bash', 'formatted': 'RUN apk add --no-cache \\\n\tbash\n'}, {'line_number': {'start': 7, 'end': 7}, 'instruction': 'COPY', 'instruction_details': {'source': ['sendemail'], 'parsed_source_files': [], 'target': '/usr/bin/sendemail'}, '_raw': 'COPY sendemail /usr/bin/sendemail', 'formatted': 'COPY sendemail /usr/bin/sendemail\n'}, {'line_number': {'start': 9, 'end': 9}, 'instruction': 'ENTRYPOINT', 'instruction_details': {'executable': 'sendemail', 'arguments': []}, '_raw': 'ENTRYPOINT [ "sendemail" ]', 'formatted': 'ENTRYPOINT [ "sendemail" ]\n'}]),
        ("../fixtures/nginx.Dockerfile", [{'line_number': {'start': 1, 'end': 1}, 'instruction': 'COMMENT', 'instruction_details': {'comment': ''}, '_raw': 'COMMENT ', 'formatted': '#\n'}, {'line_number': {'start': 2, 'end': 2}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'NOTE: THIS DOCKERFILE IS GENERATED VIA "update.sh"'}, '_raw': 'COMMENT  NOTE: THIS DOCKERFILE IS GENERATED VIA "update.sh"', 'formatted': '# NOTE: THIS DOCKERFILE IS GENERATED VIA "update.sh"\n'}, {'line_number': {'start': 3, 'end': 3}, 'instruction': 'COMMENT', 'instruction_details': {'comment': ''}, '_raw': 'COMMENT ', 'formatted': '#\n'}, {'line_number': {'start': 4, 'end': 4}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'PLEASE DO NOT EDIT IT DIRECTLY.'}, '_raw': 'COMMENT  PLEASE DO NOT EDIT IT DIRECTLY.', 'formatted': '# PLEASE DO NOT EDIT IT DIRECTLY.\n'}, {'line_number': {'start': 5, 'end': 5}, 'instruction': 'COMMENT', 'instruction_details': {'comment': ''}, '_raw': 'COMMENT ', 'formatted': '#\n'}, {'line_number': {'start': 6, 'end': 6}, 'instruction': 'FROM', 'instruction_details': {'image': 'alpine', 'version': '3.15'}, '_raw': 'FROM alpine:3.15', 'formatted': 'FROM alpine:3.15\n'}, {'line_number': {'start': 8, 'end': 8}, 'instruction': 'LABEL', 'instruction_details': [{'label': 'maintainer', 'default_value': 'NGINX Docker Maintainers <docker-maint@nginx.com>'}], '_raw': 'LABEL maintainer="NGINX Docker Maintainers <docker-maint@nginx.com>"', 'formatted': 'LABEL maintainer="NGINX Docker Maintainers <docker-maint@nginx.com>"\n'}, {'line_number': {'start': 10, 'end': 10}, 'instruction': 'ENV', 'instruction_details': [{'env': 'NGINX_VERSION', 'default_value': '1.21.6'}], '_raw': 'ENV NGINX_VERSION 1.21.6', 'formatted': 'ENV NGINX_VERSION 1.21.6\n'}, {'line_number': {'start': 11, 'end': 11}, 'instruction': 'ENV', 'instruction_details': [{'env': 'NJS_VERSION', 'default_value': '  0.7.3'}], '_raw': 'ENV NJS_VERSION   0.7.3', 'formatted': 'ENV NJS_VERSION   0.7.3\n'}, {'line_number': {'start': 12, 'end': 12}, 'instruction': 'ENV', 'instruction_details': [{'env': 'PKG_RELEASE', 'default_value': '  1'}], '_raw': 'ENV PKG_RELEASE   1', 'formatted': 'ENV PKG_RELEASE   1\n'}, {'line_number': {'start': 14, 'end': 121}, 'instruction': 'RUN', 'instruction_details': {'executable': 'set', 'arguments': '-x \\&& addgroup -g 101 -S nginx \\&& adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx \\&& apkArch="$(cat /etc/apk/arch)" \\&& nginxPackages=" \\nginx=${NGINX_VERSION}-r${PKG_RELEASE} \\nginx-module-xslt=${NGINX_VERSION}-r${PKG_RELEASE} \\nginx-module-geoip=${NGINX_VERSION}-r${PKG_RELEASE} \\nginx-module-image-filter=${NGINX_VERSION}-r${PKG_RELEASE} \\nginx-module-njs=${NGINX_VERSION}.${NJS_VERSION}-r${PKG_RELEASE} \\" \\&& apk add --no-cache --virtual .checksum-deps \\openssl \\&& case "$apkArch" in \\x86_64|aarch64) \\set -x \\&& KEY_SHA512="e7fa8303923d9b95db37a77ad46c68fd4755ff935d0a534d26eba83de193c76166c68bfe7f65471bf8881004ef4aa6df3e34689c305662750c0172fca5d8552a *stdin" \\&& wget -O /tmp/nginx_signing.rsa.pub https://nginx.org/keys/nginx_signing.rsa.pub \\&& if [ "$(openssl rsa -pubin -in /tmp/nginx_signing.rsa.pub -text -noout | openssl sha512 -r)" = "$KEY_SHA512" ]; then \\echo "key verification succeeded!"; \\mv /tmp/nginx_signing.rsa.pub /etc/apk/keys/; \\else \\echo "key verification failed!"; \\exit 1; \\fi \\&& apk add -X "https://nginx.org/packages/mainline/alpine/v$(egrep -o \'^[0-9]+\\.[0-9]+\' /etc/alpine-release)/main" --no-cache $nginxPackages \\;; \\*) \\set -x \\&& tempDir="$(mktemp -d)" \\&& chown nobody:nobody $tempDir \\&& apk add --no-cache --virtual .build-deps \\gcc \\libc-dev \\make \\openssl-dev \\pcre2-dev \\zlib-dev \\linux-headers \\libxslt-dev \\gd-dev \\geoip-dev \\perl-dev \\libedit-dev \\bash \\alpine-sdk \\findutils \\&& su nobody -s /bin/sh -c " \\export HOME=${tempDir} \\&& cd ${tempDir} \\&& curl -f -O https://hg.nginx.org/pkg-oss/archive/688.tar.gz \\&& PKGOSSCHECKSUM=\\"a8ab6ff80ab67c6c9567a9103b52a42a5962e9c1bc7091b7710aaf553a3b484af61b0797dd9b048c518e371a6f69e34d474cfaaeaa116fd2824bffa1cd9d4718 *688.tar.gz\\" \\&& if [ \\"\\$(openssl sha512 -r 688.tar.gz)\\" = \\"\\$PKGOSSCHECKSUM\\" ]; then \\echo \\"pkg-oss tarball checksum verification succeeded!\\"; \\else \\echo \\"pkg-oss tarball checksum verification failed!\\"; \\exit 1; \\fi \\&& tar xzvf 688.tar.gz \\&& cd pkg-oss-688 \\&& cd alpine \\&& make all \\&& apk index -o ${tempDir}/packages/alpine/${apkArch}/APKINDEX.tar.gz ${tempDir}/packages/alpine/${apkArch}/*.apk \\&& abuild-sign -k ${tempDir}/.abuild/abuild-key.rsa ${tempDir}/packages/alpine/${apkArch}/APKINDEX.tar.gz \\" \\&& cp ${tempDir}/.abuild/abuild-key.rsa.pub /etc/apk/keys/ \\&& apk del .build-deps \\&& apk add -X ${tempDir}/packages/alpine/ --no-cache $nginxPackages \\;; \\esac \\&& apk del .checksum-deps \\&& if [ -n "$tempDir" ]; then rm -rf "$tempDir"; fi \\&& if [ -n "/etc/apk/keys/abuild-key.rsa.pub" ]; then rm -f /etc/apk/keys/abuild-key.rsa.pub; fi \\&& if [ -n "/etc/apk/keys/nginx_signing.rsa.pub" ]; then rm -f /etc/apk/keys/nginx_signing.rsa.pub; fi \\&& apk add --no-cache --virtual .gettext gettext \\&& mv /usr/bin/envsubst /tmp/ \\\\&& runDeps="$( \\scanelf --needed --nobanner /tmp/envsubst \\| awk \'{ gsub(/,/, "\\nso:", $2); print "so:" $2 }\' \\| sort -u \\| xargs -r apk info --installed \\| sort -u \\)" \\&& apk add --no-cache $runDeps \\&& apk del .gettext \\&& mv /tmp/envsubst /usr/local/bin/ \\&& apk add --no-cache tzdata \\&& apk add --no-cache curl ca-certificates \\&& ln -sf /dev/stdout /var/log/nginx/access.log \\&& ln -sf /dev/stderr /var/log/nginx/error.log \\&& mkdir /docker-entrypoint.d'}, '_raw': 'RUN set -x \\&& addgroup -g 101 -S nginx \\&& adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx \\&& apkArch="$(cat /etc/apk/arch)" \\&& nginxPackages=" \\nginx=${NGINX_VERSION}-r${PKG_RELEASE} \\nginx-module-xslt=${NGINX_VERSION}-r${PKG_RELEASE} \\nginx-module-geoip=${NGINX_VERSION}-r${PKG_RELEASE} \\nginx-module-image-filter=${NGINX_VERSION}-r${PKG_RELEASE} \\nginx-module-njs=${NGINX_VERSION}.${NJS_VERSION}-r${PKG_RELEASE} \\" \\&& apk add --no-cache --virtual .checksum-deps \\openssl \\&& case "$apkArch" in \\x86_64|aarch64) \\set -x \\&& KEY_SHA512="e7fa8303923d9b95db37a77ad46c68fd4755ff935d0a534d26eba83de193c76166c68bfe7f65471bf8881004ef4aa6df3e34689c305662750c0172fca5d8552a *stdin" \\&& wget -O /tmp/nginx_signing.rsa.pub https://nginx.org/keys/nginx_signing.rsa.pub \\&& if [ "$(openssl rsa -pubin -in /tmp/nginx_signing.rsa.pub -text -noout | openssl sha512 -r)" = "$KEY_SHA512" ]; then \\echo "key verification succeeded!"; \\mv /tmp/nginx_signing.rsa.pub /etc/apk/keys/; \\else \\echo "key verification failed!"; \\exit 1; \\fi \\&& apk add -X "https://nginx.org/packages/mainline/alpine/v$(egrep -o \'^[0-9]+\\.[0-9]+\' /etc/alpine-release)/main" --no-cache $nginxPackages \\;; \\*) \\set -x \\&& tempDir="$(mktemp -d)" \\&& chown nobody:nobody $tempDir \\&& apk add --no-cache --virtual .build-deps \\gcc \\libc-dev \\make \\openssl-dev \\pcre2-dev \\zlib-dev \\linux-headers \\libxslt-dev \\gd-dev \\geoip-dev \\perl-dev \\libedit-dev \\bash \\alpine-sdk \\findutils \\&& su nobody -s /bin/sh -c " \\export HOME=${tempDir} \\&& cd ${tempDir} \\&& curl -f -O https://hg.nginx.org/pkg-oss/archive/688.tar.gz \\&& PKGOSSCHECKSUM=\\"a8ab6ff80ab67c6c9567a9103b52a42a5962e9c1bc7091b7710aaf553a3b484af61b0797dd9b048c518e371a6f69e34d474cfaaeaa116fd2824bffa1cd9d4718 *688.tar.gz\\" \\&& if [ \\"\\$(openssl sha512 -r 688.tar.gz)\\" = \\"\\$PKGOSSCHECKSUM\\" ]; then \\echo \\"pkg-oss tarball checksum verification succeeded!\\"; \\else \\echo \\"pkg-oss tarball checksum verification failed!\\"; \\exit 1; \\fi \\&& tar xzvf 688.tar.gz \\&& cd pkg-oss-688 \\&& cd alpine \\&& make all \\&& apk index -o ${tempDir}/packages/alpine/${apkArch}/APKINDEX.tar.gz ${tempDir}/packages/alpine/${apkArch}/*.apk \\&& abuild-sign -k ${tempDir}/.abuild/abuild-key.rsa ${tempDir}/packages/alpine/${apkArch}/APKINDEX.tar.gz \\" \\&& cp ${tempDir}/.abuild/abuild-key.rsa.pub /etc/apk/keys/ \\&& apk del .build-deps \\&& apk add -X ${tempDir}/packages/alpine/ --no-cache $nginxPackages \\;; \\esac \\&& apk del .checksum-deps \\&& if [ -n "$tempDir" ]; then rm -rf "$tempDir"; fi \\&& if [ -n "/etc/apk/keys/abuild-key.rsa.pub" ]; then rm -f /etc/apk/keys/abuild-key.rsa.pub; fi \\&& if [ -n "/etc/apk/keys/nginx_signing.rsa.pub" ]; then rm -f /etc/apk/keys/nginx_signing.rsa.pub; fi \\&& apk add --no-cache --virtual .gettext gettext \\&& mv /usr/bin/envsubst /tmp/ \\\\&& runDeps="$( \\scanelf --needed --nobanner /tmp/envsubst \\| awk \'{ gsub(/,/, "\\nso:", $2); print "so:" $2 }\' \\| sort -u \\| xargs -r apk info --installed \\| sort -u \\)" \\&& apk add --no-cache $runDeps \\&& apk del .gettext \\&& mv /tmp/envsubst /usr/local/bin/ \\&& apk add --no-cache tzdata \\&& apk add --no-cache curl ca-certificates \\&& ln -sf /dev/stdout /var/log/nginx/access.log \\&& ln -sf /dev/stderr /var/log/nginx/error.log \\&& mkdir /docker-entrypoint.d', 'formatted': 'RUN set -x \\\n\t&& addgroup -g 101 -S nginx \\\n\t&& adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx \\\n\t&& apkArch="$(cat /etc/apk/arch)" \\\n\t&& nginxPackages=" \\\n\tnginx=${NGINX_VERSION}-r${PKG_RELEASE} \\\n\tnginx-module-xslt=${NGINX_VERSION}-r${PKG_RELEASE} \\\n\tnginx-module-geoip=${NGINX_VERSION}-r${PKG_RELEASE} \\\n\tnginx-module-image-filter=${NGINX_VERSION}-r${PKG_RELEASE} \\\n\tnginx-module-njs=${NGINX_VERSION}.${NJS_VERSION}-r${PKG_RELEASE} \\\n\t" \\\n\t&& apk add --no-cache --virtual .checksum-deps \\\n\topenssl \\\n\t&& case "$apkArch" in \\\n\tx86_64|aarch64) \\\n\tset -x \\\n\t&& KEY_SHA512="e7fa8303923d9b95db37a77ad46c68fd4755ff935d0a534d26eba83de193c76166c68bfe7f65471bf8881004ef4aa6df3e34689c305662750c0172fca5d8552a *stdin" \\\n\t&& wget -O /tmp/nginx_signing.rsa.pub https://nginx.org/keys/nginx_signing.rsa.pub \\\n\t&& if [ "$(openssl rsa -pubin -in /tmp/nginx_signing.rsa.pub -text -noout | openssl sha512 -r)" = "$KEY_SHA512" ]; then \\\n\techo "key verification succeeded!"; \\\n\tmv /tmp/nginx_signing.rsa.pub /etc/apk/keys/; \\\n\telse \\\n\techo "key verification failed!"; \\\n\texit 1; \\\n\tfi \\\n\t&& apk add -X "https://nginx.org/packages/mainline/alpine/v$(egrep -o \'^[0-9]+\\\n\t.[0-9]+\' /etc/alpine-release)/main" --no-cache $nginxPackages \\\n\t;; \\\n\t*) \\\n\tset -x \\\n\t&& tempDir="$(mktemp -d)" \\\n\t&& chown nobody:nobody $tempDir \\\n\t&& apk add --no-cache --virtual .build-deps \\\n\tgcc \\\n\tlibc-dev \\\n\tmake \\\n\topenssl-dev \\\n\tpcre2-dev \\\n\tzlib-dev \\\n\tlinux-headers \\\n\tlibxslt-dev \\\n\tgd-dev \\\n\tgeoip-dev \\\n\tperl-dev \\\n\tlibedit-dev \\\n\tbash \\\n\talpine-sdk \\\n\tfindutils \\\n\t&& su nobody -s /bin/sh -c " \\\n\texport HOME=${tempDir} \\\n\t&& cd ${tempDir} \\\n\t&& curl -f -O https://hg.nginx.org/pkg-oss/archive/688.tar.gz \\\n\t&& PKGOSSCHECKSUM=\\\n\t"a8ab6ff80ab67c6c9567a9103b52a42a5962e9c1bc7091b7710aaf553a3b484af61b0797dd9b048c518e371a6f69e34d474cfaaeaa116fd2824bffa1cd9d4718 *688.tar.gz\\\n\t" \\\n\t&& if [ \\\n\t"\\\n\t$(openssl sha512 -r 688.tar.gz)\\\n\t" = \\\n\t"\\\n\t$PKGOSSCHECKSUM\\\n\t" ]; then \\\n\techo \\\n\t"pkg-oss tarball checksum verification succeeded!\\\n\t"; \\\n\telse \\\n\techo \\\n\t"pkg-oss tarball checksum verification failed!\\\n\t"; \\\n\texit 1; \\\n\tfi \\\n\t&& tar xzvf 688.tar.gz \\\n\t&& cd pkg-oss-688 \\\n\t&& cd alpine \\\n\t&& make all \\\n\t&& apk index -o ${tempDir}/packages/alpine/${apkArch}/APKINDEX.tar.gz ${tempDir}/packages/alpine/${apkArch}/*.apk \\\n\t&& abuild-sign -k ${tempDir}/.abuild/abuild-key.rsa ${tempDir}/packages/alpine/${apkArch}/APKINDEX.tar.gz \\\n\t" \\\n\t&& cp ${tempDir}/.abuild/abuild-key.rsa.pub /etc/apk/keys/ \\\n\t&& apk del .build-deps \\\n\t&& apk add -X ${tempDir}/packages/alpine/ --no-cache $nginxPackages \\\n\t;; \\\n\tesac \\\n\t&& apk del .checksum-deps \\\n\t&& if [ -n "$tempDir" ]; then rm -rf "$tempDir"; fi \\\n\t&& if [ -n "/etc/apk/keys/abuild-key.rsa.pub" ]; then rm -f /etc/apk/keys/abuild-key.rsa.pub; fi \\\n\t&& if [ -n "/etc/apk/keys/nginx_signing.rsa.pub" ]; then rm -f /etc/apk/keys/nginx_signing.rsa.pub; fi \\\n\t&& apk add --no-cache --virtual .gettext gettext \\\n\t&& mv /usr/bin/envsubst /tmp/ \\\n\t\\\n\t&& runDeps="$( \\\n\tscanelf --needed --nobanner /tmp/envsubst \\\n\t| awk \'{ gsub(/,/, "\\\n\tnso:", $2); print "so:" $2 }\' \\\n\t| sort -u \\\n\t| xargs -r apk info --installed \\\n\t| sort -u \\\n\t)" \\\n\t&& apk add --no-cache $runDeps \\\n\t&& apk del .gettext \\\n\t&& mv /tmp/envsubst /usr/local/bin/ \\\n\t&& apk add --no-cache tzdata \\\n\t&& apk add --no-cache curl ca-certificates \\\n\t&& ln -sf /dev/stdout /var/log/nginx/access.log \\\n\t&& ln -sf /dev/stderr /var/log/nginx/error.log \\\n\t&& mkdir /docker-entrypoint.d\n'}, {'line_number': {'start': 96, 'end': 96}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'the rest away. To do this, we need to install `gettext`'}, '_raw': 'COMMENT  the rest away. To do this, we need to install `gettext`', 'formatted': '# the rest away. To do this, we need to install `gettext`\n'}, {'line_number': {'start': 97, 'end': 97}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'then move `envsubst` out of the way so `gettext` can'}, '_raw': 'COMMENT  then move `envsubst` out of the way so `gettext` can', 'formatted': '# then move `envsubst` out of the way so `gettext` can\n'}, {'line_number': {'start': 123, 'end': 123}, 'instruction': 'COPY', 'instruction_details': {'source': ['docker-entrypoint.sh'], 'parsed_source_files': [], 'target': '/'}, '_raw': 'COPY docker-entrypoint.sh /', 'formatted': 'COPY docker-entrypoint.sh /\n'}, {'line_number': {'start': 124, 'end': 124}, 'instruction': 'COPY', 'instruction_details': {'source': ['10-listen-on-ipv6-by-default.sh'], 'parsed_source_files': [], 'target': '/docker-entrypoint.d'}, '_raw': 'COPY 10-listen-on-ipv6-by-default.sh /docker-entrypoint.d', 'formatted': 'COPY 10-listen-on-ipv6-by-default.sh /docker-entrypoint.d\n'}, {'line_number': {'start': 125, 'end': 125}, 'instruction': 'COPY', 'instruction_details': {'source': ['20-envsubst-on-templates.sh'], 'parsed_source_files': [], 'target': '/docker-entrypoint.d'}, '_raw': 'COPY 20-envsubst-on-templates.sh /docker-entrypoint.d', 'formatted': 'COPY 20-envsubst-on-templates.sh /docker-entrypoint.d\n'}, {'line_number': {'start': 126, 'end': 126}, 'instruction': 'COPY', 'instruction_details': {'source': ['30-tune-worker-processes.sh'], 'parsed_source_files': [], 'target': '/docker-entrypoint.d'}, '_raw': 'COPY 30-tune-worker-processes.sh /docker-entrypoint.d', 'formatted': 'COPY 30-tune-worker-processes.sh /docker-entrypoint.d\n'}, {'line_number': {'start': 127, 'end': 127}, 'instruction': 'ENTRYPOINT', 'instruction_details': {'executable': '/docker-entrypoint.sh', 'arguments': []}, '_raw': 'ENTRYPOINT ["/docker-entrypoint.sh"]', 'formatted': 'ENTRYPOINT ["/docker-entrypoint.sh"]\n'}, {'line_number': {'start': 129, 'end': 129}, 'instruction': 'EXPOSE', 'instruction_details': {'port': '80'}, '_raw': 'EXPOSE 80', 'formatted': 'EXPOSE 80\n'}, {'line_number': {'start': 131, 'end': 131}, 'instruction': 'STOPSIGNAL', 'instruction_details': {'stopsignal': 'SIGQUIT'}, '_raw': 'STOPSIGNAL SIGQUIT', 'formatted': 'STOPSIGNAL SIGQUIT\n'}, {'line_number': {'start': 133, 'end': 133}, 'instruction': 'CMD', 'instruction_details': {'executable': 'nginx', 'arguments': ['-g', 'daemon off;']}, '_raw': 'CMD ["nginx", "-g", "daemon off;"]', 'formatted': 'CMD ["nginx", "-g", "daemon off;"]\n'}]),
        ("../fixtures/postgres.Dockerfile", [{'line_number': {'start': 1, 'end': 1}, 'instruction': 'COMMENT', 'instruction_details': {'comment': '"ported" by Adam Miller <maxamillion@fedoraproject.org> from'}, '_raw': 'COMMENT  "ported" by Adam Miller <maxamillion@fedoraproject.org> from', 'formatted': '# "ported" by Adam Miller <maxamillion@fedoraproject.org> from\n'}, {'line_number': {'start': 2, 'end': 2}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'https://github.com/fedora-cloud/Fedora-Dockerfiles'}, '_raw': 'COMMENT    https://github.com/fedora-cloud/Fedora-Dockerfiles', 'formatted': '#   https://github.com/fedora-cloud/Fedora-Dockerfiles\n'}, {'line_number': {'start': 3, 'end': 3}, 'instruction': 'COMMENT', 'instruction_details': {'comment': ''}, '_raw': 'COMMENT ', 'formatted': '#\n'}, {'line_number': {'start': 4, 'end': 4}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'Originally written for Fedora-Dockerfiles by'}, '_raw': 'COMMENT  Originally written for Fedora-Dockerfiles by', 'formatted': '# Originally written for Fedora-Dockerfiles by\n'}, {'line_number': {'start': 5, 'end': 5}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'scollier <scollier@redhat.com>'}, '_raw': 'COMMENT    scollier <scollier@redhat.com>', 'formatted': '#   scollier <scollier@redhat.com>\n'}, {'line_number': {'start': 7, 'end': 7}, 'instruction': 'FROM', 'instruction_details': {'image': 'centos', 'version': 'centos7'}, '_raw': 'FROM centos:centos7', 'formatted': 'FROM centos:centos7\n'}, {'line_number': {'start': 8, 'end': 8}, 'instruction': 'MAINTAINER', 'instruction_details': {'maintainer': 'The CentOS Project <cloud-ops@centos.org>'}, '_raw': 'MAINTAINER The CentOS Project <cloud-ops@centos.org>', 'formatted': 'MAINTAINER The CentOS Project <cloud-ops@centos.org>\n'}, {'line_number': {'start': 10, 'end': 10}, 'instruction': 'RUN', 'instruction_details': {'executable': 'yum', 'arguments': '-y update; yum clean all'}, '_raw': 'RUN yum -y update; yum clean all', 'formatted': 'RUN yum -y update; yum clean all\n'}, {'line_number': {'start': 11, 'end': 11}, 'instruction': 'RUN', 'instruction_details': {'executable': 'yum', 'arguments': '-y install sudo epel-release; yum clean all'}, '_raw': 'RUN yum -y install sudo epel-release; yum clean all', 'formatted': 'RUN yum -y install sudo epel-release; yum clean all\n'}, {'line_number': {'start': 12, 'end': 12}, 'instruction': 'RUN', 'instruction_details': {'executable': 'yum', 'arguments': '-y install postgresql-server postgresql postgresql-contrib supervisor pwgen; yum clean all'}, '_raw': 'RUN yum -y install postgresql-server postgresql postgresql-contrib supervisor pwgen; yum clean all', 'formatted': 'RUN yum -y install postgresql-server postgresql postgresql-contrib supervisor pwgen; yum clean all\n'}, {'line_number': {'start': 14, 'end': 14}, 'instruction': 'ADD', 'instruction_details': {'source': ['./postgresql-setup'], 'parsed_source_files': [], 'target': '/usr/bin/postgresql-setup'}, '_raw': 'ADD ./postgresql-setup /usr/bin/postgresql-setup', 'formatted': 'ADD ./postgresql-setup /usr/bin/postgresql-setup\n'}, {'line_number': {'start': 15, 'end': 15}, 'instruction': 'ADD', 'instruction_details': {'source': ['./supervisord.conf'], 'parsed_source_files': [], 'target': '/etc/supervisord.conf'}, '_raw': 'ADD ./supervisord.conf /etc/supervisord.conf', 'formatted': 'ADD ./supervisord.conf /etc/supervisord.conf\n'}, {'line_number': {'start': 16, 'end': 16}, 'instruction': 'ADD', 'instruction_details': {'source': ['./start_postgres.sh'], 'parsed_source_files': [], 'target': '/start_postgres.sh'}, '_raw': 'ADD ./start_postgres.sh /start_postgres.sh', 'formatted': 'ADD ./start_postgres.sh /start_postgres.sh\n'}, {'line_number': {'start': 18, 'end': 18}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'Sudo requires a tty. fix that.'}, '_raw': 'COMMENT Sudo requires a tty. fix that.', 'formatted': '#Sudo requires a tty. fix that.\n'}, {'line_number': {'start': 19, 'end': 19}, 'instruction': 'RUN', 'instruction_details': {'executable': 'sed', 'arguments': "-i 's/.*requiretty$/#Defaults requiretty/' /etc/sudoers"}, '_raw': "RUN sed -i 's/.*requiretty$/#Defaults requiretty/' /etc/sudoers", 'formatted': "RUN sed -i 's/.*requiretty$/#Defaults requiretty/' /etc/sudoers\n"}, {'line_number': {'start': 20, 'end': 20}, 'instruction': 'RUN', 'instruction_details': {'executable': 'chmod', 'arguments': '+x /usr/bin/postgresql-setup'}, '_raw': 'RUN chmod +x /usr/bin/postgresql-setup', 'formatted': 'RUN chmod +x /usr/bin/postgresql-setup\n'}, {'line_number': {'start': 21, 'end': 21}, 'instruction': 'RUN', 'instruction_details': {'executable': 'chmod', 'arguments': '+x /start_postgres.sh'}, '_raw': 'RUN chmod +x /start_postgres.sh', 'formatted': 'RUN chmod +x /start_postgres.sh\n'}, {'line_number': {'start': 23, 'end': 23}, 'instruction': 'RUN', 'instruction_details': {'executable': '/usr/bin/postgresql-setup', 'arguments': 'initdb'}, '_raw': 'RUN /usr/bin/postgresql-setup initdb', 'formatted': 'RUN /usr/bin/postgresql-setup initdb\n'}, {'line_number': {'start': 25, 'end': 25}, 'instruction': 'ADD', 'instruction_details': {'source': ['./postgresql.conf'], 'parsed_source_files': [], 'target': '/var/lib/pgsql/data/postgresql.conf'}, '_raw': 'ADD ./postgresql.conf /var/lib/pgsql/data/postgresql.conf', 'formatted': 'ADD ./postgresql.conf /var/lib/pgsql/data/postgresql.conf\n'}, {'line_number': {'start': 27, 'end': 27}, 'instruction': 'RUN', 'instruction_details': {'executable': 'chown', 'arguments': '-v postgres.postgres /var/lib/pgsql/data/postgresql.conf'}, '_raw': 'RUN chown -v postgres.postgres /var/lib/pgsql/data/postgresql.conf', 'formatted': 'RUN chown -v postgres.postgres /var/lib/pgsql/data/postgresql.conf\n'}, {'line_number': {'start': 29, 'end': 29}, 'instruction': 'RUN', 'instruction_details': {'executable': 'echo', 'arguments': '"host    all             all             0.0.0.0/0               md5" >> /var/lib/pgsql/data/pg_hba.conf'}, '_raw': 'RUN echo "host    all             all             0.0.0.0/0               md5" >> /var/lib/pgsql/data/pg_hba.conf', 'formatted': 'RUN echo "host    all             all             0.0.0.0/0               md5" >> /var/lib/pgsql/data/pg_hba.conf\n'}, {'line_number': {'start': 31, 'end': 31}, 'instruction': 'VOLUME', 'instruction_details': {'volume': '["/var/lib/pgsql"]'}, '_raw': 'VOLUME ["/var/lib/pgsql"]', 'formatted': 'VOLUME ["/var/lib/pgsql"]\n'}, {'line_number': {'start': 33, 'end': 33}, 'instruction': 'EXPOSE', 'instruction_details': {'port': '5432'}, '_raw': 'EXPOSE 5432', 'formatted': 'EXPOSE 5432\n'}, {'line_number': {'start': 35, 'end': 35}, 'instruction': 'CMD', 'instruction_details': {'executable': '/bin/bash', 'arguments': ['/start_postgres.sh']}, '_raw': 'CMD ["/bin/bash", "/start_postgres.sh"]', 'formatted': 'CMD ["/bin/bash", "/start_postgres.sh"]\n'}]),
        ("../fixtures/python.Dockerfile", [{'line_number': {'start': 1, 'end': 1}, 'instruction': 'COMMENT', 'instruction_details': {'comment': '"ported" by Adam Miller <maxamillion@fedoraproject.org> from'}, '_raw': 'COMMENT  "ported" by Adam Miller <maxamillion@fedoraproject.org> from', 'formatted': '# "ported" by Adam Miller <maxamillion@fedoraproject.org> from\n'}, {'line_number': {'start': 2, 'end': 2}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'https://github.com/fedora-cloud/Fedora-Dockerfiles'}, '_raw': 'COMMENT    https://github.com/fedora-cloud/Fedora-Dockerfiles', 'formatted': '#   https://github.com/fedora-cloud/Fedora-Dockerfiles\n'}, {'line_number': {'start': 3, 'end': 3}, 'instruction': 'COMMENT', 'instruction_details': {'comment': ''}, '_raw': 'COMMENT ', 'formatted': '#\n'}, {'line_number': {'start': 4, 'end': 4}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'Originally written for Fedora-Dockerfiles by'}, '_raw': 'COMMENT  Originally written for Fedora-Dockerfiles by', 'formatted': '# Originally written for Fedora-Dockerfiles by\n'}, {'line_number': {'start': 5, 'end': 5}, 'instruction': 'COMMENT', 'instruction_details': {'comment': '"Aditya Patawari" <adimania@fedoraproject.org>'}, '_raw': 'COMMENT    "Aditya Patawari" <adimania@fedoraproject.org>', 'formatted': '#   "Aditya Patawari" <adimania@fedoraproject.org>\n'}, {'line_number': {'start': 7, 'end': 7}, 'instruction': 'FROM', 'instruction_details': {'image': 'centos', 'version': 'centos7'}, '_raw': 'FROM centos:centos7', 'formatted': 'FROM centos:centos7\n'}, {'line_number': {'start': 8, 'end': 8}, 'instruction': 'MAINTAINER', 'instruction_details': {'maintainer': 'The CentOS Project <cloud-ops@centos.org>'}, '_raw': 'MAINTAINER The CentOS Project <cloud-ops@centos.org>', 'formatted': 'MAINTAINER The CentOS Project <cloud-ops@centos.org>\n'}, {'line_number': {'start': 10, 'end': 10}, 'instruction': 'RUN', 'instruction_details': {'executable': 'yum', 'arguments': '-y update; yum clean all'}, '_raw': 'RUN yum -y update; yum clean all', 'formatted': 'RUN yum -y update; yum clean all\n'}, {'line_number': {'start': 11, 'end': 11}, 'instruction': 'RUN', 'instruction_details': {'executable': 'yum', 'arguments': '-y install epel-release; yum clean all'}, '_raw': 'RUN yum -y install epel-release; yum clean all', 'formatted': 'RUN yum -y install epel-release; yum clean all\n'}, {'line_number': {'start': 12, 'end': 12}, 'instruction': 'RUN', 'instruction_details': {'executable': 'yum', 'arguments': '-y install python-pip; yum clean all'}, '_raw': 'RUN yum -y install python-pip; yum clean all', 'formatted': 'RUN yum -y install python-pip; yum clean all\n'}, {'line_number': {'start': 14, 'end': 14}, 'instruction': 'ADD', 'instruction_details': {'source': ['../dockerfiles'], 'parsed_source_files': [], 'target': '/src'}, '_raw': 'ADD ../dockerfiles /src', 'formatted': 'ADD ../dockerfiles /src\n'}, {'line_number': {'start': 16, 'end': 16}, 'instruction': 'RUN', 'instruction_details': {'executable': 'cd', 'arguments': '/src; pip install -r requirements.txt'}, '_raw': 'RUN cd /src; pip install -r requirements.txt', 'formatted': 'RUN cd /src; pip install -r requirements.txt\n'}, {'line_number': {'start': 18, 'end': 18}, 'instruction': 'EXPOSE', 'instruction_details': {'port': '8080'}, '_raw': 'EXPOSE 8080', 'formatted': 'EXPOSE 8080\n'}, {'line_number': {'start': 20, 'end': 20}, 'instruction': 'CMD', 'instruction_details': {'executable': 'python', 'arguments': ['/src/index.py']}, '_raw': 'CMD ["python", "/src/index.py"]', 'formatted': 'CMD ["python", "/src/index.py"]\n'}]),
        ("../fixtures/rstudio.Dockerfile", [{'line_number': {'start': 1, 'end': 1}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'Run RStudio in a container'}, '_raw': 'COMMENT  Run RStudio in a container', 'formatted': '# Run RStudio in a container\n'}, {'line_number': {'start': 2, 'end': 2}, 'instruction': 'COMMENT', 'instruction_details': {'comment': ''}, '_raw': 'COMMENT ', 'formatted': '#\n'}, {'line_number': {'start': 3, 'end': 3}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'docker run -it \\'}, '_raw': 'COMMENT  docker run -it \\', 'formatted': '# docker run -it \\\n'}, {'line_number': {'start': 4, 'end': 4}, 'instruction': 'COMMENT', 'instruction_details': {'comment': '-v /tmp/.X11-unix:/tmp/.X11-unix \\  mount the X11 socket'}, '_raw': 'COMMENT \t-v /tmp/.X11-unix:/tmp/.X11-unix \\  mount the X11 socket', 'formatted': '#\t-v /tmp/.X11-unix:/tmp/.X11-unix \\ # mount the X11 socket\n'}, {'line_number': {'start': 5, 'end': 5}, 'instruction': 'COMMENT', 'instruction_details': {'comment': '-e DISPLAY=unix$DISPLAY \\'}, '_raw': 'COMMENT \t-e DISPLAY=unix$DISPLAY \\', 'formatted': '#\t-e DISPLAY=unix$DISPLAY \\\n'}, {'line_number': {'start': 6, 'end': 6}, 'instruction': 'COMMENT', 'instruction_details': {'comment': '-v $HOME/rscripts:/root/rscripts \\'}, '_raw': 'COMMENT \t-v $HOME/rscripts:/root/rscripts \\', 'formatted': '#\t-v $HOME/rscripts:/root/rscripts \\\n'}, {'line_number': {'start': 7, 'end': 7}, 'instruction': 'COMMENT', 'instruction_details': {'comment': '--device /dev/dri \\'}, '_raw': 'COMMENT \t--device /dev/dri \\', 'formatted': '#\t--device /dev/dri \\\n'}, {'line_number': {'start': 8, 'end': 8}, 'instruction': 'COMMENT', 'instruction_details': {'comment': '--name rstudio \\'}, '_raw': 'COMMENT \t--name rstudio \\', 'formatted': '#\t--name rstudio \\\n'}, {'line_number': {'start': 9, 'end': 9}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'jess/rstudio'}, '_raw': 'COMMENT \tjess/rstudio', 'formatted': '#\tjess/rstudio\n'}, {'line_number': {'start': 10, 'end': 10}, 'instruction': 'COMMENT', 'instruction_details': {'comment': ''}, '_raw': 'COMMENT ', 'formatted': '#\n'}, {'line_number': {'start': 12, 'end': 12}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'Base docker image'}, '_raw': 'COMMENT  Base docker image', 'formatted': '# Base docker image\n'}, {'line_number': {'start': 13, 'end': 13}, 'instruction': 'FROM', 'instruction_details': {'image': 'debian', 'version': 'bullseye-slim'}, '_raw': 'FROM debian:bullseye-slim', 'formatted': 'FROM debian:bullseye-slim\n'}, {'line_number': {'start': 14, 'end': 14}, 'instruction': 'LABEL', 'instruction_details': [{'label': 'maintainer', 'default_value': 'Jessie Frazelle <jess@linux.com>'}], '_raw': 'LABEL maintainer "Jessie Frazelle <jess@linux.com>"', 'formatted': 'LABEL maintainer "Jessie Frazelle <jess@linux.com>"\n'}, {'line_number': {'start': 16, 'end': 16}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'Install Rstudio deps'}, '_raw': 'COMMENT  Install Rstudio deps', 'formatted': '# Install Rstudio deps\n'}, {'line_number': {'start': 17, 'end': 57}, 'instruction': 'RUN', 'instruction_details': {'executable': 'apt-get', 'arguments': 'update && apt-get install -y \\ca-certificates \\curl \\fcitx-frontend-qt5 \\fcitx-modules \\fcitx-module-dbus \\libasound2 \\libclang-dev \\libedit2 \\libgl1-mesa-dri \\libgl1-mesa-glx \\libgstreamer1.0-0 \\libgstreamer-plugins-base1.0-0 \\libjpeg-dev \\libjpeg62-turbo \\libjpeg62-turbo-dev \\libpresage1v5 \\libpresage-data \\libqt5core5a \\libqt5dbus5 \\libqt5gui5 \\libqt5network5 \\libqt5printsupport5 \\libqt5webkit5 \\libqt5widgets5 \\libnss3 \\libtiff5 \\libxcomposite1 \\libxcursor1 \\libxslt1.1 \\libxtst6 \\littler \\locales \\r-base \\r-base-dev \\r-recommended \\--no-install-recommends \\&& echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \\&& locale-gen en_US.utf8 \\&& /usr/sbin/update-locale LANG=en_US.UTF-8 \\&& rm -rf /var/lib/apt/lists/*'}, '_raw': 'RUN apt-get update && apt-get install -y \\ca-certificates \\curl \\fcitx-frontend-qt5 \\fcitx-modules \\fcitx-module-dbus \\libasound2 \\libclang-dev \\libedit2 \\libgl1-mesa-dri \\libgl1-mesa-glx \\libgstreamer1.0-0 \\libgstreamer-plugins-base1.0-0 \\libjpeg-dev \\libjpeg62-turbo \\libjpeg62-turbo-dev \\libpresage1v5 \\libpresage-data \\libqt5core5a \\libqt5dbus5 \\libqt5gui5 \\libqt5network5 \\libqt5printsupport5 \\libqt5webkit5 \\libqt5widgets5 \\libnss3 \\libtiff5 \\libxcomposite1 \\libxcursor1 \\libxslt1.1 \\libxtst6 \\littler \\locales \\r-base \\r-base-dev \\r-recommended \\--no-install-recommends \\&& echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \\&& locale-gen en_US.utf8 \\&& /usr/sbin/update-locale LANG=en_US.UTF-8 \\&& rm -rf /var/lib/apt/lists/*', 'formatted': 'RUN apt-get update && apt-get install -y \\\n\tca-certificates \\\n\tcurl \\\n\tfcitx-frontend-qt5 \\\n\tfcitx-modules \\\n\tfcitx-module-dbus \\\n\tlibasound2 \\\n\tlibclang-dev \\\n\tlibedit2 \\\n\tlibgl1-mesa-dri \\\n\tlibgl1-mesa-glx \\\n\tlibgstreamer1.0-0 \\\n\tlibgstreamer-plugins-base1.0-0 \\\n\tlibjpeg-dev \\\n\tlibjpeg62-turbo \\\n\tlibjpeg62-turbo-dev \\\n\tlibpresage1v5 \\\n\tlibpresage-data \\\n\tlibqt5core5a \\\n\tlibqt5dbus5 \\\n\tlibqt5gui5 \\\n\tlibqt5network5 \\\n\tlibqt5printsupport5 \\\n\tlibqt5webkit5 \\\n\tlibqt5widgets5 \\\n\tlibnss3 \\\n\tlibtiff5 \\\n\tlibxcomposite1 \\\n\tlibxcursor1 \\\n\tlibxslt1.1 \\\n\tlibxtst6 \\\n\tlittler \\\n\tlocales \\\n\tr-base \\\n\tr-base-dev \\\n\tr-recommended \\\n\t--no-install-recommends \\\n\t&& echo "en_US.UTF-8 UTF-8" >> /etc/locale.gen \\\n\t&& locale-gen en_US.utf8 \\\n\t&& /usr/sbin/update-locale LANG=en_US.UTF-8 \\\n\t&& rm -rf /var/lib/apt/lists/*\n'}, {'line_number': {'start': 59, 'end': 59}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'https://www.rstudio.com/products/rstudio/download/download'}, '_raw': 'COMMENT  https://www.rstudio.com/products/rstudio/download/download', 'formatted': '# https://www.rstudio.com/products/rstudio/download/#download\n'}, {'line_number': {'start': 60, 'end': 60}, 'instruction': 'ENV', 'instruction_details': [{'env': 'RSTUDIO_VERSION', 'default_value': '1.3.959'}], '_raw': 'ENV RSTUDIO_VERSION 1.3.959', 'formatted': 'ENV RSTUDIO_VERSION 1.3.959\n'}, {'line_number': {'start': 62, 'end': 62}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'Download the source'}, '_raw': 'COMMENT  Download the source', 'formatted': '# Download the source\n'}, {'line_number': {'start': 63, 'end': 66}, 'instruction': 'RUN', 'instruction_details': {'executable': 'curl', 'arguments': '-sSL "https://download1.rstudio.org/desktop/bionic/amd64/rstudio-${RSTUDIO_VERSION}-amd64.deb" -o /tmp/rstudio-amd64.deb \\&& dpkg -i /tmp/rstudio-amd64.deb \\&& rm -rf /tmp/*.deb \\&& ln -f -s /usr/lib/rstudio/bin/rstudio /usr/bin/rstudio'}, '_raw': 'RUN curl -sSL "https://download1.rstudio.org/desktop/bionic/amd64/rstudio-${RSTUDIO_VERSION}-amd64.deb" -o /tmp/rstudio-amd64.deb \\&& dpkg -i /tmp/rstudio-amd64.deb \\&& rm -rf /tmp/*.deb \\&& ln -f -s /usr/lib/rstudio/bin/rstudio /usr/bin/rstudio', 'formatted': 'RUN curl -sSL "https://download1.rstudio.org/desktop/bionic/amd64/rstudio-${RSTUDIO_VERSION}-amd64.deb" -o /tmp/rstudio-amd64.deb \\\n\t&& dpkg -i /tmp/rstudio-amd64.deb \\\n\t&& rm -rf /tmp/*.deb \\\n\t&& ln -f -s /usr/lib/rstudio/bin/rstudio /usr/bin/rstudio\n'}, {'line_number': {'start': 69, 'end': 69}, 'instruction': 'ENV', 'instruction_details': [{'env': 'LC_ALL', 'default_value': 'en_US.UTF-8'}], '_raw': 'ENV LC_ALL en_US.UTF-8', 'formatted': 'ENV LC_ALL en_US.UTF-8\n'}, {'line_number': {'start': 70, 'end': 70}, 'instruction': 'ENV', 'instruction_details': [{'env': 'LANG', 'default_value': 'en_US.UTF-8'}], '_raw': 'ENV LANG en_US.UTF-8', 'formatted': 'ENV LANG en_US.UTF-8\n'}, {'line_number': {'start': 72, 'end': 72}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'Set default CRAN repo'}, '_raw': 'COMMENT  Set default CRAN repo', 'formatted': '# Set default CRAN repo\n'}, {'line_number': {'start': 73, 'end': 82}, 'instruction': 'RUN', 'instruction_details': {'executable': 'mkdir', 'arguments': '-p /etc/R \\&& echo \'options(repos = c(CRAN = "https://cran.rstudio.com/"), download.file.method = "libcurl")\' >> /etc/R/Rprofile.site \\&& echo \'source("/etc/R/Rprofile.site")\' >> /etc/littler.r \\&& ln -s /usr/share/doc/littler/examples/install.r /usr/local/bin/install.r \\&& ln -s /usr/share/doc/littler/examples/install2.r /usr/local/bin/install2.r \\&& ln -s /usr/share/doc/littler/examples/installGithub.r /usr/local/bin/installGithub.r \\&& ln -s /usr/share/doc/littler/examples/testInstalled.r /usr/local/bin/testInstalled.r \\&& rm -rf /tmp/downloaded_packages/ /tmp/*.rds \\&& echo \'"\\e[5~": history-search-backward\' >> /etc/inputrc \\&& echo \'"\\e[6~": history-search-backward\' >> /etc/inputrc'}, '_raw': 'RUN mkdir -p /etc/R \\&& echo \'options(repos = c(CRAN = "https://cran.rstudio.com/"), download.file.method = "libcurl")\' >> /etc/R/Rprofile.site \\&& echo \'source("/etc/R/Rprofile.site")\' >> /etc/littler.r \\&& ln -s /usr/share/doc/littler/examples/install.r /usr/local/bin/install.r \\&& ln -s /usr/share/doc/littler/examples/install2.r /usr/local/bin/install2.r \\&& ln -s /usr/share/doc/littler/examples/installGithub.r /usr/local/bin/installGithub.r \\&& ln -s /usr/share/doc/littler/examples/testInstalled.r /usr/local/bin/testInstalled.r \\&& rm -rf /tmp/downloaded_packages/ /tmp/*.rds \\&& echo \'"\\e[5~": history-search-backward\' >> /etc/inputrc \\&& echo \'"\\e[6~": history-search-backward\' >> /etc/inputrc', 'formatted': 'RUN mkdir -p /etc/R \\\n\t&& echo \'options(repos = c(CRAN = "https://cran.rstudio.com/"), download.file.method = "libcurl")\' >> /etc/R/Rprofile.site \\\n\t&& echo \'source("/etc/R/Rprofile.site")\' >> /etc/littler.r \\\n\t&& ln -s /usr/share/doc/littler/examples/install.r /usr/local/bin/install.r \\\n\t&& ln -s /usr/share/doc/littler/examples/install2.r /usr/local/bin/install2.r \\\n\t&& ln -s /usr/share/doc/littler/examples/installGithub.r /usr/local/bin/installGithub.r \\\n\t&& ln -s /usr/share/doc/littler/examples/testInstalled.r /usr/local/bin/testInstalled.r \\\n\t&& rm -rf /tmp/downloaded_packages/ /tmp/*.rds \\\n\t&& echo \'"\\\n\te[5~": history-search-backward\' >> /etc/inputrc \\\n\t&& echo \'"\\\n\te[6~": history-search-backward\' >> /etc/inputrc\n'}, {'line_number': {'start': 84, 'end': 84}, 'instruction': 'ENV', 'instruction_details': [{'env': 'HOME', 'default_value': '/home/user'}], '_raw': 'ENV HOME /home/user', 'formatted': 'ENV HOME /home/user\n'}, {'line_number': {'start': 85, 'end': 86}, 'instruction': 'RUN', 'instruction_details': {'executable': 'useradd', 'arguments': '--create-home --home-dir $HOME user \\&& chown -R user:user $HOME'}, '_raw': 'RUN useradd --create-home --home-dir $HOME user \\&& chown -R user:user $HOME', 'formatted': 'RUN useradd --create-home --home-dir $HOME user \\\n\t&& chown -R user:user $HOME\n'}, {'line_number': {'start': 88, 'end': 88}, 'instruction': 'WORKDIR', 'instruction_details': {'workdir': '$HOME'}, '_raw': 'WORKDIR $HOME', 'formatted': 'WORKDIR $HOME\n'}, {'line_number': {'start': 90, 'end': 90}, 'instruction': 'USER', 'instruction_details': {'user': 'user'}, '_raw': 'USER user', 'formatted': 'USER user\n'}, {'line_number': {'start': 92, 'end': 92}, 'instruction': 'COMMENT', 'instruction_details': {'comment': 'Autorun Rstudio'}, '_raw': 'COMMENT  Autorun Rstudio', 'formatted': '# Autorun Rstudio\n'}, {'line_number': {'start': 93, 'end': 93}, 'instruction': 'ENTRYPOINT', 'instruction_details': {'executable': 'rstudio', 'arguments': []}, '_raw': 'ENTRYPOINT [ "rstudio" ]', 'formatted': 'ENTRYPOINT [ "rstudio" ]\n'}])
    ]
)
def test_dockerfiles(dockerfile, expected):
    dfp = DockerfileParser(dockerfile=dockerfile)
    assert dfp.df_ast == expected


@pytest.mark.parametrize(
    "raw,maintainer",
    [
        ("MAINTAINER Fred", "Fred")
    ]
)
def test_maintainers(raw, maintainer):
    dfp = DockerfileParser(raw_text=raw)
    assert dfp.maintainers[0]["instruction_details"].get("maintainer") == maintainer

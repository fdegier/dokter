import argparse
import inspect

from parser import DockerfileParser


class Analyzer:
    def __init__(self, dockerfile: str = None, raw_text: str = None, dockerignore: str = ""):
        if dockerfile is not None:
            self.dfp = DockerfileParser(dockerfile=dockerfile, dockerignore=dockerignore)
        elif raw_text is not None:
            self.dfp = DockerfileParser(raw_text=raw_text, dockerignore=dockerignore)
        else:
            raise TypeError("Neither a Dockerfile path nor raw text input were provided")
        self.dockerfile = dockerfile
        self.results = []
        self.errors = 0
        self.warnings = 0

        self.raw_text = True if raw_text else False
        self.verbose_explanation = False

    def _formatter(self, rule, data, severity, rule_info):
        if self.verbose_explanation is True:
            rule_info = f"\n{rule_info.split(':return:', 1)[0]}"
        else:
            rule_info = rule_info.splitlines()[0]
        if data:
            self.results.append(f"{self.dockerfile}:{data['line_number']['start']:<3} - {rule.upper()} - {severity.upper():<7} - {rule_info}")
        else:
            self.results.append(f"{self.dockerfile}:0   - {rule.upper()} - {severity.upper():<7} - {rule_info}")
        if severity.upper() == "ERROR":
            self.errors += 1
        elif severity.upper() == "WARNING":
            self.warnings += 1

    def _return_results(self):
        return self.warnings, self.errors

    def dfa001(self):
        """
        Verify that no credentials are leaking by copying in sensitive files.

        Examples include: copying over a .env file, SSH private keys, settings files etc.
        :return:
        """
        rule = inspect.stack()[0][3]
        severity = "ERROR"
        sensitive_files = [
            ".env", ".pem", ".properties"
            "settings", "config", "secrets", "application", "dev", "appsettings", "credentials", "default", "strings",
            "environment"
        ]

        for word in sensitive_files:
            for i in self.dfp.copies:
                for source in i["instruction_details"]["source"]:
                    if word in source.lower() or word in i["instruction_details"]["target"].lower():
                        self._formatter(rule=rule, data=i, severity=severity,
                                        rule_info=inspect.getdoc(self.dfa001))

    def dfa002(self):
        """
        Usa a .dockerignore file to exclude files being copied over.

        By using a .dockerignore files, the build will generally be faster because it has to transfer less data to the
        daemon, it also helps prevent copying sensitive files. For more information see:
        https://docs.docker.com/engine/reference/builder/#dockerignore-file
        :return:
        """
        rule = inspect.stack()[0][3]
        severity = "WARNING"
        if len(self.dfp.docker_ignore_files) == 0:
            self._formatter(data=None, rule=rule, severity=severity, rule_info=inspect.getdoc(self.dfa002))

    def dfa003(self):
        """
        When using "COPY . <target>" make sure to have a .dockerignore file. Best to copy specific folders.

        By using a .dockerignore files, the build will generally be faster because it has to transfer less data to the
        daemon, it also helps prevent copying sensitive files. For more information see:
        https://docs.docker.com/engine/reference/builder/#dockerignore-file

        Example of secure instruction:

        ++++++++
        COPY src /app/src
        COPY requirements.txt /app/
        ++++++++

        Example of insecure instruction:
        ++++++++
        COPY . /app
        ++++++++
        :return:
        """
        rule = inspect.stack()[0][3]
        severity = "ERROR"
        for i in self.dfp.copies:
            for source in i["instruction_details"]["source"]:
                if source == ".":
                    self._formatter(rule=rule, data=i, severity=severity, rule_info=inspect.getdoc(self.dfa003))

    def dfa004(self):
        """
        Verify that build args doesn't contain sensitive information, use secret mounts instead.

        Build args are stored in the history of the docker image and can be retrieved. Secret mounts are not persisted
        and are therefor a better option if you temporarily need sensitive information to build your image. If sensitive
        information is required during runtime of the containers, use environment variables.

        Example of secure instruction:

        ++++++++
        RUN --mount=type=secret,id=docker_token docker login -u user -p $(cat /run/secrets/docker_token)
        ++++++++

        Example of insecure instruction:
        ++++++++
        ARG TOKEN
        RUN docker login -u user -p $TOKEN
        ++++++++
        :return:
        """
        rule = inspect.stack()[0][3]
        severity = "ERROR"

        sensitive_words = [
            "key", "secret", "token", "pass"
        ]

        for word in sensitive_words:
            for i in self.dfp.args:
                if word in i["instruction_details"]["argument"]:
                    self._formatter(data=i, severity=severity, rule=rule, rule_info=inspect.getdoc(self.dfa004))

    def dfa005(self):
        """
        Don't use root but use the least privileged user.

        In a Docker container a root user is the same UID as root on the machine, this could be exploited. After doing
        things required by root always switch back to the least privileged user.

        Example of secure instruction:

        ++++++++
        FROM python:3.10.0
        RUN adduser -D appuser && chown -R appuser /app
        USER appuser
        CMD ["python", "main.py"]
        ++++++++

        Example of insecure instruction:
        ++++++++
        FROM python:3.10.0
        CMD ["python", "main.py"]
        ++++++++
        :return:
        """
        rule = inspect.stack()[0][3]
        severity = "ERROR"
        last_user = self.dfp.users[-1]
        if len(self.dfp.users) > 0 and last_user["instruction_details"]["user"].lower() == "root":
            self._formatter(data=last_user, severity=severity, rule=rule, rule_info=inspect.getdoc(self.dfa005))

    def dfa006(self):
        """
        The name of the Dockerfile must be 'Dockerfile' or a pattern of '<purpose>.Dockerfile'

        To ensure contents are recognized as a Dockerfile and correctly rendered in IDE's and version control systems.

        Good:
        - Dockerfile
        - api.Dockerfile
        - dev.Dockerfile
        - api.dev.Dockerfile

        Neutral:
        - Dockerfile.api

        Bad:
        - dockerfile
        - DockerFile
        - Dockerfile1
        - Dockerfile-api
        :return:
        """
        rule = inspect.stack()[0][3]
        severity = "WARNING"
        if self.dockerfile.split(".")[-1] != "Dockerfile":
            self._formatter(rule=rule, data=None, severity=severity, rule_info=inspect.getdoc(self.dfa006))

    def dfa007(self):
        """
        Only use ADD for downloading from a URL or automatically unzipping local files, use COPY for other local files.

        See also: https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#add-or-copy
        :return:
        """
        rule = inspect.stack()[0][3]
        severity = "WARNING"
        for i in self.dfp.adds:
            for source in i["instruction_details"]["source"]:
                # Docker actually checks if a file is compressed regardless of name, but this is a good first step
                if source.startswith("http") is True:
                    pass
                elif source.endswith(".gz") is True:
                    pass
                else:
                    self._formatter(rule=rule, data=i, severity=severity, rule_info=inspect.getdoc(self.dfa007))

    def dfa008(self):
        """
        Chain multiple RUN instructions together to reduce the number of layers and size of the image.
        :return:
        """
        rule = inspect.stack()[0][3]
        severity = "ERROR"
        for i, instruction in enumerate(self.dfp.instructions):
            if instruction == "RUN" and instruction == self.dfp.df_ast[i - 1]["instruction"]:
                self._formatter(rule=rule, severity=severity, data=self.dfp.df_ast[i],
                                rule_info=inspect.getdoc(self.dfa008))

    def dfa009(self):
        """
        Follow correct order to optimize caching
        :return:
        """
        pass

    def dfa010(self):
        """
        Include a healthcheck for long-running or persistent containers.
        :return:
        """
        rule = inspect.stack()[0][3]
        severity = "WARNING"
        if "HEALTHCHECK" not in self.dfp.instructions:
            self._formatter(rule=rule, data=None, severity=severity, rule_info=inspect.getdoc(self.dfa010))

    def dfa011(self):
        """
        CMD or ENTRYPOINT should be the last instruction.
        :return:
        """
        rule = inspect.stack()[0][3]
        severity = "ERROR"

        instructions_past_entrypoint = self.dfp.df_ast[self.dfp.instructions.index("ENTRYPOINT")+1:]
        instructions_past_cmd = self.dfp.df_ast[self.dfp.instructions.index("CMD")+1:]

        for i in instructions_past_entrypoint + instructions_past_cmd:
            if i["instruction"] not in ["CMD", "COMMENT"]:
                self._formatter(rule=rule, severity=severity, data=i, rule_info=inspect.getdoc(self.dfa011))

    def run(self):
        # A bit of a hack to run all the rules
        for f in [i for i, f in inspect.getmembers(object=Analyzer) if i.startswith("dfa")]:
            getattr(Analyzer, f)(self)

        # Print the results
        for i in sorted(set(self.results)):
            print(i)

        # For testing returning the number of warnings and errors, should exit with a code
        return self.warnings, self.errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dockerfile", dest="dockerfile",  required=False, default="fixtures/faulty.Dockerfile",
                        help="Path to Dockerfile location")
    args = parser.parse_args()
    a = Analyzer(dockerfile=args.dockerfile)
    a.run()

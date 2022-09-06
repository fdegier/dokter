import base64
import datetime
import inspect
import json
import os
import time
import uuid

from . import __version__
from .parser import DockerfileParser
from .shellcheck import ShellCheck


class Analyzer:
    def __init__(self, dockerfile: str = None, raw_text: str = None, dockerignore: str = ".dockerignore",
                 verbose: bool = False, explain_rule: str = None, gitlab_codequality: bool = False,
                 gitlab_sast: bool = False, write_df: bool = False, show_df: bool = False,
                 silent: bool = False, **kwargs):
        if dockerfile is not None:
            self.dfp = DockerfileParser(dockerfile=dockerfile, dockerignore=dockerignore)
        elif raw_text is not None:
            self.dfp = DockerfileParser(raw_text=raw_text, dockerignore=dockerignore)
        elif explain_rule is not None:
            self.explain(rule=explain_rule)
        else:
            print("Neither a Dockerfile path nor raw text input were provided")
            exit(1)
        self.dockerfile = dockerfile
        self.raw_text = raw_text
        self.results = []
        self.results_code_climate = []
        self.shellcheck_severity_cc_map = dict(ERROR="blocker", WARNING="major", INFO="minor", STYLE="info")
        self.report = dict(INFO=0, MINOR=0, MAJOR=0, CRITICAL=0, BLOCKER=0)

        self.raw_text = True if raw_text else False
        self.verbose_explanation = verbose
        self.silent = silent
        self.gitlab_codequality = gitlab_codequality
        self.show_dockerfile = show_df
        self.write_dockerfile = write_df
        self.shellcheck = ShellCheck()
        self.kwargs = kwargs
        self.gitlab_sast = gitlab_sast
        self.gitlab_sast_severity_map = {
            "INFO": "Info",
            "MINOR": "Low",
            "MAJOR": "High",
            "CRITICAL": "Critical",
            "BLOCKER": "Critical"
        }
        self.gitlab_security_scanner = {
            "version": "14.0.4",
            "vulnerabilities": [],
            "remediations": [],
            "scan": {
                "analyzer":
                    {
                        "id": "dokter",
                        "name": "Dokter",
                        "url": "https://gitlab.com/gitlab-org/incubation-engineering/ai-assist/dokter",
                        "vendor":
                            {
                                "name": "GitLab"
                            },
                        "version": "0.0.0" if __version__ == "dev" else __version__
                    },
                "scanner":
                    {
                        "id": "dokter",
                        "name": "Dokter",
                        "url": "https://gitlab.com/gitlab-org/incubation-engineering/ai-assist/dokter",
                        "vendor":
                            {
                                "name": "GitLab"
                            },
                        "version": "0.0.0" if __version__ == "dev" else __version__
                    },
                "type": "sast",
                "start_time": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "end_time": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "status": "success"
            }
        }

    def _patch_maker(self, data):
        if "_raw" not in data:
            return ""
        start_line = data["line_number"]["start"]
        no_lines = data["line_number"]["end"] - start_line
        if no_lines > 0:
            end_line_offset = f",{no_lines}"
        else:
            end_line_offset = ""

        patch_base = f"diff --git a/{self.dockerfile} b/{self.dockerfile}\n" \
                     f"index 5d311b9..a3f6959 100644\n" \
                     f"@@ -{start_line}{end_line_offset} +{start_line}{end_line_offset} @@\n"

        for i in ['-' + i for i in data['_raw'].replace("\\", "\\ \n").split(" \n")]:
            patch_base += f"{i}\n"
        for i in ['+' + i for i in data['formatted'].splitlines()]:
            patch_base += f"{i}\n"
        return str(base64.b64encode(patch_base.encode("ascii")), 'ascii')

    def _formatter(self, rule: str, data: dict, severity: str, rule_info: str, categories: list = None,
                   autocorrect: bool = False):
        cc_entry = {
            "location": {
                "lines": {
                    "begin": data["line_number"]["start"],
                    "end": data["line_number"]["end"]
                },
                "path": self.dockerfile
            },
            "severity": severity,
            "type": "issue",
            "categories": categories,
            "check_name": rule.upper(),
            "description": rule_info.splitlines()[0]
        }
        self.results_code_climate.append(cc_entry)
        cve = ""
        gss_entry_id = str(uuid.uuid4())
        gss_entry = {
            "id": gss_entry_id,
            "category": "sast",
            "message": f'{rule_info.splitlines()[0]}',
            "description": rule_info.split(":return:", 1)[0],
            "cve": cve,
            "severity": self.gitlab_sast_severity_map.get(severity.upper(), "Unknown"),
            "scanner": dict(id="dokter", name="Dokter"),
            "location":
                {
                    "file": self.dockerfile,
                    "start_line": data["line_number"]["start"],
                    "end_line": data["line_number"]["end"]
                },
            "identifiers": [dict(type="dokter_id", name=rule.upper(), value=gss_entry_id,
                                 url=f"https://gitlab.com/gitlab-org/incubation-engineering/ai-assist"
                                     f"/dokter/-/blob/main/docs/{rule.lower()}.md")]
        }

        self.gitlab_security_scanner["vulnerabilities"].append(gss_entry)

        if autocorrect:
            gss_entry_remediation = {
                "fixes": [
                    {
                        "id": gss_entry_id,
                        "cve": cve,
                    }
                ],
                "summary": rule_info.splitlines()[0],
                "diff": self._patch_maker(data=data)
            }
            self.gitlab_security_scanner["remediations"].append(gss_entry_remediation)

        if self.verbose_explanation is True:
            rule_info = f"\n{rule_info.split(':return:', 1)[0]}"
        else:
            rule_info = rule_info.splitlines()[0]

        self.results.append(f"{self.dockerfile}:{data['line_number']['start']:<3} - {rule.upper()} "
                            f"- {severity.upper():<7} - {rule_info}")

        self.report[severity.upper()] += 1

    def _return_results(self) -> dict:
        return self.report

    def dfa000(self):
        """
        Violation of Shellcheck rule

        Autocorrect: True
        :return:
        """
        autocorrect = True
        categories = ["Style"]
        for i in self.dfp.runs:
            sc_results = self.shellcheck.check(
                shell_command=f'{i["instruction_details"]["executable"]} {i["instruction_details"]["arguments"]}'
            )
            for result in sc_results:
                rule = result["sc_rule"]
                if result["fixed_line"] is not None:
                    corrected = i["_raw"].replace(result["wrong_line"], result["fixed_line"])
                    i["formatted"] = self.dfp.format_and_correct_sh(instruction=i["instruction"], raw_command=corrected,
                                                                    raw_line=i["_raw"])

                severity = self.shellcheck_severity_cc_map.get(result["severity"].upper(), "info")
                self._formatter(rule=rule, severity=severity, data=i, rule_info=f'Shellcheck: {result["sc_rule_desc"]}',
                                categories=categories, autocorrect=autocorrect)

    def dfa001(self):
        """
        Verify that no credentials are leaking by copying in sensitive files.

        Examples include: copying over a .env file, SSH private keys, settings files etc.

        Autocorrect: False
        :return:
        """
        autocorrect = False
        rule = inspect.stack()[0][3]
        severity = "critical"
        categories = ["Security"]
        sensitive_files = [
            ".env", ".pem", ".properties"
                            "settings", "config", "secrets", "application", "dev", "appsettings", "credentials",
            "default", "strings",
            "environment"
        ]

        for word in sensitive_files:
            for i in self.dfp.copies:
                for source in i["instruction_details"]["source"]:
                    if word in source.lower() or word in i["instruction_details"]["target"].lower():
                        self._formatter(rule=rule, data=i, severity=severity, categories=categories,
                                        rule_info=inspect.getdoc(self.dfa001), autocorrect=autocorrect)

    def dfa002(self):
        """
        Use a .dockerignore file to exclude files being copied over.

        By using a .dockerignore files, the build will generally be faster because it has to transfer less data to the
        daemon, it also helps prevent copying sensitive files. For more information see:
        https://docs.docker.com/engine/reference/builder/#dockerignore-file

        Autocorrect: False
        :return:
        """
        autocorrect = True
        rule = inspect.stack()[0][3]
        severity = "info"
        categories = ["Security"]
        if len(self.dfp.docker_ignore_files) == 0:
            data = {"line_number": {"start": 0, "end": 0}}
            self._formatter(data=data, rule=rule, severity=severity, rule_info=inspect.getdoc(self.dfa002),
                            categories=categories, autocorrect=autocorrect)

    def dfa003(self):
        """
        When using "COPY . <target>" make sure to have a .dockerignore file. Best to copy specific folders.

        By using a .dockerignore files, the build will generally be faster because it has to transfer less data to the
        daemon, it also helps prevent copying sensitive files. For more information see:
        https://docs.docker.com/engine/reference/builder/#dockerignore-file

        Example of secure instruction:

        ```
        COPY src /app/src
        COPY requirements.txt /app/
        ```

        Example of insecure instruction:
        ```
        COPY . /app
        ```

        Autocorrect: False
        :return:
        """
        autocorrect = False
        rule = inspect.stack()[0][3]
        severity = "major"
        categories = ["Security"]
        for i in self.dfp.copies:
            for source in i["instruction_details"]["source"]:
                if source == ".":
                    self._formatter(rule=rule, data=i, severity=severity, rule_info=inspect.getdoc(self.dfa003),
                                    categories=categories, autocorrect=autocorrect)

    def dfa004(self):
        """
        Verify that build args doesn't contain sensitive information, use secret mounts instead.

        Build args are stored in the history of the docker image and can be retrieved. Secret mounts are not persisted
        and are therefor a better option if you temporarily need sensitive information to build your image. If sensitive
        information is required during runtime of the containers, use environment variables.

        Example of secure instruction:

        ```
        RUN --mount=type=secret,id=docker_token docker login -u user -p $(cat /run/secrets/docker_token)
        ```

        Example of insecure instruction:
        ```
        ARG TOKEN
        RUN docker login -u user -p $TOKEN
        ```

        Autocorrect: False
        :return:
        """
        autocorrect = False
        rule = inspect.stack()[0][3]
        severity = "critical"
        categories = ["Security"]

        sensitive_words = [
            "key", "secret", "token", "pass"
        ]

        for word in sensitive_words:
            for i in self.dfp.args:
                if word.lower() in i["instruction_details"]["argument"].lower():
                    self._formatter(data=i, severity=severity, rule=rule, rule_info=inspect.getdoc(self.dfa004),
                                    categories=categories, autocorrect=autocorrect)

    def dfa005(self):
        """
        Don't use root but use the least privileged user.

        In a Docker container a root user is the same UID as root on the machine, this could be exploited. After doing
        things required by root always switch back to the least privileged user.

        Example of secure instruction:

        ```
        FROM python:3.10.0
        RUN useradd -D appuser && chown -R appuser /app
        USER appuser
        CMD ["python", "main.py"]
        ```

        Example of insecure instruction:
        ```
        FROM python:3.10.0
        CMD ["python", "main.py"]
        ```

        Autocorrect: True
        :return:
        """
        autocorrect = True
        rule = inspect.stack()[0][3]
        severity = "major"
        categories = ["Security"]
        if len(self.dfp.users) > 0:
            last_user = self.dfp.users[-1]
            if len(self.dfp.users) > 0 and last_user["instruction_details"]["user"].lower() == "root":
                self._formatter(data=last_user, severity=severity, rule=rule, rule_info=inspect.getdoc(self.dfa005),
                                categories=categories, autocorrect=autocorrect)
                workdir = "/app" if len(self.dfp.workdirs) == 0 else \
                    self.dfp.workdirs[-1]["instruction_details"]["workdir"]
                last_user["formatted"] = f"WORKDIR {workdir}\nRUN useradd -M appuser &&" \
                                         f" chown -R appuser {workdir}\nUSER appuser\n"

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

        Autocorrect: False
        :return:
        """
        autocorrect = False
        rule = inspect.stack()[0][3]
        severity = "minor"
        categories = ["Style"]
        if os.path.basename(self.dockerfile).split(".")[-1] != "Dockerfile":
            data = {"line_number": {"start": 0, "end": 0}}
            self._formatter(rule=rule, data=data, severity=severity, rule_info=inspect.getdoc(self.dfa006),
                            categories=categories, autocorrect=autocorrect)

    def dfa007(self):
        """
        Only use ADD for downloading from a URL or automatically unzipping local files, use COPY for other local files.

        See also: https://docs.docker.com/develop/develop-images/dockerfile_best-practices/#add-or-copy

        Autocorrect: True
        :return:
        """
        autocorrect = True
        rule = inspect.stack()[0][3]
        severity = "minor"
        categories = ["Bug Risk"]
        for i in self.dfp.adds:
            for source in i["instruction_details"]["source"]:
                # Docker actually checks if a file is compressed regardless of name, but this is a good first step
                if source.startswith("http") is True:
                    pass
                elif source.endswith(".gz") is True:
                    pass
                else:
                    self._formatter(rule=rule, data=i, severity=severity, rule_info=inspect.getdoc(self.dfa007),
                                    categories=categories, autocorrect=autocorrect)
                    i["formatted"] = i["formatted"].replace("ADD ", "COPY ")

    def dfa008(self):
        """
        Chain multiple RUN instructions together to reduce the number of layers and size of the image.

        Autocorrect: True
        :return:
        """
        autocorrect = True
        rule = inspect.stack()[0][3]
        severity = "major"
        categories = ["Performance"]
        first_run = None
        for i, instruction in enumerate(self.dfp.instructions):
            if instruction == "RUN" and instruction == self.dfp.df_ast[i - 1]["instruction"]:
                self._formatter(rule=rule, severity=severity, data=self.dfp.df_ast[i], categories=categories,
                                rule_info=inspect.getdoc(self.dfa008), autocorrect=autocorrect)
                if first_run is None:
                    first_run = self.dfp.df_ast[i - 1]
                corrected = self.dfp.df_ast[i]['formatted'].replace(f"{self.dfp.df_ast[i]['instruction']} ", '')
                first_run["formatted"] = first_run["formatted"][:-1] + " && \\\n" + "\t" + corrected
                # Delete the unneeded RUN statement
                del self.dfp.df_ast[i]["formatted"]

    def dfa009(self):
        """
        To be added: Follow correct order to optimize caching.
        :return:
        """
        pass

    def dfa010(self):
        """
        Include a healthcheck for long-running or persistent containers.

        Autocorrect: False
        :return:
        """
        autocorrect = False
        rule = inspect.stack()[0][3]
        severity = "info"
        categories = ["Performance"]
        if "HEALTHCHECK" not in self.dfp.instructions:
            data = {"line_number": {"start": 0, "end": 0}}
            self._formatter(rule=rule, data=data, severity=severity, rule_info=inspect.getdoc(self.dfa010),
                            categories=categories, autocorrect=autocorrect)

    def dfa011(self):
        """
        CMD or ENTRYPOINT should be the last instruction.
        :return:
        """
        autocorrect = False
        rule = inspect.stack()[0][3]
        severity = "major"
        categories = ["Style"]

        # Check if multi-stage
        df_ast = self.dfp.df_ast
        dfp_instructions = self.dfp.instructions
        froms = [(n, i) for n, i in enumerate(self.dfp.instructions) if i == "FROM"]
        if len(froms) > 1:
            multi_stage_offset = froms[-1][0]
            dfp_instructions = self.dfp.instructions[multi_stage_offset:]
            df_ast = self.dfp.df_ast[multi_stage_offset:]

        instructions_past_entrypoint = []
        if "ENTRYPOINT" in dfp_instructions:
            instructions_past_entrypoint = df_ast[dfp_instructions.index("ENTRYPOINT") + 1:]

        instructions_past_cmd = []
        if "CMD" in dfp_instructions:
            instructions_past_cmd = df_ast[dfp_instructions.index("CMD") + 1:]

        for i in instructions_past_entrypoint + instructions_past_cmd:
            if i["instruction"] not in ["CMD", "COMMENT"]:
                self._formatter(rule=rule, severity=severity, data=i, rule_info=inspect.getdoc(self.dfa011),
                                categories=categories, autocorrect=autocorrect)

    def dfa012(self):
        """
        MAINTAINER is deprecated, use LABEL instead.

        Incorrect:
        ```
        MAINTAINER dev@someproject.org
        ```

        Correct:
        ```
        LABEL maintainer="dev@someproject.org"
        ```

        Autocorrect: True
        :return:
        """
        autocorrect = True
        rule = inspect.stack()[0][3]
        severity = "major"
        categories = ["Style"]
        if len(self.dfp.maintainers) > 0:
            for i in self.dfp.maintainers:
                self._formatter(rule=rule, severity=severity, data=i, rule_info=inspect.getdoc(self.dfa012),
                                categories=categories, autocorrect=autocorrect)
                i["formatted"] = i["formatted"].replace("MAINTAINER ", "LABEL maintainer=")

    @staticmethod
    def _write_file(location, data):
        with open(location, "w") as f:
            f.write(data)

    def formatter(self):
        a = [i for i in self.dfp.df_ast if i.get("formatted") is not None]
        data = ""
        for line, instruction in enumerate(a):
            next_instruction = self.shellcheck.get_index(li=a, index=line, offset=1)
            curr_instruction = instruction["instruction"]
            if curr_instruction == "COMMENT":
                data += instruction['formatted']
            elif next_instruction is not None:
                if curr_instruction != next_instruction["instruction"]:
                    data += f"{instruction['formatted']}\n"
                else:
                    data += instruction['formatted']
            else:
                data += f"{instruction['formatted']}\n"
        return data

    def run(self):
        # A bit of a hack to run all the rules
        for f in [i for i, f in inspect.getmembers(object=Analyzer) if i.startswith("dfa")]:
            getattr(Analyzer, f)(self)

        # Print the results
        if self.silent is False:
            for i in sorted(set(self.results)):
                print(i)

        if self.gitlab_codequality:
            report_location = f"dokter-{os.environ.get('CI_COMMIT_SHA', int(time.time()))}.json"
            self._write_file(location=report_location, data=json.dumps(self.results_code_climate))
            print(f"\nCode Quality report written to: {report_location}")

        if self.gitlab_sast:
            self.gitlab_security_scanner["end_time"] = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            report_location = f"dokter-sast-{os.environ.get('CI_COMMIT_SHA', int(time.time()))}.json"
            self._write_file(location=report_location, data=json.dumps(self.gitlab_security_scanner))
            print(f"\nSAST report written to: {report_location}")

        new_dockerfile = self.formatter()

        if self.write_dockerfile:
            report_location = "Dockerfile"
            if self.dockerfile is not None:
                report_location = self.dockerfile
            self._write_file(location=report_location, data=new_dockerfile)
            print(f"\nNew Dockerfile written to: {report_location}")

        if self.show_dockerfile:
            print("This is the new Dockerfile:\n")
            print(new_dockerfile)

        return self.report

    @staticmethod
    def explain(rule):
        try:
            out = f"Explanation for rule '{rule}':\n{getattr(Analyzer, rule.lower()).__doc__.split(':return:', 1)[0]}"
        except AttributeError:
            out = "Rule does not exists"
        print(out)
        return out

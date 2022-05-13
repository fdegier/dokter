import argparse

from src.parser import DockerfileParser


class Analyzer:
    def __init__(self, dockerfile: str = None, raw_text: str = None):
        if dockerfile is not None:
            self.dfp = DockerfileParser(dockerfile=dockerfile)
        elif raw_text is not None:
            self.dfp = DockerfileParser(raw_text=raw_text)
        else:
            raise TypeError("Neither a Dockerfile path nor raw text input were provided")
        self.dockerfile = dockerfile
        self.results = []
        self.errors = 0
        self.warnings = 0

        self.raw_text = True if raw_text else False

    def _formatter(self, data, severity, rule_info):
        print(f"{self.dockerfile}:{data['line_number']['start']} - {severity.upper()} - {rule_info}")
        if severity.upper() == "ERROR":
            self.errors += 1
        elif severity.upper() == "WARNING":
            self.warnings += 1

    def rule_1(self):
        """
        Verify that no credentials are leaking
        :return:
        """
        sensitive_files = [
            ".env", ".pem", ".properties"
            "settings", "config", "secrets", "application", "dev", "appsettings", "credentials", "default", "strings",
            "environment"
        ]

        for word in sensitive_files:
            for i in self.dfp.copies:
                for source in i["instruction_details"]["source"]:
                    if word in source:
                        self._formatter(data=i, severity="ERROR",
                                        rule_info="Error, make sure to not copy sensitive information")

    def rule_2(self):
        """
        Verify that build args doesn't contain sensitive information
        :return:
        """
        sensitive_words = [
            "key", "secret", "token", "pass"
        ]

        for word in sensitive_words:
            for i in self.dfp.args:
                if word in i["instruction_details"]["argument"]:
                    self._formatter(data=i, severity="ERROR",
                                    rule_info="Error, make sure that a build arg does not contain secrets")

    def rule_3(self):
        """
        Verify that last user is not root
        :return:
        """
        if len(self.dfp.users) > 0 and self.dfp.users[-1]["instruction_details"]["user"].lower() == "root":
            self._formatter(data=self.dfp.users[-1], severity="ERROR",
                            rule_info="Error, make sure the last user is not root")

    def run(self):
        self.rule_1()
        self.rule_2()
        self.rule_3()
        return self.warnings, self.errors


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--dockerfile", dest="dockerfile",  required=False, default="fixtures/faulty.Dockerfile",
                        help="Path to Dockerfile location")
    args = parser.parse_args()
    a = Analyzer(dockerfile=args.dockerfile)
    a.run()

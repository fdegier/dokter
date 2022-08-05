import os
import re
import subprocess


class ShellCheck:
    def __init__(self):
        self.tmp_file = "tmp.sh"
        self.sc_rule_pattern = "SC[0-9]{4}"
        self.sc_severity_pattern = "(info)|(error)|(warning)|(style)"

    def _write_to_file(self, command):
        with open(self.tmp_file, 'w') as f:
            f.write(command)

    @staticmethod
    def get_index(li: list, index: [int, str], offset: int = 0):
        if isinstance(index, int):
            try:
                index = (index + offset) if index >= 0 else 0
                return li[index]
            except IndexError:
                return None
        elif isinstance(index, str):
            try:
                index = (li.index(index) + offset) if li.index(index) > 0 else 0
                return li[index]
            except ValueError:
                return None

    def check(self, shell_command: str, shell: str = "sh"):
        output = []
        self._write_to_file(command=shell_command)

        cmd = ["shellcheck", "-s", shell, self.tmp_file]
        try:
            raw_output = [i for i in subprocess.run(cmd, stderr=subprocess.STDOUT,
                                                    stdout=subprocess.PIPE).stdout.decode("utf-8").splitlines()
                          if i != ""]
        except Exception as E:
            print(f"Error: {E}")
            raw_output = []
        finally:
            os.remove(self.tmp_file)
        if len(raw_output) == 0:
            return output
        raw_output = raw_output[:raw_output.index("For more information:")]
        blobs = [raw_output.index(i) for i in raw_output if i.startswith(f"In {self.tmp_file} line")]
        for i, x in enumerate(blobs):
            start_index = x
            end_index = self.get_index(li=blobs, index=i+1)
            y = raw_output[start_index:end_index]
            output.append(
                {
                    "line_number": y[0].split(" line ", 1)[1],
                    "severity": re.search(pattern=self.sc_severity_pattern, string=y[2]).group(),
                    "sc_rule": re.search(pattern=self.sc_rule_pattern, string=y[2]).group(),
                    "wrong_line": y[1],
                    "fixed_line": self.get_index(li=y, index="Did you mean: ", offset=1)
                }
            )
        return output

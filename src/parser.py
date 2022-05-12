import ast
import os


class DockerfileParser:
    def __init__(self, dockerfile: str = None, raw_text: str = None):
        self.valid_instructions = ["#", "COMMENT", "FROM", "COPY", "ADD", "WORKDIR", "EXPOSE", "USER", "ARG", "ENV",
                                   "LABEL", "RUN", "CMD", "ENTRYPOINT", "ONBUILD", "HEALTHCHECK", "STOPSIGNAL",
                                   "VOLUME", "SHELL"]
        if dockerfile is not None:
            self.df_content = self._read_dockerfile(path=dockerfile)
        elif raw_text is not None:
            self.df_content = raw_text.splitlines()
        else:
            raise TypeError("Neither a Dockerfile path nor raw text input were provided")

        self.df_ast = self.parse_dockerfile()

    @staticmethod
    def _read_dockerfile(path: str) -> list:
        if os.path.exists(path):
            with open(path, 'r') as f:
                data = f.read().splitlines()
            return data
        else:
            raise FileNotFoundError(f"Dockerfile not found, path: {path}")

    def _get_state(self, line: str) -> str:
        if line == "":
            state = "blank"
        elif line.startswith("#"):
            state = "comment"
        elif line.split(" ", 1)[0] in self.valid_instructions and line.endswith("\\"):
            state = "new_multi_line_command"
        elif line.endswith("\\"):
            state = "continued_multi_line_command"
        elif not line.endswith("\\") and line.split(" ", 1)[0] not in self.valid_instructions:
            state = "end_multi_line_command"
        else:
            state = "new_command"
        return state

    @staticmethod
    def _get_instruction(line: str) -> [str, None]:
        if line != "":
            if line.startswith("#"):
                instruction = "COMMENT"
            else:
                instruction = line.split(" ", 1)[0]
            return instruction
        return None

    @staticmethod
    def _get_raw_command(line: str) -> [str, None]:
        if line.startswith("#"):
            return line.split("#", 1)[1]
        elif line != "":
            return line.split(" ", 1)[1]
        return None

    @staticmethod
    def _parse_json_notation(command: str) -> dict:
        try:
            run_eval = ast.literal_eval(command)
        except (SyntaxError, ValueError):
            run_eval = command
        if isinstance(run_eval, list):
            return dict(executable=run_eval[0], arguments=run_eval[1:])
        else:
            run_split = command.split(" ", 1)
            if len(run_split) == 1:
                return dict(executable=run_split[0], arguments=[])
            return dict(executable=run_split[0], arguments=run_split[1])

    def _parse_command(self, instruction: str, command: str) -> dict:
        if instruction == "COMMENT":
            return dict(comment=command.strip())
        elif instruction == "FROM":
            if ":" in command:
                image_split = command.split(":")
                return dict(image=image_split[0], version=image_split[1])
            else:
                return dict(image=command)
        elif instruction in ["COPY", "ADD"]:
            copy_split = command.split(" ")
            copy_dict = {}
            if copy_split[0].startswith("--chown"):
                copy_dict["chown"] = copy_split[0].split("=", 1)[1]
                copy_dict["source"] = copy_split[1]
                copy_dict["target"] = copy_split[2]
            elif len(copy_split) > 2:
                copy_dict["source"] = copy_split[:-1]
                copy_dict["target"] = copy_split[-1]
            else:
                copy_dict["source"] = copy_split[0]
                copy_dict["target"] = copy_split[1]
            return copy_dict
        elif instruction == "USER":
            if ":" in command:
                user_split = command.split(":")
                return dict(user=user_split[0], group=user_split[1])
            else:
                return dict(user=command)
        elif instruction == "ARG":
            if "=" in command:
                arg_split = command.split("=")
                return dict(argument=arg_split[0], default_value=arg_split[1])
            else:
                return dict(argument=command)
        elif instruction == "ENV":
            if "=" in command:
                env_split = command.split("=")
                return dict(environment_variable=env_split[0], default_value=env_split[1])
            elif " " in command:
                env_split = command.split(" ")
                return dict(environment_variable=env_split[0], default_value=env_split[1])
            else:
                return dict(environment_variable=command)
        elif instruction == "LABEL":
            if len(command.split("=")) > 2:
                return dict(raw_labels=command)
            else:
                command_split = command.split("=")
                return dict(key=command_split[0], value=command_split[1].strip("'").strip('"'))
        elif instruction in ["RUN", "ENTRYPOINT", "CMD", "SHELL"]:
            return self._parse_json_notation(command=command)
        elif instruction == "EXPOSE":
            if "/" in command:
                expose_split = command.split("/")
                return dict(port=expose_split[0], protocol=expose_split[1])
            return dict(port=command)
        elif instruction in ["WORKDIR", "STOPSIGNAL", "VOLUME"]:
            return {instruction.lower(): command}
        elif instruction in ["HEALTHCHECK", "ONBUILD"]:
            command_split = command.replace(instruction, "").strip()
            command_split = self._parse_json_notation(command=command_split)
            return {
                "sub_instruction": command_split['executable'],
                **self._parse_json_notation(command=command_split['arguments'])
            }
        else:
            raise NotImplementedError(f"Instruction is not implemented: {instruction}")

    @staticmethod
    def _concat_multi_line_instruction(lines: list) -> str:
        single_line = ""
        for i in lines:
            single_line += i["raw_command"]
        # TODO: Not sure if this is needed?
        # single_line.replace("\\", "")

        lines[0]["state"] = "multi_line_command"
        lines[0]["line_number"]["end"] = max([i["line_number"]["start"] for i in lines])
        lines[0]["raw_command"] = single_line
        return lines[0]

    def split_multi_lines(self, lines: list) -> list:
        result = []
        start_index = 0
        for i, x in enumerate(lines):
            if x["state"] == "end_multi_line_command":
                result.append(self._concat_multi_line_instruction(lines=lines[start_index:i + 1]))
                start_index = i+1
        return result

    def parse_dockerfile(self) -> list[dict]:
        parsed = [{"line_number": dict(start=line_number + 1),
                   "raw_line": i,
                   "state": self._get_state(line=i),
                   "instruction": self._get_instruction(line=i),
                   "raw_command": self._get_raw_command(line=i)
                   }
                  for line_number, i in enumerate(self.df_content)]

        multi_line_instructions = self.split_multi_lines([i for i in parsed if "_multi_line_" in i["state"]])
        single_line_instructions = sorted(
            [i for i in parsed if i["state"] in ["new_command", "comment"]] + multi_line_instructions,
            key=lambda d: d['line_number']['start']
        )

        enriched = [dict(
                         line_number=i["line_number"],
                         instruction=i["instruction"],
                         instruction_details=self._parse_command(instruction=i["instruction"],
                                                                 command=i["raw_command"]),
                         _raw=i["raw_line"]
                         )
                    for i in single_line_instructions]
        return enriched

    def _get_instructions(self, instruction: str) -> list[dict]:
        return [i for i in self.df_ast if i["instruction"] == instruction]

    @property
    def users(self) -> list[dict]:
        return self._get_instructions(instruction="USER")

    @property
    def froms(self) -> list[dict]:
        return self._get_instructions(instruction="FROM")

    @property
    def instructions(self) -> list[dict]:
        return [i["instruction"] for i in self.df_ast]

    @property
    def copies(self) -> list[dict]:
        return self._get_instructions(instruction="COPY")

    @property
    def adds(self) -> list[dict]:
        return self._get_instructions(instruction="ADD")

    @property
    def comments(self) -> list[dict]:
        return self._get_instructions(instruction="COMMENT")

    @property
    def args(self) -> list[dict]:
        return self._get_instructions(instruction="ARG")

    @property
    def envs(self) -> list[dict]:
        return self._get_instructions(instruction="ENV")

    @property
    def labels(self) -> list[dict]:
        return self._get_instructions(instruction="LABEL")

    @property
    def runs(self) -> list[dict]:
        return self._get_instructions(instruction="RUN")

    @property
    def entrypoints(self) -> list[dict]:
        return self._get_instructions(instruction="ENTRYPOINT")

    @property
    def cmds(self) -> list[dict]:
        return self._get_instructions(instruction="CMD")

    @property
    def shells(self) -> list[dict]:
        return self._get_instructions(instruction="SHELL")

    @property
    def exposes(self) -> list[dict]:
        return self._get_instructions(instruction="EXPOSE")

    @property
    def workdirs(self) -> list[dict]:
        return self._get_instructions(instruction="WORKDIR")

    @property
    def stopsignals(self) -> list[dict]:
        return self._get_instructions(instruction="STOPSIGNAL")

    @property
    def volumes(self) -> list[dict]:
        return self._get_instructions(instruction="VOLUME")

    @property
    def healthchecks(self) -> list[dict]:
        return self._get_instructions(instruction="HEALTHCHECK")

    @property
    def onbuilds(self) -> list[dict]:
        return self._get_instructions(instruction="ONBUILD")


if __name__ == "__main__":
    parser = DockerfileParser(dockerfile="fixtures/Dockerfile")

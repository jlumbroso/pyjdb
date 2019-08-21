import typing as _typ

import pexpect as _pexpect

from . import helpers as _helpers


class JdbProcess(object):
    def __init__(self, class_name, class_path=None, entry_method="main"):
        self.pty = None
        self.class_name = class_name
        self.class_path = class_path
        self.entry_method = entry_method

    @property
    def active(self) -> bool:
        """
        Provides whether the `JdbProcess` is active. If it is not, it must be
        reset using the `spawn` method.

        :return: A `Boolean` representing the status of the `JdbProcess`.
        """

        return not (self.pty is None or self.pty.closed or self.pty.eof())

    def _build_jdb_call(self, args: _typ.Optional[_typ.AnyStr] = None) -> str:
        """

        :param args:
        :return:
        """

        # The command name
        cmd = [_helpers.JDB_NAME]

        # The classpath
        if self.class_path is not None:
            cmd.append("-classpath")
            cmd.append(":".join(self.class_path))

        # The class name
        cmd.append(self.class_name)

        # Optional args
        if args is not None and args != "":
            cmd.append(args)

        return " ".join(cmd)

    def spawn(self, args: _typ.Optional[str] = None) -> _typ.NoReturn:
        """

        :param args:
        :return:
        """

        # noinspection PyBroadException
        try:
            self.pty.close()
        except:
            pass

        self.pty = _pexpect.spawnu(self._build_jdb_call(args=args))

        self.pty.sendline(
            "stop in {class_name}.{entry_method}".format(
                class_name=self.class_name, entry_method=self.entry_method
            )
        )

        self.pty.expect(".*Deferring breakpoint.*")
        self.pty.sendline("run")
        self.pty.expect(".*Breakpoint hit:")

        # Run dummy method to clear
        self.locals()

    def step(self, modifier=" in") -> _typ.NoReturn:
        """

        :return:
        """

        if not self.active:
            return None

        # Make a step
        self.pty.sendline("step{}".format(modifier))

    def locals(
        self
    ) -> _typ.Optional[_typ.Tuple[_typ.Dict[str, _typ.Any], _typ.Dict[str, _typ.Any]]]:
        """

        :return:
        """

        if not self.active:
            return None

        # Print out all local variables
        self.pty.sendline("locals")

        # Expect the variables from method arguments
        self.pty.expect("Method arguments:")

        # Expect the variables locally declared
        self.pty.expect("Local variables:")

        raw_str_args = self.pty.before

        # Seek forward to prompt
        self.pty.expect(r".*\[.*\] ")

        raw_str_locals = self.pty.after

        # Parse the strings
        args = _helpers.parse_jdb_values(raw_str_args)
        local = _helpers.parse_jdb_values(raw_str_locals)

        return args, local

    def dump(self, obj: str) -> _typ.Optional[str]:
        if not self.active:
            return None

        # First get a prompt
        self.pty.sendline("")
        self.pty.expect(r".*\[.*\] ")
        rawstr_prompt = self.pty.after.strip()

        # Escape prompt
        esc_prompt = rawstr_prompt
        esc_prompt = esc_prompt.replace("[", r"\[")
        esc_prompt = esc_prompt.replace("]", r"\]")

        # Send command
        self.pty.sendline("dump {}".format(obj))

        # Expect output
        pattern = "{obj} = .*{prompt}".format(obj=obj, prompt=esc_prompt)
        self.pty.expect(pattern)

        # Parse output
        ret = self.pty.after

        # - remove last line break and prompt that follows
        last_line_break = ret.rfind("\n")
        ret = ret[:last_line_break].strip()

        # - remove obj name and equal sign
        ret = ret.replace("{} =".format(obj), "").strip()

        # Parse the value
        parsed_ret = _helpers.parse_jdb_value(ret)

        return parsed_ret

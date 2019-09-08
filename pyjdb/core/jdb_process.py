import typing as _typ

import pexpect as _pexpect

from pyjdb.core import helpers as _helpers, exceptions as _exceptions


class JdbProcess(object):
    def __init__(self, class_name, class_path=None, entry_method="main", exclude_classes=None):
        self.pty = None
        self.target = None
        self.class_name = class_name
        self.class_path = class_path
        self.entry_method = entry_method
        self.trace = None
        self.trace_max = 10000
        self.exclude_classes = exclude_classes

    @property
    def active(self) -> bool:
        """
        Provides whether the `JdbProcess` is active. If it is not, it must be
        reset using the `spawn` method.

        :return: A `Boolean` representing the status of the `JdbProcess`.
        """

        return not (self.pty is None or self.pty.closed or self.pty.eof())

    def _build_call_base(
            self,
            args: _typ.Optional[_typ.Union[_typ.AnyStr, list]] = None,
            launch_class: bool = True,
            base_name: _typ.Union[str, _typ.List[str]] = _helpers.JDB_NAME
    ) -> str:

        # The command name
        if type(base_name) is list:
            cmd = base_name[:]
        else:
            cmd = [base_name]

        if launch_class:
            # Build the classpath
            if self.class_path is not None:
                cmd.append("-classpath")

                if type(self.class_path) is list:
                    # Specified as list
                    cp = self.class_path[:]
                    if "." not in cp:
                        cp = ["."] + cp
                    cmd.append(":".join(cp))
                else:
                    # Specified as str
                    cp = self.class_path[:]
                    if not (".:" in cp or ":." in cp):
                        cp = ".:{}".format(cp)
                    cmd.append(cp)

            # The class name
            cmd.append(self.class_name)

        # Optional args
        if args is not None and args != "":
            if type(args) is list:
                cmd += args
            else:
                cmd.append(args)

        return " ".join(cmd)

    def _build_jdb_call(
            self,
            args: _typ.Optional[_typ.AnyStr] = None,
            port: _typ.Optional[int] = None
    ) -> str:
        """

        :param args:
        :return:
        """

        if port is not None:
            return self._build_call_base(
                args=["-attach", "{}".format(port)],
                base_name=_helpers.JDB_NAME,
                launch_class=False,
            )
        else:
            return self._build_call_base(
                args=args,
                base_name=_helpers.JDB_NAME,
                launch_class=True,
            )

    def _build_java_call(
            self,
            port: int,
            args: _typ.Optional[_typ.AnyStr] = None,
    ) -> str:
        """

        :param args:
        :return:
        """

        # The command name
        base_cmd = _helpers.JAVA_DEBUG_CMD.format(port=port).split()

        return self._build_call_base(
            args=args,
            base_name=base_cmd,
            launch_class=True,
        )

    def close(self):
        if self.pty is not None:
            # noinspection PyBroadException
            try:
                self.pty.close()
            except:
                pass

        if self.target is not None:
            # noinspection PyBroadException
            try:
                self.target.close()
            except:
                pass
            finally:
                self.target = None

    def spawn(self, args: _typ.Optional[str] = None, capture_target=False) -> _typ.NoReturn:
        """

        :param args:
        :return:
        """

        # In case we have a live process going: Terminate it
        self.close()

        if capture_target:
            # Pick a port
            port = 8899

            # Launch the class separately on a port
            self.target = _pexpect.spawnu(self._build_java_call(args=args, port=port))
            self.target.expect("Listening[^:]*: \d+")

            # Connect JDB
            self.pty = _pexpect.spawnu(self._build_jdb_call(port=port))
        else:
            # Launch the class through JDB
            self.pty = _pexpect.spawnu(self._build_jdb_call(args=args))

        self.pty.sendline(
            "stop in {class_name}.{entry_method}".format(
                class_name=self.class_name, entry_method=self.entry_method
            )
        )

        self.pty.expect(".*Deferring breakpoint.*")
        self.pty.sendline("run")
        self.pty.expect(".*Breakpoint hit:")

        # Activate precise tracing information:
        # - exclude standard library from events
        exclude_list = _helpers.JDB_DEFAULT_EXCLUDED[:] + [""]
        if self.exclude_classes is not None:
            exclude_list = exclude_list + self.exclude_classes
        self.pty.sendline("exclude {}".format(",".join(exclude_list)))
        # - provide information on methods being entered, exited (and return value)
        self.pty.sendline("trace methods 1")

        # Run dummy method to clear
        self.locals()

        # Reset trace
        self._reset_trace_history()

    def target_send_line(self, line):
        if self.target is not None:
            size = self.target.sendline(line)
            self.target.flush()
            return size

    def target_send_file(self, file_name):
        return self.target_send_line(open(file_name).read())

    def _reset_trace_history(self) -> _typ.NoReturn:
        self.trace = list()

    def _append_trace_history(self, info: _typ.Mapping) -> _typ.NoReturn:
        if self.trace is None:
            self._reset_trace_history()

        # Add the info to the list
        self.trace.append(info)

        # Cull the excess frames
        if self.trace_max is not None and self.trace_max > 0:
            if len(self.trace) > self.trace_max:
                self.trace = self.trace[-self.trace_max:]

    def step(self, modifier: str = " in", include_locals: bool = False) -> _typ.Dict[str, _typ.Any]:
        """

        :return:
        """

        if not self.active:
            return None

        # Make a step
        self.pty.sendline("step{}".format(modifier))

        # Collect location
        try:
            self.pty.expect(_helpers.REGEXP_PATT_STEP_EXPECT)

        except _pexpect.EOF as e:
            e.__class__ = _exceptions.JdbHostExitedException
            raise e

        except _pexpect.TIMEOUT as e:
            e.__class__ = _exceptions.JdbException
            raise e

        info = _helpers.parse_jdb_step(self.pty.after)
        if info is None or len(info) == 0:
            # print("Error")
            # print(self.pty.after)
            raise _exceptions.JdbHostErrorException("Unexpected error: '{}'".format(self.pty.after))

        # Obtain local variables (or attempt to)
        loc = self.locals()

        if loc is not None:
            args, vars = loc

            # Detect if method was just called and fill calling information if so
            if "Method entered" in self.pty.before and args is not None:
                info["call"] = args

            if include_locals and vars is not None:
                info["locals"] = vars

        # Add to record
        self._append_trace_history(info)

        return info

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

        # Expect the variables from method arguments (or a message that we don't have
        # debug information for this frame).
        self.pty.expect(
            "(No local variables[^\r\n]*|.*ocal variable "
            "information not available[^\r\n]*|Method arguments:)")

        # If there is debug information, which we detect by the presence of the message
        # "Method", then also look for local variables.
        if "Method" in self.pty.after:
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

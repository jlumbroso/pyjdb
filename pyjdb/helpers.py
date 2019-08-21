import re as _re
import subprocess as _subprocess
import typing as _typ


JDB_NAME = "jdb"
JDB_VERSION_FLAG = "-version"
REGEXP_PATT_VERSION = r"^[0-9]+(\.[0-9]+(\.[0-9]+)?)?$"
REGEXP_PATT_CSV = r"\".*?\"|'.*?'|[^,]+"

REGEXP_CSV = _re.compile(REGEXP_PATT_CSV)


def make_matcher(regexp: str) -> _typ.Callable[[str], bool]:
    """
    Returns a helper function that will return `True` when provided with a
    string that matches the provided `regexp` pattern, and `False`
    otherwise.

    :param regexp: The regular expression against which to match strings.
    :return: The helper function that will check strings against the pattern.
    """

    p = _re.compile(regexp)

    def reject(s):
        return p.match(s) is not None

    return reject


def filter_regexp(regexp: str, lst: _typ.Iterator[str]) -> _typ.Iterator[str]:
    """
    Filters a list of strings `lst` to only retain those which match the
    regular expression provided through `regexp`.

    :param regexp: The regular expression against which to match strings.
    :param lst: An iterator of strings to filter.
    :return: An iterator of strings that have been filtered by `regexp`.
    """

    return filter(make_matcher(regexp), lst)


def head(it: _typ.Iterator) -> _typ.Optional[_typ.Any]:
    try:
        return it.__next__()
    except AttributeError:
        # NoneType provided
        return None
    except NameError:
        # Not an iterator
        return None
    except StopIteration:
        # Iterator empty
        return None


def parse_jdb_version() -> _typ.Optional[str]:
    """
    Returns the version of `jdb` if the command is available and in the
    PATH; returns `None` otherwise.

    :return: The version of `jdb` as a string.
    """
    try:
        version_str = _subprocess.run(
            [JDB_NAME, JDB_VERSION_FLAG], stdout=_subprocess.PIPE
        ).stdout.decode("utf-8")

    except FileNotFoundError:
        return None

    version = head(filter_regexp(regexp=REGEXP_PATT_VERSION, lst=version_str.split()))

    return version


def parse_jdb_value(value: str) -> _typ.Any:
    """
    Returns a Python-typed value given a string parsed from `jdb`
    output. Supports strings, characters, integers, floats and
    boolean values.

    :param value: The `jdb` value as a string.
    :return: The value as a Python type.
    """

    # Assume we are dealing with a string that can be sliced/diced
    if type(value) is not str:
        return value

    # Objects should not be modified for the moment
    # NOTE: Could expand arrays (or simple types of arrays)
    if value[0:8] == "instance":
        return value

    # Arrays
    if value[0] == "{" and value[-1] == "}":

        # NOTE: below did not work, because quotes were not saved
        # which interfered with the string vs int detection
        # #csv_like_data = [value[1:-1].strip()]
        # #csv_reader = _csv.reader(csv_like_data, skipinitialspace=True)
        # #return list(map(parse_jdb_value, _itertools.chain(*csv_reader)))

        data = value[1:-1].strip()
        values = map(str.strip, REGEXP_CSV.findall(data))
        return list(map(parse_jdb_value, values))

    # NoneType
    if value == "null":
        return None

    # Quoted string
    if len(value) >= 2 and value[0] == value[-1] and value[0] in ["'", '"']:
        return value[1:-1]

    # Boolean type
    if value in ["true", "false"]:
        return value == "true"

    # We may have an int or a float, so test in least restrictive order
    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    # Unknown type
    return value


def parse_jdb_values(text: str) -> _typ.Dict[str, _typ.Any]:
    """
    Returns a dictionary of Python-typed values, given a list of
    variables as produced by `jdb`'s output of a command such as
    `locals`---that is, one line per variable, with the name and
    value separated by an '=' character.

    :param text: The output from `jdb`.
    :return: A dictionary of parsed variables.
    """
    # Remove /r
    text = text.replace("\r\n", "\n")

    # Strip trailing spaces
    text = text.strip()

    # Split into lines
    lines = text.splitlines()

    # Parse each line
    variables = []
    for line in lines:
        if "=" not in line:
            continue

        parts = line.split(sep="=", maxsplit=1)
        name = parts[0].strip()
        value = parts[1].strip()

        parsed_value = parse_jdb_value(value)

        variables.append((name, parsed_value))

    # Turn the list into a dict
    # >variables_dict = _collections.OrderedDict(variables)
    variables_dict = dict(variables)

    return variables_dict

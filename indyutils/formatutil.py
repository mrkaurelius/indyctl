WARNING = '\033[93m'
OKGREEN = '\033[92m'
FAIL = '\033[91m'
ENDC = '\033[0m'


def print_warn(str):
    print(f"{WARNING}{str}{ENDC}")


def warnf(str):
    return f"{WARNING}{str}{ENDC}"


def print_ok(str):
    print(f"{OKGREEN}{str}{ENDC}")


def okf(str):
    return f"{OKGREEN}{str}{ENDC}"


def print_fail(str):
    print(f"{FAIL}{str}{ENDC}")


def failf(str):
    return f"{FAIL}{str}{ENDC}"


def print_log(value_color="", value_noncolor=""):
    """set the colors for text."""
    HEADER = '\033[92m'
    ENDC = '\033[0m'
    print(HEADER + value_color + ENDC + str(value_noncolor))
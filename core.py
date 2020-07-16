#!/usr/bin/env python3

import contextlib
import datetime
import math
import os
import pathlib
import shutil
import string
import subprocess
import sys
import logging
import tempfile
from typing import List

import humanize
import numpy
import requests

import logger_factory

MINIMUM_PYTHON_VERSION = (3, 8)

FILENAME_WORD_SEPARATOR = "-"

ENCODING = "UTF-8"

INDENTATION = "  "
USER_HOME = os.path.expanduser("~")
USER_CODE_DIRECTORY = os.path.join(USER_HOME, "code")
COMPUTER_MANAGER_DIRECTORY = os.path.join(USER_CODE_DIRECTORY, "computer-manager")
LOGS_DIRECTORY = pathlib.Path(os.path.join(COMPUTER_MANAGER_DIRECTORY, "logs"))
DATA_DIRECTORY = "data"
INCLUDE_DIRECTORY = "include"
DOWNLOAD_DIRECTORY = "downloads"
DOWNLOAD_CHUNK_SIZE = 256
PIP_FILENAME = "pip.txt"
PACKAGES_FILE_NAME = "packages.txt"
BASH_HISTORY_FILE = os.path.join(USER_HOME, ".bash_history")
CURRENT_JETBRAINS_VERSION = "2018.3.1"
MAXIMUM_RECENTLY_MODIFIED_REPOSITORIES = 10
GIT_DATE_FORMAT = "%a %b %d %H:%M:%S %Y %z"
GIT_LOG_DATE_LINE_PREFIX = "Date:"
GIT_LARGE_FILE_THRESHOLD = 128 * 1024

IDEA_LINK_FORMAT = "https://download.jetbrains.com/idea/ideaIU-{}.tar.gz"
CLION_LINK_FORMAT = "https://download.jetbrains.com/cpp/CLion-{}.tar.gz"
PYCHARM_LINK_FORMAT = "https://download.jetbrains.com/python/pycharm-professional-{}.tar.gz"
WEBSTORM_LINK_FORMAT = "https://download.jetbrains.com/webstorm/WebStorm-{}.tar.gz"
DATAGRIP_LINK_FORMAT = "https://download.jetbrains.com/datagrip/datagrip-{}.tar.gz"

SWAP_EXTENSION = ".swap"
JETBRAINS_CHECKSUM_SUFFIX = ".sha256"
JETBRAINS_INSTALL_DIRECTORY = "jetbrains"


def get_jetbrains_links():
    formats = [
        IDEA_LINK_FORMAT,
        CLION_LINK_FORMAT,
        PYCHARM_LINK_FORMAT,
        WEBSTORM_LINK_FORMAT,
        DATAGRIP_LINK_FORMAT,
    ]
    return [link.format(CURRENT_JETBRAINS_VERSION) for link in formats]


def validate_command_name(command: str):
    valid_set = set(string.ascii_lowercase + "-" + ":")
    for character in command:
        if character not in valid_set:
            raise ValueError("'{}' is not allowed in a command name.".format(character))


class Sentence:
    """
    A sentence is a series of words.
    """

    def __init__(self, words: List[str]):
        self.words = words

    def starts_with(self, sentence):
        if len(sentence.words) > len(self.words):
            return False
        return self.words[: len(sentence.words)] == sentence.words

    def remove_prefix(self, sentence):
        assert self.starts_with(sentence)
        return Sentence(self.words[len(sentence.words) :])

    def __str__(self) -> str:
        return " ".join(self.words)


class Command:
    def __init__(self, invocation: str, action):
        assert isinstance(invocation, str), "Invocation should be a string."
        validate_command_name(invocation)
        self.invocation = Sentence([invocation])
        self.action = action

    def matches(self, request: Sentence) -> bool:
        return request.starts_with(self.invocation)

    def answer(self, request: Sentence, logger: logging.Logger):
        self.action(request.remove_prefix(self.invocation), logger)

    def __str__(self) -> str:
        return str(self.invocation)


@contextlib.contextmanager
def change_directory(new_directory):
    previous_directory = os.getcwd()
    if not os.path.exists(new_directory):
        os.mkdir(new_directory)
    os.chdir(new_directory)
    try:
        yield
    finally:
        os.chdir(previous_directory)


def assert_is_path_friendly(entry: str):
    valid_path_characters = string.digits + string.ascii_letters + "-" + "."
    for char in entry:
        assert char in valid_path_characters, entry + " is not a valid path."


def get_computer_manager_directory():
    return COMPUTER_MANAGER_DIRECTORY


def get_path_to_housekeeper_data_file(filename):
    return os.path.join(get_computer_manager_directory(), DATA_DIRECTORY, filename)


def get_path_to_housekeeper_include_file(filename):
    return os.path.join(get_computer_manager_directory(), INCLUDE_DIRECTORY, filename)


def download(link, filename):
    r = requests.get(link, stream=True)
    with open(filename, "wb") as fd:
        for chunk in r.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
            fd.write(chunk)


def install_snappy(sentence: Sentence, logger: logging.Logger):
    subprocess.check_call(["bash", get_path_to_housekeeper_include_file("snappy-1.sh")])
    subprocess.check_call(["bash", get_path_to_housekeeper_include_file("snappy-2.sh")])
    print("Please reboot now in order to get Snappy running.")


def install_jetbrains_products(sentence: Sentence, logger: logging.Logger):
    subprocess.check_call(["bash", get_path_to_housekeeper_include_file("jetbrains-from-snappy.sh")])


def install_postman(sentence: Sentence, logger: logging.Logger):
    subprocess.check_call(["bash", get_path_to_housekeeper_include_file("postman-from-snappy.sh")])


def has_git_repository(path: str) -> bool:
    with change_directory(path):
        if os.path.exists(os.path.join(path, ".git")):
            return True
    return False


class NoLastCommitDateException(Exception):
    pass


class Repository:
    def __init__(self, path: str, basename: str):
        assert has_git_repository(path)
        self.path = path
        self.basename = basename

    def is_dirty(self) -> bool:
        with change_directory(self.path):
            command = "git status --short"
            try:
                output = subprocess.check_output(command.split())
            except subprocess.CalledProcessError:
                raise Exception("Failed when evaluating if {} is dirty.".format(self.basename))
        if output:
            return True
        return False

    def get_last_commit_date(self) -> datetime.datetime:
        with change_directory(self.path):
            command = "git log -1 --all --date-order"
            try:
                output = subprocess.check_output(command.split())
            except subprocess.CalledProcessError:
                raise Exception("Failed when evaluating the last commit date of {}.".format(self.basename))
            try:
                lines = str(output, ENCODING).split("\n")
                for line in lines:
                    if line.startswith(GIT_LOG_DATE_LINE_PREFIX):
                        date_string = line[len(GIT_LOG_DATE_LINE_PREFIX) :].strip()
                        return datetime.datetime.strptime(date_string, GIT_DATE_FORMAT)
            except IndexError:
                raise Exception("Failed to parse the last commit date of {}.".format(self.basename))
        raise NoLastCommitDateException("Could not find the last commit date of {}.".format(self.basename))


def list_large_files_in_repository(sentence: Sentence, logger: logging.Logger):
    if len(sentence.words) != 1:
        print("You must specify the path to the repository to be investigated.")
        return
    repository_path = pathlib.Path(sentence.words[0])
    if not (repository_path / ".git").is_dir():
        print("The specified directory is not a Git repository.")
        return
    with change_directory(repository_path):
        objects_output = subprocess.check_output(["git", "rev-list", "--objects", "--all"], text=True)
        cat_file_output = subprocess.check_output(["git", "cat-file", "--batch-check=%(objecttype) %(objectname) %(objectsize) %(rest)"], input=objects_output, text=True)
    blobs = [line.split() for line in cat_file_output.split("\n") if line and line.split()[0] == "blob"]
    blobs = sorted(filter(lambda line: int(line[2]) > GIT_LARGE_FILE_THRESHOLD, blobs), key=lambda line: int(line[2]), reverse=True)
    if blobs:
        count = len(blobs)
        total_size = 0
        for blob in blobs:
            total_size += int(blob[2])
        print(f"Found {count} blob{'s' if count != 1 else ''} larger than {GIT_LARGE_FILE_THRESHOLD} bytes, totaling {humanize.naturalsize(total_size,binary=True)}.")
        for blob in blobs:
            print(" ".join(blob))


def print_most_recently_modified_repositories(repositories: List[Repository]):
    repositories_with_last_modified_date = []
    for repository in repositories:
        try:
            last_commit_date = repository.get_last_commit_date()
            repositories_with_last_modified_date.append((repository, last_commit_date))
        except NoLastCommitDateException:
            pass
    if not repositories_with_last_modified_date:
        return
    repositories_with_last_modified_date.sort(key=lambda t: t[1], reverse=True)
    while len(repositories_with_last_modified_date) > MAXIMUM_RECENTLY_MODIFIED_REPOSITORIES:
        repositories_with_last_modified_date.pop()
    longest_repository_name_length = 0
    for repository, _ in repositories_with_last_modified_date:
        longest_repository_name_length = max(longest_repository_name_length, len(repository.basename))
    print("Most recently modified:")
    for repository, last_commit_date in repositories_with_last_modified_date:
        print(f"{INDENTATION}{repository.basename:{longest_repository_name_length}} {last_commit_date}")


def print_repositories(repositories: List[Repository], label: str):
    if not repositories:
        print(f"There are no {label} repositories.")
        return
    if len(repositories) == 1:
        print(f"Found a {label} repository:")
    else:
        print(f"Found {len(repositories)} {label} repositories:")
    for repository in repositories:
        print("{}{}".format(INDENTATION, repository.basename))


def analyze_repositories(sentence: Sentence, logger: logging.Logger):
    repositories: List[Repository] = []
    for basename in sorted(os.listdir(path=USER_CODE_DIRECTORY)):
        assert_is_path_friendly(basename)
        path = os.path.join(USER_CODE_DIRECTORY, basename)
        if pathlib.Path(path).is_dir():
            if has_git_repository(path):
                repositories.append(Repository(path, basename))
    repositories.sort(key=lambda r: str.casefold(r.basename))
    dirty_repositories = []
    clean_repositories = []
    for repository in repositories:
        if repository.is_dirty():
            dirty_repositories.append(repository)
        else:
            clean_repositories.append(repository)
    print(f"Found {len(repositories)} repositories.")
    print_most_recently_modified_repositories(repositories)
    print_repositories(dirty_repositories, "dirty")
    print_repositories(clean_repositories, "clean")


def clean_bash_history_of_file(full_path):
    """
    Removes duplicates from the provided bash history file, keeping only the latest entry.

    This would change (a.out, b.out a.out) to simply (b.out, a.out).

    This operation might also affect whitespace.

    :return a tuple with before and after line count
    """
    with open(full_path) as bash_history_file_handler:
        text = bash_history_file_handler.read()
    lines = [line.strip() for line in text.split("\n") if line]
    lines.reverse()
    seen = set()
    first_time_lines = []
    for line in lines:
        if line not in seen:
            first_time_lines.append(line)
            seen.add(line)
    first_time_lines.reverse()
    with tempfile.NamedTemporaryFile(delete=False) as temporary_file:
        temporary_file.write(bytes("\n".join(first_time_lines), ENCODING))
        temporary_file.write(bytes("\n", ENCODING))
    shutil.move(temporary_file.name, full_path)
    return len(lines), len(seen)


def to_human_readable_size(size, decimal_places=3):
    """
    Converts a byte count to a human-readable file size.

    Copied from https://stackoverflow.com/a/43690506/3271844.
    """
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.{decimal_places}f} {unit}"


def count_lines(path: str) -> int:
    with open(path) as handle:
        return len(handle.readlines())


def pluralize_if_required(count: int, singular: str, plural: str) -> str:
    if count == 1:
        return str(count) + " " + singular
    return f"{count:,} {plural}"


def analyze_bash_history(sentence: Sentence, logger: logging.Logger):
    lines_string = pluralize_if_required(count_lines(BASH_HISTORY_FILE), "line", "lines")
    size_string = to_human_readable_size(os.path.getsize(BASH_HISTORY_FILE))
    print(f"Bash history is {lines_string} long and uses {size_string}.")
    line_lengths = []
    with open(BASH_HISTORY_FILE) as file_handle:
        for line in file_handle.readlines():
            line_lengths.append(len(line))
    for fraction in (0.25, 0.5, 0.75):
        amount = numpy.quantile(line_lengths, fraction)
        print("{:.0%} of the lines are less than {} characters long.".format(fraction, math.ceil(amount)))


def clean_bash_history(sentence: Sentence, logger: logging.Logger):
    before, after = clean_bash_history_of_file(BASH_HISTORY_FILE)
    if before != after:
        removed = before - after
        print("Removed {} line{}.".format(removed, "s" if removed > 1 else ""))
    else:
        print("Removed nothing.")


def install_operating_system_packages():
    with open(get_path_to_housekeeper_data_file(PACKAGES_FILE_NAME)) as packages_file:
        packages = [line.strip() for line in packages_file.readlines()]
    command = "sudo zypper in" + " " + " ".join(packages)
    print(command)
    subprocess.call(command.split())


def normalize_filename_character(character: str):
    assert len(character) == 1
    if character == " ":
        return FILENAME_WORD_SEPARATOR
    elif character.isupper():
        return character.lower()
    return character


def normalize_filename(filename: str) -> str:
    normalized_characters = [normalize_filename_character(character) for character in filename]
    result_without_redundancy: List[str] = []
    for character in normalized_characters:
        if character == FILENAME_WORD_SEPARATOR:
            if not result_without_redundancy or result_without_redundancy[-1] != FILENAME_WORD_SEPARATOR:
                result_without_redundancy.append(character)
        else:
            result_without_redundancy.append(character)
    return "".join(result_without_redundancy)


def normalize_filenames(sentence: Sentence, logger: logging.Logger):
    if sentence.words:
        print("This command does not expect any arguments.")
        return
    for filename in os.listdir(os.curdir):
        normalized_filename = normalize_filename(filename)
        if os.path.isfile(filename) and not os.path.exists(normalized_filename):
            shutil.move(filename, normalized_filename)


def install_python_packages():
    command = "pip install --user -r " + get_path_to_housekeeper_data_file(PIP_FILENAME)
    print(command)
    subprocess.call(command.split())


def install_packages(sentence: Sentence, logger: logging.Logger):
    install_operating_system_packages()
    install_python_packages()


def update_distribution(sentence: Sentence, logger: logging.Logger):
    command = "sudo zypper dup --auto-agree-with-licenses"
    print(command)
    subprocess.call(command.split())
    command = "sudo zypper remove --no-confirm PackageKit"
    print(command)
    subprocess.call(command.split())


def get_package_list():
    with open(get_path_to_housekeeper_data_file(PACKAGES_FILE_NAME)) as packages_file:
        packages = [line.strip() for line in packages_file.readlines()]
    return packages


def set_package_list(package_list: List[str]):
    packages_swap_file_name = PACKAGES_FILE_NAME + SWAP_EXTENSION
    packages_swap_file_path = get_path_to_housekeeper_data_file(packages_swap_file_name)
    with open(packages_swap_file_path, "w") as packages_file:
        print("\n".join(package_list), file=packages_file)
    shutil.move(packages_swap_file_path, get_path_to_housekeeper_data_file(PACKAGES_FILE_NAME))


def add_package(sentence: Sentence, logger: logging.Logger):
    packages = get_package_list()
    packages.append(str(sentence))
    packages = list(set(packages))
    packages.sort()
    set_package_list(packages)


def list_packages(sentence: Sentence, logger: logging.Logger):
    print("\n".join(get_package_list()))


def get_commands():
    return [
        Command("list-commands", print_commands),
        Command("bash-history:analyze", analyze_bash_history),
        Command("bash-history:clean", clean_bash_history),
        Command("repository:list-large-files", list_large_files_in_repository),
        Command("repositories:analyze", analyze_repositories),
        Command("packages:add", add_package),
        Command("packages:list", list_packages),
        Command("packages:install", install_packages),
        Command("distribution:update", update_distribution),
        Command("snappy:install", install_snappy),
        Command("jetbrains:install", install_jetbrains_products),
        Command("postman:install", install_postman),
        Command("directory:normalize-filenames", normalize_filenames),
    ]


def print_commands(sentence: Sentence, logger: logging.Logger):
    for command in get_commands():
        print(command)


def main():
    if sys.version_info < MINIMUM_PYTHON_VERSION:
        sys.exit("Python {}.{} or later is required.".format(MINIMUM_PYTHON_VERSION[0], MINIMUM_PYTHON_VERSION[1]))
    if len(sys.argv) < 2:
        print("You must tell me what to do.")
        return
    logger = logger_factory.make_logger("computer-manager", LOGS_DIRECTORY)

    request = Sentence(sys.argv[1:])
    for command in get_commands():
        if command.matches(request):
            command.answer(request, logger)
            return
    print("Not a valid command.")


if __name__ == "__main__":
    print("Use the manager script.")

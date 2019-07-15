#!/usr/bin/env python3

import tempfile
import contextlib
import requests
import subprocess
import os
import sys
import string
import shutil

FILENAME_WORD_SEPARATOR = '-'

ENCODING = 'UTF-8'

INDENTATION = '  '
USER_HOME = os.path.expanduser('~')
USER_CODE_DIRECTORY = os.path.join(USER_HOME, 'code')
COMPUTER_MANAGER_DIRECTORY = os.path.join(USER_CODE_DIRECTORY, 'computer-manager')
DATA_DIRECTORY = 'data'
DOWNLOAD_DIRECTORY = 'downloads'
DOWNLOAD_CHUNK_SIZE = 256
PIP_FILENAME = 'pip.txt'
PACKAGES_FILE_NAME = 'packages.txt'
BASH_HISTORY_FILE = os.path.join(USER_HOME, '.bash_history')
CURRENT_JETBRAINS_VERSION = "2018.3.1"

IDEA_LINK_FORMAT = "https://download.jetbrains.com/idea/ideaIU-{}.tar.gz"
CLION_LINK_FORMAT = "https://download.jetbrains.com/cpp/CLion-{}.tar.gz"
PYCHARM_LINK_FORMAT = "https://download.jetbrains.com/python/pycharm-professional-{}.tar.gz"
WEBSTORM_LINK_FORMAT = "https://download.jetbrains.com/webstorm/WebStorm-{}.tar.gz"
DATAGRIP_LINK_FORMAT = "https://download.jetbrains.com/datagrip/datagrip-{}.tar.gz"

SWAP_EXTENSION = '.swap'
JETBRAINS_CHECKSUM_SUFFIX = '.sha256'
JETBRAINS_INSTALL_DIRECTORY = 'jetbrains'


def get_jetbrains_links():
    formats = [IDEA_LINK_FORMAT, CLION_LINK_FORMAT, PYCHARM_LINK_FORMAT, WEBSTORM_LINK_FORMAT, DATAGRIP_LINK_FORMAT]
    return [link.format(CURRENT_JETBRAINS_VERSION) for link in formats]


def validate_command_name(command: str):
    valid_set = set(string.ascii_lowercase + '-' + ':')
    for character in command:
        if character not in valid_set:
            raise ValueError("'{}' is not allowed in a command name.".format(character))


class Sentence:
    """
    A sentence is a series of words.
    """

    def __init__(self, words: [str]):
        self.words = words

    def starts_with(self, sentence):
        if len(sentence.words) > len(self.words):
            return False
        return self.words[:len(sentence.words)] == sentence.words

    def remove_prefix(self, sentence):
        assert self.starts_with(sentence)
        return Sentence(self.words[len(sentence.words):])

    def __str__(self) -> str:
        return ' '.join(self.words)


class Command:
    def __init__(self, invocation: str, action):
        assert isinstance(invocation, str), 'Invocation should be a string.'
        validate_command_name(invocation)
        self.invocation = Sentence([invocation])
        self.action = action

    def matches(self, request: Sentence) -> bool:
        return request.starts_with(self.invocation)

    def answer(self, request: Sentence):
        self.action(request.remove_prefix(self.invocation))

    def __str__(self) -> str:
        return str(self.invocation)


@contextlib.contextmanager
def change_directory(new_directory):
    previous_directory = os.getcwd()
    new_directory = new_directory
    if not os.path.exists(new_directory):
        os.mkdir(new_directory)
    os.chdir(new_directory)
    try:
        yield
    finally:
        os.chdir(previous_directory)


def assert_is_path_friendly(entry: str):
    valid_path_characters = string.digits + string.ascii_letters + '-' + '.'
    for char in entry:
        assert char in valid_path_characters, entry + ' is not a valid path.'


def get_housekeeper_directory():
    return os.path.dirname(sys.argv[0])


def get_path_to_housekeeper_data_file(filename):
    return os.path.join(get_housekeeper_directory(), DATA_DIRECTORY, filename)


def download(link, filename):
    r = requests.get(link, stream=True)
    with open(filename, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=DOWNLOAD_CHUNK_SIZE):
            fd.write(chunk)


def get_daughter_directory():
    return COMPUTER_MANAGER_DIRECTORY


def download_jetbrains_products(sentence: Sentence):
    for file_link in get_jetbrains_links():
        with change_directory(os.path.join(get_daughter_directory(), DOWNLOAD_DIRECTORY)):
            print('Downloading {}...'.format(os.path.basename(file_link)), end='', flush=True)
            file_checksum_link = file_link + JETBRAINS_CHECKSUM_SUFFIX
            file_checksum_name = os.path.basename(file_checksum_link)
            download(file_checksum_link, file_checksum_name)
            # Try the checksum, if it fails, download the file.
            try:
                command = 'sha256sum -c {}'.format(file_checksum_name).split()
                checksum_output = subprocess.check_output(command, stderr=subprocess.DEVNULL)
                if checksum_output.decode('utf-8').strip().endswith('OK'):
                    print(' already downloaded.')
                    continue
            except subprocess.CalledProcessError:
                pass
            file_name = os.path.basename(file_link)
            download(file_link, file_name)
            print(' done.')


def install_jetbrains_products(sentence: Sentence):
    download_jetbrains_products(sentence)
    for file_link in get_jetbrains_links():
        file_name = os.path.basename(file_link)
        with change_directory(os.path.join(get_daughter_directory(), JETBRAINS_INSTALL_DIRECTORY)):
            tar_file = os.path.join(get_daughter_directory(), DOWNLOAD_DIRECTORY, file_name)
            subprocess.call('tar --extract --file {}'.format(tar_file).split())
            print('Extracted {}.'.format(file_name))


def list_repositories(sentece: Sentence):
    dirty = []
    clean = []
    for basename in sorted(os.listdir(path=USER_CODE_DIRECTORY)):
        assert_is_path_friendly(basename)
        full_path = os.path.join(USER_CODE_DIRECTORY, basename)
        with change_directory(full_path):
            if not os.path.exists(os.path.join(full_path, '.git')):
                continue
            command = 'git status --short'
            try:
                output = subprocess.check_output(command.split())
            except subprocess.CalledProcessError:
                print('Failed when evaluating {}.'.format(basename))
                return
        if output:
            dirty.append(basename)
        else:
            clean.append(basename)
    print('Found {} repositories.'.format(len(dirty) + len(clean)))
    if dirty:
        print('Dirty:')
        for repository in dirty:
            print('{}{}'.format(INDENTATION, repository))
    if clean:
        print('Clean:')
        for repository in clean:
            print('{}{}'.format(INDENTATION, repository))


def clean_bash_history_of_file(full_path):
    """
    Removes duplicates from the provided bash history file, keeping only the latest entry.

    This would change (a.out, b.out a.out) to simply (b.out, a.out).

    This operation might also affect whitespace.

    :return a tuple with before and after line count
    """
    with open(full_path) as bash_history_file_handler:
        text = bash_history_file_handler.read()
    lines = [line.strip() for line in text.split('\n') if line]
    lines.reverse()
    seen = set()
    first_time_lines = []
    for line in lines:
        if line not in seen:
            first_time_lines.append(line)
            seen.add(line)
    first_time_lines.reverse()
    with tempfile.NamedTemporaryFile(delete=False) as temporary_file:
        temporary_file.write(bytes('\n'.join(first_time_lines), ENCODING))
        temporary_file.write(bytes('\n', ENCODING))
    shutil.move(temporary_file.name, full_path)
    return len(lines), len(seen)


def clean_bash_history(sentence: Sentence):
    before, after = clean_bash_history_of_file(BASH_HISTORY_FILE)
    if before != after:
        removed = before - after
        print('Removed {} line{}.'.format(removed, 's' if removed > 1 else ''))
    else:
        print('Removed nothing.')


def install_operating_system_packages():
    with open(get_path_to_housekeeper_data_file(PACKAGES_FILE_NAME)) as packages_file:
        packages = [line.strip() for line in packages_file.readlines()]
    command = 'sudo zypper in' + ' ' + ' '.join(packages)
    print(command)
    subprocess.call(command.split())


def normalize_filename_character(character: str):
    assert len(character) == 1
    if character == ' ':
        return FILENAME_WORD_SEPARATOR
    elif character.isupper():
        return character.lower()
    return character


def normalize_filename(filename: str):
    normalized_characters = [normalize_filename_character(character) for character in filename]
    result_without_redundancy = []
    for character in normalized_characters:
        if character == FILENAME_WORD_SEPARATOR:
            if not result_without_redundancy or result_without_redundancy[-1] != FILENAME_WORD_SEPARATOR:
                result_without_redundancy.append(character)
        else:
            result_without_redundancy.append(character)
    return ''.join(result_without_redundancy)


def normalize_filenames(sentence: Sentence):
    if sentence.words:
        print('This command does not expect any arguments.')
        return
    for filename in os.listdir(os.curdir):
        normalized_filename = normalize_filename(filename)
        if os.path.isfile(filename) and not os.path.exists(normalized_filename):
            shutil.move(filename, normalized_filename)


def install_python_packages():
    command = 'pip install --user -r ' + get_path_to_housekeeper_data_file(PIP_FILENAME)
    print(command)
    subprocess.call(command.split())


def install_packages(sentence: Sentence):
    install_operating_system_packages()
    install_python_packages()


def update_distribution(sentence: Sentence):
    command = 'sudo zypper dup --auto-agree-with-licenses'
    print(command)
    subprocess.call(command.split())
    command = 'sudo zypper remove --no-confirm PackageKit'
    print(command)
    subprocess.call(command.split())


def get_package_list():
    with open(get_path_to_housekeeper_data_file(PACKAGES_FILE_NAME)) as packages_file:
        packages = [line.strip() for line in packages_file.readlines()]
    return packages


def set_package_list(package_list: [str]):
    packages_swap_file_name = PACKAGES_FILE_NAME + SWAP_EXTENSION
    packages_swap_file_path = get_path_to_housekeeper_data_file(packages_swap_file_name)
    with open(packages_swap_file_path, 'w') as packages_file:
        print('\n'.join(package_list), file=packages_file)
    shutil.move(packages_swap_file_path, get_path_to_housekeeper_data_file(PACKAGES_FILE_NAME))


def add_package(sentence: Sentence):
    packages = get_package_list()
    packages.append(str(sentence))
    packages = list(set(packages))
    packages.sort()
    set_package_list(packages)


def list_packages(sentence: Sentence):
    print('\n'.join(get_package_list()))


def get_commands():
    return [Command('list-commands', print_commands),
            Command('bash-history:clean', clean_bash_history),
            Command('repositories:analyze', list_repositories),
            Command('packages:add', add_package),
            Command('packages:list', list_packages),
            Command('packages:install', install_packages),
            Command('distribution:update', update_distribution),
            Command('jetbrains:download', download_jetbrains_products),
            Command('jetbrains:install', install_jetbrains_products),
            Command('directory:normalize-filenames', normalize_filenames)]


def print_commands(sentence: Sentence):
    for command in get_commands():
        print(command)


def main():
    if len(sys.argv) < 2:
        print('You must tell me what to do.')
        return
    request = Sentence(sys.argv[1:])
    for command in get_commands():
        if command.matches(request):
            command.answer(request)
            return
    print('Not a valid command.')


if __name__ == '__main__':
    print('Use the manager script.')

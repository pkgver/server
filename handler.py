import re

import git

from database import query

repo = git.Repo('./nixpkgs')
config_writer = repo.config_writer()
config_writer.set_value('feature', 'manyFiles', '1')
config_writer.release()

version_pattern = re.compile(r'version\s*=\s*"(.+?)(?=")')
name_pattern = re.compile(r'name\s*=\s*"((?=[^"]*(\d+\.\d+|\d+-\d+)).+?)"')


def get_package_path(package_name):
    commit_tree = repo.head.commit.tree
    all_packages = commit_tree['pkgs/top-level/all-packages.nix'].data_stream.read().decode('utf-8')
    if not (path := re.search(f'^\s*\\b{package_name}\\b\s*=.*', all_packages, flags=re.MULTILINE)):
        return None

    path = path.group(0).split()[3].replace('..', 'pkgs') + '/default.nix'

    print(path)
    return path


def get_versions_from_commits(package_path, package_name, from_commit: str = None):
    versions = {}

    args = ['--pretty=format:%H', '--name-only', '--follow', package_path]
    if from_commit:
        args.insert(0, f'{from_commit}..HEAD')

    log = repo.git.log(*args)
    # reverse list
    log = [i for i in log.split('\n')[::-1] if i]

    it = iter(log)
    for filepath in it:
        commit_hash = next(it)
        commit = repo.commit(commit_hash)
        file_content = commit.tree[filepath].data_stream.read().decode('utf-8')
        if version := version_pattern.search(file_content):
            version = version.group(1)
        else:
            if version := name_pattern.search(file_content):
                version = version.group(1).replace(f'{package_name}-', '')
            else:
                version = commit_hash[0:7]

        versions[version] = commit_hash

    return versions


def get_package_versions(package_name, package_path):
    args = [package_path, package_name]
    if query("SELECT * FROM version WHERE LOWER(package) = ?", package_name):
        # latest commit hash
        latest = \
            query("SELECT commit_hash FROM version WHERE LOWER(package) = ? ORDER BY timestamp DESC LIMIT 1",
                  package_name)[
                0][0]
        args += [latest]

    versions = get_versions_from_commits(*args)

    if versions:
        for version, commit_hash in versions.items():
            query('INSERT INTO version(package, version, commit_hash) VALUES (?, ?, ?)', package_name, version,
                  commit_hash)

    result = query('SELECT version, commit_hash FROM version WHERE LOWER(package) = ? ORDER BY timestamp DESC',
                   package_name)
    return result

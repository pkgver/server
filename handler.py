import re

import git

from database import query

repo = git.Repo('./nixpkgs')
config_writer = repo.config_writer()
config_writer.set_value('feature', 'manyFiles', '1')
config_writer.release()

version_pattern = re.compile(r'version\s*=\s*"(.+?)(?=")')


def get_package_path(package_name):
    commit_tree = repo.head.commit.tree
    all_packages = commit_tree['pkgs/top-level/all-packages.nix'].data_stream.read().decode('utf-8')
    if not (path := re.search(f'\\b{package_name}\\b\s*=.*', all_packages, flags=re.MULTILINE)):
        return None

    path = path.group(0).split()[3].replace('..', 'pkgs') + '/default.nix'

    print(path)
    return path


def get_versions_from_commits(package_path, from_commit: str = None):
    versions = {}

    args = ['--pretty=format:%H', '--name-only', '--follow', package_path]
    if from_commit:
        args.insert(0, f'{from_commit}..HEAD')

    log = repo.git.log(*args)
    log = [i for i in log.split('\n') if i]

    it = iter(log)
    for commit_hash in it:
        commit = repo.commit(commit_hash)
        file_content = commit.tree[next(it)].data_stream.read().decode('utf-8')
        if version := version_pattern.search(file_content):
            version = version.group(1)
        else:
            version = commit_hash[0:7]

        versions[version] = commit_hash

    return versions


def get_package_versions(package_name, package_path):
    args = [package_path]
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
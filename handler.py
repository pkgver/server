import os
import subprocess
from os.path import join

from database import query


def execute(command: list):
    p = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return p


def get_package_path(package_name):
    execute(['git', 'pull'])
    path = execute(['grep', f'^\s*{package_name}\s*=', 'pkgs/top-level/all-packages.nix'])
    if not path.stdout:
        return None
    result = path.stdout.split()[3].replace('..', 'pkgs') + "/default.nix"
    print(result)
    return result


def get_versions_from_commits(package_path, from_commit: str = None):
    versions = {}
    cmd = [join(os.environ['PROOT'], 'versions.sh'), package_path]
    if from_commit:
        cmd += [f'{from_commit}..HEAD']
    commits = execute(cmd)

    for commit in commits.stdout.split('\n')[::-1]:
        if commit:
            hash, version = commit.split()
            versions[version] = hash

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

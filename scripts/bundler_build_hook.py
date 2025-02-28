import pathlib
import shutil
import subprocess

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class RollupBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        subprocess.check_output("npm install", shell=True)
        subprocess.check_output("npm run bundle", shell=True)

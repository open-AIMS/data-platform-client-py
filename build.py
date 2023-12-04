#   -*- coding: utf-8 -*-
import os.path

from pybuilder.core import use_plugin, init, Project

use_plugin("python.core")
use_plugin("python.distutils")
use_plugin("pypi:pybuilder_pytest")

name = "data-platform-client-py"
default_task = "publish"

version = "1.0"


@init
def set_properties(project: Project):
    project.depends_on_requirements("requirements.txt")
    project.build_depends_on_requirements("dev-requirements.txt")

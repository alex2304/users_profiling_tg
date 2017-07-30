# -*- coding: utf-8 -*-

from . import metadata

# TODO: refactor mystem framework

__version__ = metadata.version
__author__ = metadata.authors[0]
__license__ = metadata.license
__copyright__ = metadata.copyright

from .mystem import (Mystem, autoinstall)  # noqa
from .constants import (MYSTEM_BIN, MYSTEM_DIR, MYSTEM_EXE)  # noqa

from datetime import datetime

from os.path import join

from uber.jinja import template_overrides
from uber.utils import mount_site_sections, static_overrides

from magstock._version import __version__  # noqa: F401
from .config import config

from . import models  # noqa: F401,E402,F403
from . import model_checks  # noqa: F401,E402,F403
from . import receipt_items  # noqa: F401
from . import forms  # noqa: F401

mount_site_sections(config['module_root'])
static_overrides(join(config['module_root'], 'static'))
template_overrides(join(config['module_root'], 'templates'))

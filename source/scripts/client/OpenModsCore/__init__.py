# -*- coding: utf-8 -*-
import ResMgr
from .config import *
from .utils import *

curCV = ResMgr.openSection('../paths.xml')['Paths'].values()[0].asString
print 'Current OpenModsCore version: 2.8.6 (%(file_compile_date)s)'

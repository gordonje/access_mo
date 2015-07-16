#!/usr/bin/env python
# -*- coding: utf-8 -*-

from models import *
from urlparse import urlparse

db.create_tables([
				  Source_Page
			], True)
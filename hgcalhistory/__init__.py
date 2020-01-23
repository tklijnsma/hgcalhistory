#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .logger import setup_logger
logger = setup_logger()


import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gROOT.ProcessLine("gErrorIgnoreLevel = kError;")

from . import utils, rootutils
from .event import Event, EventFactory
from .dataformats import Track, Vertex
from .plots import Plot3D
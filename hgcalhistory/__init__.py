#!/usr/bin/env python
# -*- coding: utf-8 -*-
from .logger import setup_logger
logger = setup_logger()


import ROOT
ROOT.gROOT.SetBatch(True)
ROOT.gROOT.ProcessLine("gErrorIgnoreLevel = kError;")
ROOT.gStyle.SetOptStat(0)

from . import utils, rootutils, seutils
from .event import Event, EventFactory
from .dataformats import Track, Vertex, CaloHitWithPosition
from .datacontainers import Histogram2D, Histogram2DFillable
from .plots import Plot3D, HitsPlot
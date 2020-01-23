#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os.path as osp
import logging, os, uuid
from time import strftime
from array import array

logger = logging.getLogger('hgcalhistory')

import ROOT


# Slightly easier-to-work-with containers


# class Vertex(object):
#     """docstring for Vertex"""
#     def __init__(self, vertex):
#         super(Vertex, self).__init__()
#         self.vertex = vertex

#     def xyz(self):
#         pos = self.vertex.position()
#         return pos.X(), pos.Y(), pos.Z()

#     def index(self):
#         return self.vertex.vertexId()

#     def track_index(self):
#         return self.vertex.parentIndex()


# class Track(object):

#     def __init__(self, track):
#         super(Vertex, self).__init__()
#         self.track = track

#     def xyz(self):
#         pos = self.track.trackerSurfacePosition()
#         return pos.X(), pos.Y(), pos.Z()

#     def index(self):
#         return self.track.trackId()

#     def vertex_index(self):
#         return self.track.vertIndex()


class Vertex(ROOT.SimVertex):

    def __repr__(self):
        return (
            '<Vertex {0} x={1} y={2} z={3}>'
            .format(self.id(), *self.xyz())
            )

    def xyz(self):
        pos = self.position()
        return pos.X(), pos.Y(), pos.Z()

    def id(self):
        return self.vertexId()

    def track_id(self):
        return self.parentIndex()


class Track(ROOT.SimTrack):

    pdgid_line_colors = {
        13 : ROOT.kBlue-9,
        11 : ROOT.kGreen+3,
        22 : ROOT.kRed
        }
    other_color = ROOT.kMagenta+1

    def __repr__(self):
        return '<Track {0} pdgid={1} x={2} y={3} z={4}>'.format(self.id(), self.pdgid(), *self.xyz())

    def xyz(self):
        pos = self.trackerSurfacePosition()
        return pos.X(), pos.Y(), pos.Z()

    def id(self):
        return self.trackId()

    def vertex_index(self):
        return self.vertIndex()

    def pdgid(self):
        return self.type()

    def get_polyline(self, vertex):
        line = ROOT.TPolyLine3D(2)
        line.SetPoint(0, *vertex.xyz())
        line.SetPoint(1, *self.xyz())
        line.SetLineColor(
            self.pdgid_line_colors.get(abs(self.pdgid()), self.other_color)
            )
        ROOT.SetOwnership(line, False)
        return line



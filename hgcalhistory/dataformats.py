#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os.path as osp
import logging, os, uuid
from time import strftime
from array import array

logger = logging.getLogger('hgcalhistory')

import ROOT


PDGID_COLORS = {
    13 : ROOT.kBlue-9,
    11 : ROOT.kGreen+3,
    22 : ROOT.kRed
    }
PDGID_OTHER_COLOR = ROOT.kMagenta+1

def pdgid_to_color(pdgid):
    return PDGID_COLORS.get(abs(pdgid), PDGID_OTHER_COLOR)



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
        line.SetLineColor(pdgid_to_color(self.pdgid()))
        ROOT.SetOwnership(line, False)
        return line


class CaloHitWithPosition(ROOT.PCaloHitWithPosition):

    def track_id(self):
        return  self.geantTrackId()

    def get_polymarker(self, track=None):
        marker = ROOT.TPolyMarker3D(
            1,
            array('f', [ self.position_.x(), self.position_.y(), self.position_.z() ]),
            # 8
            24
            )
        marker.SetMarkerColor(pdgid_to_color(track.pdgid()) if track else 9)
        marker.SetMarkerSize(0.4)
        ROOT.SetOwnership(marker, False)
        return marker







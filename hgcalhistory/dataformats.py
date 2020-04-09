#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import print_function

import os.path as osp, logging, os, uuid
from time import strftime
from array import array
import hgcalhistory

logger = logging.getLogger('hgcalhistory')

import ROOT


class Vertex(ROOT.SimVertex):

    def __repr__(self):
        return (
            '<Vertex {0} x={1:.3f} y={2:.3f} z={3:.3f}>'
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

    width = 8
    digits = 3

    def formatfloat(self, float):
        return (
            '{0:+{width}.{digits}f}'
            .format(float, width=self.width, digits=self.digits)
            )

    def __repr__(self):
        return (
            '<Track {0:<5} pdgid={1:<5} E={2} x={3} y={4} z={5}'
            .format(
                self.id(), self.pdgid(),
                self.formatfloat(self.energy()),
                *[self.formatfloat(x) for x in self.xyz()]
                )
            )

    def energy(self):
        # return self.trackerSurfaceMomentum().energy()
        return self.momentum().E()

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
        line.SetLineColor(hgcalhistory.physutils.pdgid_to_color(self.pdgid()))
        ROOT.SetOwnership(line, False)
        return line

    def get_projected_line(self, vertex, do_coordinate='x'):
        """
        Returns a projection of the track on the x-z plane.
        Set `do_coordinate` to 'y' for the y-z plane instead
        """
        line = ROOT.TGraph(2)
        vertex_x, vertex_y, vertex_z = vertex.xyz()
        line.SetPoint(0, vertex_z, vertex_x if do_coordinate == 'x' else vertex_y)
        track_x, track_y, track_z = self.xyz()
        line.SetPoint(1, track_z, track_x if do_coordinate == 'x' else track_y)
        line.SetLineColor(hgcalhistory.physutils.pdgid_to_color(self.pdgid()))
        ROOT.SetOwnership(line, False)
        return line


class CaloHitWithPosition(ROOT.PCaloHitWithPosition):

    def xyz(self):
        return self.position_.x(), self.position_.y(), self.position_.z()

    def track_id(self):
        return self.geantTrackId()

    def get_polymarker(self, track=None):
        marker = ROOT.TPolyMarker3D(
            1,
            array('f', [ self.position_.x(), self.position_.y(), self.position_.z() ]),
            # 8
            24
            )
        marker.SetMarkerColor(hgcalhistory.physutils.pdgid_to_color(track.pdgid()) if track else 9)
        marker.SetMarkerSize(0.4)
        ROOT.SetOwnership(marker, False)
        return marker

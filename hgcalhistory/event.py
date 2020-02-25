#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os, shutil, logging
import os.path as osp, numpy as np
from array import array
import hgcalhistory
logger = logging.getLogger('hgcalhistory')
import ROOT

class EventFactory(object):
    """docstring for EventFactory"""
    def __init__(self, rootfile):
        super(EventFactory, self).__init__()
        self.rootfile = rootfile
        logger.info('Opening %s', self.rootfile)
        self.tfile = ROOT.TFile.Open(self.rootfile)
        self.tree = self.tfile.Get('Events')

    def __del__(self):
        try:
            self.tfile.Close()
        except:
            pass

    def __iter__(self):
        for event in self.tree:
            yield event


class Event(object):
    """

    """

    def __init__(self, rootevent):
        super(Event, self).__init__()
        self.rootevent = rootevent
        
        self.tracks = []
        for t in self.rootevent.SimTracks_g4SimHits__SIM.product():
            t.__class__ = hgcalhistory.Track
            self.tracks.append(t)

        self.vertexs = []
        for v in self.rootevent.SimVertexs_g4SimHits__SIM.product():
            v.__class__ = hgcalhistory.Vertex
            self.vertexs.append(v)

        self.calohits = []
        for h in self.rootevent.PCaloHitWithPositions_PCaloHitWithPositionProducer__SIM.product():
            # Skip any non-HGCAL hits
            if not(h.inEE_ or h.inHsi_ or h.inHsc_):
                continue
            h.__class__ = hgcalhistory.CaloHitWithPosition
            self.calohits.append(h)

        self.n_tracks = len(self.tracks)
        self.n_vertexs = len(self.vertexs)

        self._tracks_position_collection = None
        self._vertexs_position_collection = None


    def has_photon(self):
        for track in self.tracks:
            if track.pdgid() == 22:
                return True
        else:
            return False

    def has_calohits_inEE(self):
        for hit in self.calohits:
            if hit.inEE_:
                return True
        else:
            return False

    def get_vertex_by_id(self, id):
        for v in self.vertexs:
            if v.id() == id:
                return v
        else:
            return None

    def get_track_by_id(self, id):
        for v in self.tracks:
            if v.id() == id:
                return v
        else:
            raise ValueError(
                'Track id {0}: no such track in event. Available track ids: {1}'
                .format(id, [v.id() for v in self.tracks])
                )

    def get_vertex_for_track(self, track):
        vertex_index = track.vertex_index()
        if vertex_index == -1:
            return None
        return self.vertexs[vertex_index]

    def _get_tracks_position_collection(self):
        if not(self._tracks_position_collection is None):
            return self._tracks_position_collection
        self._tracks_position_collection = PositionCollection()
        for t in self.tracks:
            self._tracks_position_collection.add(*t.xyz())
        return self._tracks_position_collection

    track_positions = property(_get_tracks_position_collection)

    def _get_vertexs_position_collection(self):
        if not(self._vertexs_position_collection is None):
            return self._vertexs_position_collection
        self._vertexs_position_collection = PositionCollection()
        for v in self.vertexs:
            self._vertexs_position_collection.add(*v.xyz())
        return self._vertexs_position_collection

    vertex_positions = property(_get_vertexs_position_collection)

    def debug_content_dump(self):
        for track in self.tracks:
            vertex = self.get_vertex_for_track(track)
            if vertex is None:
                logger.info('%s has no vertex', track)
                continue
            if vertex.track_id() != -1:
                track_for_vertex = self.get_track_by_id(vertex.track_id())
                if not track_for_vertex is None:
                    logger.debug(
                        '%s  <<  Vertex %s  <<  Track %s',
                        track, vertex.id(), track_for_vertex.id()
                        )
                else:
                    logger.debug(
                        '%s  <<  Vertex %s  <<  Track %s (does not exist)',
                        track, vertex.id(), vertex.track_id()
                        )
            else:
                logger.debug(
                    '%s  <<  Vertex %s (no parent track)',
                    track, vertex.id()
                    )

        for hit in self.calohits:

            volume = 'Uns'
            if hit.inEE_:
                volume = 'EE '
            elif hit.inHsc_:
                volume = 'Hsc'
            elif hit.inHsi_:
                volume = 'Hsi'
            else:
                logger.warning('Hit %s has no HGCAL volume', hit.id())

            track_id = hit.track_id()
            if track_id == 0:
                logger.debug('Hit %s (%s) has track id 0 (no such track)', hit.id(), volume)
            else:
                try:
                    track = self.get_track_by_id(track_id)
                    logger.debug(
                        'Hit %s (%s) has track id %s which is pdgid %s',
                        hit.id(), volume, track_id, track.pdgid()
                        )
                except ValueError:
                    logger.debug(
                        'Hit %s (%s) has track id %s which does not exist',
                        hit.id(), volume, track_id
                        )


class PositionCollection(object):
    """docstring for PositionCollection"""
    def __init__(self):
        super(PositionCollection, self).__init__()
        self.x = []
        self.y = []
        self.z = []
        self.concat = []
    
    def add(self, x, y, z):
        self.x.append(x)
        self.y.append(y)
        self.z.append(z)
        self.concat.extend([x, y, z])

    def xmin(self):
        return min(self.x)
    def xmax(self):
        return max(self.x)
    def ymin(self):
        return min(self.y)
    def ymax(self):
        return max(self.y)
    def zmin(self):
        return min(self.z)
    def zmax(self):
        return max(self.z)

    def minmax_xyz(self):
        return self.xmin(), self.ymin(), self.zmin(), \
            self.xmax(), self.ymax(), self.zmax()

    def as_array(self):
        return array('f', self.concat)

    def as_tpolymarker3d(self, marker_style=9):
        r = ROOT.TPolyMarker3D(
            len(self.x),
            self.as_array(),
            marker_style
            )
        ROOT.SetOwnership(r, False)
        return r

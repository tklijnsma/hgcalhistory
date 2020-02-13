#  Towards Exposing the Truth for HGCAL

This repo contains some code to interpret the GEN-level .root-files outputted by a (e.g.) muon gun.

It now requires also a new DataFormat `PCaloHitWithPosition`, which is like a PCaloHit but contains also the position information (clearly this isn't friendly on disk usage but for this history-debugging effort it should be okay). The data format can be found here: https://github.com/tklijnsma/DataFormats-HGCALHistoryFormats .

## Installation

```
cmsrel CMSSW_11_0_0_pre10
cd CMSSW_11_0_0_pre10/src
cmsenv

git clone https://github.com/tklijnsma/DataFormats-HGCALHistoryFormats.git DataFormats/HGCALHistoryFormats
scram b

virtualenv hgcalenv
source hgcalenv/bin/activate
git clone https://github.com/tklijnsma/hgcalhistory.git
pip install -e hgcalhistory
```

## Example

```
import hgcalhistory
import os.path as osp

def make_plots_one_rootfile(rootfile):
    hgcalhistory.rootutils.PLOTDIR = 'testplots'
    for i_event, rootevent in enumerate(hgcalhistory.EventFactory(rootfile)):
        hgcalhistory.logger.info('Processing i_event %s in %s', i_event, rootfile)
        event = hgcalhistory.Event(rootevent)
        # Skip events that don't have a photon or no hits in EE
        if not event.has_photon(): continue
        if not event.has_calohits_inEE(): continue
        name = osp.basename(rootfile).replace('.root', '') + '_' + str(i_event)
        hgcalhistory.plots.Plot3DWithCaloHits(name).plot(event)
        hgcalhistory.plots.HitsPlotSplitColorCoded(name).plot(event)
        hgcalhistory.plots.HitsPlotSplitColorCoded(name, color_coding='pdgid').plot(event)

make_plots_one_rootfile(
    'root://cmseos.fnal.gov//store/user/klijnsma/hgcal/history/4796403_EminFinePhoton500p0_EminFineTrack10000p0_MuonPt100p0/5_PCaloHitPositions_1006_numEvent50.root',
    )
```

## Example .root file from muon gun

There is an example file available in `root://cmseos.fnal.gov//store/user/klijnsma/hgcal/history/4796403_EminFinePhoton500p0_EminFineTrack10000p0_MuonPt100p0/5_PCaloHitPositions_1006_numEvent50.root` . If you can't access it, email me and I'll copy it to CERN EOS.

If you want to generate samples yourself, see https://github.com/tklijnsma/HGCALDev-PCaloHitWithPostionProducer .
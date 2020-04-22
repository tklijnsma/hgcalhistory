import uuid
import ROOT

PDGID_COLORS = {
    1  :  16, # Unspecified track, lightgrey
    13 :  9, # muon, violet
    11 :  ROOT.kGreen+3, # electron, dark green
    22 :  2, # photon, red
    211 : ROOT.kOrange+7  # pion, orange
    }
PDGID_OTHER_COLOR = 13 # Anything else, darkgray

PDGID_TITLES = {
    1 : '?',
    13 : '#mu',
    11 : 'e',
    22 : '#gamma',
    211 : '#pi',
    }
PDGID_OTHER_TITLE = 'other'

def pdgid_to_color(pdgid):
    return PDGID_COLORS.get(abs(pdgid), PDGID_OTHER_COLOR)

def pdgid_to_title(pdgid):
    return PDGID_TITLES.get(abs(pdgid), PDGID_OTHER_TITLE)

def pdgid_legend_dummies():
    # Create dummy objects
    dummies = []
    for pdgid in sorted(PDGID_COLORS.keys() + [ -999999 ]):
        dummy = ROOT.TGraph(1)
        dummy.SetName(str(uuid.uuid4()))
        dummy.SetTitle(pdgid_to_title(pdgid))
        dummy.SetPoint(0, -999., -999.)
        color = pdgid_to_color(pdgid)
        dummy.SetLineColor(color)
        dummy.SetMarkerColor(color)
        ROOT.SetOwnership(dummy, False)
        dummies.append(dummy)
    return dummies


# HGCAL layers

layers = range(1, 28)
z_pos_layers = [
    322.10275269, 323.04727173, 325.07275391, 326.01730347, 328.04275513,
    328.98727417, 331.01272583, 331.95724487, 333.98275757, 334.92724609,
    336.95275879, 337.89724731, 339.92276001, 340.86727905, 342.89273071,
    343.83724976, 345.86276245, 346.80725098, 348.83276367, 349.7772522,
    351.80276489, 352.7472229,  354.77279663, 355.71725464, 357.74276733,
    358.68725586, 360.71276855, 361.65725708
    ]
z_neg_layers = [
    -322.10275269, -323.04727173, -325.07275391, -326.01730347, -328.04275513,
    -328.98727417, -331.01272583, -331.95724487, -333.98275757, -334.92724609,
    -336.95275879, -337.89724731, -339.92276001, -340.86721802, -342.89279175,
    -343.83724976, -345.86276245, -346.80725098, -348.83276367, -349.7772522,
    -351.80276489, -352.74728394, -354.7727356,  -355.71725464, -357.74276733,
    -358.68725586, -360.71276855, -361.65725708,
    ]

hgcal_zmin_pos = min(z_pos_layers)
hgcal_zmax_pos = max(z_pos_layers)
hgcal_zmin_neg = min(z_neg_layers)
hgcal_zmax_neg = max(z_neg_layers)

def in_hgcal(z):
    """
    Determines whether z is in hgcal
    """
    return in_hgcal_pos(z) or in_hgcal_neg(z)

def in_hgcal_pos(z):
    return z >= hgcal_zmin_pos and z <= hgcal_zmax_pos

def in_hgcal_neg(z):
    return z >= hgcal_zmin_neg and z <= hgcal_zmax_neg

def get_z_for_layer(layer, do_endcap='+'):
    if not layer in layers:
        raise ValueError(
            'Layer {0} is not registered'.format(layer)
            )
    index = layers.index(layer)
    if do_endcap == '+':
        return z_pos_layers[index]
    else:
        return z_neg_layers[index]

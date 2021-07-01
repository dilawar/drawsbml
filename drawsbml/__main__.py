__author__ = "Dilawar Singh"
__email__ = "dilawar.s.rajput@gmail.com"
__copyright__ = "Copyright 2017-, Dilawar Singh"

import libsbml
import networkx as nx
import subprocess
import re

import typing as T

from pathlib import Path

import logging

logger = logging.getLogger(__name__)


GRAPHVIZ_OPTIONS = ["-Gsplines=ortho", "-Goverlap=prism", "-Granksep=2", "-Gnodesep=1"]


def path_to_label(path):
    return path.split("/")[-1]


def elem_to_label(elem):
    name = elem.name or elem.id
    name = re.sub(r'\[(\w+)\]', r'\n\1', name)
    return name.split("/")[-1]


def get_path(n, compt=""):
    if compt:
        return n.getName()
    else:
        return "/%s/%s" % (compt, n.getName())


def color_hex(color, prefix="#"):
    if len(color) == 3:
        color = color + (255,)
    hexColor = prefix + "".join(["%02x" % x for x in color])
    return hexColor


class SBML:
    """
    SBML class
    """

    def __init__(self, filepath: T.Optional[Path] = None):
        self.sbml = None
        self.filepath = filepath
        self.model = None
        self.compartments: T.Dict[str, T.Any] = {}
        self.species: T.Dict[str, T.Any] = {}
        self.reactions: T.Dict[str, T.Any] = {}
        self.currentCompt = ""
        self.g = nx.DiGraph()
        if filepath is not None:
            self.load(filepath)

    def load(self, filepath: Path):
        assert filepath.exists()
        self.filepath = filepath
        try:
            self.sbml = libsbml.readSBML(self.filepath)
        except Exception as e:
            logger.error(f"Failed to load {self.filepath}")
            logger.error(f"\tError was {e}")
            quit(0)
        logger.info("SBML is loaded")

    def addSpecies(self, elem):
        baseCompt = self.compartments[elem.getCompartment()]
        path = "%s/%s" % (baseCompt, elem.id)
        color = (0, 0, 255, 100)
        if elem.getConstant():
            color = (0, 255, 0, 100)

        self.g.add_node(
            path,
            type="species",
            label=elem_to_label(elem),
            color="red",
            shape="rect",
            #fillcolor=color_hex(color),
            #style="filled",
            fontsize=8,
        )
        self.species[elem.id] = path
        logger.debug("Added Species elem %s" % path)

    def getStoichiometry(self, s):
        if s.getStoichiometry():
            return int(s.getStoichiometry())
        else:
            return 1

    def addKineticLaw(self, klaw, reacpath):
        kmath = klaw.getMath()
        mathExpr = libsbml.formulaToString(kmath)

        # localParams = klaw.getListOfLocalParameters()

        # Draw edge from node to reaction.
        allNodes = [kmath]
        while len(allNodes) > 0:
            n = allNodes.pop()
            npath = get_path(n, self.currentCompt)
            species = self.species.get(npath, "")
            if species:
                self.g.add_edge(species, reacpath)

            for i in range(n.getNumChildren()):
                c = n.getChild(i)
                allNodes.append(c)

        logger.debug("KLAW %s" % mathExpr)

    def addReaction(self, elem):
        logger.info(f"Adding reaction id {elem}")
        compt = elem.getCompartment() or self.currentCompt
        assert self.currentCompt, (
            "I could not determine compartment for reaction %s" % elem.id
        )

        curCompt = self.compartments[compt]
        reacid = elem.id
        reacpath = "%s/%s" % (curCompt, reacid)

        subs = elem.getListOfReactants()
        prds = elem.getListOfProducts()
        subs1, prds1 = [], []

        color = (0, 0, 255, 100)
        self.g.add_node(
            reacpath,
            type="reaction",
            label=path_to_label(reacpath),
            # xlabel=elem_to_label(elem),
            shape="ellipse",
            fillcolor=color_hex(color),
            style="filled",
        )

        klaw = elem.getKineticLaw()
        if klaw is not None:
            self.addKineticLaw(klaw, reacpath)

        for s in subs:
            sname = s.getSpecies()
            spath = self.species[sname]
            for _ in range(self.getStoichiometry(s)):
                self.g.add_edge(spath, reacpath)
                subs1.append(spath)

        for p in prds:
            pname = p.getSpecies()
            ppath = self.species[pname]
            for _ in range(self.getStoichiometry(p)):
                self.g.add_edge(reacpath, ppath)
                prds1.append(ppath)

        logger.info(
            "Added reaction: %s <--> %s" % (" + ".join(subs1), " + ".join(prds1))
        )

    def addCompartment(self, c, parent):
        comptPath = "%s/%s" % (parent, c.id)
        logger.info("Loading compartment %s" % comptPath)
        self.compartments[c.id] = comptPath
        self.currentCompt = c.id

    def prune_graph(self):
        disconnectedNodes = [
            node for node, deg in dict(self.g.degree()).items() if deg == 0
        ]
        for n in disconnectedNodes:
            logger.warning(f"Disconnected node {n}")
        self.g.remove_nodes_from(disconnectedNodes)

    def generate_graph(self):
        root = ""
        self.model = self.sbml.getModel()
        [
            self.addCompartment(compt, root)
            for compt in self.model.getListOfCompartments()
        ]

        # logger.info(f"Total species {self.model.getNumSpecies()}")
        # logger.info(f"Total reactions {self.model.getNumReactions()}")

        [self.addSpecies(species) for species in self.model.getListOfSpecies()]
        [self.addReaction(reac) for reac in self.model.getListOfReactions()]
        self.prune_graph()

    def write_topology(self, outfile):
        nx.drawing.nx_pydot.write_dot(self.g, outfile)
        logger.info("Wrote topology to %s" % outfile)
        return outfile

    def plot_gv(self, program, gvfile, outfile, extra=[]) -> Path:
        outfile = outfile or "%s.png" % gvfile
        outfile = Path(outfile)
        ext = outfile.suffix[1:]  # remove leading '.'
        cmd = [program] + extra + [f"-T{ext}", gvfile, "-o", str(outfile)]
        logger.debug(" executing : %s" % " ".join(cmd))
        try:
            s = subprocess.run(cmd, check=True, capture_output=True)
            logger.debug(s.stdout)
        except Exception as e:
            logger.error(f"Failed to plot because command `{' '.join(cmd)}` failed!")
            raise e

        return outfile

    def draw(self, **kwargs):
        gvfile = kwargs.get("gv_file", "") or "%s.gv" % kwargs["input"]
        self.write_topology(gvfile)
        outfile = self.plot_gv(
            program=kwargs["graphviz_program"],
            gvfile=gvfile,
            extra=GRAPHVIZ_OPTIONS + kwargs.get("gv_extra", []),
            outfile=kwargs.get("output", ""),
        )
        logger.info("Wrote image to %s" % outfile)


def run(**kwargs):
    infile = Path(kwargs["input"])
    assert infile.exists()

    sbml = SBML(infile)
    sbml.generate_graph()
    sbml.draw(**kwargs)


def main():
    import argparse

    # Argument parser.
    description = """Draw SBML"""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--input", "-i", required=True, help="Input file. Must be a valid SBML file."
    )
    parser.add_argument(
        "--output",
        "-o",
        required=False,
        help="Output file. If not given input+.png is used.",
    )
    parser.add_argument(
        "--graphviz-program",
        "-p",
        required=False,
        default="neato",
        help="Which graphviz layout engine to use (default neato)"
        "e.g. neato|dot|twopi|circo etc.",
    )
    parser.add_argument(
        "--gv-extra",
        "-e",
        required=False,
        action="append",
        default=[],
        help="Extra argument passed to graphviz program e.g. -Gsplines=slines",
    )
    args = parser.parse_args()
    run(**vars(args))

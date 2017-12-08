#!/usr/bin/env python

"""
sbml_to_graph.py: 

"""
    
__author__           = "Dilawar Singh"
__copyright__        = "Copyright 2017-, Dilawar Singh"
__version__          = "1.0.0"
__maintainer__       = "Dilawar Singh"
__email__            = "dilawars@ncbs.res.in"
__status__           = "Development"

import sys
import os
import matplotlib.pyplot as plt
import numpy as np
import libsbml
import networkx as nx
import subprocess

import logging
logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
        datefmt='%m-%d %H:%M'
    )


def path_to_label( path ):
    return path.split( '/' )[-1]

def get_path( n, compt = ''):
    if compt:
        return n.getName( )
    else:
        return '/%s/%s' % (compt, n.getName( ))

def color_hex( color, prefix = '#' ):
    if len( color ) == 3:
        color = color + (255,)
    hexColor = prefix + ''.join( [ '%02x' % x for x in color ] )
    return hexColor


class SBML( ):
    """
    SBML class
    """

    def __init__(self, filepath = '' ):
        self.sbml = None
        self.filepath = filepath
        self.model = None
        self.compartments = { }
        self.species = { }
        self.reactions = { }
        self.currentCompt = ''
        self.g = nx.DiGraph( )
        if filepath:
            self.load( filepath  )

    def load( self, filepath ):
        self.filepath = filepath
        try:
            self.sbml = libsbml.readSBML( self.filepath )
        except Exception as e:
            logging.error( 'Failed to load %s' % self.filepath )
            logging.error( '\tError was %s' % e )
            quit( -1 )
        logging.info( "SBML is loaded" )

    def addSpeciesById( self, i ):
        elem = self.model.getSpecies( i )
        baseCompt = self.compartments[ elem.getCompartment( ) ]
        path = '%s/%s' % ( baseCompt, elem.id)
        color = (0,0,255,100)
        if elem.getConstant( ):
            color = (0,255,0,100)

        self.g.add_node( path
                , type = 'species'
                , label = path_to_label( path ) 
                #, xlabel = path_to_label( path ) 
                , color = 'red'
                , shape = 'circle'
                , fillcolor = color_hex( color )
                , style = 'filled'
                , fontsize = 8
                )
        self.species[ elem.id ] = path
        logging.debug( "Added Species elem %s" % path )

    def getStoichiometry( self, s ):
        if s.getStoichiometry( ):
            return int( s.getStoichiometry( ) )
        else:
            return 1

    def addReactionById( self, i ):
        elem = self.model.getReaction( i )
        compt = elem.getCompartment( ) or self.currentCompt
        assert self.currentCompt, \
            "I could not determine compartment for reaction %s" % elem.id 

        curCompt = self.compartments[ compt ] 
        reacid = elem.id 
        reacpath = '%s/%s' % (curCompt, reacid )

        subs = elem.getListOfReactants( )
        prds = elem.getListOfProducts( )
        subs1, prds1 = [ ], [ ]

        self.g.add_node( reacpath
                , type = 'reaction'
                , label = '' #path_to_label( reacpath )
                , xlabel = path_to_label( reacpath )
                , shape = 'square'
                )

        klaw = elem.getKineticLaw( )
        kmath = klaw.getMath( )
        mathExpr = libsbml.formulaToString( kmath )
        localParams = klaw.getListOfLocalParameters( )

        # Draw edge from node to reaction.
        allNodes = [ kmath ]
        while len( allNodes ) > 0:
            n = allNodes.pop( )
            npath = get_path( n, self.currentCompt )
            species = self.species.get( npath, '' )
            if species:
                self.g.add_edge( species, reacpath )

            for i in range( n.getNumChildren( ) ):
                c = n.getChild( i )
                allNodes.append( c )

        logging.debug( 'KLAW %s' % mathExpr )


        for i, s in enumerate( subs ):
            sname = s.getSpecies( )
            spath = self.species[ sname ]
            for i in range( self.getStoichiometry( s ) ):
                self.g.add_edge( spath, reacpath )
                subs1.append( spath )

        for i, p in enumerate( prds ):
            pname = p.getSpecies( )
            ppath = self.species[ pname ]
            for i in range( self.getStoichiometry( p ) ):
                self.g.add_edge( reacpath, ppath )
                prds1.append( ppath )

        logging.debug( 'Added reaction: %s <--> %s' % (
            ' + '.join(subs1), ' + '.join(prds1) )
            )


    def addCompartmentById( self, i, parent ):
        c = self.model.getCompartment( i )
        comptPath = '%s/%s' % (parent, c.id )
        logging.info( 'Loading compartment %s' % comptPath )
        self.compartments[ c.id ] = comptPath
        self.currentCompt = c.id


    def generate_graph( self ):
        root = ''
        self.model = self.sbml.getModel( )
        [ self.addCompartmentById( i, root ) for i in
                range(self.model.getNumCompartments() ) ]
        [ self.addSpeciesById( i ) for i in 
                range( self.model.getNumSpecies( ) ) ]
        [ self.addReactionById( i ) for i in 
                range( self.model.getNumReactions( ) ) ]


    def write_topology( self, outfile ):
        nx.drawing.nx_pydot.write_dot( self.g, outfile )
        logging.info( "Wrote topology to %s" % outfile )
        return outfile 

    def plot_gv( self, program, gvfile, outfile, extra = [ ] ):
        pngfile = outfile or '%s.png' 
        cmd = [program ] + extra + [ '-Tpng', gvfile, '-o', pngfile]
        logging.debug( '| Running : %s' % ' '.join( cmd ) )
        try:
            subprocess.call( cmd )
        except Exception as e:
            logging.error( 'Failed to plot due to %s' % e )
            logging.error( '| Command : %s' % ' '.join( cmd ) )
            quit( -1 )

        return pngfile 

    def draw( self, **kwargs ):
        gvfile = kwargs.get( 'gv_file', '' ) or '%s.gv' % kwargs['input']
        self.write_topology( gvfile )
        outfile = self.plot_gv(
                program = kwargs[ 'graphviz_program' ]
                , gvfile = gvfile
                , extra = [ '-Gsplines=ortho', '-Goverlap=false'
                    , '-Gnodesep=1'] + kwargs.get( 'gv_extra', [ ] )
                , outfile = kwargs.get( 'output', '' )
                )
        logging.info( 'Wrote image to %s' % outfile )

def main( **kwargs ):
    infile = kwargs[ 'input' ]
    sbml = SBML( infile )
    sbml.generate_graph( )
    sbml.draw( **kwargs )

if __name__ == '__main__':
    import argparse
    # Argument parser.
    description = '''Draw SBML'''
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('--input', '-i'
        , required = True
        , help = 'Input file. Must be a valid SBML file.'
        )
    parser.add_argument('--output', '-o'
        , required = False
        , help = 'Output file. If not given input+.png is used.'
        )
    parser.add_argument('--graphviz-program', '-p'
        , required = False
        , default = 'neato'
        , help = 'Which graphviz layout engine to use (default neato)'
                'e.g. neato|dot|twopi|circo etc.'
        )
    parser.add_argument('--gv-extra', '-e'
        , required = False
        , action = 'append'
        , default = [ ]
        , help = 'Extra argument passed to graphviz program e.g. -Gsplines=slines'
        )
    class Args: pass 
    args = Args()
    parser.parse_args(namespace=args)
    main( **vars(args) )

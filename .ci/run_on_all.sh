#!/bin/bash

# Call is from top-level.

find sbml -type f -name "*.*ml" | xargs -I file ./drawsbml.py -i file

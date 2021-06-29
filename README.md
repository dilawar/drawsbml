# drawsbml

Draw Signalling Pathway in SBML.

# Dependencies

- graphviz
    `sudo apt install graphviz`

- python-networkx
        `pip3 install networkx --user`
    or,
        `sudo apt install python-networkx`

- libsbml
    `pip3 install python-libsbml --user`

# Usage

    ./drawsbml.py -i ./BIOMD0000000002.xml -o a.png

## help

    ./drawsbml.py -h


## Examples

Following is the drawing of [this mode](https://www.ebi.ac.uk/biomodels-main/BIOMD0000000100)

![BIOMD0000000100.xml](./sbml/BIOMD0000000100.xml.gv.png)

Following is the drawing of [this model](https://www.ebi.ac.uk/biomodels-main/BIOMD0000000200)

![BIOMD0000000200.xml](./sbml/BIOMD0000000200.xml.gv.png)

# Need help

This is a very basic script for quickly plotting a moderate size SBML model.

In case, you need help of want enhancement, please open an issue on this repository. Attach your SBML model file.

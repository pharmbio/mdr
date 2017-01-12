# MDRDB
## Database-backed GUI for analysis and management of data associated with multi-drug resistant bacteria.
_not ready for general release_

### Init
Scripts within the _cli_ and _misc_ folders are used to preprocess input data (bacterial sequencing results) and reference genomes. Some steps are performed outside these scripts.

### Data
The _data_ folder holds scripts for [MLST](http://pubmlst.org) and [CARD](https://card.mcmaster.ca) processing. The actual data are not part of this repo since they are subject to change frequently and are controlled externally.

### GUI
The _cgi_ folder holds the scripts for general interface to the processed data. The first level is the general search page, shown below.

![Screenshot](/img/ex01.png)

A breif summary of the matching hits is produced, as shown.

![Screenshot](/img/ex02.png)

Clicking an ID button produces a more detailed view of the individual result, as shown.

![Screenshot](/img/ex03b.png)

### Contact
Wesley Schaal, wesley.schaal@farmbio.uu.se  
In association with Ola Spjuth and Åsa Melhus

[![Screenshot](/img/pharmbio-logo.png)](https://pharmb.io)

Sponsors and colloraborators:
![Screenshot](/img/aff_uu.png)

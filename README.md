# sortere2osm
Converts recycling centres and containers from Sortere.no to OSM

Usage: <code>python sortere2osm.py [input_filename.json] > output_filename.osm</code>

If no input file is given data will be loaded from the Sortere.no API

Recycling containers with identical coordinates will be merged.

Wiki: [Recycling Import Norway](https://wiki.openstreetmap.org/wiki/Import/Catalogue/Recycling_Import_Norway)

API: [data.sortere.no/api/docs/](http://data.sortere.no/api/docs/)

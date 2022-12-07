#!/usr/bin/env python
# -*- coding: utf8

# sortere2osm
# Converts Sortere recycling stations from Sortere api (JSON) to osm format for import/update
# Usage: python sortere2osm.py [input_filename.json] > output_filename.osm
# If no input filename given then data will be read from Sortere api
# Reads postal codes from Bring/Posten + county names from Kartverket to get county information


import json
import cgi
import HTMLParser
import sys
import csv
import urllib2


version = "v0.2.0"

recycling_transform = {
	2: "",						# Other
	9: "batteries",				# Batteries
	13: "cars",					# Cars
	17: "rubble",				# Waste from construction and demolition
	18: "paper",				# Corrugated cardboard
	24: "tyres",				# Tyres
	26: "paper",				# Beverage carton
	29: "electrical_items",		# Electrical items waste
	31: "paper",				# Cardboard, packaging inserts
	37: "hazardous_waste",		# Hazardous waste
	40: "refund_bottles",		# Bottles, cans with deposit-refund (usually donated to charity)
	44: "second_hand",			# Items for second hand use
	46: "glass_bottles",		# Glass packaging (jars etc)
	48: "rubble",				# Large items (too big for container)
	50: "garden_waste",			# Garden waste
	56: "wood",					# Impregnated wood
	58: "scrap_metal",			# Scrap metal
	75: "organic",				# Food waste
	78: "drugs",				# Medical waste
	80: "glass_bottles",		# Light metal packaging (cans etc)
	82: "metal",				# Metal
	97: "paper",				# Paper
	99: "paper",				# Cardboard and paper
	104: "plastic_packaging",	# Plastic packaging
	110: "waste",				# Residual, general waste
	113: "metal",				# Combination of metals
	130: "clothes",				# Clothes and shoes for second hand use
	131: "wood",				# Wood
	137: "glass",				# Window glass
	143: "explosives",			# Explosive waste
	167: "hazardous_waste",		# Waste which cannot be decomposed any further and which cannot be recycled
	168: "waste",				# Non-burnable waste
	169: "polystyrene_foam",	# Polystyrene
	173: "plastic",				# Mixed plastic waste
	174: "plasterboard",		# Plasterboard
	176: "plastic",				# Plastic (not packaging)
	177: "electrical_items",	# Small appliances
	180: "waste",				# Burnable residual waste
	184: "rubble",				# Clean, solid natural substances (dirt, rocks etc.)
	185: "rubble",				# Inert waste, i.e. with no physical, chemical or organic transformation (bricks, concrete, porcelain, glass etc.)
	186: "",					# Compost (for sale at the recycling centre)
	191: "asbestos",			# Asbestos
	192: "marine_waste",		# Marine debris, waste recovered along the shores
	208: "boats",				# Small leisure boats
	209: "boats",				# Large leisure boats without inboard engine
	210: "boats"				# Large leisure boats with inboard engine
}

name_transform = [
	('Avfallsmottak', 'avfallsmottak'),
	('Avfallsdeponi', 'avfallsdeponi'),
	('Avfallsanlegg', 'avfallsanlegg'),
	('Avfallsstasjon', 'avfallsstasjon'),
	('Bruktbutikk', 'bruktbutikk'),
	('Gjenbruksstasjon', 'gjenbruksstasjon'),
	('Gjenbrukstorg', 'gjenbrukstorg'),
	('Gjenvinningsstasjon', 'gjenvinningsstasjon'),
	('Hageavfallsmottak', 'hageavfallsmottak'),
	(u'Miljøstasjon', u'miljøstasjon'),
	(u'Miljøstasjoner', u'miljøstasjon'),
	(u'miljøstasjoner', u'miljøstasjon'),
	(u'Miljøsentral', u'miljøsentral'),
	(u'Miljøpark', u'miljøpark'),
	(u'Miljøanlegg', u'miljøanlegg'),
	(u'Miljøtorg', u'miljøtorg'),
	('Ombruksstasjon', 'ombruksstasjon'),
	('Reovasjonsanlegg', 'renovasjonsanlegg'),
	('Renovasjonsplass', 'renovasjonsplass'),
	('Sorteringsanlegg', 'sorteringsanlegg')
]


# Produce a tag for OSM file

def make_osm_line(key,value):
    if value:
		parser = HTMLParser.HTMLParser()
		value = parser.unescape(value)
		encoded_value = cgi.escape(value.encode('utf-8'),True)
		print ('    <tag k="%s" v="%s" />' % (key, encoded_value))


# Concatenate address line

def get_address(street, postal_code, city):

	address = ""
	if street:
		address = street + ", "
	if postal_code:
		address = address + postal_code + " "
	if city:
		address = address + city

	return address


# Fix URL

def get_url(url):

	if url and url != "Dalekvam":
		url = url.lower()
		url = url.replace("www.", "").replace(">","").replace("<","")
		if url[0:4] != "http":
			url = "http://" + url
		return url
	else:
		return ""


# Fix name

def fix_name(name):

	name = name.strip().replace("  "," ")
	if name == name.upper():
		name = name.lower()

	for word in name_transform:
		name = name.replace(word[0], word[1])
	name = name[0].upper() + name[1:]

	return name


# Write message

def message(line):

	sys.stderr.write(line)
	sys.stderr.flush()


# Main program

if __name__ == '__main__':

	# Read all data into memory

	message ("sortere2osm %s\n" % version)
	message ("Reading data... ")

	filename = 'https://data.sortere.no/api/v3/kartpunkter?api_key=*******&limit=100000'
	
	if len(sys.argv) > 1:
		filename = sys.argv[1]

	file = urllib2.urlopen(filename)
	station_data = json.load(file)
	file.close()

	# Read county names

	filename = "https://register.geonorge.no/api/sosi-kodelister/fylkesnummer.json?"
	file = urllib2.urlopen(filename)
	county_data = json.load(file)
	file.close()

	county_names = {}
	for county in county_data['containeditems']:
		if county['status'] == "Gyldig":
			county_names[county['codevalue']] = county['label'].strip()

	# Read postal code to municipality code translation table used to determine county (first two digits of municipality code)

	municipality_id = [None] * 10000
	filename = 'https://www.bring.no/postnummerregister-ansi.txt'
	file = urllib2.urlopen(filename)
	postal_codes = csv.DictReader(file, fieldnames=['post_code','post_city','municipality_code','municipality_name','post_type'], delimiter="\t")

	for row in postal_codes:
		municipality_id[int(row['post_code'])] = row['municipality_code']
	file.close()

	# Merge containers with equal coordinates (centres and mobile containers not touched)

	message ("\nMerging duplicates... ")

	duplicates = 0
	index1 = 0
	while index1 < len(station_data['results']):
		station1 = station_data['results'][index1]
		station1['id'] = str(station1['id'])
	
		if station1['kind'] == "returpunkt":
			index2 = index1 + 1

			while index2 < len(station_data['results']):
				station2 = station_data['results'][index2]

				if (station1['lat'] == station2['lat']) and (station1['lng'] == station2['lng']) and (station2['kind'] == "returpunkt"):
					station1['merged'] = True
					station1['id'] += ";" + str(station2['id'])
					duplicates += 1

					for waste2 in station2['_embedded']['avfallstyper']:
						found = False

						for waste1 in station1['_embedded']['avfallstyper']:
							if waste1['id'] == waste2['id']:
								found = True
								break

						if not found:
							station1['_embedded']['avfallstyper'].append(waste2)

					del station_data['results'][index2]

				else:
					index2 += 1

		index1 += 1


	# Produce OSM file header

	message ("\nProducing file... ")

	print ('<?xml version="1.0" encoding="UTF-8"?>')
	print ('<osm version="0.6" generator="sortere2osm %s" upload="false">' % version)

	start_id = -1000
	node_id = start_id

	# Loop through all stores and produce OSM tags

	for station in station_data['results']:

		node_id -= 1

		# Generate tagging

		print('  <node id="%i" lat="%s" lon="%s">' % (node_id, station['lat'], station['lng']) )

		make_osm_line("amenity", "recycling")
		make_osm_line("ref:sortere", station['id'])
		make_osm_line("source", "Sortere.no")

		# Recycle container

		if station['kind'] == 'returpunkt':

			make_osm_line("recycling_type", "container")
			make_osm_line("description", fix_name(station['navn']))
			make_osm_line("ADDRESS", get_address(station['gateadresse'], station['postnummer'], station['poststed']))

			if station['beskrivelseNb']:
				make_osm_line("DESCRIPTION", station['beskrivelseNb'].strip())

		# Recycle centre

		elif station['kind'] == 'gjenvinningsstasjon':

			if (station['navnNb'][:10] != "Returpunkt") and (station['navnNb'].find("optibag") < 0):

				make_osm_line("recycling_type", "centre")
				make_osm_line("name", fix_name(station['navnNb']))
				make_osm_line("website", get_url(station['eksternUrl']))

				if station['telefonnummer']:
					make_osm_line("phone", "+47 " + station['telefonnummer'])

			else:  # Fix wrong coding in Hammerfest + "optibags"

				make_osm_line("recycling_type", "container")
				make_osm_line("description", fix_name(station['navnNb']))

			make_osm_line("ADDRESS", get_address(station['gateadresse'], station['postnummer'], station['poststed']))

		# Mobile recycle container

		elif station['kind'] == 'mobilgjenvinningsstasjon':

			make_osm_line("recycling_type", "container")
			make_osm_line("description", fix_name(station['navn']))
#			make_osm_line("opening_hours", " ".join(station['tidsbeskrivelserNb']))
			make_osm_line("website", get_url(station['hjemmesideUrl']))

			if station['telefonnr']:
				make_osm_line("phone", "+47 " + station['telefonnr'])

			if "avfallsselskap" in station['_embedded']:
				operator = station['_embedded']['avfallsselskap']
				make_osm_line("operator", operator['navn'])
				make_osm_line("ADDRESS_OPERATOR", get_address(operator['gateadresse'], operator['postnummer'], operator['poststed']))

		else:

			raise KeyError('Unknown kind: "%s"' % station['kind'])

		# Access tag for vacation homes

		if "ikon" in station:
			make_osm_line("TYPE", station['ikon'])
			if station['ikon'] == "hyttepunkt":
				make_osm_line("access", "permissive")

		# Find county from looking up postal code translation, first two digits

		if 'kommune' in station['_embedded']:
			county_id = station['_embedded']['kommune']['nummer'][0:2]
			if county_id in county_names:
				make_osm_line("COUNTY", county_names[county_id])
		elif 'postnummer' in station:
			if station['postnummer']:
				postal_code = int(station['postnummer'])
				if municipality_id[postal_code]:
					county_id = municipality_id[postal_code][0:2]
					if county_id in county_names:
						make_osm_line("COUNTY", county_names[county_id])

		# Loop waste types

		recycling_tags = []

		for waste in station['_embedded']['avfallstyper']:
			if waste['id'] in recycling_transform:
				recycling_tag = recycling_transform[waste['id']]
				if (recycling_tag != "") and not(recycling_tag in recycling_tags):
					recycling_tags.append(recycling_transform[waste['id']])
			else:
				raise KeyError('Unknown waste: "%s" - %s' % str(waste['id']), waste['navnNb'])

			make_osm_line("RECYCLING:" + str(waste['id']), waste['navnNb'])

		for tag in recycling_tags:
			make_osm_line("recycling:" + tag, "yes")

#		if (recycling_tags == []) and ("ikon" in station) and (station['ikon'] == "hyttepunkt"):  # Some containers are not taggee with waste types
#			make_osm_line("recycling:waste", "yes")

		# Note about merged containers

		if "merged" in station:
			make_osm_line("MERGED", "yes")


		# Done with OSM store node

		print('  </node>')


	# Produce OSM file footer

	print('</osm>')

	message ("\nDone: %i stations (+%i duplicates)\n" % (start_id - node_id, duplicates))

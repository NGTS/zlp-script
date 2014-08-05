def parse_section_definition(sec):
    out = {}
    coord_regions = sec.replace('[', '').replace(']', '').split(',')
    out['x'] = slice(*map(int, coord_regions[0].split(':')))
    out['y'] = slice(*map(int, coord_regions[1].split(':')))

    return out

def extract_region(data, section_definition):
    section = parse_section_definition(section_definition)
    return data[section['y'], section['x']]

def extract_overscan(hdulist):
    header = hdulist[0].header
    image = hdulist[0].data
    biassec = header['biassec']

    return extract_region(image, biassec)



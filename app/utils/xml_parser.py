import xml.etree.ElementTree as ET


def xml_to_plain_text(xml_string):
    try:
        root = ET.fromstring(xml_string)
        plain_text = "".join(root.itertext())
        return plain_text.strip()
    except ET.ParseError as e:
        print(f"Error al analizar el XML: {e}")
        return None

import xml.etree.ElementTree as ET
import pandas as pd
class XML2DataFrame:

    def __init__(self, xml_data):
        self.root = ET.XML(xml_data)

    def parse_root(self, root):
        """Return a list of dictionaries from the text and attributes of the
        children under this XML root."""
        parsed_root = dict()
        for key in root.keys():
            if key not in parsed_root:
                parsed_root[key] = root.attrib.get(key)
                
        return [parsed_root]# + [ self.parse_element(child) for child in root.getchildren() ]

    def process_data(self):
        """ Initiate the root XML, parse it, and return a dataframe"""
        structure_data = self.parse_root(self.root)
        return pd.DataFrame(structure_data)

#  xml2df = XML2DataFrame(xml_data)
#  xml_dataframe = xml2df.process_data()

from bs4 import BeautifulSoup


def normalize_xml_string(content: str) -> str:
    """
    Normalize XML by parsing and re-serializing with BeautifulSoup to
    standardize formatting.
    """
    # Parse with BeautifulSoup and re-serialize to normalize formatting
    soup = BeautifulSoup(content, features="xml")
    return str(soup).strip()

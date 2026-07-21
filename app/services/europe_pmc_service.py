"""Europe PMC Service Module.

This service handles all interactions with the Europe PMC API and XML processing.
It provides methods to fetch and extract plain text from scientific publications.

Responsibilities:
- API communication with Europe PMC
- XML parsing and text extraction
- Content processing and formatting

Author: Open Targets AI API
"""

import logging
from xml.etree import ElementTree as ET

import httpx
from defusedxml.ElementTree import fromstring as safe_fromstring
from fastapi import HTTPException

# Configure module logger
logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS AND CONFIGURATION
# =============================================================================

EUROPE_PMC_BASE_URL = 'https://www.ebi.ac.uk/europepmc/webservices/rest'

# Request configuration
REQUEST_TIMEOUT = 30  # seconds
REQUEST_HEADERS = {
    'Accept': 'application/xml',
    'User-Agent': 'Mozilla/5.0 (compatible; Research Bot)',
}

# Content extraction settings
MIN_REFERENCES_LENGTH = 50  # Minimum length to include references section


# =============================================================================
# URL BUILDING UTILITIES
# =============================================================================


def build_publication_url(pmc_id: str) -> str:
    """Build the Europe PMC full-text XML URL for a given PMC ID.

    Args:
        pmc_id (str): The PMC ID of the publication (e.g., 'PMC1234567')

    Returns:
        str: Complete URL for fetching the full-text XML

    Example:
        >>> build_publication_url('PMC1234567')
        'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC1234567/fullTextXML'
    """
    return f'{EUROPE_PMC_BASE_URL}/{pmc_id}/fullTextXML'


# =============================================================================
# XML PROCESSING UTILITIES
# =============================================================================


def extract_text_from_element(element: ET.Element) -> str:
    """Recursively extract all text content from an XML element and its children.

    This function traverses the XML tree structure and concatenates all text
    content, including text within nested elements and tail text.

    Args:
        element (ET.Element): The XML element to extract text from

    Returns:
        str: Concatenated text content with spaces between elements
    """
    text = ''

    # Add the element's direct text content
    if element.text:
        text += element.text.strip() + ' '

    # Recursively process all child elements
    for child in element:
        text += extract_text_from_element(child)
        # Add tail text (text that comes after the closing tag)
        if child.tail:
            text += child.tail.strip() + ' '

    return text


def xml_to_dict(element: ET.Element) -> dict:
    """Recursively convert an XML element to a dictionary structure.

    This is an alternative approach for XML processing that converts
    the XML tree into a nested dictionary format for easier manipulation.

    Args:
        element (ET.Element): The XML element to convert

    Returns:
        dict: Dictionary representation of the XML structure
    """
    result = {}

    for child in element:
        if len(child):  # If the child has sub-elements, recurse
            result[child.tag] = xml_to_dict(child)
        else:
            # Leaf node - store the text content
            result[child.tag] = child.text.strip() if child.text else ''

    return result


# =============================================================================
# SECTION PROCESSING FUNCTIONS
# =============================================================================


def handle_section_recursive(section: ET.Element) -> str:
    """Recursively process a section element and extract formatted text.

    This function handles the hierarchical structure of academic papers,
    processing titles, paragraphs, and nested subsections.

    Args:
        section (ET.Element): The section element to process

    Returns:
        str: Formatted text content of the section
    """
    section_text = ''

    # Extract section title
    title = section.find('title')
    if title is not None and title.text:
        section_text += f'\n{title.text.strip()}\n\n'

    # Process all paragraphs in this section
    for paragraph in section.findall('p'):
        if paragraph.text or list(paragraph):
            paragraph_text = extract_text_from_element(paragraph)
            if paragraph_text.strip():
                section_text += f'{paragraph_text.strip()}\n\n'

    # Recursively process nested subsections
    for child_section in section.findall('sec'):
        section_text += handle_section_recursive(child_section)

    return section_text


def extract_title_from_xml(root: ET.Element) -> tuple[str, bool]:
    """Extract the article title from various possible XML locations.

    Args:
        root (ET.Element): The root XML element

    Returns:
        tuple[str, bool]: (title_text, found_flag)
    """
    # Try multiple common locations for article title
    title_elem = root.find('.//article-title') or root.find('.//title-group/article-title') or root.find('.//title')

    if title_elem is not None and title_elem.text:
        logger.info('Extracted title from publication')
        return title_elem.text.strip(), True

    return '', False


def extract_abstract_from_xml(root: ET.Element) -> tuple[str, bool]:
    """Extract the abstract from various possible XML locations.

    Args:
        root (ET.Element): The root XML element

    Returns:
        tuple[str, bool]: (abstract_text, found_flag)
    """
    # Try primary abstract location
    abstract_elem = root.find('.//abstract')

    if abstract_elem is not None:
        abstract_text = extract_text_from_element(abstract_elem)
        if abstract_text.strip():
            logger.info('Extracted abstract from publication')
            return abstract_text.strip(), True

    # Try alternative abstract locations
    abstract_elem = root.find('.//article-meta//abstract') or root.find('.//front//abstract')
    if abstract_elem is not None:
        abstract_text = extract_text_from_element(abstract_elem)
        if abstract_text.strip():
            logger.info('Extracted abstract from alternative location')
            return abstract_text.strip(), True

    return '', False


def extract_body_content_from_xml(root: ET.Element) -> tuple[str, bool]:
    """Extract the main body content from the XML document.

    Args:
        root (ET.Element): The root XML element

    Returns:
        tuple[str, bool]: (body_text, found_flag)
    """
    # Find the body element
    body = root.find('.//body')
    if body is None:
        # Try alternative body structures
        body = root.find('.//article-body') or root.find('.//content')
        if body is None:
            logger.warning('No body element found, trying to extract from root')
            body = root

    if body is not None:
        body_text = ''

        # Process structured sections
        sections = body.findall('sec')
        if sections:
            logger.info(f'Found {len(sections)} main sections in body')
            for section in sections:
                body_text += handle_section_recursive(section)
        else:
            # Fallback: extract all text from body if no sections found
            logger.info('No sections found, extracting all text from body')
            body_text = extract_text_from_element(body)

        if body_text.strip():
            return body_text.strip(), True

    return '', False


def extract_references_from_xml(root: ET.Element) -> tuple[str, bool]:
    """Extract the references section if present and substantial.

    Args:
        root (ET.Element): The root XML element

    Returns:
        tuple[str, bool]: (references_text, found_flag)
    """
    refs_elem = root.find('.//ref-list') or root.find('.//references')

    if refs_elem is not None:
        refs_text = extract_text_from_element(refs_elem)
        # Only include if substantial (avoid empty or minimal reference sections)
        if refs_text.strip() and len(refs_text.strip()) > MIN_REFERENCES_LENGTH:
            logger.info('Extracted references section')
            return refs_text.strip(), True

    return '', False


# =============================================================================
# ALTERNATIVE PROCESSING METHODS
# =============================================================================


def extract_plain_text_from_dict(pub_body_json: dict) -> str:
    """Extract plain text from a dictionary representation of the XML.

    This is an alternative processing method that works with the dictionary
    structure created by xml_to_dict().

    Args:
        pub_body_json (dict): Dictionary representation of the publication XML

    Returns:
        str: Extracted plain text content
    """

    def handle_paragraph(paragraph_data, title: str) -> str:
        """Process paragraph data from dictionary structure."""
        section_text = [title + ' \n ']

        if isinstance(paragraph_data, list):
            section_text.extend((p if isinstance(p, str) else p.get('#text', '')) + ' \n ' for p in paragraph_data)
        else:
            text = paragraph_data if isinstance(paragraph_data, str) else paragraph_data.get('#text', '')
            section_text.append(text + ' \n ')

        return ''.join(section_text)

    def handle_section(element_data: dict) -> str:
        """Recursively process section data from dictionary structure."""
        text_parts = []

        if isinstance(element_data.get('sec'), list):
            for section in element_data['sec']:
                title = section.get('title', '')
                paragraphs = section.get('p')
                child_sections = section.get('sec')

                if paragraphs:
                    text_parts.append(handle_paragraph(paragraphs, title))
                if child_sections:
                    text_parts.append(handle_section(section))

        return ''.join(text_parts)

    return handle_section(pub_body_json)


# =============================================================================
# MAIN TEXT EXTRACTION FUNCTIONS
# =============================================================================


def extract_plain_text_from_xml(xml_data: str, include_references: bool = False) -> str:
    """Comprehensive extraction of plain text from Europe PMC XML.

    This function extracts major components of a scientific publication:
    - Title
    - Abstract
    - Main body content (all sections and subsections)
    - References (optional, excluded by default to reduce token usage)

    The extracted text is formatted with clear section headers for easy
    identification of different parts of the publication.

    Args:
        xml_data (str): Raw XML string from Europe PMC
        include_references (bool): Whether to include references section (default: False)

    Returns:
        str: Formatted plain text with publication content

    Raises:
        HTTPException: If XML parsing fails or no content is found
    """
    try:
        root = safe_fromstring(xml_data)
        full_text = ''

        # 1. Extract Title
        title_text, title_found = extract_title_from_xml(root)
        if title_found:
            full_text += f'TITLE: {title_text}\n\n'

        # 2. Extract Abstract
        abstract_text, abstract_found = extract_abstract_from_xml(root)
        if abstract_found:
            full_text += f'ABSTRACT: {abstract_text}\n\n'

        # 3. Extract Main Body Content
        body_text, body_found = extract_body_content_from_xml(root)
        if body_found:
            full_text += f'MAIN CONTENT:\n\n{body_text}\n\n'

        # 4. Extract References (optional)
        if include_references:
            refs_text, refs_found = extract_references_from_xml(root)
            if refs_found:
                full_text += f'REFERENCES:\n{refs_text}\n\n'
        else:
            refs_found = False  # For logging purposes

        # Validate that we extracted meaningful content
        result = full_text.strip()
        if not result:
            return 'No readable content found in the publication.'

        logger.info(
            f'Successfully extracted {len(result)} characters of text '
            f'(Title: {title_found}, Abstract: {abstract_found}, '
            f'Body: {body_found}, References: {refs_found})'
        )

        return result

    except ET.ParseError as e:
        logger.error(f'Error parsing XML data: {e}')
        raise HTTPException(status_code=500, detail='Error parsing publication text')


# =============================================================================
# MAIN SERVICE FUNCTIONS
# =============================================================================


async def fetch_publication_xml(pmc_id: str) -> str:
    """Fetch raw XML content from Europe PMC for a given PMC ID.

    Args:
        pmc_id (str): The PMC ID of the publication to fetch

    Returns:
        str: Raw XML content from Europe PMC

    Raises:
        HTTPException: For various error conditions:
            - 404: Publication not found
            - 502: Invalid response format
            - 503: Europe PMC service error
            - 500: Network or processing errors
    """
    url = build_publication_url(pmc_id)
    logger.info(f'Fetching publication XML from URL: {url}')

    try:
        # Make HTTP request with timeout and appropriate headers
        logger.info(f'Requesting publication XML for PMC ID: {pmc_id}')
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(url, headers=REQUEST_HEADERS)

        # Log response details for debugging
        logger.info(f'Response status: {response.status_code}')
        logger.info(f'Response content type: {response.headers.get("content-type", "unknown")}')

        # Handle specific HTTP status codes
        if response.status_code == 404:
            logger.error(f'Publication with PMC ID {pmc_id} not found')
            raise HTTPException(status_code=404, detail=f'Publication with PMC ID {pmc_id} not found')

        if not response.is_success:
            logger.error(f'HTTP error {response.status_code}: {response.text[:500]}...')
            raise HTTPException(
                status_code=503,
                detail=f'Error fetching publication from EuropePMC (HTTP {response.status_code})',
            )

        # Validate response format
        if not response.text.strip().startswith('<'):
            logger.error(f'Invalid response format. Content preview: {response.text[:200]}...')
            raise HTTPException(status_code=502, detail='Invalid response format from EuropePMC service')

        logger.info(f'Successfully fetched XML for PMC ID {pmc_id}')
        return response.text

    except httpx.RequestError as e:
        logger.error(f'Network error for PMC ID {pmc_id}: {e}')
        raise HTTPException(
            status_code=500,
            detail='Error communicating with EuropePMC service',
        )


async def extract_publication_text(pmc_id: str, include_references: bool = False) -> str:
    """Extract plain text from a Europe PMC publication.

    This is the main service method that coordinates the complete workflow:
    1. Fetch XML from Europe PMC
    2. Parse XML content
    3. Extract plain text using multiple strategies

    Args:
        pmc_id (str): The PMC ID of the publication to process
        include_references (bool): Whether to include references section (default: False)

    Returns:
        str: Complete plain text content of the publication

    Raises:
        HTTPException: For various error conditions during processing
    """
    try:
        # Step 1: Fetch XML content
        xml_content = await fetch_publication_xml(pmc_id)

        # Step 2: Parse XML with error handling
        try:
            xml_data = safe_fromstring(xml_content)
            logger.info(f'Successfully parsed XML for PMC ID {pmc_id}')
        except ET.ParseError as e:
            logger.error(f'XML parsing error for PMC ID {pmc_id}: {e}')
            # Fallback to direct XML string processing
            return extract_plain_text_from_xml(xml_content, include_references)

        # Step 3: Try dictionary-based extraction first
        try:
            pub_body_json = xml_to_dict(xml_data)
            plain_text = extract_plain_text_from_dict(pub_body_json)

            if plain_text and len(plain_text.strip()) > 0:
                logger.info(f'Successfully extracted text using dictionary method for PMC ID {pmc_id}')
                return plain_text
        except Exception as e:
            logger.warning(f'Dictionary extraction failed for PMC ID {pmc_id}: {e}')

        # Step 4: Fallback to comprehensive XML parsing
        logger.info(f'Using comprehensive XML parsing for PMC ID {pmc_id}')
        return extract_plain_text_from_xml(xml_content, include_references)

    except Exception as e:
        logger.error(f'Unexpected error processing PMC ID {pmc_id}: {e}')
        raise HTTPException(
            status_code=500,
            detail='Unexpected error processing publication text',
        )

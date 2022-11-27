from functools import partial
import json
from operator import attrgetter
import re
import time
from urllib.parse import urlencode, urljoin
import warnings


BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
PMC_URL = "esearch.fcgi?retmax=10000&"
SUMMARY_URL = "esummary.fcgi?&retmode=json&"
def build_pmc_search_url(term):
    if " " in term:
        term = f'"{term}"'
    return f"{BASE_URL}{PMC_URL}" + urlencode(
        {"db": "pmc", "term": term}
    )

def build_pmc_summary_url(pmcid):
    return f"{BASE_URL}{SUMMARY_URL}" + urlencode(
        {"db": "pmc", "id": pmcid}
    )

def get_pmcids(term):
    query = build_pmc_search_url(term)
    html = BeautifulSoup(requests.get(query).text, features='xml')
    try:
        n_results = int(html.find_all("Count")[0].text)
        if n_results > 10000:
            warnings.warn(
                "more than 10000 results, this silly hack may be "
                "too limited. try a more restrictive search or call me"
            )
    except (IndexError, AttributeError, KeyError, TypeError):
        warnings.warn(
            "couldn't parse count on initial metadata result, "
            "there could be so many results we don't know about, "
            "it boggles the mind"
        )
    ids = html.find_all("Id")
    return tuple(
        map(lambda c: int(c[0]), map(attrgetter("contents"), ids))
    )

def get_pmcid_metadata(pmcid):
    sum_query = build_pmc_summary_url(pmcid)
    results = json.loads(requests.get(sum_query).text)
    if 'error' in results.keys():
        raise ConnectionRefusedError("Server has raised rate limit error.")
    uid = results['result']['uids'][0]
    citation = results['result'][uid]
    return {
        'year':re.search(r"(19|20)\d{2}", citation['pubdate']).group(),
        'title': citation['title'],
        'pmcid': pmcid
    }
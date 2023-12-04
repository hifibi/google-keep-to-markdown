# stash.py
from datetime import datetime
from pathlib import Path
import logging
import requests
from typing import List
import apputils as utils
from local_secrets.db_config import couch as dcfg

logger = logging.getLogger()

def post_to_endpoint(endpoint: str, docs = None, **kwargs) -> dict:
    """
    Post doc(s) to endpoint with keyword args

    Parameters
    - docs (list or dictionary): list of dictionaries or single dictionary to be posted
    """

    # database configuration
    couchdb_address = dcfg.get("address")
    database = dcfg.get("database")
    username = dcfg.get("username")
    password = dcfg.get("password")

    # base_url = f"{couchdb_address}/{database}"
    base_url = "/".join([couchdb_address,database])
    logger.debug(f'{base_url=}')

    # url = base_url + endpoint
    url = "/".join([base_url,endpoint])
    logger.debug(f'{url=}')
    payload = {"docs": docs} if docs is not None else None

    response = None
    try:
        # POST bulk data to CouchDB with HTTP authentication
        response = requests.post(url, json=payload, auth=(username, password))

        # Check if the request was successful
        if response.status_code == 201:
            logger.info(f"{len(docs)} documents successfully stored in CouchDB.")
        else:
            logger.info(f"Failed to store documents. Status code: {response.status_code}")
            logger.info(response.text)

    except Exception as e:
        logger.info(f"Error: {e}")
        sdate = datetime.now().strftime('%Y-%m-%d_%H%M%S')
        string_data = str([str(d) for d in docs])
        tgt = Path('/local_secrets/stash_dump')
        if not tgt.exists():
            tgt.mkdir(parents=True)
        utils.write_text_file(string_data, tgt / sdate)

    return response


def add_new_doc(doc: dict) -> dict:
    """
    Write a dictionary to CouchDB using bulk_docs API.

    Parameters:
    - doc (list): dictionary to be stored in CouchDB.
    """

    endpoint = ""
    return post_to_endpoint(endpoint=endpoint, docs=doc)



def stash_bulk(docs: List[dict]):
    """
    Write a list of dictionaries to CouchDB using bulk_docs API.

    Parameters:
    - docs (list): List of dictionaries to be stored in CouchDB.
    """

    endpoint = "_bulk_docs"
    return post_to_endpoint(endpoint=endpoint, docs=docs)

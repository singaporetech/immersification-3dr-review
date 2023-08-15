# -*- coding: utf-8 -*-
"""
Created on Tue Jun 20 15:58:51 2023
@author: Nirmal

Retrieve papers using PapersWithCode API and filter based on various criteria.
Refer: https://paperswithcode.com/api/v1/docs/

Dependencies:
    paperswithcode (for paperswithcode API)
    $ pip install paperswithcode-client

    requests (for HTTP requests)
    $ conda install requests
"""

import sys
import os
import time
import multiprocessing
import requests
from tqdm import tqdm
from datetime import datetime
from paperswithcode import PapersWithCodeClient


# -------------------------------- Parameters ---------------------------------
# Subject area (task) of the papers to search for.
# IDs can be obtained from the paperswithcode URL.
# e.g., https://paperswithcode.com/task/3d-reconstruction
task_id = '3d-reconstruction'

# Paperswithcode API does not support the retrieval of all papers at once.
# It returns search results as pages with a max limit of 500 items per page.
# No need to change this value.
items_per_page = 500

# Only papers pulished within these dates will be retained.
# Date should be a string in 'yyyy-mm-dd' format.
min_date = '2018-01-01'
max_date = '2023-07-31'

# Query to search in Title and Abstract.
# Convert the AND-OR query to nested list format as shown below.
# ('a' OR 'b') AND ('c' or 'd' or 'e')  ->  [['a', 'b'], ['c', 'd', 'e']]
# and_or_query = [['online', 'progressive', 'collaborative', 'real-time'],
#                 ['3D', 'scene', 'depth'],
#                 ['reconstruct', 'estimation', 'prediction']]
and_or_query = [['online', 'progressive', 'collab', 'real-time', 'end-to-end']]

# Exclude papers containing any of these terms in the Title or Abstract(?).
# Be careful when using small words (face, hand, etc) as they will match with
# many generic words (surface, interface, handle, etc).
not_query = ['facial', 'human', 'underwater', 'road surface',
             'morphable', 'deform',
             'x-ray', 'histology', 'endoscopic']

# Text formatting of the list of papers (Accepeted values = 1 or 2).
# 1: [Without abstract] Single line for each paper with idx, title, and year of publication.
# 2: [With abstract] Multi-line with idx, title, year, and abstract on separate
#    lines, and an empty line between individual papers.
format_type = 2

# Whether to save the included and discarded list of papers to file
is_save = True
# -----------------------------------------------------------------------------


# Extract all values of a particular key from json data
def extract_values(json_data, key):
    if isinstance(json_data, dict):
        for k, v in json_data.items():
            if k == key:
                yield v
            elif isinstance(v, (dict, list)):
                yield from extract_values(v, key)
    elif isinstance(json_data, list):
        for item in json_data:
            yield from extract_values(item, key)


# Check if a string contains at least one substring from each nested list
def check_substrings(string, nested_lists):
    for sublist in nested_lists:
        found = False
        for substring in sublist:
            if substring in string:
                found = True
                break
        if not found:
            return False
    return True


# Create a folder with timestamp as folder name
def create_timestamp_folder():
    timestamp = time.strftime("%Y-%m-%d %H_%M_%S")
    folder_name = str(timestamp)
    try:
        os.makedirs(folder_name)
    except OSError as error:
        print(error)
    return folder_name


# Save papers' metadata to file
def save_to_file(papers, papers_idx, folder_name, file_name, format_type=1):
    content = ''
    for i in (papers_idx):
        paper = papers[i]
        if format_type==1:
            content = content + str(i) + " " + paper['title'] + ", " + str(paper['published']) + "\n"
        elif format_type==2:
            content = content + str(i) + "\n" + paper['title'] + "\n" + str(paper['published']) \
                + "\n" + str(paper['abstract']) + "\n\n"
        else:
            raise ValueError('Invalid format_type, use values 1 or 2.')

    # Create new file and write contents to file
    file_path = os.path.join(folder_name, file_name)
    with open(file_path, 'wb') as file:
        file.write(content.encode('utf-8'))

    return content


# Taken from: https://stackoverflow.com/a/60376121/7046003
class Logger(object):
    """
    Class to log output of the command line to a log file

    Usage:
        log = Logger('logfile.log')
        log.start()
        print("inside file")
        log.stop()
        print("outside file")
        log.start()
        print("inside again")
        log.stop()
    """

    def __init__(self, filename):
        self.filename = filename

    class Transcript:
        def __init__(self, filename):
            self.terminal = sys.stdout
            self.log = open(filename, "a")
        def __getattr__(self, attr):
            return getattr(self.terminal, attr)
        def write(self, message):
            self.terminal.write(message)
            self.log.write(message)
        def flush(self):
            pass

    def start(self):
        sys.stdout = self.Transcript(self.filename)

    def stop(self):
        sys.stdout.log.close()
        sys.stdout = sys.stdout.terminal


# Main function
if __name__=="__main__":
    # Intialise API client
    client = PapersWithCodeClient()

    # (Temporary) list of retrieved results
    results = []

    # Create a new folder inside the working directory to save log and data
    if is_save:
        folder_name = create_timestamp_folder()
        file_path = os.path.join(folder_name, 'log.txt')
        log = Logger(file_path)
        log.start()

    # Print parameters
    cur_time = time.strftime('%d %b %Y, %H:%M:%S')
    print(cur_time + '\n')
    print('task_id: {}'.format(task_id))
    print('items_per_page: {}'.format(items_per_page))
    print('min_date: {}'.format(min_date))
    print('max_date: {}'.format(max_date))
    print('and_or_query: {}'.format(and_or_query))
    print('not_query: {}'.format(not_query))
    print('format_type: {}'.format(format_type))

    # ----------------- Grab the first page of search results -----------------
    # NB: Paperswithcode API page number starts at 1, not 0
    page_no = 1

    print('')
    print('Retrieving pages of \'{}\''.format(task_id))
    print('Fetching page {}...'.format(page_no), end='')

    url = "https://paperswithcode.com/api/v1/tasks/" + task_id + "/papers/"
    params = {'page':page_no, 'items_per_page':items_per_page}

    r = requests.get(url=url, params=params)
    data = r.json()
    results.append(data['results'])

    n_retrieved = len(data['results'])
    print('contains {} papers'.format(n_retrieved))
    # -------------------------------------------------------------------------

    # ----------------------- Grab the remaining pages ------------------------
    # `data['next']` contains url for the next page, `None` if its the last page
    while data['next']:
        page_no = page_no + 1
        print('Fetching page {}...'.format(page_no), end='')

        r = requests.get(url=data['next'])
        data = r.json()
        results.append(data['results'])

        n_retrieved = len(data['results'])
        print('contains {} papers'.format(n_retrieved))
    print('Retrieval done!')
    # -------------------------------------------------------------------------

    # Merge the retrieved pages into single list of dict
    papers = []
    for result in results:
        papers = papers + result

    # Print total number of retrieved papers and pages
    print('')
    print('Total pages retrieved  = {}'.format(len(results)))
    print('Total papers retrieved = {}'.format(len(papers)))

    # Check if the the no. of papers retrieved matches the server generated no.
    # `data['count']` from GET response shows the paper count.
    assert(data['count']==len(papers))

    # Extract id of all papers
    papers_id = list(extract_values(papers, 'id'))

    # Index numbers of all papers
    papers_idx = list(range(len(papers)))

    # Save full list of papers to file
    if is_save:
        file_name = 'papers_list_1.txt'
        papers_list_1 = save_to_file(papers, papers_idx, folder_name, file_name, format_type)

    # -------- Find which of the retrieved papers have associated code --------
    papers_wcode_id = []
    papers_wcode_idx = []

    print('')
    print('Filtering out papers that do not have associated code...', end='')

    # List of all paper URLs
    urls = []
    for id in papers_id:
        url = "https://paperswithcode.com/api/v1/papers/" + id + "/repositories/"
        urls.append(url)

    n_cpu = multiprocessing.cpu_count()
    if n_cpu < 4:
        # Sequential HTTP requests
        # NB: Too slow, takes ~14 min for 1270 papers
        for i,url in tqdm(enumerate(urls)):
            r = requests.get(url=url)

            # `r.json()['count']` shows how many implementations each paper has
            if r.json()['count'] > 0:
                papers_wcode_id.append(papers_id[i])
                papers_wcode_idx.append(i)
    else:
        # Concurrent HTTP requests via threading
        # NB: Takes only 30 seconds for 1270 papers when max_workers=10
        from concurrent.futures import ThreadPoolExecutor

        def get_url(url):
            return requests.get(url)

        # No. of threads to use for concurrent HTTP requests
        max_workers = n_cpu - 2

        # Make HTTP requests
        with ThreadPoolExecutor(max_workers=max_workers) as pool:
            responses = list(pool.map(get_url, urls))

        # Collect HTTP responses
        for i,response in enumerate(responses):
            if response.json()['count'] > 0:
                papers_wcode_id.append(papers_id[i])
                papers_wcode_idx.append(i)

    print('done!')
    # -------------------------------------------------------------------------

    # Save filtered list of papers to file
    if is_save:
        file_name = 'papers_list_2.txt'
        papers_list_2 = save_to_file(papers, papers_wcode_idx, folder_name, file_name, format_type)

    # Save discarded list of papers to file
    discard_wcode_idx = [idx for idx in papers_idx if idx not in papers_wcode_idx]
    if is_save:
        file_name = 'discard_list_2.txt'
        discard_list_2 = save_to_file(papers, discard_wcode_idx, folder_name, file_name, format_type)

    print('Removed {} papers from list'.format(len(papers_id)-len(papers_wcode_id)))
    print('Remaining papers in list = {}'.format(len(papers_wcode_id)))

    # -------------- Filter papers based on year of publication ---------------
    papers_year_id = []
    papers_year_idx = []

    # Convert string to datetime object
    min_date = datetime.strptime(min_date, '%Y-%m-%d')
    max_date = datetime.strptime(max_date, '%Y-%m-%d')

    print('')
    print('Filtering out papers published before {} and after {}...'.format(min_date, max_date), end='')

    # Filter out publications outside the specified time period
    for i,idx in enumerate(papers_wcode_idx):
        if (papers[idx]['published'] is not None):
            pub_date = datetime.strptime(papers[idx]['published'], '%Y-%m-%d')
            if (min_date <= pub_date) and (pub_date <= max_date):
                papers_year_id.append(papers_id[idx])
                papers_year_idx.append(idx)

    print('done!')
    print('Removed {} papers from list'.format(len(papers_wcode_id)-len(papers_year_id)))
    print('Remaining papers in list = {}'.format(len(papers_year_id)))

    # Save filtered list of papers to file
    if is_save:
        file_name = 'papers_list_3.txt'
        papers_list_3 = save_to_file(papers, papers_year_idx, folder_name, file_name, format_type)

    # Save discarded list of papers to file
    discard_year_idx = [idx for idx in papers_wcode_idx if idx not in papers_year_idx]
    if is_save:
        file_name = 'discard_list_3.txt'
        discard_list_3 = save_to_file(papers, discard_year_idx, folder_name, file_name, format_type)
    # -------------------------------------------------------------------------

    # -------------- Filter papers based on AND-OR search query ---------------
    papers_aoq_id = []
    papers_aoq_idx = []

    # Convert all query strings to lowercase
    and_or_query = [[qq.lower() for qq in q] for q in and_or_query]

    print('')
    print('Filtering papers based on AND-OR query...', end='')

    for i,idx in enumerate(papers_year_idx):
        paper = papers[idx]
        content = str.lower(paper['title']) + ' ' + str.lower(paper['abstract'])
        if check_substrings(content, and_or_query):
            # Add to new list
            papers_aoq_id.append(papers_id[idx])
            papers_aoq_idx.append(idx)

    print('done!')
    print('Removed {} papers from list'.format(len(papers_year_id)-len(papers_aoq_id)))
    print('Remaining papers in list = {}'.format(len(papers_aoq_id)))

    # Save filtered list of papers to file
    if is_save:
        file_name = 'papers_list_4.txt'
        papers_list_4 = save_to_file(papers, papers_aoq_idx, folder_name, file_name, format_type)

    # Save discarded list of papers to file
    discard_aoq_idx = [idx for idx in papers_year_idx if idx not in papers_aoq_idx]
    if is_save:
        file_name = 'discard_list_4.txt'
        discard_list_4 = save_to_file(papers, discard_aoq_idx, folder_name, file_name, format_type)
    # -------------------------------------------------------------------------

    # ------------------ Filter papers based on NOT operator ------------------
    papers_notq_id = []
    papers_notq_idx = []

    # Convert all query strings to lowercase
    not_query = [q.lower() for q in not_query]

    print('')
    print('Filtering papers based on NOT query...', end='')

    for i,idx in enumerate(papers_aoq_idx):
        paper = papers[idx]
        content = str.lower(paper['title']) + ' ' + str.lower(paper['abstract'])

        is_present = False
        for nq in not_query:
            if nq in content:
                is_present = True
                break
        if not is_present:
            # Add to new list
            papers_notq_id.append(papers_id[idx])
            papers_notq_idx.append(idx)

    print('done!')
    print('Removed {} papers from list'.format(len(papers_aoq_id)-len(papers_notq_id)))
    print('Remaining papers in list = {}'.format(len(papers_notq_id)))

    # Save filtered list of papers to file
    if is_save:
        file_name = 'papers_list_5.txt'
        papers_list_5 = save_to_file(papers, papers_notq_idx, folder_name, file_name, format_type)

    # Save discarded list of papers to file
    discard_notq_idx = [idx for idx in papers_aoq_idx if idx not in papers_notq_idx]
    if is_save:
        file_name = 'discard_list_5.txt'
        discard_list_5 = save_to_file(papers, discard_notq_idx, folder_name, file_name, format_type)

    # Stop logging and save log to file
    if is_save:
        log.stop()
    # -------------------------------------------------------------------------

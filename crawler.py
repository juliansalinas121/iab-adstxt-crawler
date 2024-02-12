import sys
import os
import csv
import socket
import logging
from optparse import OptionParser
from urllib.parse import urlparse
import requests
import re
import tempfile
import multiprocessing
from multiprocessing import Pool
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from datetime import datetime

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

def process_adstxt_row_to_db(data_row, comment, hostname, adsystem_id):
    exchange_host = data_row[0].lower().strip()
    seller_account_id = data_row[1].lower().strip()
    account_type = data_row[2].lower().strip()
    tag_id = data_row[3].lower().strip() if len(data_row) == 4 else ''
    print(hostname, exchange_host, adsystem_id, seller_account_id, account_type, tag_id, comment)

def process_contentdirective_row_to_db(case, site_hostname, rhs_hostname, comment):
    print(case, site_hostname, rhs_hostname, comment)

def fetch_adsystem_id(adsystem_domain):
    return 1

def crawl_to_db(ahost, referral_domain=False):
    rowcnt = 0
    referral_domains = []
    myheaders = {
        'User-Agent':
        'AdsTxtCrawler/1.0; +https://github.com/yourusername/adstxt-crawler; Contact: your.email@example.com'
        'Accept':
        'text/plain',
    }
    aurl = 'http://{thehost}/ads.txt'.format(thehost=ahost)
    accept = False
    try:
        r = requests.get(aurl, headers=myheaders, timeout=5)
        if (r.status_code == 200):
            text = r.text.lower()
            if ('html' not in text and 'body' not in text and 'div' not in text
                    and 'span' not in text):
                accept = True
    except:
        pass

    if (accept):
        text = r.text.encode('utf_8')
        text = text.decode('utf-8-sig').encode('utf_8')
        text = re.sub(re.compile('[^\x20-\x7E\r\n]'), '', text.decode())

        with tempfile.NamedTemporaryFile(delete=False) as tmp_csv_file:
            tmpfile = tmp_csv_file.name
            tmp_csv_file.write(text.encode())

        with open(tmpfile, 'r') as tmp_csv_file:
            line_reader = csv.reader(
                tmp_csv_file, delimiter='#', quotechar='|')
            comment = ''
            for line in line_reader:
                try:
                    data_line = line[0]
                except:
                    data_line = ""

                data_delimiter = ','
                if data_line.find("\t") != -1:
                    data_delimiter = '\t'

                data_reader = csv.reader([data_line], delimiter=data_delimiter, quotechar='|')
                for row in data_reader:
                    if len(row) > 0 and row[0].startswith('#'):
                        continue

                    directive_pattern = 'domain='
                    if len(row) > 0 and directive_pattern in row[0].lower():
                        s = row[0].lower().split('=')
                        rhs_host = ''
                        comment  = ''
                        if len(s) > 1:
                            lhs = s[0].strip()
                            rhs = s[1].strip().split('#')

                            if(len(rhs) > 0):
                                rhs_host = rhs[0].strip().lower()
                            if(len(rhs) > 1):
                                comment  = rhs[1].strip()

                            if(lhs.startswith('subdomain')):
                                referral_domains.append(rhs_host)

                            elif(lhs.startswith('contentproducerdomain')):
                                referral_domains.append(rhs_host)
                                rowcnt += 1
                                process_contentdirective_row_to_db('cd', ahost, rhs_host, comment)

                            elif(lhs.startswith('contentdistributordomain')):
                                referral_domains.append(rhs_host)
                                rowcnt += 1
                                process_contentdirective_row_to_db('cp', ahost, rhs_host, comment)

                    if len(row) < 3:
                        continue

                    if (len(line) > 1) and (len(line[1]) > 0):
                         comment = line[1]

                    adsystem_domain = row[0].lower().strip()
                    adsystem_id = fetch_adsystem_id(adsystem_domain)
                    rowcnt += 1
                    process_adstxt_row_to_db(row, comment, ahost, adsystem_id)

        os.remove(tmpfile)

    if not referral_domain:
        for ahost in referral_domains:
            rowcnt += crawl_to_db(ahost, referral_domain=True)

    return rowcnt

def load_url_queue(csvfilename, url_queue):
    cnt = 0
    with open(csvfilename, 'r', encoding='utf-8', errors='ignore') as csvfile:

        targets_reader = csv.reader(csvfile, delimiter=',', quotechar='|')
        for row in targets_reader:
            if len(row) < 1 or row[0].startswith('#'):
                continue

            for item in row:
                host = "localhost"
                if "http:" in item or "https:" in item :
                    parsed_uri = urlparse(row[0])
                    host = parsed_uri.netloc
                else:
                    host = item
                try:
                    ip = socket.gethostbyname(host)
                    if "127.0.0" not in ip and "0.0.0.0" not in ip:
                        url_queue.append(host)
                        cnt += 1
                except:
                    pass
    return cnt

def set_log_file(log_level):
    file_name = 'adstxt_crawler.log'
    log_format = '%(asctime)s %(filename)s:%(lineno)d:%(levelname)s  %(message)s'
    log_level = logging.WARNING
    if log_level == 1:
        log_level = logging.INFO
    elif log_level != 2:
        log_level = logging.DEBUG
    logging.basicConfig(filename=file_name, level=log_level, format=log_format)

if __name__ == '__main__':
    crawl_url_queue = []
    cnt_urls = 0
    cnt_records = 0
    cnt_urls_processed = 0

    arg_parser = OptionParser()
    arg_parser.add_option("-t", "--targets", dest="target_filename",
                      help="list of domains to crawl ads.txt from", metavar="FILE")
    arg_parser.add_option("-v", "--verbose", dest="verbose", action='count',
                      help="Increase verbosity (specify multiple times for more)")
    arg_parser.add_option("-p", "--thread_pool", dest="num_threads", default=4,
                      type="int", help="number of crawling threads to use")

    (options, args) = arg_parser.parse_args()

    if len(sys.argv)==1:
        arg_parser.print_help()
        exit(1)

    set_log_file(options.verbose)

    if options.target_filename and len(options.target_filename) > 1:
        cnt_urls = load_url_queue(options.target_filename, crawl_url_queue)
    else:
        print("Missing target domains file name argument")
        arg_parser.print_help()
        exit(1)

    target = options.target_filename

    if (cnt_urls < 1):
        print("No Crawl")
        logging.warning("No Crawl")
        exit(1)

    if(options.num_threads > 1):
        print(f"Thread Pool Crawl [{options.num_threads}]")
        logging.warning(f"Thread Pool Crawl [{options.num_threads}]")
        p = Pool(options.num_threads)
        records = p.map(crawl_to_db, crawl_url_queue)
        p.close()
        cnt_records = sum(records)
    else:
        print("Single Threaded Crawl")
        logging.warning("Single Threaded Crawl")
        for ahost in crawl_url_queue:
            cnt_records += crawl_to_db(ahost)

    print(f'Wrote {cnt_records} records from {cnt_urls} URLs')
    logging.warning(f'Wrote {cnt_records} records from {cnt_urls} URLs')
    logging.warning("Finished crawl.")
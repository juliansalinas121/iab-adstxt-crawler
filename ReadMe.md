Ads.txt Crawler

## Overview

This project provides a streamlined Python script for crawling and verifying ads.txt files from specified domains. Designed with simplicity in mind, it bypasses the complexity and database dependencies of traditional crawlers, making it an ideal tool for quick checks, testing domain accessibility, and ensuring that DSPs (Demand Side Platforms) and SSPs (Supply Side Platforms) can crawl ads.txt files without firewall blocks from common data center IPs, such as AWS.

## Key Features

- **Ease of Use**: No complicated setup or database requirements.
- **Firewall Check**: Tests domain accessibility to ensure ads.txt files are crawlable from data center IPs.
- **Simplified Output**: Directly prints crawl results, facilitating quick reviews and checks.
- **Configurable**: Supports basic customizations including target domains and crawl concurrency.

## Prerequisites

- Python 3.x
- Requests library

## Installation

1. Clone this repository or download the script directly.
2. Install required Python packages:

```bash
pip install requests
```

## Usage

To use the crawler, you need a list of domains you want to crawl in a CSV file. The script can be run with the following command:

```bash
python crawler_script.py -t path/to/your/target_domains.csv
```

### Options

- `-t`, `--targets`: Specify the target domains file (CSV format).
- `-v`, `--verbose`: Increase verbosity for more detailed logging.
- `-p`, `--thread_pool`: Set the number of crawling threads to use (default is 4).

## Contributing
Maintainer: Julian Salians, julian.salinas121@gmail.com

Your contributions are welcome! Please feel free to submit issues or pull requests with improvements or bug fixes.

## Disclaimer

This script is provided for testing and educational purposes. Users are responsible for ensuring that their use of the script complies with website terms of service, legal requirements, and ethical standards.

## License

This project is released under the MIT License. See the `LICENSE` file for more details.

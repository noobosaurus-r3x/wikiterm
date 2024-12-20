import requests
from bs4 import BeautifulSoup 
import html2text 
from rich.console import Console
from rich.markdown import Markdown
from rich.theme import Theme
import argparse
import subprocess
import sys
import os
import re
import traceback
import shlex
import platform

def search_wikipedia(query, lang='en'):
    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "opensearch",
        "search": query,
        "limit": 10,
        "namespace": 0,
        "format": "json",
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None  # Handle HTTP errors
    data = response.json()
    return data[1]  # List of article titles

def fetch_wikipedia_article(title, lang='en', section=None):
    # Sanitize the lang input to prevent injection vulnerabilities
    lang = re.sub(r'[^a-zA-Z0-9\-]', '', lang)

    if section is not None:
        # Fetch the wikitext of the section
        url = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "prop": "revisions",
            "titles": title,
            "rvprop": "content",
            "rvsection": section,
            "format": "json",
            "redirects": True,
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return None, "HTTP error occurred."
        data = response.json()

        pages = data.get('query', {}).get('pages', {})
        page = next(iter(pages.values()), {})
        if 'revisions' not in page:
            return None, "Section not found."

        wikitext = page['revisions'][0].get('*', '')

        # Find all reference groups in the wikitext
        groups = set(re.findall(r'<ref\s+group="([^"]+)"', wikitext))
        groups.update(re.findall(r"<ref\s+group='([^']+)'", wikitext))

        wikitext += '\n\n<references />'
        for group in groups:
            wikitext += f'\n\n<references group="{group}" />'

        url = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "parse",
            "format": "json",
            "text": wikitext,
            "contentmodel": "wikitext",
            "prop": "text",
        }
        response = requests.post(url, data=params)
        if response.status_code != 200:
            return None, "HTTP error during parsing."
        data = response.json()

        if "error" in data:
            return None, "Error parsing wikitext."

        html_content = data.get("parse", {}).get("text", {}).get("*", "")
    else:
        url = f"https://{lang}.wikipedia.org/w/api.php"
        params = {
            "action": "parse",
            "page": title,
            "format": "json",
            "redirects": True,
            "prop": "text",
            "disableeditsection": True,
        }
        response = requests.get(url, params=params)
        if response.status_code != 200:
            return None, "HTTP error occurred."
        data = response.json()

        if "error" in data:
            return None, "Article not found."

        html_content = data.get("parse", {}).get("text", {}).get("*", "")

    if not html_content:
        return None, "HTML content is empty or malformed."

    soup = BeautifulSoup(html_content, 'html.parser')

    for element in soup(['script', 'style', 'noscript', 'meta', 'link', 'iframe']):
        element.decompose()

    for element in soup.select('.navbox, .catlinks, .printfooter, .infobox, .metadata, .ambox, .mw-editsection'):
        element.decompose()

    for element in soup.find_all('span', class_='mw-editsection'):
        element.decompose()

    for p in soup.find_all('p'):
        if not p.get_text(strip=True):
            p.decompose()

    for a in soup.find_all('a'):
        href = a.get('href', '')
        if href.startswith('/wiki/'):
            a['href'] = f"https://{lang}.wikipedia.org{href}"

    for tag in soup.find_all():
        if not tag.get_text(strip=True) and not tag.find('img'):
            tag.decompose()

    cleaned_html = str(soup)

    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = True
    h.bypass_tables = False
    h.body_width = 0
    h.unicode_snob = True
    markdown_content = h.handle(cleaned_html)

    return markdown_content.strip(), None

def list_sections(title, lang='en'):
    # Sanitize the lang input to prevent injection vulnerabilities
    lang = re.sub(r'[^a-zA-Z0-9\-]', '', lang)

    url = f"https://{lang}.wikipedia.org/w/api.php"
    params = {
        "action": "parse",
        "page": title,
        "format": "json",
        "prop": "sections",
    }
    response = requests.get(url, params=params)
    if response.status_code != 200:
        return None, "HTTP error occurred."
    data = response.json()

    if "error" in data:
        return None, "Article not found."

    sections = data.get("parse", {}).get("sections", [])
    return sections, None

def main():
    parser = argparse.ArgumentParser(description='Read Wikipedia articles from the terminal.')
    parser.add_argument('title', nargs='*', help='Title of the Wikipedia article')
    parser.add_argument('-l', '--lang', default='en', help='Language code (default: en)')
    parser.add_argument('-s', '--search', action='store_true', help='Search for articles')
    parser.add_argument('-S', '--section', action='store_true', help='Select section to display')
    parser.add_argument('-o', '--output', help='Save output to a file')
    parser.add_argument('-p', '--pager', action='store_true', help='Use pager for long articles')

    args = parser.parse_args()

    custom_theme = Theme({
        "markdown.link": "underline",
        "markdown.code": "dim",
        "markdown.h1": "bold",
        "markdown.h2": "bold",
        "markdown.h3": "bold",
        "markdown.list": "bold",
    })

    console = Console()

    try:
        if args.search:
            if not args.title:
                console.print("[bold red]Error:[/bold red] No search query provided.")
                sys.exit(1)
            query = ' '.join(args.title)
            while True:
                results = search_wikipedia(query, lang=args.lang)
                if not results:
                    console.print(f"No results found for '{query}'.")
                    sys.exit(0)
                console.print("\nSearch results:")
                for idx, title in enumerate(results, 1):
                    console.print(f"{idx}. {title}")
                choice = input("Select an article by number (or 'q' to quit, 's' to search again): ")
                if choice.lower() == 'q':
                    sys.exit(0)
                if choice.lower() == 's':
                    query = input("Enter a new search query: ")
                    continue
                try:
                    idx = int(choice) - 1
                    if idx < 0 or idx >= len(results):
                        raise ValueError
                    title = results[idx]
                except ValueError:
                    console.print("[bold red]Invalid selection.[/bold red]")
                    continue

                while True:
                    section = None
                    if args.section:
                        sections, error = list_sections(title, lang=args.lang)
                        if error:
                            console.print(f"[bold red]{error}[/bold red]")
                            break
                        if not sections:
                            console.print("No sections available.")
                            break
                        else:
                            console.print("\nAvailable sections:")
                            for sec in sections:
                                indent = '  ' * (int(sec['toclevel']) - 1)
                                line = f"{sec['index']}. {indent}{sec['line']}"
                                console.print(line)
                            choice_sec = input("Select a section by number (or 'b' to go back): ")
                            if choice_sec.lower() == 'b':
                                break
                            try:
                                if not choice_sec.isdigit():
                                    raise ValueError
                                section_indices = [sec['index'] for sec in sections]
                                if choice_sec not in section_indices:
                                    raise ValueError
                                section = int(choice_sec)
                            except ValueError:
                                console.print("[bold red]Invalid selection.[/bold red]")
                                continue
                    else:
                        section = None

                    article_content, error = fetch_wikipedia_article(title, lang=args.lang, section=section)
                    if error:
                        console.print(f"[bold red]{error}[/bold red]")
                        continue

                    if section and args.section:
                        section_title = next((sec['line'] for sec in sections if sec['index'] == str(section)), None)
                        if section_title:
                            console.print(f"\n# {section_title}\n")

                    markdown = Markdown(article_content, hyperlinks=True)

                    if args.output:
                        with open(args.output, 'w', encoding='utf-8') as f:
                            f.write(article_content)
                        console.print(f"Article saved to [bold]{args.output}[/bold]")
                    else:
                        if args.pager:
                            pager = os.environ.get('PAGER', 'less -R')
                            try:
                                p = subprocess.Popen([pager], stdin=subprocess.PIPE)
                                p.communicate(input=console.export_text(markdown).encode('utf-8'))
                            except Exception as e:
                                console.print(f"[bold red]Error using pager: {e}[/bold red]")
                                console.print(markdown)
                        else:
                            console.print(markdown)

                    if args.section:
                        choice = input("\nWould you like to select another section? (y/n): ")
                        if choice.lower() != 'y':
                            break
                        else:
                            continue
                    else:
                        break

                choice = input("\nWould you like to select another article? (y/n): ")
                if choice.lower() != 'y':
                    break

        else:
            if not args.title:
                console.print("[bold red]Error:[/bold red] No article title provided.")
                sys.exit(1)
            title = ' '.join(args.title)

            while True:
                section = None
                if args.section:
                    sections, error = list_sections(title, lang=args.lang)
                    if error:
                        console.print(f"[bold red]{error}[/bold red]")
                        sys.exit(1)
                    if not sections:
                        console.print("No sections available.")
                    else:
                        console.print("\nAvailable sections:")
                        for sec in sections:
                            indent = '  ' * (int(sec['toclevel']) - 1)
                            line = f"{sec['index']}. {indent}{sec['line']}"
                            console.print(line)
                        choice_sec = input("Select a section by number (or press Enter to skip): ")
                        if not choice_sec:
                            section = None
                        else:
                            try:
                                if not choice_sec.isdigit():
                                    raise ValueError
                                section_indices = [sec['index'] for sec in sections]
                                if choice_sec not in section_indices:
                                    raise ValueError
                                section = int(choice_sec)
                            except ValueError:
                                console.print("[bold red]Invalid selection.[/bold red]")
                                continue

                article_content, error = fetch_wikipedia_article(title, lang=args.lang, section=section)
                if error:
                    console.print(f"[bold red]{error}[/bold red]")
                    sys.exit(1)

                if section and args.section:
                    section_title = next((sec['line'] for sec in sections if sec['index'] == str(section)), None)
                    if section_title:
                        console.print(f"\n# {section_title}\n")

                markdown = Markdown(article_content, hyperlinks=True)

                if args.output:
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write(article_content)
                    console.print(f"Article saved to [bold]{args.output}[/bold]")
                else:
                    if args.pager:
                        pager = os.environ.get('PAGER', 'less -R')
                        try:
                            # Split the pager command
                            pager_cmd = shlex.split(pager)
                            p = subprocess.Popen(pager_cmd, stdin=subprocess.PIPE)
                            # Send the raw article content
                            p.communicate(input=article_content.encode('utf-8'))
                        except Exception as e:
                            console.print(f"[bold red]Error using pager: {e}[/bold red]")
                            console.print(markdown)
                    else:
                        console.print(markdown)

                if args.section:
                    choice = input("\nWould you like to select another section? (y/n): ")
                    if choice.lower() != 'y':
                        break
                    else:
                        continue
                else:
                    break

    except Exception as e:
        console.print("[bold red]An error occurred:[/bold red] " + str(e))
        traceback.print_exc()
        logging.error("An exception occurred", exc_info=True)
        input("Press Enter to exit...")  # Pause before exiting

if __name__ == "__main__":
    main()

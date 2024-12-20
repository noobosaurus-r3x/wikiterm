# wikiterm

**wikiterm** is a Python-based terminal tool that allows users to search for and read Wikipedia articles directly from the command line. Think of it as your nerdy, bookish friend who reads Wikipedia all day but lives in your terminal.

> **Note:** I am not a professional developer; I just glued some Python scripts together with hope and caffeine. While it works, some features, like `-p` (pager), might remind you of a teenager's first coding project. Use it for testing or to impress your cat.

## Features
- **Search Wikipedia**: Use the `-s` flag to differentiate between articles with similar titles or keywords. You still need to provide part of an article title to search effectively, but it helps narrow down multiple options.
- **View Articles**: Fetch and display Wikipedia articles in Markdown format right where you feel most at home: the command line.
- **List Sections**: Use the `-S` flag to view and navigate article sections. You can now skip straight to the "Controversies" section of any article.
- **Save to File**: Export fetched articles to a file using the `-o` option, so you can prove to people that you read.
- **Multi-Language Support**: Fetch articles from Wikipedia in your preferred language using the `-l` flag. Bonjour! Hola! 你好!
- Clickable links.

## Known Limitations
- The `-p` (pager) option is functional but not polished. Think of it as the "alpha stage" of features. It’s like a chair with three legs—it works, but don’t lean too hard on it.
- The rest of the flags are more like four-legged chairs: functional and reliable, but not necessarily pretty.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/wikiterm.git
   cd wikiterm
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Basic syntax:
```bash
python wikiterm.py [OPTIONS] <TITLE>
```

### Examples

Search for articles:
```bash
python wikiterm.py -s python
```
> This will return a list of articles with titles that include the word "python." You can then choose the specific article to fetch.

Fetch and view an article:
```bash
python wikiterm.py "Python (programming language)"
```

View sections of an article:
```bash
python wikiterm.py -S "Python (programming language)"
```

Save an article to a file:
```bash
python wikiterm.py -o output.md "Python (programming language)"
```

### Options

| Option       | Description |
|--------------|-------------|
| `-s`         | Search for articles with a keyword to refine options. |
| `-l <lang>`  | Specify the language for Wikipedia (default: `en`). |
| `-S`         | List and navigate sections of the article. |
| `-o <file>`  | Save the article content to a file. |
| `-p`         | Use a pager for long articles (experimental). |

## Contribution

As this is a personal project, contributions are welcome but may not always be immediately addressed. Feel free to open issues, submit pull requests, or just send snacks.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

---

Happy exploring Wikipedia from your terminal! And remember, if you mess something up, it’s a feature, not a bug.

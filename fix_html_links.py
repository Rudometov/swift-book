#!/usr/bin/env python3
import os
import sys
from bs4 import BeautifulSoup

def build_html_index(project_root):
    """
    Build a dictionary mapping HTML file basenames to a list of relative paths
    from the project root. For example:
        { "AboutSwift.html": ["HTML/AboutSwift.html"], ... }
    """
    index = {}
    for root, dirs, files in os.walk(project_root):
        for file in files:
            if file.lower().endswith('.html'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, project_root)
                index.setdefault(file, []).append(rel_path)
    return index

def find_target_path(href, index, project_root):
    """
    Given a href (e.g. "AboutSwift.html" or "subdir/AboutSwift.html"), try to find the
    target file in the project.
    1. First, remove any leading slash for normalization.
    2. Check if the file exists exactly as specified (relative to project_root).
    3. If not found, search by basename in the index.
    Returns the relative path (from project_root) of the target file, or None if not found.
    """
    normalized_href = href.lstrip('/')
    # Try the given path first:
    candidate_path = os.path.join(project_root, normalized_href)
    if os.path.exists(candidate_path):
        return os.path.relpath(candidate_path, project_root)
    # Otherwise, search by the basename (e.g. "AboutSwift.html")
    base = os.path.basename(normalized_href)
    if base in index:
        if len(index[base]) > 1:
            print(f"Warning: multiple targets found for {base}: {index[base]}. Using the first one.")
        return index[base][0]
    return None

def fix_links_in_html(file_path, project_root, index):
    """
    Open an HTML file and update all link and image paths:
      - For <a> tags, if the href does not start with '#' or an external URL,
        look up the target file using the index and update the link to the correct
        relative path from the file's location.
      - For <img> tags, if the src is a bare filename (no slashes), update it to
        "../Assets/FILENAME@2x.png".

    Additionally, if processing The-Swift-Programming-Language.html, the script:
      - Removes all <span class="citation"> elements.
      - Removes the <h2 id="topics">Topics</h2> element.
      - Changes all <h3> tags to <h2>.
      - Removes unwanted paragraphs:
            <p> {
            }</p>
        and
            <p>(scope:
        global) { (disabled) (disabled)
        (disabled)
        }</p>
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    soup = BeautifulSoup(content, 'html.parser')
    changed = False

    # Process <a> tags.
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Skip in-page anchors and external links.
        if href.startswith('#') or href.startswith('http://') or href.startswith('https://'):
            continue
        # Find the target file.
        target_rel = find_target_path(href, index, project_root)
        if target_rel:
            target_full_path = os.path.join(project_root, target_rel)
            new_href = os.path.relpath(target_full_path, os.path.dirname(file_path))
            if new_href != href:
                print(f"In {file_path}: updating link '{href}' -> '{new_href}'")
                a['href'] = new_href
                changed = True
        else:
            print(f"In {file_path}: target not found for link '{href}'")

    # Process <img> tags.
    for img in soup.find_all('img', src=True):
        src = img['src']
        # Skip external images.
        if src.startswith('http://') or src.startswith('https://'):
            continue
        # Process only if src is a bare filename (i.e. no directory separator)
        if '/' not in src:
            base, _ = os.path.splitext(src)
            new_src = f"../Assets/{base}@2x.png"
            if new_src != src:
                print(f"In {file_path}: updating img src '{src}' -> '{new_src}'")
                img['src'] = new_src
                changed = True

    # Additional transformations for The-Swift-Programming-Language.html
    if os.path.basename(file_path) == "The-Swift-Programming-Language.html":
        # Remove all <span class="citation"> elements.
        citations = soup.find_all('span', class_="citation")
        for span in citations:
            span.decompose()
            changed = True

        # Remove the <h2 id="topics">Topics</h2> element.
        h2_topics = soup.find("h2", id="topics")
        if h2_topics and h2_topics.get_text(strip=True) == "Topics":
            h2_topics.decompose()
            changed = True

        # Change all <h3> tags to <h2>
        h3_tags = soup.find_all('h3')
        for h3 in h3_tags:
            h3.name = "h2"
            changed = True

        # Remove unwanted <p> elements.
        # We'll normalize the text by stripping and removing all whitespace.
        unwanted_texts = {
            "{}",  # For <p> { \n}</p>
            "(scope:global){(disabled)(disabled)(disabled)}"  # For the second paragraph.
        }
        p_tags = soup.find_all('p')
        for p in p_tags:
            normalized = ''.join(p.get_text(strip=True).split())
            if normalized in unwanted_texts:
                print(f"In {file_path}: removing <p> with text '{p.get_text(strip=True)}'")
                p.decompose()
                changed = True

    if changed:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        print(f"Updated file: {file_path}")
    else:
        print(f"No changes in file: {file_path}")

def main():
    # Use current working directory as default project root, or allow override as argument.
    project_root = os.getcwd()
    if len(sys.argv) > 1:
        project_root = os.path.abspath(sys.argv[1])

    print(f"Building HTML index for project: {project_root}")
    index = build_html_index(project_root)
    print("HTML index built:")
    for filename, paths in index.items():
        print(f"  {filename}: {paths}")

    # Process each HTML file in the project.
    for root, dirs, files in os.walk(project_root):
        for filename in files:
            if filename.lower().endswith('.html'):
                file_path = os.path.join(root, filename)
                print(f"\nProcessing file: {file_path}")
                fix_links_in_html(file_path, project_root, index)

if __name__ == '__main__':
    main()

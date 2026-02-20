#!/usr/bin/env python3
"""
Simpler script to sync content from a Google Doc to data/index.md
Uses Google Docs export feature (no OAuth required, but doc must be publicly viewable)

Usage:
    python scripts/sync_google_doc_simple.py --doc-id DOCUMENT_ID --output data/index.md

Or set environment variable:
    export GOOGLE_DOC_ID="your-document-id"
    python scripts/sync_google_doc_simple.py
"""

import os
import sys
import argparse
from pathlib import Path
import urllib.request
import html2text

def get_document_content(doc_id):
    """Fetch content from Google Doc using export URL."""
    # Export as HTML
    export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=html"
    
    try:
        with urllib.request.urlopen(export_url) as response:
            html_content = response.read().decode('utf-8')
    except urllib.error.HTTPError as e:
        if e.code == 403:
            print("Error: Document is not publicly accessible.")
            print("Please share the document with 'Anyone with the link can view'")
            print("Or use sync_google_doc.py with OAuth authentication")
            sys.exit(1)
        else:
            raise
    
    # Convert HTML to Markdown
    h = html2text.HTML2Text()
    h.ignore_links = False
    h.ignore_images = False
    h.body_width = 0  # Don't wrap lines
    h.unicode_snob = True
    
    markdown_content = h.handle(html_content)
    
    return markdown_content

def update_data_page(doc_id, output_file):
    """Update data/index.md with content from Google Doc."""
    print(f"Fetching content from Google Doc: {doc_id}")
    
    # Get content from Google Doc
    markdown_content = get_document_content(doc_id)
    
    # Read existing file to preserve front matter
    output_path = Path(output_file)
    front_matter = []
    if output_path.exists():
        with open(output_path, 'r') as f:
            lines = f.readlines()
            in_front_matter = False
            
            for i, line in enumerate(lines):
                if line.strip() == '---':
                    if not in_front_matter:
                        in_front_matter = True
                        front_matter.append(line)
                    else:
                        front_matter.append(line)
                        break
                elif in_front_matter:
                    front_matter.append(line)
    else:
        # Default front matter if file doesn't exist
        front_matter = [
            '---\n',
            'title: Data\n',
            'layout: page\n',
            'order: date\n',
            'banner: OIBcrop.jpg\n',
            'banner_position: left\n',
            '---\n',
            '\n'
        ]
    
    # Write updated file
    with open(output_path, 'w') as f:
        f.writelines(front_matter)
        f.write('\n')
        f.write(markdown_content)
    
    print(f"Successfully updated {output_file}")

def main():
    parser = argparse.ArgumentParser(
        description='Sync content from Google Doc to data/index.md (simple version)'
    )
    parser.add_argument(
        '--doc-id',
        default=os.getenv('GOOGLE_DOC_ID'),
        help='Google Doc document ID (or set GOOGLE_DOC_ID env var)'
    )
    parser.add_argument(
        '--output',
        default='data/index.md',
        help='Output markdown file path (default: data/index.md)'
    )
    
    args = parser.parse_args()
    
    if not args.doc_id:
        print("Error: Document ID required. Use --doc-id or set GOOGLE_DOC_ID env var")
        print("\nTo get the document ID:")
        print("  From the Google Doc URL: https://docs.google.com/document/d/DOCUMENT_ID/edit")
        sys.exit(1)
    
    update_data_page(args.doc_id, args.output)

if __name__ == '__main__':
    main()

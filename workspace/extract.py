import pypdf

reader = pypdf.PdfReader('omniweb_omniverse_agentic_map.pdf')
text = '\n---PAGE---\n'.join([page.extract_text() for page in reader.pages])

with open('pdf_text.txt', 'w', encoding='utf-8') as f:
    f.write(text)

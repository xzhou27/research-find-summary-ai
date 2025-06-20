# app.py
from flask import Flask, render_template, request, Response, jsonify
import requests
import xml.etree.ElementTree as ET
import time
import json
import heapq
from typing import List, Dict, Tuple
import getpass


# ---------------------------
# PubMed Query Configuration
# ---------------------------
BATCH_SIZE = 10000
DELAY_BETWEEN_REQUESTS = 3

# Global variable to store PubMed articles (in memory)
papers_data = []

# Global variable to store API key
api_key = None

# --- Ranking Functions ---
# (This ranking code uses a keyword-based scoring method.)

# Keyword weights and bonus multipliers.
keyword_weights = {
    'rnaseq': 5,
    'rna-seq': 5,
    'rna': 2,
    'marker': 3,
    'markers': 3,
    'biomarker': 3,
    'prognosis': 3,
    'prognostic': 3,
    'transcriptome': 1,
    'expression': 1,
    'signature': 1,
    'survival': 1,
    'cancer': 1,
    'metastasis': 1,
    'dysregulated': 1,
    'differential': 1,
    'risk': 1,
    'clinicopathological': 1,
    'bioinformatics': 1,
    'prediction': 1,
    'sequencing': 1,
    # Bigrams:
    'rna-seq data': 2,
    'mrna expression': 2,
    'gene expression': 2,
    'differential expression': 2,
    'expression profile': 2,
    'disease prognosis': 2,
    'prognostic marker': 2,
    'biomarker discovery': 2,
    'kaplan meier': 2,
    'hazard ratio': 2,
    'survival analysis': 2,
    'tumor progression': 2,
    'cancer prognosis': 2,
    'overall survival': 2,
    'multivariate analysis': 2,
    'risk stratification': 2,
    'genomic profiling': 2,
    'transcriptomic analysis': 2,
    # Trigrams:
    'rna sequencing data': 2,
    'differential gene expression': 2,
    'rna-seq derived markers': 2,
    'overall survival analysis': 2,
    'tumor gene expression': 2,
    'kaplan-meier survival analysis': 2,
    'long noncoding rna': 2,
    'prognostic gene signature': 2,
    'clinicopathological prognostic factors': 2,
    'expression profiling studies': 2,
    'biomarker discovery pipeline': 2,
    'high risk patients': 2,
    'low risk group': 2,
    'immune-related genes': 2,
    'mrna expression profiles': 2
}

combinations = {
    ('rnaseq', 'prognosis'): 8,
    ('rna-seq', 'prognosis'): 8,
    ('rnaseq', 'prognostic'): 8,
    ('rna-seq', 'prognostic'): 8,
    ('rna', 'biomarker'): 5,
    ('survival', 'analysis'): 3,
    ('gene', 'expression'): 3,
    ('risk', 'stratification'): 3,
    ('prognostic', 'signature'): 3,
}

def calculate_relevance_score(abstract: str, keywords: List[str]) -> int:
    abstract_lower = abstract.lower()
    score = 0
    for keyword in keywords:
        keyword_lower = keyword.lower()
        count = abstract_lower.count(keyword_lower)
        weight = keyword_weights.get(keyword_lower, 1)
        score += count * weight
    for (keyword1, keyword2), multiplier in combinations.items():
        if keyword1 in abstract_lower and keyword2 in abstract_lower:
            base_score = min(abstract_lower.count(keyword1), abstract_lower.count(keyword2))
            score += base_score * multiplier
    return score


def find_top_relevant_papers_from_data(papers: List[Dict],
                                       keywords: List[str],
                                       scoring_method: str = "keyword",
                                       api_key: str = None,
                                       top_n: int = 5) -> List[Tuple[float, str, str]]:
    top_papers = []
    for paper in papers:
        abstract = paper.get('abstract', '')
        title = paper.get('title', '')
        if not abstract:
            continue
        if scoring_method == "keyword":
            final_score = calculate_relevance_score(abstract, keywords) / 100.0
        # else:  # For "claude" method
        #     final_score = calculate_claude_relevance_score(abstract, api_key)
        if len(top_papers) < top_n:
            heapq.heappush(top_papers, (final_score, title, abstract))
        elif final_score > top_papers[0][0]:
            heapq.heapreplace(top_papers, (final_score, title, abstract))
    return sorted(top_papers, reverse=True)

# Define the list of keywords (as provided)
default_keywords = [
    "RNA", "RNAseq", "RNA-seq", "Biomarker", "Prognosis", "Prognostic", "Marker",
    "Transcriptome", "Expression", "Signature", "Survival", "Cancer", "Metastasis",
    "Dysregulated", "Differential", "Risk", "Clinicopathological", "Bioinformatics",
    "Prediction", "Sequencing",
    "RNA markers", "RNA biomarkers", "RNA-seq data", "mRNA expression",
    "gene expression", "differential expression", "expression profile",
    "disease prognosis", "prognostic marker", "biomarker discovery",
    "Kaplan Meier", "hazard ratio", "survival analysis", "tumor progression",
    "cancer prognosis", "overall survival", "multivariate analysis",
    "risk stratification", "genomic profiling", "transcriptomic analysis",
    "RNA sequencing data", "differential gene expression", "RNA-seq derived markers",
    "overall survival analysis", "tumor gene expression", "Kaplan-Meier survival analysis",
    "long noncoding RNA", "prognostic gene signature", "clinicopathological prognostic factors",
    "expression profiling studies", "biomarker discovery pipeline", "high risk patients",
    "low risk group", "immune-related genes", "mRNA expression profiles"
]

def rank_papers(top_n: int) -> str:
    if not papers_data:
        return "No papers data available. Please run the PubMed query first."
    top_papers = find_top_relevant_papers_from_data(papers_data, default_keywords, scoring_method="keyword", top_n=top_n)
    result_lines = []
    result_lines.append(f"Top {top_n} Relevant Papers:")
    result_lines.append("-" * 50)
    for score, title, abstract in top_papers:
        result_lines.append(f"Score: {score}")
        result_lines.append(f"Paper Name: {title}")
        result_lines.append(f"Abstract: {abstract[:200]}...")  # Show first 200 characters
        result_lines.append("-" * 50)
    return "\n".join(result_lines)




# ---------------------------
# PubMed Query Functions
# ---------------------------
def fetch_pubmed_ids(query, retmax=100000):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    params = {
        "db": "pubmed",
        "term": query,
        "retmode": "xml",
        "retmax": retmax,
        "usehistory": "y"
    }
    response = requests.get(base_url, params=params)
    root = ET.fromstring(response.text)
    count = int(root.find("Count").text)
    webenv = root.find("WebEnv").text
    query_key = root.find("QueryKey").text
    id_list_elem = root.find("IdList")
    id_list = [id_elem.text for id_elem in id_list_elem.findall("Id")]
    return webenv, query_key, count, id_list

def fetch_articles_as_xml(webenv, query_key, retstart=0, retmax=10000):
    base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    params = {
        "db": "pubmed",
        "query_key": query_key,
        "WebEnv": webenv,
        "retstart": retstart,
        "retmax": retmax,
        "rettype": "abstract",
        "retmode": "xml"
    }
    response = requests.get(base_url, params=params)
    return response.text

def parse_pubmed_xml_to_json(xml_data):
    articles_json = []
    root = ET.fromstring(xml_data)
    for article in root.findall(".//PubmedArticle"):
        pmid_elem = article.find(".//PMID")
        pmid = pmid_elem.text if pmid_elem is not None else ""
        title_elem = article.find(".//ArticleTitle")
        title = title_elem.text if title_elem is not None else ""
        abstract_elems = article.findall(".//AbstractText")
        abstract_text_parts = []
        for elem in abstract_elems:
            abstract_text_parts.append("".join(elem.itertext()))
        abstract_text = " ".join(abstract_text_parts)
        journal_elem = article.find(".//Journal/Title")
        journal = journal_elem.text if journal_elem is not None else ""
        year_elem = article.find(".//JournalIssue/PubDate/Year")
        pub_year = year_elem.text if year_elem is not None else ""
        author_elems = article.findall(".//AuthorList/Author")
        authors = []
        for auth in author_elems:
            last_name = auth.find("LastName")
            fore_name = auth.find("ForeName")
            name = ""
            if last_name is not None:
                name += last_name.text
            if fore_name is not None:
                name += ", " + fore_name.text
            if name:
                authors.append(name)
        pub_types = article.findall(".//PublicationTypeList/PublicationType")
        pub_type_strings = [pt.text for pt in pub_types if pt.text]
        if "Journal Article" not in pub_type_strings:
            continue
        article_dict = {
            "pmid": pmid,
            "title": title,
            "abstract": abstract_text,
            "journal": journal,
            "publication_year": pub_year,
            "authors": authors
        }
        articles_json.append(article_dict)
    return articles_json

def stream_pubmed_query(selected_journals, start_date, end_date):
    global papers_data
    papers_data = []  # Clear previous results
    for journal in selected_journals:
        yield f"\nProcessing journal: {journal}\n"
        query = f'"{journal}"[Journal] AND ("{start_date}"[Date - Publication] : "{end_date}"[Date - Publication])'
        try:
            webenv, query_key, count, id_list = fetch_pubmed_ids(query)
        except Exception as e:
            yield f"Error fetching IDs for {journal}: {e}\n"
            continue
        yield f"Found {count} articles for {journal}.\n"
        journal_articles = []
        for start in range(0, count, BATCH_SIZE):
            yield f"Fetching records ...\n"
            try:
                xml_chunk = fetch_articles_as_xml(webenv, query_key, retstart=start, retmax=BATCH_SIZE)
                chunk_json = parse_pubmed_xml_to_json(xml_chunk)
                journal_articles.extend(chunk_json)
            except Exception as e:
                yield f"Error fetching records {start} to {start+BATCH_SIZE} for {journal}: {e}\n"
            time.sleep(DELAY_BETWEEN_REQUESTS)
        papers_data.extend(journal_articles)
        yield f"Completed processing {len(journal_articles)} articles from {journal}\n"
    yield f"\nQuery finished. Total articles collected: {len(papers_data)}\n"

# ---------------------------
# PDF Summarization Endpoint
# ---------------------------
# Import functions from summarizer.py
from summarizer import pdf_to_text_file, summarization_stream

def get_api_key():
    """Prompt user for API key if not already set"""
    global api_key
    if api_key is None:
        print("\n" + "="*60)
        print("API KEY REQUIRED")
        print("="*60)
        print("This application requires an Anthropic API key for PDF summarization.")
        print("You can get your API key from: https://console.anthropic.com/")
        print("="*60)
        api_key = getpass.getpass("Please enter your Anthropic API key: ")
        if not api_key:
            print("Error: API key is required to run this application.")
            exit(1)
        print("API key received successfully!")
        print("="*60 + "\n")
    return api_key

# ---------------------------
# Flask Routes
# ---------------------------
app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_query():
    data = request.get_json()
    selected_journals = data.get('journals', [])
    start_date = data.get('start_date', "2024/01/1")
    end_date = data.get('end_date', "3000")
    return Response(stream_pubmed_query(selected_journals, start_date, end_date),
                    mimetype='text/plain')

@app.route('/rank', methods=['POST'])
def rank_query():
    data = request.get_json()
    top_n = int(data.get('top_n', 5))
    ranking_result = rank_papers(top_n)
    return jsonify({"output": ranking_result})

@app.route('/summarize', methods=['POST'])
def summarize():
    """
    Endpoint to handle PDF upload, convert the PDF to text, then run the summarization process.
    The process prints messages in real time.
    """
    if 'pdf' not in request.files:
        return "No file uploaded", 400
    pdf_file = request.files['pdf']
    file_bytes = pdf_file.read()
    pdf_text = pdf_to_text_file(file_bytes)
    
    # Get API key for summarization
    current_api_key = get_api_key()
    
    def generate():
        yield "PDF converted to txt\n"
        for output in summarization_stream(pdf_text, current_api_key):
            yield output
    return Response(generate(), mimetype='text/plain')

if __name__ == '__main__':
    # Prompt for API key when application starts
    get_api_key()
    app.run(debug=True)

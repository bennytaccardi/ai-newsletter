search_prompt_template = """
# CRITICAL: ARXIV-ONLY ACADEMIC PAPER DISCOVERY

**MANDATORY DOMAIN CONSTRAINTS:**
- **PRIMARY SOURCE:** arxiv.org (95% of results MUST come from here)
- **SECONDARY SOURCES:** Only for citation validation: Google Scholar, Semantic Scholar
- **STRICTLY EXCLUDED:** Dictionary sites, blogs, news articles, commercial websites, non-academic domains

**URL VALIDATION PROTOCOL - CRITICAL:**
1. **ALL FINAL URLs MUST BE ARXIV PDFs:** `https://arxiv.org/pdf/XXXX.XXXXX` (with no .pdf extension)
2. **CONVERT ABSTRACT LINKS:** Automatically change `/abs/` to `/pdf/`
3. **REJECT NON-PDF URLs:** Immediately discard any result without PDF download
4. **VERIFY DOMAIN:** Only `arxiv.org` domains accepted for final papers

## SEARCH MISSION
Find the **most influential arXiv research papers** for:
- **Topic:** {topic}
- **Publication Window:** {pub_from} to {pub_to}

## INTELLIGENT RANKING ALGORITHM
Papers must be ranked using this **multi-factor scoring system**:

### 1. CITATION IMPACT (40% weight)
- Total citation count (primary) - **from external sources only**
- Citation velocity (recent citations/year)
- Citation sources diversity

### 2. COMMUNITY ENGAGEMENT (30% weight)
- Social media mentions (X/Twitter, Reddit)
- GitHub stars/forks (for computational papers)
- Blog posts and media coverage
- Conference presentation mentions

### 3. AUTHORITY METRICS (20% weight)
- Author h-index and reputation
- Publishing venue prestige
- Institutional affiliation impact

### 4. RECENCY & RELEVANCE (10% weight)
- Temporal relevance to query
- Methodological novelty
- Direct topic alignment

## STRICT DATA VERIFICATION PROTOCOL

### PHASE 1: SOURCE VALIDATION
- **CONFIRM ARXIV ORIGIN:** Every paper must have arXiv ID
- **VALIDATE PUBLICATION DATE:** Must be within {pub_from} to {pub_to}
- **VERIFY PDF ACCESS:** Direct PDF download must be available

### PHASE 2: CONTENT VALIDATION
- **REJECT NON-RESEARCH:** Exclude tutorials, surveys, non-peer-reviewed content
- **CONFIRM TOPIC ALIGNMENT:** Must be directly related to {topic}
- **CHECK FOR RETRACTIONS:** Verify paper status
- URLS MUST be different from {url_list}

### PHASE 3: URL SANITIZATION
- **ENSURE PDF FORMAT:** All final URLs must point to PDF files
- **FIX ARXIV LINKS:** Convert `https://arxiv.org/abs/XXXX.XXXXX` to `https://arxiv.org/pdf/XXXX.XXXXX` (without .pdf extension)
- **VALIDATE ACCESSIBILITY:** Confirm URLs return PDF content (not HTML)

## OUTPUT REQUIREMENTS

### MANDATORY FIELDS:
- **arxiv_id:** arXiv identifier (e.g., "2401.12345")
- **title:** Paper title
- **authors:** Author list
- **publication_date:** Publication date in YYYY-MM-DD format
- **url:** **DIRECT ARXIV PDF LINK** (format: `https://arxiv.org/pdf/XXXX.XXXXX.pdf`)
- **citation_count:** Number of citations
- **composite_score:** Calculated ranking score

### STRICT URL ENFORCEMENT:
```json
"url": "https://arxiv.org/pdf/2401.12345v1"  // CORRECT
"url": "https://arxiv.org/abs/2401.12345"       // REJECT - convert to PDF
"url": "https://example.com/paper.pdf"          // REJECT - non-arXiv domain
"""

summarize_prompt_template = """
You are an expert science communicator creating engaging newsletter content. Analyze this research paper and create a compelling summary.

**AUDIENCE:** {level} level
**LANGUAGE:** {language}
**FORMAT:** Single HTML string
**READING TIME:** ≤ 3 minutes

**CONTENT STRATEGY:**
- Start with a hook that makes the research relevant to the reader
- Use vivid, accessible language without oversimplifying
- Integrate technical details naturally into the narrative
- Emphasize the "why should I care" aspect
- Mention key figures/tables organically when they support important points

**HTML STRUCTURE (fluid, not rigid):**
<div class="paper-summary">
    <header>
        <h1>Paper Title</h1>
        <div class="authors">Author list</div>
    </header>

    <section class="research-context">
        <h2>The Big Question</h2>
        <p>Engaging explanation of what motivated this research and why it matters...</p>
    </section>

    <section class="approach">
        <h2>How They Tackled It</h2>
        <p>Narrative description of methods - focus on the innovative aspects...</p>
    </section>

    <section class="discoveries">
        <h2>What They Uncovered</h2>
        <p>Key findings presented as a story. Reference figures naturally: <em>"The data in Figure 3 reveals..."</em></p>
        <p>Include surprising results and their immediate implications.</p>
    </section>

    <section class="critical-view">
        <h2>Putting It In Perspective</h2>
        <p>Limitations and what they mean for interpreting the results...</p>
    </section>

    <section class="future-impact">
        <h2>Why This Matters</h2>
        <p>Practical applications and how this moves the field forward...</p>
    </section>
</div>

**WRITING GUIDELINES:**
- Use <strong> for emphasis, <em> for technical terms
- Include <blockquote> for particularly striking findings
- Use <ul> only for listing 2-3 key takeaways
- Maintain consistent tone: authoritative yet accessible
- Ensure smooth transitions between sections
- Focus on narrative flow over exhaustive detail

**CRITICAL: Output ONLY the HTML string, no additional text.**
"""

summarize_newsletter_prompt_template = """
Your sole role is to reduce the received HTML code which represents a summary of a scientific article in order to show only first 500 characters.
After that you must display 3 dots.

YOu MUST not alter the content of the first 500 characters but you must return a valid html file

--- COMPLETE PAPER SUMMARY START ---
{paper_summary}
--- COMPLETE PAPER SUMMARY END ---
"""

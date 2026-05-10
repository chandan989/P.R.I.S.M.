# P.R.I.S.M. Knowledge Base Initialization

This directory contains sample data and initialization scripts for the P.R.I.S.M. knowledge base.

## Sample Data Structure

```
knowledge_base/sources/
├── fda/
│   ├── drug_labels/
│   ├── safety_communications/
│   └── medwatch/
├── drugbank/
│   ├── interaction_profiles/
│   ├── enzyme_data/
│   └── pharmacokinetics/
├── pubmed/
│   ├── pharmacovigilance/
│   ├── clinical_trials/
│   └── case_reports/
├── mimic/
│   ├── clinical_notes/
│   ├── medication_records/
│   └── lab_results/
└── formulary/
    ├── institutional_drugs/
    ├── dosage_guidelines/
    └── contraindications/
```

## Document Format

Each document should be a JSON file with the following structure:

```json
{
  "doc_id": "unique-document-id",
  "content": "Document text content",
  "metadata": {
    "source": "fda|drugbank|pubmed|mimic|formulary",
    "category": "category-name",
    "drugs": ["drug1", "drug2"],
    "severity": "critical|moderate|low",
    "date": "2024-01-01",
    "url": "https://source-url-if-available"
  }
}
```

## Adding Documents

### Manual Addition

```python
from knowledge_base import KnowledgeBase

kb = KnowledgeBase()

kb.add_document(
    doc_id="fda-warfarin-label",
    content="Warfarin is contraindicated with clarithromycin due to increased bleeding risk...",
    metadata={
        "source": "fda",
        "category": "drug_labels",
        "drugs": ["warfarin", "clarithromycin"],
        "severity": "critical"
    }
)

kb.save_index()
```

### Batch Import

```bash
python scripts/import_documents.py --directory ./data/fda_labels
```

## Sample Documents

### FDA Drug Label Example

```json
{
  "doc_id": "fda-warfarin-label-2024",
  "content": "Warfarin sodium tablets are indicated for the prophylaxis and/or treatment of venous thrombosis and its extension, and pulmonary embolism. CONTRAINDICATIONS: Warfarin is contraindicated in any localized or general physical condition or personal circumstance in which the hazard of hemorrhage might be greater than the potential clinical benefits of anticoagulation. DRUG INTERACTIONS: Many drugs, both prescription and over-the-counter, can affect the INR. CYP3A4 and CYP2C9 inhibitors like clarithromycin can significantly increase warfarin levels and bleeding risk.",
  "metadata": {
    "source": "fda",
    "category": "drug_labels",
    "drugs": ["warfarin", "clarithromycin"],
    "severity": "critical",
    "date": "2024-01-15",
    "url": "https://www.accessdata.fda.gov/drugsatfda_docs/label/2024/009218s054lbl.pdf"
  }
}
```

### DrugBank Interaction Example

```json
{
  "doc_id": "drugbank-warfarin-clarithromycin",
  "content": "Warfarin and clarithromycin interaction: Clarithromycin is a potent inhibitor of CYP3A4, the primary enzyme responsible for warfarin metabolism. This interaction leads to increased warfarin plasma concentrations and enhanced anticoagulant effect, significantly increasing the risk of bleeding. INR should be monitored closely if these drugs must be co-administered.",
  "metadata": {
    "source": "drugbank",
    "category": "interaction_profiles",
    "drugs": ["warfarin", "clarithromycin"],
    "severity": "critical",
    "date": "2024-02-01",
    "enzymes": ["CYP3A4"]
  }
}
```

### PubMed Pharmacovigilance Example

```json
{
  "doc_id": "pubmed-case-warfarin-bleeding-2024",
  "content": "Case report: A 72-year-old male patient on stable warfarin therapy developed major gastrointestinal bleeding 5 days after starting clarithromycin for pneumonia. The patient's INR increased from 2.1 to 8.3. This case highlights the importance of recognizing the warfarin-clarithromycin interaction and monitoring INR when macrolide antibiotics are prescribed to patients on warfarin.",
  "metadata": {
    "source": "pubmed",
    "category": "case_reports",
    "drugs": ["warfarin", "clarithromycin"],
    "severity": "critical",
    "date": "2024-03-10",
    "pmid": "12345678"
  }
}
```

## Initialization Steps

1. **Create directory structure**
   ```bash
   mkdir -p knowledge_base/sources/{fda,drugbank,pubmed,mimic,formulary}/{drug_labels,safety_communications,medwatch,interaction_profiles,enzyme_data,pharmacokinetics,pharmacovigilance,clinical_trials,case_reports,clinical_notes,medication_records,lab_results,institutional_drugs,dosage_guidelines,contraindications}
   ```

2. **Import sample documents**
   ```bash
   python scripts/import_sample_data.py
   ```

3. **Build the index**
   ```bash
   python knowledge_base/knowledge_base.py --rebuild
   ```

4. **Verify the index**
   ```bash
   python knowledge_base/knowledge_base.py --stats
   ```

## Data Sources

### FDA Drug Labels
- Download from: https://www.accessdata.fda.gov/scripts/cder/daf/
- Format: Structured XML/JSON
- Update frequency: Weekly

### DrugBank
- Requires license: https://go.drugbank.com/
- Format: XML/JSON
- Update frequency: Quarterly

### PubMed
- Access via: https://pubmed.ncbi.nlm.nih.gov/
- Format: Abstracts in XML/JSON
- Update frequency: Daily

### MIMIC-IV
- Requires access request: https://physionet.org/content/mimiciv/
- Format: De-identified clinical data
- Update frequency: Static (v2.2)

### Institutional Formulary
- Source: Hospital pharmacy systems
- Format: Custom (varies by institution)
- Update frequency: Monthly

## Quality Guidelines

### Document Selection Criteria

1. **Relevance**: Must relate to drug interactions, contraindications, or pharmacology
2. **Authority**: Must come from reputable sources (FDA, DrugBank, peer-reviewed journals)
3. **Currency**: Prefer documents from the last 5 years
4. **Completeness**: Must contain sufficient detail for verification

### Content Standards

1. **Accuracy**: Information must be factually correct
2. **Clarity**: Language should be unambiguous
3. **Specificity**: Include specific drug names, dosages, and mechanisms
4. **Evidence**: Include supporting evidence where applicable

## Maintenance

### Regular Updates

```bash
# Check for staleness
python knowledge_base/delta_agent/pull_delta.py --check-staleness

# Force update
python knowledge_base/delta_agent/pull_delta.py --force
```

### Index Rebuild

```bash
# Rebuild from source documents
python knowledge_base/knowledge_base.py --rebuild
```

### Backup Management

```bash
# Clean up old backups
python knowledge_base/delta_agent/apply_delta.py --cleanup-backups
```

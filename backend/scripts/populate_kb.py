#!/usr/bin/env python3
"""
P.R.I.S.M. Knowledge Base Population Script

Populates the knowledge base with real clinical data from PubMed, DrugBank, FDA, and other sources.

This script supports:
- PubMed API (biopython)
- DrugBank API
- FDA Drug Label API
- ClinicalTrials.gov API
- Local JSON/CSV imports

Requirements:
- pip install biopython requests pandas
"""

import os
import sys
import json
import logging
import requests
import time
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "knowledge_base"))

from knowledge_base import KnowledgeBase

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PubMedFetcher:
    """Fetches clinical data from PubMed."""

    def __init__(self, email: Optional[str] = None, api_key: Optional[str] = None):
        """
        Initialize PubMed fetcher.

        Args:
            email: Email for PubMed API (required)
            api_key: Optional API key for higher rate limits
        """
        self.email = email
        self.api_key = api_key
        self.base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def search(self, query: str, max_results: int = 100) -> List[str]:
        """
        Search PubMed for articles.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of PubMed IDs
        """
        url = f"{self.base_url}/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json"
        }

        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("esearchresult", {}).get("idlist", [])
        except Exception as e:
            logger.error(f"PubMed search failed: {e}")
            return []

    def fetch_abstract(self, pmid: str) -> Optional[Dict[str, Any]]:
        """
        Fetch abstract for a PubMed article.

        Args:
            pmid: PubMed ID

        Returns:
            Article data or None
        """
        url = f"{self.base_url}/efetch.fcgi"
        params = {
            "db": "pubmed",
            "id": pmid,
            "retmode": "xml"
        }

        if self.email:
            params["email"] = self.email
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            # Add rate limiting
            time.sleep(0.35)  # Stay under 3 requests/second limit

            response = requests.get(url, params=params)
            response.raise_for_status()

            # Parse XML response
            root = ET.fromstring(response.text)

            # Define namespace
            ns = {'pubmed': 'http://www.ncbi.nlm.nih.gov/PubMed'}

            # Extract title
            title_elem = root.find('.//pubmed:ArticleTitle', ns)
            title = title_elem.text if title_elem is not None else ""

            # Extract abstract
            abstract_text = ""
            abstract_elem = root.find('.//pubmed:AbstractText', ns)
            if abstract_elem is not None:
                abstract_text = abstract_elem.text or ""

            # Extract authors
            authors = []
            author_list = root.findall('.//pubmed:Author', ns)
            for author in author_list[:5]:  # Limit to first 5 authors
                last_name = author.find('pubmed:LastName', ns)
                fore_name = author.find('pubmed:ForeName', ns)
                if last_name is not None and fore_name is not None:
                    authors.append(f"{fore_name.text} {last_name.text}")
                elif last_name is not None:
                    authors.append(last_name.text)

            # Extract journal
            journal_elem = root.find('.//pubmed:Journal/pubmed:Title', ns)
            journal = journal_elem.text if journal_elem is not None else ""

            # Extract publication date
            pub_date = ""
            year_elem = root.find('.//pubmed:PubDate/pubmed:Year', ns)
            if year_elem is not None:
                pub_date = year_elem.text

            return {
                "pmid": pmid,
                "title": title,
                "abstract": abstract_text,
                "authors": authors,
                "journal": journal,
                "publication_date": pub_date
            }

        except Exception as e:
            logger.error(f"Failed to fetch abstract {pmid}: {e}")
            return None


class DrugBankFetcher:
    """Fetches drug data from DrugBank."""

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize DrugBank fetcher.

        Args:
            api_key: DrugBank API key
        """
        self.api_key = api_key
        self.base_url = "https://go.drugbank.com/api/v1"

    def fetch_drug(self, drug_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch drug information.

        Args:
            drug_name: Drug name

        Returns:
            Drug data or None
        """
        if not self.api_key:
            logger.warning("DrugBank API key not provided")
            return None

        url = f"{self.base_url}/drugs/{drug_name}"
        headers = {"Authorization": f"Bearer {self.api_key}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Failed to fetch drug {drug_name}: {e}")
            return None


class ClinicalTrialsFetcher:
    """Fetches clinical trial data from ClinicalTrials.gov."""

    def __init__(self):
        """Initialize ClinicalTrials.gov fetcher."""
        self.base_url = "https://clinicaltrials.gov/api/v2/studies"

    def search(self, query: str, max_results: int = 50) -> List[Dict[str, Any]]:
        """
        Search ClinicalTrials.gov for studies.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            List of study data
        """
        params = {
            "query.term": query,
            "pageSize": max_results,
            "fields": "ProtocolSection.IdentificationModule.NCTId,ProtocolSection.IdentificationModule.BriefTitle,ProtocolSection.DescriptionModule.BriefSummary,ProtocolSection.DescriptionModule.DetailedDescription,ProtocolSection.EligibilityModule.EligibilityCriteria,ProtocolSection.InterventionsModule.Interventions,ProtocolSection.ConditionsModule.Conditions"
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()

            studies = []
            for study in data.get("studies", []):
                protocol = study.get("protocolSection", {})
                identification = protocol.get("identificationModule", {})
                description = protocol.get("descriptionModule", {})
                eligibility = protocol.get("eligibilityModule", {})
                interventions = protocol.get("interventionsModule", {})
                conditions = protocol.get("conditionsModule", {})

                # Extract study data
                nct_id = identification.get("nctId", "")
                title = identification.get("briefTitle", "")
                brief_summary = description.get("briefSummary", "")
                detailed_description = description.get("detailedDescription", "")

                # Extract eligibility criteria
                eligibility_text = ""
                if eligibility:
                    criteria = eligibility.get("eligibilityCriteria", "")
                    if isinstance(criteria, list):
                        eligibility_text = "\n".join([c.get("text", "") for c in criteria])
                    else:
                        eligibility_text = criteria

                # Extract interventions
                interventions_text = ""
                if interventions:
                    intervention_list = interventions.get("interventions", [])
                    for intervention in intervention_list[:3]:  # Limit to first 3
                        intervention_type = intervention.get("type", "")
                        intervention_name = intervention.get("name", "")
                        if intervention_type and intervention_name:
                            interventions_text += f"{intervention_type}: {intervention_name}\n"

                # Extract conditions
                conditions_list = conditions.get("conditions", [])
                conditions_text = ", ".join(conditions_list) if conditions_list else ""

                studies.append({
                    "nct_id": nct_id,
                    "title": title,
                    "brief_summary": brief_summary,
                    "detailed_description": detailed_description,
                    "eligibility_criteria": eligibility_text,
                    "interventions": interventions_text,
                    "conditions": conditions_text
                })

            return studies

        except Exception as e:
            logger.error(f"ClinicalTrials search failed: {e}")
            return []


class FDALabelFetcher:
    """Fetches FDA drug labels."""

    def __init__(self):
        """Initialize FDA label fetcher."""
        self.base_url = "https://api.fda.gov/drug/label.json"

    def fetch_label(self, drug_name: str) -> Optional[Dict[str, Any]]:
        """
        Fetch FDA drug label.

        Args:
            drug_name: Drug name

        Returns:
            Label data or None
        """
        params = {
            "search": f'openfda.brand_name:"{drug_name}"',
            "limit": 1
        }

        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])

            if not results:
                logger.warning(f"No FDA label found for {drug_name}")
                return None

            label = results[0]

            # Extract structured sections
            extracted_data = {
                "drug_name": drug_name,
                "boxed_warning": self._extract_section(label, "boxed_warning"),
                "contraindications": self._extract_section(label, "contraindications"),
                "warnings": self._extract_section(label, "warnings_and_precautions"),
                "adverse_reactions": self._extract_section(label, "adverse_reactions"),
                "drug_interactions": self._extract_section(label, "drug_interactions"),
                "use_in_specific_populations": self._extract_section(label, "use_in_specific_populations"),
                "dosage_and_administration": self._extract_section(label, "dosage_and_administration")
            }

            return extracted_data

        except Exception as e:
            logger.error(f"Failed to fetch FDA label for {drug_name}: {e}")
            return None

    def _extract_section(self, label: Dict, section_name: str) -> str:
        """
        Extract a section from FDA label.

        Args:
            label: FDA label data
            section_name: Name of section to extract

        Returns:
            Section text content
        """
        section = label.get(section_name, [])

        if not section:
            return ""

        # Handle different section formats
        if isinstance(section, list):
            # Join multiple subsections
            texts = []
            for subsection in section:
                if isinstance(subsection, dict):
                    # Extract text from nested structure
                    text = self._extract_text_from_dict(subsection)
                    if text:
                        texts.append(text)
                elif isinstance(subsection, str):
                    texts.append(subsection)
            return "\n\n".join(texts)
        elif isinstance(section, dict):
            return self._extract_text_from_dict(section)
        elif isinstance(section, str):
            return section

        return ""

    def _extract_text_from_dict(self, data: Dict) -> str:
        """
        Recursively extract text from nested dictionary structure.

        Args:
            data: Dictionary data

        Returns:
            Extracted text
        """
        texts = []

        for key, value in data.items():
            if isinstance(value, str):
                texts.append(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, str):
                        texts.append(item)
                    elif isinstance(item, dict):
                        texts.append(self._extract_text_from_dict(item))
            elif isinstance(value, dict):
                texts.append(self._extract_text_from_dict(value))

        return "\n".join(texts)


class KnowledgeBasePopulator:
    """Populates the knowledge base with clinical documents."""

    def __init__(self, kb_root: str = "./knowledge_base"):
        """
        Initialize the populator.

        Args:
            kb_root: Root path of the knowledge base
        """
        self.kb_root = Path(kb_root)
        self.kb = KnowledgeBase(str(self.kb_root))

        # Initialize fetchers
        self.pubmed = PubMedFetcher(
            email=os.getenv("PUBMED_EMAIL"),
            api_key=os.getenv("PUBMED_API_KEY")
        )
        self.drugbank = DrugBankFetcher(api_key=os.getenv("DRUGBANK_API_KEY"))
        self.fda = FDALabelFetcher()
        self.clinical_trials = ClinicalTrialsFetcher()

    def fetch_from_pubmed(self, query: str, max_results: int = 50) -> int:
        """
        Fetch and add documents from PubMed.

        Args:
            query: PubMed search query
            max_results: Maximum number of results

        Returns:
            Number of documents added
        """
        logger.info(f"Fetching from PubMed: {query}")

        pmids = self.pubmed.search(query, max_results)
        added_count = 0

        for pmid in pmids:
                    article = self.pubmed.fetch_abstract(pmid)
                    if article:
                        doc_id = f"pubmed_{pmid}"

                        # Build content from article data
                        content_parts = []
                        if article.get('title'):
                            content_parts.append(f"Title: {article['title']}")
                        if article.get('abstract'):
                            content_parts.append(f"Abstract: {article['abstract']}")
                        if article.get('authors'):
                            content_parts.append(f"Authors: {', '.join(article['authors'])}")
                        if article.get('journal'):
                            content_parts.append(f"Journal: {article['journal']}")
                        if article.get('publication_date'):
                            content_parts.append(f"Publication Date: {article['publication_date']}")

                        content = "\n\n".join(content_parts)

                        success = self.kb.add_document(
                            doc_id=doc_id,
                            content=content,
                            metadata={
                                "source": "PubMed",
                                "category": "clinical_evidence",
                                "pmid": pmid,
                                "last_updated": datetime.utcnow().isoformat()
                            }
                        )

                        if success:
                            added_count += 1

        logger.info(f"Added {added_count} documents from PubMed")
        return added_count

    def fetch_from_fda(self, drug_names: List[str]) -> int:
        """
        Fetch and add FDA drug labels.

        Args:
            drug_names: List of drug names

        Returns:
            Number of documents added
        """
        logger.info(f"Fetching FDA labels for {len(drug_names)} drugs")

        added_count = 0

        for drug_name in drug_names:
            label = self.fda.fetch_label(drug_name)
            if label:
                doc_id = f"fda_{drug_name.lower().replace(' ', '_')}"

                # Extract relevant information
                content_parts = []
                content_parts.append(f"Drug: {drug_name}")

                if label.get("boxed_warning"):
                    content_parts.append(f"BOXED WARNING: {label['boxed_warning']}")
                if label.get("contraindications"):
                    content_parts.append(f"CONTRAINDICATIONS: {label['contraindications']}")
                if label.get("warnings"):
                    content_parts.append(f"WARNINGS AND PRECAUTIONS: {label['warnings']}")
                if label.get("adverse_reactions"):
                    content_parts.append(f"ADVERSE REACTIONS: {label['adverse_reactions']}")
                if label.get("drug_interactions"):
                    content_parts.append(f"DRUG INTERACTIONS: {label['drug_interactions']}")
                if label.get("use_in_specific_populations"):
                    content_parts.append(f"USE IN SPECIFIC POPULATIONS: {label['use_in_specific_populations']}")
                if label.get("dosage_and_administration"):
                    content_parts.append(f"DOSAGE AND ADMINISTRATION: {label['dosage_and_administration']}")

                content = "\n\n".join(content_parts)

                success = self.kb.add_document(
                    doc_id=doc_id,
                    content=content,
                    metadata={
                        "source": "FDA",
                        "category": "drug_label",
                        "drug": drug_name,
                        "last_updated": datetime.utcnow().isoformat()
                    }
                )

                if success:
                    added_count += 1
            else:
                logger.warning(f"Could not fetch FDA label for {drug_name}")

        logger.info(f"Added {added_count} FDA labels")
        return added_count

    def fetch_from_clinical_trials(self, query: str, max_results: int = 30) -> int:
        """
        Fetch and add clinical trial data.

        Args:
            query: Search query
            max_results: Maximum number of results

        Returns:
            Number of documents added
        """
        logger.info(f"Fetching from ClinicalTrials.gov: {query}")

        studies = self.clinical_trials.search(query, max_results)
        added_count = 0

        for study in studies:
            nct_id = study.get("nct_id", "")
            if not nct_id:
                continue

            doc_id = f"clinical_trials_{nct_id}"

            # Build content from study data
            content_parts = []
            if study.get('title'):
                content_parts.append(f"Title: {study['title']}")
            if study.get('conditions'):
                content_parts.append(f"Conditions: {study['conditions']}")
            if study.get('brief_summary'):
                content_parts.append(f"Brief Summary: {study['brief_summary']}")
            if study.get('detailed_description'):
                content_parts.append(f"Detailed Description: {study['detailed_description']}")
            if study.get('eligibility_criteria'):
                content_parts.append(f"Eligibility Criteria: {study['eligibility_criteria']}")
            if study.get('interventions'):
                content_parts.append(f"Interventions: {study['interventions']}")

            content = "\n\n".join(content_parts)

            success = self.kb.add_document(
                doc_id=doc_id,
                content=content,
                metadata={
                    "source": "ClinicalTrials.gov",
                    "category": "clinical_evidence",
                    "nct_id": nct_id,
                    "last_updated": datetime.utcnow().isoformat()
                }
            )

            if success:
                added_count += 1

        logger.info(f"Added {added_count} documents from ClinicalTrials.gov")
        return added_count

    def import_from_json(self, json_file: str) -> int:
        """
        Import documents from a JSON file.

        Args:
            json_file: Path to JSON file

        Returns:
            Number of documents added
        """
        logger.info(f"Importing from {json_file}")

        with open(json_file, 'r') as f:
            data = json.load(f)

        added_count = 0

        if isinstance(data, list):
            documents = data
        elif isinstance(data, dict):
            documents = [data]
        else:
            logger.error(f"Invalid JSON format in {json_file}")
            return 0

        for doc in documents:
            doc_id = doc.get("doc_id") or doc.get("id")
            content = doc.get("content") or doc.get("text")
            metadata = doc.get("metadata", {})

            if not doc_id or not content:
                logger.warning(f"Skipping document missing id or content")
                continue

            success = self.kb.add_document(
                doc_id=doc_id,
                content=content,
                metadata=metadata
            )

            if success:
                added_count += 1

        logger.info(f"Imported {added_count} documents from {json_file}")
        return added_count

    def add_sample_data(self) -> int:
        """
        Add curated sample clinical data as fallback.

        Returns:
            Number of documents added
        """
        logger.info("Adding sample clinical data")

        sample_documents = self._get_sample_documents()
        added_count = 0

        for doc in sample_documents:
            doc_id = doc.get("doc_id")
            content = doc.get("content")
            metadata = doc.get("metadata", {})

            if not doc_id or not content:
                logger.warning(f"Skipping sample document missing id or content")
                continue

            success = self.kb.add_document(
                doc_id=doc_id,
                content=content,
                metadata=metadata
            )

            if success:
                added_count += 1

        logger.info(f"Added {added_count} sample documents")
        return added_count

    def _get_sample_documents(self) -> List[Dict[str, Any]]:
        """
        Get curated sample clinical documents.

        Returns:
            List of sample documents
        """
        return [
            # Drug Interactions
            {
                "doc_id": "sample_warfarin_interactions",
                "content": "Warfarin Drug Interactions: Warfarin has significant drug-drug interactions that can increase bleeding risk. Major interactions include: (1) Antibiotics - clarithromycin, erythromycin, azithromycin, and fluoroquinolones can increase warfarin levels by inhibiting CYP3A4. (2) Antiplatelet agents - aspirin, clopidogrel, and NSAIDs increase bleeding risk when combined with warfarin. (3) Amiodarone - significantly increases warfarin effect, requiring dose reduction by 30-50%. (4) SSRIs - increase bleeding risk through platelet inhibition. (5) Statins - some statins may increase warfarin levels. Monitor INR closely when starting or stopping interacting medications.",
                "metadata": {
                    "source": "Sample",
                    "category": "drug_interactions",
                    "drugs": ["warfarin", "clarithromycin", "amiodarone", "aspirin", "clopidogrel"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_clarithromycin_interactions",
                "content": "Clarithromycin Drug Interactions: Clarithromycin is a strong CYP3A4 inhibitor with numerous drug interactions. Contraindicated combinations include: (1) Cisapride - risk of QT prolongation and cardiac arrhythmias. (2) Pimozide - increased risk of cardiac arrhythmias. (3) Ergot alkaloids - ergotism risk. (4) Lovastatin and simvastatin - increased risk of myopathy and rhabdomyolysis. (5) Colchicine - increased colchicine levels, potentially fatal. Significant interactions requiring monitoring: (1) Warfarin - increased INR and bleeding risk. (2) Digoxin - increased digoxin levels. (3) Theophylline - increased theophylline levels. (4) Benzodiazepines - increased sedation. (5) Oral hypoglycemics - increased hypoglycemia risk.",
                "metadata": {
                    "source": "Sample",
                    "category": "drug_interactions",
                    "drugs": ["clarithromycin", "cisapride", "pimozide", "lovastatin", "simvastatin", "colchicine"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_amiodarone_interactions",
                "content": "Amiodarone Drug Interactions: Amiodarone has numerous significant drug interactions due to its effects on multiple CYP enzymes and P-glycoprotein. Major interactions include: (1) Warfarin - increases INR by 2-5 fold, requires warfarin dose reduction of 30-50%. (2) Digoxin - increases digoxin levels by 70-100%, requires dose reduction. (3) Antiarrhythmics - quinidine, procainamide, flecainide, and propafenone levels increased. (4) Statins - simvastatin and lovastatin contraindicated due to rhabdomyolysis risk. (5) Beta-blockers - additive bradycardia and AV block risk. (6) QT-prolonging drugs - increased risk of torsades de pointes. Monitor drug levels and adjust doses accordingly.",
                "metadata": {
                    "source": "Sample",
                    "category": "drug_interactions",
                    "drugs": ["amiodarone", "warfarin", "digoxin", "simvastatin", "lovastatin"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_ace_inhibitor_interactions",
                "content": "ACE Inhibitor Drug Interactions: ACE inhibitors have several important drug interactions. (1) Potassium-sparing diuretics (spironolactone, amiloride, triamterene) and potassium supplements - increased risk of hyperkalemia. (2) NSAIDs - may reduce antihypertensive effect and increase risk of renal impairment. (3) Lithium - increased lithium levels and toxicity risk. (4) Aliskiren - increased risk of hypotension, hyperkalemia, and renal impairment in diabetic patients. (5) Angiotensin receptor blockers - increased risk of hypotension, hyperkalemia, and renal impairment. Monitor blood pressure, renal function, and potassium levels when combining these medications.",
                "metadata": {
                    "source": "Sample",
                    "category": "drug_interactions",
                    "drugs": ["ace_inhibitors", "lisinopril", "enalapril", "spironolactone", "nsaids", "lithium"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_beta_blocker_interactions",
                "content": "Beta-Blocker Drug Interactions: Beta-blockers have several clinically significant interactions. (1) Calcium channel blockers (verapamil, diltiazem) - increased risk of bradycardia, heart block, and heart failure. (2) Antiarrhythmics (amiodarone, disopyramide) - increased risk of bradycardia and conduction abnormalities. (3) Insulin and oral hypoglycemics - may mask hypoglycemia symptoms. (4) Clonidine - may cause rebound hypertension if clonidine withdrawn. (5) NSAIDs - may reduce antihypertensive effect. (6) Sympathomimetics - may reduce beta-blocker efficacy. Monitor heart rate, blood pressure, and blood glucose when combining these medications.",
                "metadata": {
                    "source": "Sample",
                    "category": "drug_interactions",
                    "drugs": ["beta_blockers", "metoprolol", "propranolol", "verapamil", "diltiazem", "amiodarone"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_statin_interactions",
                "content": "Statin Drug Interactions: Statins have important drug interactions affecting metabolism and safety. (1) CYP3A4 inhibitors (clarithromycin, erythromycin, azole antifungals, protease inhibitors) - significantly increase simvastatin, lovastatin, and atorvastatin levels, increasing myopathy and rhabdomyolysis risk. (2) Gemfibrozil - increases statin levels and myopathy risk. (3) Niacin - increased risk of myopathy, especially with simvastatin. (4) Cyclosporine - increases statin levels. (5) Warfarin - may increase INR with some statins. (6) Digoxin - may increase digoxin levels. Monitor CK levels and for muscle symptoms when combining statins with interacting medications.",
                "metadata": {
                    "source": "Sample",
                    "category": "drug_interactions",
                    "drugs": ["statins", "simvastatin", "lovastatin", "atorvastatin", "gemfibrozil", "niacin", "cyclosporine"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_metformin_interactions",
                "content": "Metformin Drug Interactions: Metformin has several important drug interactions. (1) Cationic drugs (cimetidine, ranitidine, digoxin, quinidine, trimethoprim, vancomycin) - may compete for renal tubular clearance and increase metformin levels. (2) Carbonic anhydrase inhibitors (acetazolamide, topiramate) - increase risk of metabolic acidosis. (3) Alcohol - increases lactic acidosis risk. (4) Diuretics - may increase risk of renal impairment and lactic acidosis. (5) Iodinated contrast media - may increase risk of lactic acidosis in patients with renal impairment. Monitor renal function and discontinue metformin if renal impairment develops.",
                "metadata": {
                    "source": "Sample",
                    "category": "drug_interactions",
                    "drugs": ["metformin", "cimetidine", "digoxin", "quinidine", "acetazolamide", "topiramate"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_ssri_interactions",
                "content": "SSRI Drug Interactions: SSRIs have several important drug interactions. (1) MAOIs - contraindicated combination due to serotonin syndrome risk. Wait 2 weeks after stopping MAOI before starting SSRI, or 2 weeks after stopping SSRI before starting MAOI (5 weeks for fluoxetine). (2) Other serotonergic drugs (SNRIs, TCAs, tramadol, linezolid, methylene blue) - increased serotonin syndrome risk. (3) Antiplatelet agents and anticoagulants - increased bleeding risk. (4) NSAIDs - increased bleeding risk. (5) CYP2D6 inhibitors (fluoxetine, paroxetine) - may increase levels of other CYP2D6 substrates. (6) Warfarin - may increase INR and bleeding risk. Monitor for serotonin syndrome symptoms and bleeding when combining SSRIs with other medications.",
                "metadata": {
                    "source": "Sample",
                    "category": "drug_interactions",
                    "drugs": ["ssris", "fluoxetine", "paroxetine", "sertraline", "maois", "tramadol", "warfarin"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_fluoroquinolone_interactions",
                "content": "Fluoroquinolone Drug Interactions: Fluoroquinolones have several important drug interactions. (1) Antacids, sucralfate, iron supplements, and multivitamins with minerals - significantly reduce fluoroquinolone absorption. Separate administration by 2 hours before or 6 hours after. (2) Warfarin - may increase INR and bleeding risk. (3) Oral hypoglycemics - may increase hypoglycemia risk. (4) NSAIDs - increased risk of CNS stimulation and seizures. (5) Theophylline - increased theophylline levels and toxicity risk. (6) CYP1A2 inhibitors (ciprofloxacin) - may increase levels of other CYP1A2 substrates. Monitor drug levels and clinical effects when combining fluoroquinolones with interacting medications.",
                "metadata": {
                    "source": "Sample",
                    "category": "drug_interactions",
                    "drugs": ["fluoroquinolones", "ciprofloxacin", "levofloxacin", "moxifloxacin", "warfarin", "theophylline"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_digoxin_interactions",
                "content": "Digoxin Drug Interactions: Digoxin has numerous significant drug interactions affecting levels and toxicity risk. (1) Amiodarone - increases digoxin levels by 70-100%, requires dose reduction. (2) Quinidine - increases digoxin levels by 50-100%. (3) Verapamil and diltiazem - increase digoxin levels by 50-75%. (4) Macrolide antibiotics (clarithromycin, erythromycin) - increase digoxin levels. (5) Spironolactone - increases digoxin levels. (6) Antacids, kaolin-pectin, and cholestyramine - decrease digoxin absorption. (7) P-glycoprotein inhibitors (verapamil, quinidine, amiodarone) - increase digoxin levels. Monitor digoxin levels and adjust doses when combining with interacting medications.",
                "metadata": {
                    "source": "Sample",
                    "category": "drug_interactions",
                    "drugs": ["digoxin", "amiodarone", "quinidine", "verapamil", "diltiazem", "clarithromycin", "spironolactone"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            # Contraindications
            {
                "doc_id": "sample_ace_inhibitor_contraindications",
                "content": "ACE Inhibitor Contraindications: ACE inhibitors are contraindicated in several conditions. (1) History of angioedema related to previous ACE inhibitor therapy. (2) Hereditary or idiopathic angioedema. (3) Concomitant use with aliskiren in diabetic patients. (4) Pregnancy - ACE inhibitors can cause fetal injury and death. Discontinue immediately if pregnancy detected. (5) Bilateral renal artery stenosis - may cause acute renal failure. (6) Hypersensitivity to ACE inhibitors. Use caution in patients with renal impairment, hyperkalemia, or volume depletion. Monitor renal function and potassium levels regularly.",
                "metadata": {
                    "source": "Sample",
                    "category": "contraindications",
                    "drugs": ["ace_inhibitors", "lisinopril", "enalapril", "ramipril"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_beta_blocker_contraindications",
                "content": "Beta-Blocker Contraindications: Beta-blockers are contraindicated in several conditions. (1) Severe bradycardia (heart rate < 50 bpm). (2) Second or third degree AV block without a pacemaker. (3) Sick sinus syndrome without a pacemaker. (4) Cardiogenic shock. (5) Uncompensated heart failure. (6) Severe peripheral arterial disease. (7) Bronchial asthma - non-selective beta-blockers contraindicated. (8) Hypersensitivity to beta-blockers. Use caution in patients with diabetes (may mask hypoglycemia), depression, and myasthenia gravis. Monitor heart rate and blood pressure regularly.",
                "metadata": {
                    "source": "Sample",
                    "category": "contraindications",
                    "drugs": ["beta_blockers", "metoprolol", "propranolol", "atenolol"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_statin_contraindications",
                "content": "Statin Contraindications: Statins are contraindicated in several conditions. (1) Active liver disease or unexplained persistent elevations of liver transaminases. (2) Pregnancy - statins are teratogenic. (3) Breastfeeding - statins may be excreted in breast milk. (4) Hypersensitivity to statins. (5) Concomitant use with strong CYP3A4 inhibitors for simvastatin and lovastatin (due to rhabdomyolysis risk). Use caution in patients with history of liver disease, heavy alcohol use, or unexplained muscle symptoms. Monitor liver function tests and CK levels regularly.",
                "metadata": {
                    "source": "Sample",
                    "category": "contraindications",
                    "drugs": ["statins", "simvastatin", "lovastatin", "atorvastatin", "rosuvastatin"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_metformin_contraindications",
                "content": "Metformin Contraindications: Metformin is contraindicated in several conditions. (1) Renal impairment - eGFR < 30 mL/min/1.73 m² is contraindicated. eGFR 30-45 mL/min/1.73 m² requires dose reduction and careful monitoring. (2) Acute or chronic metabolic acidosis, including diabetic ketoacidosis. (3) Hypersensitivity to metformin. (4) Radiologic studies involving intravascular administration of iodinated contrast materials - temporarily discontinue metformin before and after procedure. (5) Severe hepatic impairment. Use caution in patients with excessive alcohol intake, hypoxic states, or dehydration. Monitor renal function regularly.",
                "metadata": {
                    "source": "Sample",
                    "category": "contraindications",
                    "drugs": ["metformin"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_ssri_contraindications",
                "content": "SSRI Contraindications: SSRIs have important contraindications. (1) Concomitant use with MAOIs - contraindicated due to serotonin syndrome risk. Wait 2 weeks after stopping MAOI before starting SSRI, or 2 weeks after stopping SSRI before starting MAOI (5 weeks for fluoxetine). (2) Linezolid and methylene blue - contraindicated due to serotonin syndrome risk. (3) Hypersensitivity to SSRIs. (4) Pimozide - contraindicated with some SSRIs due to QT prolongation risk. Use caution in patients with bipolar disorder (may induce mania), bleeding disorders, or hyponatremia risk. Monitor for serotonin syndrome symptoms, especially when starting or stopping medications.",
                "metadata": {
                    "source": "Sample",
                    "category": "contraindications",
                    "drugs": ["ssris", "fluoxetine", "paroxetine", "sertraline", "citalopram", "escitalopram"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_fluoroquinolone_contraindications",
                "content": "Fluoroquinolone Contraindications: Fluoroquinolones have important contraindications and warnings. (1) Hypersensitivity to fluoroquinolones or any quinolone antibiotic. (2) Tendon disorders or tendon rupture related to previous fluoroquinolone use. (3) Myasthenia gravis - may exacerbate muscle weakness. (4) Pregnancy - avoid unless benefits outweigh risks. (5) Breastfeeding - avoid unless benefits outweigh risks. (6) Children and adolescents - avoid unless no alternative available (may affect musculoskeletal development). Use caution in elderly patients, patients with renal impairment, and patients taking corticosteroids. Monitor for tendonitis, tendon rupture, and CNS effects.",
                "metadata": {
                    "source": "Sample",
                    "category": "contraindications",
                    "drugs": ["fluoroquinolones", "ciprofloxacin", "levofloxacin", "moxifloxacin"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_warfarin_contraindications",
                "content": "Warfarin Contraindications: Warfarin has several important contraindications. (1) Pregnancy - warfarin is teratogenic and can cause fetal hemorrhage. Use heparin instead during pregnancy. (2) Hemorrhagic tendencies or active bleeding. (3) Recent or planned surgery of the central nervous system or eye, or traumatic surgery resulting in large open surfaces. (4) Uncontrolled hypertension. (5) Threatened abortion, eclampsia, or preeclampsia. (6) Spinal puncture or other diagnostic or therapeutic procedures with potential for uncontrollable bleeding. (7) Hypersensitivity to warfarin. Use caution in patients with fall risk, liver disease, renal impairment, or alcoholism. Monitor INR regularly.",
                "metadata": {
                    "source": "Sample",
                    "category": "contraindications",
                    "drugs": ["warfarin", "coumadin"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_nitrate_contraindications",
                "content": "Nitrate Contraindications: Nitrates have important contraindications. (1) Concomitant use with phosphodiesterase-5 inhibitors (sildenafil, tadalafil, vardenafil) - contraindicated due to risk of severe hypotension. Wait at least 24 hours after sildenafil, 48 hours after tadalafil, or 24 hours after vardenafil before administering nitrates. (2) Severe anemia. (3) Increased intracranial pressure. (4) Hypersensitivity to nitrates. (5) Recent use of PDE-5 inhibitors. Use caution in patients with hypotension, volume depletion, or right ventricular infarction. Monitor blood pressure closely when initiating therapy.",
                "metadata": {
                    "source": "Sample",
                    "category": "contraindications",
                    "drugs": ["nitrates", "nitroglycerin", "isosorbide", "sildenafil", "tadalafil", "vardenafil"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            # Dosage Guidelines
            {
                "doc_id": "sample_warfarin_dosage",
                "content": "Warfarin Dosage Guidelines: Warfarin dosing requires individualization based on INR response. Initial dose: 2-5 mg orally once daily for 2-4 days. Maintenance dose: Adjust to maintain INR 2.0-3.0 for most indications (2.5-3.5 for mechanical heart valves). Dose adjustments: Increase or decrease by 5-20% based on INR results. Monitoring: Check INR daily until stable, then 2-3 times weekly for 1-2 weeks, then less frequently based on stability. Factors affecting dose: Age, body weight, diet (vitamin K intake), concurrent medications, liver function, genetic factors (CYP2C9 and VKORC1 polymorphisms). Elderly patients may require lower doses. Use lower initial doses in patients with liver impairment or malnutrition.",
                "metadata": {
                    "source": "Sample",
                    "category": "dosage_guidelines",
                    "drugs": ["warfarin", "coumadin"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_metformin_dosage",
                "content": "Metformin Dosage Guidelines: Metformin dosing requires consideration of renal function. Initial dose: 500 mg orally twice daily or 850 mg once daily with meals. Maintenance dose: 2000 mg daily in divided doses (maximum 2550 mg daily). Renal adjustment: eGFR ≥ 45 mL/min/1.73 m² - no dose adjustment needed. eGFR 30-45 mL/min/1.73 m² - not recommended to initiate, may continue if already on therapy with reduced dose. eGFR < 30 mL/min/1.73 m² - contraindicated. Administration: Take with meals to reduce gastrointestinal side effects. Extended-release formulation may improve tolerability. Monitor renal function at least annually, more frequently in elderly or at-risk patients.",
                "metadata": {
                    "source": "Sample",
                    "category": "dosage_guidelines",
                    "drugs": ["metformin", "glucophage"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_statin_dosage",
                "content": "Statin Dosage Guidelines: Statin dosing varies by agent and indication. Atorvastatin: Initial 10-20 mg daily, maximum 80 mg daily. Simvastatin: Initial 10-20 mg daily, maximum 40 mg daily (80 mg only in patients already on 80 mg without myopathy). Lovastatin: Initial 20 mg daily with evening meal, maximum 80 mg daily. Rosuvastatin: Initial 5-10 mg daily, maximum 40 mg daily. Pravastatin: Initial 10-20 mg daily, maximum 80 mg daily. High-intensity statin therapy (atorvastatin 40-80 mg or rosuvastatin 20-40 mg) recommended for high-risk patients. Moderate-intensity statin therapy recommended for moderate-risk patients. Take most statins in evening (except atorvastatin and rosuvastatin). Monitor liver function tests and CK levels as needed.",
                "metadata": {
                    "source": "Sample",
                    "category": "dosage_guidelines",
                    "drugs": ["statins", "atorvastatin", "simvastatin", "lovastatin", "rosuvastatin", "pravastatin"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_ace_inhibitor_dosage",
                "content": "ACE Inhibitor Dosage Guidelines: ACE inhibitor dosing varies by agent and indication. Lisinopril: Initial 10 mg daily for hypertension, 5 mg daily for heart failure. Maximum 80 mg daily. Enalapril: Initial 5 mg daily for hypertension, 2.5 mg daily for heart failure. Maximum 40 mg daily. Ramipril: Initial 2.5 mg daily for hypertension, 1.25 mg daily for heart failure. Maximum 10 mg daily. Captopril: Initial 25 mg 2-3 times daily for hypertension, 6.25 mg 3 times daily for heart failure. Maximum 450 mg daily. Start with lower doses in heart failure, volume depletion, or renal impairment. Titrate to target dose based on blood pressure response and tolerance. Monitor renal function and potassium levels.",
                "metadata": {
                    "source": "Sample",
                    "category": "dosage_guidelines",
                    "drugs": ["ace_inhibitors", "lisinopril", "enalapril", "ramipril", "captopril"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_beta_blocker_dosage",
                "content": "Beta-Blocker Dosage Guidelines: Beta-blocker dosing varies by agent and indication. Metoprolol tartrate: Initial 25-50 mg twice daily for hypertension, 12.5-25 mg twice daily for heart failure. Maximum 450 mg daily. Metoprolol succinate (extended-release): Initial 25-100 mg daily for hypertension, 12.5-25 mg daily for heart failure. Maximum 400 mg daily. Propranolol: Initial 40 mg twice daily for hypertension, 10-30 mg 3-4 times daily for anxiety. Maximum 640 mg daily. Atenolol: Initial 25-50 mg daily for hypertension. Maximum 100 mg daily. Start with lower doses in heart failure, bradycardia, or elderly patients. Titrate to target dose based on heart rate and blood pressure response. Monitor heart rate and blood pressure regularly.",
                "metadata": {
                    "source": "Sample",
                    "category": "dosage_guidelines",
                    "drugs": ["beta_blockers", "metoprolol", "propranolol", "atenolol"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            # Clinical Evidence
            {
                "doc_id": "sample_warfarin_evidence",
                "content": "Warfarin Clinical Evidence: Warfarin is a vitamin K antagonist anticoagulant with extensive clinical evidence supporting its use. Atrial fibrillation: Multiple trials (SPAF, BAATAF, CAFA, SPAF II) demonstrated 64% risk reduction in stroke compared to placebo. Meta-analyses show 60-70% stroke reduction. Mechanical heart valves: Warfarin is essential for preventing thromboembolism in patients with mechanical valves. Target INR 2.5-3.5 recommended. Venous thromboembolism: Warfarin is standard of care for VTE treatment and prevention. Duration varies by indication (3-12 months for provoked VTE, indefinite for unprovoked recurrent VTE). Bleeding risk: Major bleeding occurs in 1-3% of patients annually. Risk factors include age, hypertension, liver disease, concurrent medications, and INR variability. Regular monitoring and dose adjustment essential for safety and efficacy.",
                "metadata": {
                    "source": "Sample",
                    "category": "clinical_evidence",
                    "drugs": ["warfarin", "coumadin"],
                    "conditions": ["atrial_fibrillation", "mechanical_heart_valves", "venous_thromboembolism"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_statins_evidence",
                "content": "Statin Clinical Evidence: Statins are HMG-CoA reductase inhibitors with robust clinical evidence supporting cardiovascular risk reduction. Primary prevention: Meta-analyses of primary prevention trials show 20-25% reduction in major cardiovascular events per 1 mmol/L LDL-C reduction. Number needed to treat (NNT) for 5 years to prevent one major cardiovascular event is approximately 50-100. Secondary prevention: Statins reduce major cardiovascular events by 25-35% in patients with established cardiovascular disease. High-intensity statin therapy provides greater benefit than moderate-intensity. Safety: Statins are generally well-tolerated. Myopathy occurs in 0.1-0.5% of patients, rhabdomyolysis in <0.1%. Liver enzyme elevations occur in 0.5-2% but are rarely clinically significant. Diabetes risk increased by 9-12% but absolute risk is low. Benefits generally outweigh risks in appropriate patients.",
                "metadata": {
                    "source": "Sample",
                    "category": "clinical_evidence",
                    "drugs": ["statins", "atorvastatin", "simvastatin", "rosuvastatin"],
                    "conditions": ["cardiovascular_disease", "hyperlipidemia"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_ace_inhibitors_evidence",
                "content": "ACE Inhibitor Clinical Evidence: ACE inhibitors have extensive clinical evidence supporting their use in cardiovascular and renal diseases. Hypertension: Multiple trials demonstrate effective blood pressure reduction with 20-30% reduction in cardiovascular events. First-line therapy for most patients. Heart failure: SOLVD, CONSENSUS, and other trials showed 20-30% reduction in mortality and hospitalization. Standard of care for HFrEF. Post-MI: SAVE, TRACE, and AIRE trials demonstrated 20-25% reduction in mortality after myocardial infarction. Diabetic nephropathy: ACE inhibitors reduce progression of diabetic nephropathy by 30-50% compared to other antihypertensives. Renal protection independent of blood pressure effect. Safety: Generally well-tolerated. Common side effects include cough (5-20%), hyperkalemia (1-5%), and angioedema (0.1-0.5%). Contraindicated in pregnancy.",
                "metadata": {
                    "source": "Sample",
                    "category": "clinical_evidence",
                    "drugs": ["ace_inhibitors", "lisinopril", "enalapril", "ramipril"],
                    "conditions": ["hypertension", "heart_failure", "myocardial_infarction", "diabetic_nephropathy"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_metformin_evidence",
                "content": "Metformin Clinical Evidence: Metformin is a biguanide with extensive clinical evidence supporting its use in type 2 diabetes. First-line therapy: UKPDS and other trials established metformin as first-line therapy for type 2 diabetes. Reduces diabetes-related complications by 30-40%. Cardiovascular outcomes: UKPDS showed 39% reduction in myocardial infarction risk. Recent CV outcome trials (CANVAS, EMPA-REG) suggest cardiovascular benefit, though metformin itself not primarily studied for CV outcomes. Weight effects: Metformin is weight-neutral or associated with modest weight loss (1-2 kg), unlike many other diabetes medications. Safety: Generally well-tolerated. Most common side effects are gastrointestinal (diarrhea, nausea, abdominal discomfort) affecting 20-30% of patients. Lactic acidosis is rare (<0.1 per 1000 patient-years) but serious. Contraindicated in severe renal impairment.",
                "metadata": {
                    "source": "Sample",
                    "category": "clinical_evidence",
                    "drugs": ["metformin", "glucophage"],
                    "conditions": ["type_2_diabetes"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_beta_blockers_evidence",
                "content": "Beta-Blocker Clinical Evidence: Beta-blockers have strong clinical evidence supporting their use in cardiovascular diseases. Hypertension: Meta-analyses show 15-20% reduction in cardiovascular events. First-line therapy for most patients, especially those with comorbid conditions. Heart failure: MERIT-HF, COPERNICUS, and other trials demonstrated 30-35% reduction in mortality in HFrEF. Standard of care for HFrEF. Post-MI: Multiple trials showed 20-30% reduction in mortality and reinfarction after myocardial infarction. Benefit greatest in high-risk patients. Angina: Effective for reducing angina frequency and improving exercise tolerance. Arrhythmias: Effective for rate control in atrial fibrillation and prevention of ventricular arrhythmias. Safety: Generally well-tolerated. Common side effects include bradycardia, fatigue, and cold extremities. Contraindicated in severe bradycardia, heart block, and decompensated heart failure.",
                "metadata": {
                    "source": "Sample",
                    "category": "clinical_evidence",
                    "drugs": ["beta_blockers", "metoprolol", "propranolol", "atenolol"],
                    "conditions": ["hypertension", "heart_failure", "myocardial_infarction", "angina", "atrial_fibrillation"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            # Practice Guidelines
            {
                "doc_id": "sample_anticoagulation_guidelines",
                "content": "Anticoagulation Practice Guidelines: Anticoagulation therapy requires careful patient selection and monitoring. Atrial fibrillation: CHA2DS2-VASc score used to assess stroke risk. Score ≥2 in men or ≥3 in women indicates anticoagulation benefit. HAS-BLED score used to assess bleeding risk. DOACs (apixaban, rivaroxaban, dabigatran, edoxaban) preferred over warfarin for most patients with non-valvular AF. Warfarin preferred for mechanical heart valves and moderate-severe mitral stenosis. Venous thromboembolism: Anticoagulation for minimum 3 months for provoked VTE, indefinite for unprovoked recurrent VTE. DOACs preferred over warfarin for most VTE patients. Perioperative management: Bridge therapy with heparin for high-risk patients on warfarin. DOACs generally stopped 24-48 hours before surgery based on bleeding risk. Monitoring: INR monitoring every 4 weeks for stable warfarin therapy. More frequent monitoring with dose changes or interacting medications.",
                "metadata": {
                    "source": "Sample",
                    "category": "practice_guidelines",
                    "drugs": ["warfarin", "apixaban", "rivaroxaban", "dabigatran", "edoxaban"],
                    "conditions": ["atrial_fibrillation", "venous_thromboembolism"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_hypertension_guidelines",
                "content": "Hypertension Practice Guidelines: Hypertension management follows evidence-based guidelines (ACC/AHA 2017). Blood pressure goals: <130/80 mmHg for most adults. <140/90 mmHg for adults ≥65 years or those with high bleeding risk. First-line medications: Thiazide diuretics, ACE inhibitors, ARBs, and calcium channel blockers. Choice based on comorbidities and patient characteristics. ACE inhibitors/ARBs preferred for patients with diabetes, CKD, or heart failure. Calcium channel blockers preferred for Black patients or those with angina. Thiazides preferred for patients with osteoporosis risk. Combination therapy: Most patients require 2 or more medications to achieve BP goals. Fixed-dose combinations improve adherence. Monitoring: Home BP monitoring recommended for diagnosis and management. Follow-up every 4-6 weeks until BP at goal, then every 3-6 months.",
                "metadata": {
                    "source": "Sample",
                    "category": "practice_guidelines",
                    "drugs": ["ace_inhibitors", "arbs", "calcium_channel_blockers", "thiazides"],
                    "conditions": ["hypertension"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_diabetes_guidelines",
                "content": "Diabetes Practice Guidelines: Type 2 diabetes management follows comprehensive guidelines (ADA Standards of Care). HbA1c goals: <7% for most non-pregnant adults. <6.5% for younger, healthier patients if achievable without hypoglycemia. <8% for patients with limited life expectancy, history of severe hypoglycemia, or advanced complications. First-line therapy: Metformin for all patients with type 2 diabetes unless contraindicated. Second-line agents: Choose based on comorbidities and patient factors. GLP-1 agonists or SGLT2 inhibitors preferred for patients with ASCVD or high ASCVD risk. SGLT2 inhibitors preferred for patients with CKD or heart failure. GLP-1 agonists preferred for patients needing weight loss. Insulin: Required when oral agents insufficient or contraindicated. Basal-bolus regimen for most patients requiring insulin. Monitoring: HbA1c every 3 months if not at goal, every 6 months if at goal. SMBG or CGM for patients on insulin or with hypoglycemia risk.",
                "metadata": {
                    "source": "Sample",
                    "category": "practice_guidelines",
                    "drugs": ["metformin", "glp1_agonists", "sglt2_inhibitors", "insulin"],
                    "conditions": ["type_2_diabetes"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_heart_failure_guidelines",
                "content": "Heart Failure Practice Guidelines: Heart failure management follows comprehensive guidelines (ACC/AHA/HFSA 2022). Classification: Stage A (at risk) - control risk factors. Stage B (structural heart disease) - ACE inhibitors/ARBs, beta-blockers for asymptomatic LV dysfunction. Stage C (symptomatic) - GDMT (guideline-directed medical therapy) essential. Stage D (refractory) - advanced therapies consideration. GDMT for HFrEF: Quadruple therapy recommended - (1) ACE inhibitor/ARB/ARNI, (2) Beta-blocker, (3) MRA, (4) SGLT2 inhibitor. Target doses shown to improve survival. Device therapy: ICD for primary prevention in appropriate patients. CRT for LBBB with QRS ≥150 ms and EF ≤35%. Monitoring: Regular assessment of volume status, renal function, electrolytes, and medication tolerance. Titrate to target doses when possible.",
                "metadata": {
                    "source": "Sample",
                    "category": "practice_guidelines",
                    "drugs": ["ace_inhibitors", "arbs", "arni", "beta_blockers", "mra", "sglt2_inhibitors"],
                    "conditions": ["heart_failure", "hfref"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            },
            {
                "doc_id": "sample_dyslipidemia_guidelines",
                "content": "Dyslipidemia Practice Guidelines: Lipid management follows evidence-based guidelines (ACC/AHA 2018, ESC/EAS 2019). Risk assessment: 10-year ASCVD risk calculated using pooled cohort equations. Risk categories: Very high (ASCVD, diabetes with risk factors, LDL ≥190 mg/dL), High (10-year risk ≥20% or diabetes), Moderate (10-year risk 7.5-19.9%), Low (10-year risk <7.5%). LDL goals: Very high - <55 mg/dL and ≥50% reduction. High - <70 mg/dL and ≥50% reduction. Moderate - <100 mg/dL. Low - <130 mg/dL. Statin intensity: High-intensity (atorvastatin 40-80 mg, rosuvastatin 20-40 mg) for very high and high risk. Moderate-intensity for moderate risk. Lifestyle: Heart-healthy diet, regular exercise, weight management, smoking cessation essential for all patients. Monitoring: Lipid panel 4-12 weeks after starting or changing therapy, then every 3-12 months.",
                "metadata": {
                    "source": "Sample",
                    "category": "practice_guidelines",
                    "drugs": ["statins", "atorvastatin", "rosuvastatin", "ezetimibe", "pcsk9_inhibitors"],
                    "conditions": ["dyslipidemia", "ascvd"],
                    "last_updated": datetime.utcnow().isoformat()
                }
            }
        ]

    def populate(
        self,
        rebuild: bool = False,
        pubmed_queries: Optional[List[str]] = None,
        fda_drugs: Optional[List[str]] = None,
        json_files: Optional[List[str]] = None
    ):
        """
        Populate the knowledge base with documents.

        Args:
            rebuild: Whether to rebuild the index from scratch
            pubmed_queries: List of PubMed search queries
            fda_drugs: List of drug names to fetch FDA labels for
            json_files: List of JSON files to import
        """
        logger.info("Populating knowledge base...")

        if rebuild:
            logger.info("Rebuilding index from scratch")
            self.kb.rebuild_index()

        total_added = 0

        # Fetch from PubMed
        if pubmed_queries:
            for query in pubmed_queries:
                total_added += self.fetch_from_pubmed(query)

        # Fetch from FDA
        if fda_drugs:
            total_added += self.fetch_from_fda(fda_drugs)

        # Import from JSON files
        if json_files:
            for json_file in json_files:
                total_added += self.import_from_json(json_file)

        # Save index
        self.kb.save_index()

        logger.info(f"✅ Knowledge base populated with {total_added} documents")
        logger.info(f"Total documents: {self.kb.get_document_count()}")

        # Show summary
        summary = self.kb.get_sources_summary()
        logger.info("Documents by source:")
        for source, count in summary.items():
            logger.info(f"  {source}: {count}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Populate P.R.I.S.M. knowledge base with clinical data'
    )
    parser.add_argument(
        '--kb-root',
        default='./knowledge_base',
        help='Knowledge base root path'
    )
    parser.add_argument(
        '--rebuild',
        action='store_true',
        help='Rebuild index from scratch'
    )
    parser.add_argument(
        '--pubmed',
        action='append',
        help='PubMed search query (can be used multiple times)'
    )
    parser.add_argument(
        '--fda-drug',
        action='append',
        help='Drug name to fetch FDA label for (can be used multiple times)'
    )
    parser.add_argument(
        '--json',
        action='append',
        help='JSON file to import (can be used multiple times)'
    )

    args = parser.parse_args()

    populator = KnowledgeBasePopulator(args.kb_root)
    populator.populate(
        rebuild=args.rebuild,
        pubmed_queries=args.pubmed,
        fda_drugs=args.fda_drug,
        json_files=args.json
    )


if __name__ == '__main__':
    main()

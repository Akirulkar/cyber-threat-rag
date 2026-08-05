from typing import Tuple, Dict, Any
from app.models.document import ProcessedDocument
from app.ingestion.models import RawDocument, SourceType


class DocumentExtractor:
    """Extracts narrative domain text and essential attributes from raw JSON formats."""

    @classmethod
    def extract(cls, raw_doc: RawDocument) -> ProcessedDocument:
        source = raw_doc.metadata.source

        if source == SourceType.CISA:
            extracted_text, extra_attrs = cls._extract_cisa(raw_doc.raw_content)
        elif source == SourceType.MITRE:
            extracted_text, extra_attrs = cls._extract_mitre(raw_doc.raw_content)
        elif source == SourceType.NVD:
            extracted_text, extra_attrs = cls._extract_nvd(raw_doc.raw_content)
        else:
            raise ValueError(f"Unsupported source type: {source}")

        return ProcessedDocument(
            document_id=raw_doc.metadata.document_id,
            source=raw_doc.metadata.source,
            document_type=raw_doc.metadata.document_type,
            title=raw_doc.metadata.title,
            url=str(raw_doc.metadata.url),
            published_date=raw_doc.metadata.published_date,
            updated_date=raw_doc.metadata.updated_date,
            severity=raw_doc.metadata.severity,
            vendor=raw_doc.metadata.vendor,
            product=raw_doc.metadata.product,
            extracted_text=extracted_text,
            extra_attributes=extra_attrs,
        )

    @staticmethod
    def _extract_cisa(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        text_parts = [
            f"Vulnerability Name: {payload.get('vulnerabilityName', '')}",
            f"Vendor/Project: {payload.get('vendorProject', '')}",
            f"Product: {payload.get('product', '')}",
            f"Description: {payload.get('shortDescription', '')}",
            f"Required Action: {payload.get('requiredAction', '')}",
            f"Ransomware Campaign Use: {payload.get('knownRansomwareCampaignUse', 'Unknown')}",
        ]
        text = "\n".join([p for p in text_parts if p.strip()])

        extra = {
            "dueDate": payload.get("dueDate"),
            "cwes": payload.get("cwes", []),
        }
        return text, extra

    @staticmethod
    def _extract_mitre(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        platforms = ", ".join(payload.get("x_mitre_platforms", []))
        kill_chains = ", ".join(
            [kc.get("phase_name", "") for kc in payload.get("kill_chain_phases", [])]
        )

        text_parts = [
            f"Technique Name: {payload.get('name', '')}",
            f"Description: {payload.get('description', '')}",
            f"Target Platforms: {platforms}",
            f"Kill Chain Phases: {kill_chains}",
        ]
        text = "\n".join([p for p in text_parts if p.strip()])

        extra = {
            "is_subtechnique": payload.get("x_mitre_is_subtechnique", False),
            "platforms": payload.get("x_mitre_platforms", []),
        }
        return text, extra

    @staticmethod
    def _extract_nvd(payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        cve_data = payload.get("cve", {})

        # English description
        descriptions = cve_data.get("descriptions", [])
        desc_text = next(
            (d.get("value") for d in descriptions if d.get("lang") == "en"), ""
        )

        # CVSS Metrics
        metrics = cve_data.get("metrics", {})
        cvss_v31 = metrics.get("cvssMetricV31", [{}])[0].get("cvssData", {})
        cvss_v2 = metrics.get("cvssMetricV2", [{}])[0].get("cvssData", {})

        vector_str = cvss_v31.get("vectorString") or cvss_v2.get("vectorString", "N/A")
        base_score = cvss_v31.get("baseScore") or cvss_v2.get("baseScore", "N/A")

        # Weaknesses (CWE)
        weaknesses = cve_data.get("weaknesses", [])
        cwes = []
        for w in weaknesses:
            for desc in w.get("description", []):
                if desc.get("lang") == "en":
                    cwes.append(desc.get("value"))

        text_parts = [
            f"CVE ID: {cve_data.get('id', '')}",
            f"Description: {desc_text}",
            f"CVSS Base Score: {base_score}",
            f"CVSS Vector: {vector_str}",
            f"Associated Weaknesses: {', '.join(cwes)}",
        ]
        text = "\n".join([p for p in text_parts if p.strip()])

        extra = {
            "baseScore": base_score,
            "vectorString": vector_str,
            "cwes": cwes,
        }
        return text, extra

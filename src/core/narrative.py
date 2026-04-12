"""
narrative.py
------------
Converts DuckDB query results into clear, plain-English narratives
using Google Gemini 1.5 Flash.

Key features:
    - Use-case-specific narrative templates matching the NatWest problem doc
      output examples exactly
    - Jargon-free language suitable for non-technical users and leadership
    - Structured output: headline + narrative + key facts
    - Source references included in every narrative
    - Anomaly flagging when values fall outside expected ranges
"""

import yaml
import os
from loguru import logger
from dotenv import load_dotenv
import google.generativeai as genai

from src.core.intent_router import UseCase

load_dotenv()

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
_MODEL = genai.GenerativeModel("gemini-1.5-flash")


# ── Output format per use case — mirrors NatWest problem doc examples ─────────
NARRATIVE_TEMPLATES = {
    UseCase.CHANGE_ANALYSIS: """
You are a NatWest banking analyst explaining data insights to a non-technical audience.

Data results:
{data}

The user asked: "{query}"

Write a clear, plain-English explanation following this EXACT format:

HEADLINE: [One sentence summary of what changed and by how much]

EXPLANATION: [2-3 sentences explaining the main drivers. Use simple language.
Reference specific numbers. Example: "Revenue decreased by 11% in Feb.
The biggest contributor was a 22% drop in the South region due to reduced ad spend."]

KEY FACTS:
• [Specific data point 1 with number]
• [Specific data point 2 with number]
• [Specific data point 3 with number]

DATA SOURCE: [Which dataset(s) were used]

Rules:
- No jargon. Write as if explaining to a bank branch manager, not a data scientist.
- Always include specific numbers from the data.
- Keep HEADLINE under 20 words.
- Keep EXPLANATION under 60 words.
- List exactly 3 KEY FACTS.
""",

    UseCase.COMPARE: """
You are a NatWest banking analyst explaining a comparison to a non-technical audience.

Data results:
{data}

The user asked: "{query}"

Write a clear comparison following this EXACT format:

HEADLINE: [One sentence stating which performed better and by how much]

COMPARISON: [2-3 sentences comparing the two. Example: "Product A grew by 8% WoW,
outperforming Product B (+2%). Primary reason: higher return customer rate."]

KEY DIFFERENCES:
• [Metric 1: value A vs value B — difference]
• [Metric 2: value A vs value B — difference]
• [Metric 3: value A vs value B — difference]

DATA SOURCE: [Which dataset(s) were used]

Rules:
- No jargon. Be direct about which is better.
- Always state the direction (up/down, higher/lower).
- Keep HEADLINE under 20 words.
""",

    UseCase.BREAKDOWN: """
You are a NatWest banking analyst explaining a breakdown to a non-technical audience.

Data results:
{data}

The user asked: "{query}"

Write a clear breakdown following this EXACT format:

HEADLINE: [One sentence about the biggest contributor]

BREAKDOWN: [2-3 sentences explaining the composition. Example: "North region accounts
for 40% of total sales, with Retail contributing most of that share."]

TOP CONTRIBUTORS:
• [#1 item: value and % of total]
• [#2 item: value and % of total]
• [#3 item: value and % of total]

NOTABLE PATTERN: [One sentence about any outlier, concentration, or surprise in the data]

DATA SOURCE: [Which dataset(s) were used]

Rules:
- Always mention percentages of total.
- Highlight if one category is unusually dominant.
- Keep HEADLINE under 20 words.
""",

    UseCase.SUMMARIZE: """
You are a NatWest banking analyst writing a weekly digest for leadership.

Data results:
{data}

The user asked: "{query}"

Write a concise summary following this EXACT format:

HEADLINE: [One sentence capturing the most important thing that happened]

THIS PERIOD:
• Signups: [value and change vs previous period]
• Churn: [value — stable/improving/worsening]
• NPS: [value and trend]
• Revenue: [value and change]
• Handle time: [value and change]

KEY TAKEAWAY: [One sentence about the single most important thing leadership should know]

DATA SOURCE: [Which dataset(s) were used]

Rules:
- Write as if this is a Monday morning executive briefing.
- Focus on what truly matters — avoid noise.
- Use plain numbers with units (£, %, seconds).
- Example bullet: "Signups grew by 5%, churn remained stable, handle time improved by 12 seconds."
""",

    UseCase.UNKNOWN: """
You are a NatWest banking analyst answering a data question clearly.

Data results:
{data}

The user asked: "{query}"

Answer clearly and concisely:

ANSWER: [Direct answer to the question in 2-3 sentences with specific numbers]

KEY FACTS:
• [Fact 1 with number]
• [Fact 2 with number]

DATA SOURCE: [Which dataset(s) were used]

Rules:
- No jargon. Include specific numbers.
- Be direct — answer the question first, then provide context.
""",
}


class Narrative:
    """
    Converts structured query results into plain-English banking narratives
    using Gemini 1.5 Flash with use-case-specific templates.
    """

    def __init__(self, metrics_yaml_path: str = "src/semantic/metrics.yaml"):
        """
        Initialise the narrative generator.

        Args:
            metrics_yaml_path: Path to metrics.yaml for unit/format lookups.
        """
        self.metrics_yaml_path = metrics_yaml_path
        logger.info("Narrative generator initialised")

    def _format_data_for_prompt(self, data: list[dict], columns: list[str]) -> str:
        """
        Format query results into a clean table string for the LLM prompt.

        Args:
            data: List of row dicts from query_engine
            columns: Column names

        Returns:
            str: Formatted table string
        """
        if not data:
            return "No data returned."

        # Header
        lines = [" | ".join(str(col) for col in columns)]
        lines.append("-" * len(lines[0]))

        # Rows (max 20 for prompt efficiency)
        for row in data[:20]:
            lines.append(" | ".join(
                f"£{v:,.2f}" if isinstance(v, float) and "revenue" in str(k).lower()
                else f"{v:,}" if isinstance(v, (int, float)) and v > 1000
                else str(v)
                for k, v in row.items()
            ))

        return "\n".join(lines)

    def generate(
        self,
        query: str,
        use_case: UseCase,
        query_result: dict,
        metric_definitions: list[str] = None,
    ) -> dict:
        """
        Generate a plain-English narrative from query results.

        Args:
            query: Original user question
            use_case: Classified use case
            query_result: Result dict from QueryEngine.execute()
            metric_definitions: List of metric definitions applied (for trust trail)

        Returns:
            dict: {
                "headline": str,      — one-line summary
                "narrative": str,     — full formatted narrative
                "key_facts": list,    — extracted bullet points
                "data_source": str,   — which datasets were used
                "anomalies": list,    — any anomalies detected
                "success": bool
            }
        """
        if not query_result.get("success") or not query_result.get("data"):
            return {
                "headline":  "No data found for this query.",
                "narrative": "The query returned no results. Try rephrasing or broadening your question.",
                "key_facts": [],
                "data_source": "N/A",
                "anomalies": [],
                "success": False,
            }

        template   = NARRATIVE_TEMPLATES.get(use_case, NARRATIVE_TEMPLATES[UseCase.UNKNOWN])
        data_str   = self._format_data_for_prompt(
            query_result["data"],
            query_result["columns"]
        )

        prompt = template.format(data=data_str, query=query)

        try:
            response  = _MODEL.generate_content(prompt)
            raw_text  = response.text.strip()

            # Parse structured sections
            headline  = self._extract_section(raw_text, "HEADLINE")
            data_src  = self._extract_section(raw_text, "DATA SOURCE")
            key_facts = self._extract_bullets(raw_text)
            anomalies = self._detect_anomalies(query_result["data"])

            logger.info(f"Narrative generated for use case: {use_case.value}")

            return {
                "headline":    headline or "Analysis complete.",
                "narrative":   raw_text,
                "key_facts":   key_facts,
                "data_source": data_src or ", ".join(query_result.get("datasets_used", [])),
                "anomalies":   anomalies,
                "success":     True,
            }

        except Exception as e:
            logger.error(f"Narrative generation failed: {e}")
            return {
                "headline":  "Analysis complete.",
                "narrative": f"Data retrieved successfully but narrative generation encountered an issue: {str(e)}",
                "key_facts": [],
                "data_source": ", ".join(query_result.get("datasets_used", [])),
                "anomalies": [],
                "success":   False,
            }

    def _extract_section(self, text: str, section_name: str) -> str:
        """
        Extract a specific section from the narrative text.

        Args:
            text: Full narrative text
            section_name: Section header to extract (e.g. "HEADLINE")

        Returns:
            str: Content of the section, or empty string if not found
        """
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{section_name}:"):
                content = line.split(":", 1)[-1].strip()
                if content:
                    return content
                # Content might be on next line
                if i + 1 < len(lines):
                    return lines[i + 1].strip()
        return ""

    def _extract_bullets(self, text: str) -> list[str]:
        """
        Extract bullet points from the narrative text.

        Args:
            text: Full narrative text

        Returns:
            list[str]: List of bullet point strings (without leading •)
        """
        bullets = []
        for line in text.split("\n"):
            stripped = line.strip()
            if stripped.startswith("•") or stripped.startswith("-"):
                bullet_text = stripped.lstrip("•-").strip()
                if bullet_text:
                    bullets.append(bullet_text)
        return bullets

    def _detect_anomalies(self, data: list[dict]) -> list[str]:
        """
        Detect statistical anomalies in query results.
        Flags values that are unusually high or low for banking context.

        Args:
            data: Query result rows

        Returns:
            list[str]: Human-readable anomaly descriptions
        """
        anomalies = []

        for row in data:
            for col, val in row.items():
                if not isinstance(val, (int, float)):
                    continue

                col_lower = col.lower()

                # Churn rate anomaly — above 5% is unusual
                if "churn" in col_lower and "pct" in col_lower and val > 5.0:
                    anomalies.append(
                        f"⚠️ High churn rate detected: {val:.1f}% (typical range: 1–3%)"
                    )

                # NPS below 20 is a warning sign
                if "nps" in col_lower and isinstance(val, (int, float)) and val < 20:
                    anomalies.append(
                        f"⚠️ Low NPS detected: {val} (NatWest target: 40+)"
                    )

                # Budget variance above ±15% is flagged
                if "variance" in col_lower and abs(val) > 15:
                    direction = "overspend" if val > 0 else "underspend"
                    anomalies.append(
                        f"⚠️ Large budget {direction}: {val:+.1f}% variance"
                    )

                # Revenue drop > 20% is significant
                if "change" in col_lower and "pct" in col_lower and val < -20:
                    anomalies.append(
                        f"⚠️ Significant drop detected: {val:.1f}% change"
                    )

        return list(set(anomalies))[:3]   # cap at 3 anomaly flags


# ── Quick test ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    narrator = Narrative(metrics_yaml_path="src/semantic/metrics.yaml")

    mock_result = {
        "success":      True,
        "data": [
            {"region": "South", "month": "2024-01", "total_revenue": 2_450_000},
            {"region": "South", "month": "2024-02", "total_revenue": 1_930_000},
        ],
        "columns":      ["region", "month", "total_revenue"],
        "row_count":    2,
        "datasets_used": ["regional_revenue"],
    }

    result = narrator.generate(
        query="Why did revenue drop in the South region in February 2024?",
        use_case=UseCase.CHANGE_ANALYSIS,
        query_result=mock_result,
    )

    print("\n🟣 PurpleInsight — Narrative Test")
    print("=" * 60)
    print(f"Headline : {result['headline']}")
    print(f"\nNarrative:\n{result['narrative']}")
    print(f"\nKey Facts: {result['key_facts']}")
    print(f"Anomalies: {result['anomalies']}")
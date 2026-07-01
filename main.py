from dotenv import load_dotenv
load_dotenv()

"""
StreamMind — PM Agent #4: Competitive Intelligence Agent
Runs weekly via GitHub Actions cron (Monday 8 AM PT)
Researches 5 competitors using Claude + web_search tool
Sends digest via Resend, archives to Notion
"""

import os
import json
from datetime import datetime, timedelta
import anthropic
import resend
from notion_client import Client as NotionClient


def load_competitors():
    with open("competitors.json", "r") as f:
        return json.loads(f.read())["competitors"]


def research_competitor(client, competitor):
    """Use Claude with web_search to research one competitor's recent activity."""
    
    focus_areas = ", ".join(competitor["focus_areas"])
    
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=2048,
        tools=[{"type": "web_search_20250305", "name": "web_search"}],
        messages=[{
            "role": "user",
            "content": f"""Research what {competitor['name']} has done in the streaming/entertainment space in the past 7 days (since {(datetime.now() - timedelta(days=7)).strftime('%B %d, %Y')}).

Focus areas for this competitor: {focus_areas}

Search for:
1. Product changes, feature launches, or UI updates
2. Pricing or packaging changes
3. Content announcements (new shows, renewals, cancellations)
4. Business developments (partnerships, earnings, strategy shifts)
5. Hiring patterns that signal strategic direction

For each development you find, provide:
- Type: feature | pricing | content | business | hiring | other
- Summary: 2-3 sentences on what happened
- Source URL: the specific URL where you found this
- Date observed: when it happened
- Implication for a competing streaming platform: 1 sentence on what this means for us

If nothing notable happened this week, say so clearly — do not fabricate developments.

Return your findings as a JSON object. Start with {{ and end with }}. No markdown fences.

Schema:
{{
  "competitor": "{competitor['name']}",
  "developments": [
    {{
      "type": "feature | pricing | content | business | hiring | other",
      "summary": "what happened",
      "source_url": "URL",
      "date_observed": "YYYY-MM-DD",
      "implication_for_us": "what this means"
    }}
  ],
  "quiet_week": false
}}

If no developments found, set quiet_week to true and developments to an empty array."""
        }]
    )
    
    # Extract text from response (may have multiple content blocks due to web_search)
    text_parts = []
    for block in response.content:
        if block.type == "text":
            text_parts.append(block.text)
    
    full_text = "\n".join(text_parts)
    
    # Extract JSON from response
    start = full_text.find("{")
    end = full_text.rfind("}") + 1
    if start >= 0 and end > start:
        try:
            return json.loads(full_text[start:end])
        except json.JSONDecodeError:
            print(f"  Warning: Could not parse JSON for {competitor['name']}, using raw text")
            return {
                "competitor": competitor["name"],
                "developments": [],
                "quiet_week": True,
                "raw_response": full_text
            }
    else:
        return {
            "competitor": competitor["name"],
            "developments": [],
            "quiet_week": True,
            "raw_response": full_text
        }


def synthesize_findings(client, all_findings):
    """Ask Claude to synthesize cross-competitor patterns and recommendations."""
    
    findings_text = json.dumps(all_findings, indent=2)
    
    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=3000,
        messages=[
            {
                "role": "user",
                "content": f"""You are a senior competitive intelligence analyst for a streaming platform. Below are this week's findings across 5 competitors.

Synthesize them into a weekly digest with these sections:

1. TOP 5 DEVELOPMENTS THIS WEEK — the 5 most important things that happened across all competitors, ranked by strategic impact

2. PER-COMPETITOR SUMMARY — 2-3 sentences per competitor on their activity this week. If a competitor had a quiet week, say so.

3. CROSS-COMPETITOR PATTERNS — are multiple competitors doing similar things? Moving in the same direction? Only include patterns supported by 2+ competitors.

4. RECOMMENDED ACTIONS — specific actions our team should consider. Be specific ("investigate whether to match Netflix's new ad tier pricing at $7.99") not generic ("keep monitoring the space"). Include "no action needed" when that's the honest call.

Write in Markdown. Keep the entire digest under 1000 words. Write for a product strategy lead who reads this in 5 minutes every Monday.

Here are the findings:

{findings_text}"""
            }
        ]
    )
    
    return response.content[0].text


def send_email(digest, findings_count):
    """Send the digest via Resend."""
    
    resend.api_key = os.environ["RESEND_API_KEY"]
    
    week_of = datetime.now().strftime("%B %d, %Y")
    
    # Convert markdown to basic HTML
    html_body = digest.replace("\n\n", "</p><p>")
    html_body = html_body.replace("\n", "<br>")
    html_body = f"""
    <html>
    <body style="font-family: Georgia, serif; max-width: 680px; margin: 0 auto; padding: 20px; color: #1F1E1D; line-height: 1.6;">
        <h1 style="font-size: 24px; border-bottom: 2px solid #C96442; padding-bottom: 12px;">
            StreamMind — Competitive Intel Digest
        </h1>
        <p style="color: #7A736A; font-size: 14px;">Week of {week_of} · {findings_count} developments tracked across 5 competitors</p>
        <div style="white-space: pre-wrap;">{html_body}</div>
        <hr style="border: 1px solid #E5DDD0; margin-top: 32px;">
        <p style="color: #A89F92; font-size: 12px; font-style: italic;">Generated by PM Agent #4 — StreamMind Competitive Intelligence</p>
    </body>
    </html>
    """
    
    params = {
        "from": os.environ["EMAIL_FROM"],
        "to": [os.environ["EMAIL_TO"]],
        "subject": f"StreamMind — Competitive Intel Digest (Week of {week_of})",
        "html": html_body
    }
    
    result = resend.Emails.send(params)
    print(f"  Email sent: {result}")
    return result


def archive_to_notion(digest, all_findings):
    """Create a new page in the Competitive Watch Notion database."""
    
    notion = NotionClient(auth=os.environ["NOTION_TOKEN"])
    database_id = os.environ["NOTION_DATABASE_ID"]
    week_of = datetime.now().strftime("%B %d, %Y")
    
    # Count total developments
    total_devs = sum(len(f.get("developments", [])) for f in all_findings)
    
    # Build competitor summary for Notion
    competitor_names = [f["competitor"] for f in all_findings]
    
    # Notion has a 2000-char limit per block, so split digest into chunks
    chunks = []
    current_chunk = ""
    for line in digest.split("\n"):
        if len(current_chunk) + len(line) + 1 > 1900:
            chunks.append(current_chunk)
            current_chunk = line
        else:
            current_chunk += "\n" + line if current_chunk else line
    if current_chunk:
        chunks.append(current_chunk)
    
    # Build children blocks
    children = []
    for chunk in chunks:
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": chunk}}]
            }
        })
    
    page = notion.pages.create(
        parent={"database_id": database_id},
        properties={
            "Name": {"title": [{"text": {"content": f"Competitive Intel — Week of {week_of}"}}]},
            "Date": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
            "Developments": {"number": total_devs},
            "Competitors": {"multi_select": [{"name": name} for name in competitor_names]}
        },
        children=children
    )
    
    print(f"  Notion page created: {page['url']}")
    return page


def main():
    print("=" * 60)
    print(f"PM Agent #4 — Competitive Intelligence")
    print(f"Run date: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}")
    print("=" * 60)
    
    # Initialize Claude client
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    
    # Load competitors
    competitors = load_competitors()
    print(f"\nResearching {len(competitors)} competitors...")
    
    # Research each competitor
    all_findings = []
    for comp in competitors:
        print(f"\n  Researching {comp['name']}...")
        findings = research_competitor(client, comp)
        dev_count = len(findings.get("developments", []))
        quiet = findings.get("quiet_week", False)
        print(f"    Found {dev_count} developments{' (quiet week)' if quiet else ''}")
        all_findings.append(findings)
    
    # Count total developments
    total_devs = sum(len(f.get("developments", [])) for f in all_findings)
    print(f"\n  Total developments across all competitors: {total_devs}")
    
    # Synthesize findings
    print("\n  Synthesizing cross-competitor patterns...")
    digest = synthesize_findings(client, all_findings)
    print("  Digest generated")
    
    # Send email
    print("\n  Sending email digest...")
    try:
        send_email(digest, total_devs)
        print("  Email sent successfully")
    except Exception as e:
        print(f"  Email failed: {e}")
    
    # Archive to Notion
    print("\n  Archiving to Notion...")
    try:
        archive_to_notion(digest, all_findings)
        print("  Notion archive created")
    except Exception as e:
        print(f"  Notion archive failed: {e}")
    
    print("\n" + "=" * 60)
    print("PM Agent #4 complete")
    print("=" * 60)


if __name__ == "__main__":
    main()
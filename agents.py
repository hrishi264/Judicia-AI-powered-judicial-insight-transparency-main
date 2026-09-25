"""
MULTI-AGENT ORCHESTRATOR - WITH REAL DUCKDUCKGO WEB SEARCH
============================================================

Agents:
1. Law Identifier - Extracts IPC sections and laws
2. Web Research - Uses REAL DuckDuckGo search for relevant case law
3. Precedent Analyzer - Analyzes citations and precedents
4. Logic Auditor - Checks reasoning and consistency
5. Summary Writer - Creates citizen-friendly summary
6. Justice Scorer - Rates judgment fairness on 4 dimensions
7. Timeline Extractor - Extracts chronological events from the case
"""

import json
import re
import sys
from typing import TypedDict, Annotated, List
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

# Fix Windows console encoding
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

# --- AGENT STATE ---

class AgentState(TypedDict):
    """Shared state between all agents"""
    judgment_text: str
    rag_context: str
    web_research: str
    web_sources: List[dict]
    laws_found: str
    precedent_analysis: str
    logic_audit: str
    final_summary: str
    justice_score: dict
    timeline: dict
    messages: Annotated[List, list.__add__]
    current_agent: str


# --- INDIVIDUAL AGENTS ---

class LawIdentifierAgent:
    """Agent 1: Specializes in finding applicable laws and IPC sections"""
    
    def __init__(self, llm):
        self.llm = llm
        self.name = "Law Identifier"
    
    def run(self, state: AgentState) -> AgentState:
        print(f"\n🔍 {self.name} Agent is working...")
        
        prompt = f"""You are a Legal Law Identification Specialist.

YOUR JOB: Identify ALL applicable laws, IPC sections, and legal provisions from this judgment.

JUDGMENT TEXT:
{state['judgment_text'][:3000]}

RAG CONTEXT (similar cases):
{state['rag_context'][:1000]}

INSTRUCTIONS:
- Extract all IPC sections, Acts, and legal provisions mentioned
- Format each as: "Section XXX (Act Name) - Description"
- Include articles of Constitution if mentioned
- Be comprehensive and precise
- Organize by category (Criminal, Civil, Constitutional, etc.)

EXTRACT LAWS:"""

        response = self.llm.invoke([HumanMessage(content=prompt)])
        laws = response.content.strip()
        
        state['laws_found'] = laws
        state['messages'].append(AIMessage(content=f"[{self.name}] Found laws: {laws[:80]}..."))
        state['current_agent'] = self.name
        
        print(f"   ✅ Found laws: {laws[:100]}...")
        return state


class WebResearchAgent:
    """Agent 2: Uses REAL DuckDuckGo search for relevant legal links"""
    
    def __init__(self, llm, web_search_function=None):
        self.llm = llm
        self.web_search_function = web_search_function
        self.name = "Web Research"
    
    def _extract_core_facts(self, text: str, laws: str) -> str:
        """Extract core facts for better search queries"""
        prompt = f"""From this judgment, extract the MAIN LEGAL ISSUE in 5-8 words max.

Judgment excerpt: {text[:1500]}

Laws: {laws[:200]}

Examples:
- "death by negligence motor vehicle accident"
- "murder conviction appeal bail"
- "cheating fraud investment scheme"

OUTPUT (ONLY the core issue, no explanations):"""
        
        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            core = response.content.strip()[:80]
            # Clean up
            core = core.replace('"', '').replace("'", '').strip()
            return core
        except Exception:
            return "IPC case law"
    
    def _extract_primary_section(self, laws: str, text: str) -> str:
        """Extract the PRIMARY IPC section (not all sections at once)"""
        
        # Priority list - check most serious crimes first
        priority_sections = [
            ("302", "Murder"),
            ("304A", "Death by Negligence"),
            ("376", "Sexual Assault"),
            ("307", "Attempt to Murder"),
            ("498A", "Cruelty to Wife"),
            ("420", "Cheating"),
            ("379", "Theft"),
            ("506", "Criminal Intimidation"),
        ]
        
        # Check priority sections first
        for section, description in priority_sections:
            if f"Section {section}" in laws or f"{section}" in text[:2000]:
                return f"Section {section} IPC"
        
        # Fallback: regex extraction
        match = re.search(r'Section (\d+[A-Z]*)', laws or text)
        if match:
        
        
            return f"Section {match.group(1)} IPC"
        
        return "IPC"
    
    def run(self, state: AgentState) -> AgentState:
        print(f"\n🌐 {self.name} Agent is working...")
        
        if not self.web_search_function:
            print(f"   ⚠️ Web search disabled (no search function)")
            state['web_research'] = "Web search not configured"
            state['web_sources'] = []
            state['current_agent'] = self.name
            return state
        
        try:
            # Step 1: Extract core facts and primary section
            core_facts = self._extract_core_facts(state['judgment_text'], state['laws_found'])
            primary_section = self._extract_primary_section(state['laws_found'], state['judgment_text'])
            
            print(f"   🎯 Core facts: {core_facts}")
            print(f"   🎯 Primary section: {primary_section}")
            
            # Step 2: Build FOCUSED search query
            # CRITICAL: Keep it short and specific!
            search_query = f"{primary_section} {core_facts} recent judgments India"
            
            print(f"   🔎 Searching: {search_query}")
            
            # Step 3: Execute REAL web search via DuckDuckGo
            search_results = self.web_search_function(search_query)
            
            # Extract sources and answer from search results
            web_sources = search_results.get('sources', [])
            web_answer = search_results.get('answer', '')
            
            print(f"   ✅ Retrieved {len(web_sources)} web sources")
            
            # Store in state
            state['web_sources'] = web_sources
            state['web_research'] = web_answer
            
            state['messages'].append(AIMessage(
                content=f"[{self.name}] Found {len(web_sources)} relevant sources via DuckDuckGo"
            ))
            
        except Exception as e:
            print(f"   ❌ Web research error: {e}")
            import traceback
            traceback.print_exc()
            state['web_research'] = f"Web research error: {str(e)}"
            state['web_sources'] = []
        
        state['current_agent'] = self.name
        return state


class PrecedentAnalyzerAgent:
    """Agent 3: Analyzes precedents using local and web sources"""
    
    def __init__(self, llm):
        self.llm = llm
        self.name = "Precedent Analyzer"
    
    def run(self, state: AgentState) -> AgentState:
        print(f"\n📚 {self.name} Agent is working...")
        
        # Include web research findings
        web_context = ""
        if state['web_research']:
            web_context = f"\nWEB RESEARCH FINDINGS:\n{state['web_research'][:800]}\n"
        
        # Include web sources
        sources_text = ""
        if state['web_sources']:
            sources_text = "\nWEB SOURCES FOUND:\n" + "\n".join([
                f"- {s.get('title', 'Source')}: {s.get('url', 'N/A')}"
                for s in state['web_sources'][:3]
            ])
        
        prompt = f"""You are a Legal Precedent Analysis Specialist.

LAWS IDENTIFIED:
{state['laws_found'][:500]}

JUDGMENT TEXT:
{state['judgment_text'][:3000]}

RAG CONTEXT (similar cases):
{state['rag_context'][:1000]}

{web_context}

{sources_text}

ANALYZE:
1. What precedents are relevant to these laws?
2. How should the judgment be compared with precedents?
3. What guidelines are established for these sections?
4. Are there any conflicting decisions?

PRECEDENT ANALYSIS (3-4 paragraphs):"""

        response = self.llm.invoke([HumanMessage(content=prompt)])
        analysis = response.content.strip()
        
        state['precedent_analysis'] = analysis
        state['messages'].append(AIMessage(content=f"[{self.name}] Precedent analysis complete"))
        state['current_agent'] = self.name
        
        print(f"   ✅ Precedent analysis complete")
        return state


class LogicAuditorAgent:
    """Agent 4: Audits the logical consistency of the judgment"""
    
    def __init__(self, llm):
        self.llm = llm
        self.name = "Logic Auditor"
    
    def run(self, state: AgentState) -> AgentState:
        print(f"\n🧠 {self.name} Agent is working...")
        
        prompt = f"""You are a Legal Logic Consistency Auditor.

LAWS APPLIED:
{state['laws_found'][:500]}

JUDGMENT TEXT:
{state['judgment_text'][:3000]}

PRECEDENT COMPARISON:
{state['precedent_analysis'][:1000]}

AUDIT CHECKLIST:
✓ Are facts and findings consistent?
✓ Does the conclusion follow from reasoning?
✓ Are there logical gaps or contradictions?
✓ Is the burden of proof properly addressed?
✓ Are all relevant points addressed?

LOGIC AUDIT (2-3 paragraphs):"""

        response = self.llm.invoke([HumanMessage(content=prompt)])
        audit = response.content.strip()
        
        state['logic_audit'] = audit
        state['messages'].append(AIMessage(content=f"[{self.name}] Logic audit complete"))
        state['current_agent'] = self.name
        
        print(f"   ✅ Logic audit complete")
        return state


class SummaryWriterAgent:
    """Agent 5: Creates citizen-friendly summary using ALL agent findings"""
    
    def __init__(self, llm):
        self.llm = llm
        self.name = "Summary Writer"
    
    def run(self, state: AgentState) -> AgentState:
        print(f"\n✍️ {self.name} Agent is working...")
        
        prompt = f"""Create a simple, citizen-friendly summary of this legal judgment.

JUDGMENT:
{state['judgment_text'][:2000]}

LAWS INVOLVED:
{state['laws_found'][:300]}

ANALYSIS:
{state['precedent_analysis'][:500]}

STRUCTURE YOUR SUMMARY:
1. What happened? (The case briefly)
2. What did the court decide?
3. Why did the court decide this way?
4. What does this mean?

REQUIREMENTS:
- Use simple, everyday language
- Avoid legal jargon (explain if necessary)
- 4-6 sentences maximum
- Make it understandable for someone with no legal background

SUMMARY:"""

        response = self.llm.invoke([HumanMessage(content=prompt)])
        summary = response.content.strip()
        
        state['final_summary'] = summary
        state['messages'].append(AIMessage(content=f"[{self.name}] Summary complete"))
        state['current_agent'] = self.name
        
        print(f"   ✅ Summary written")
        return state


# --- JUSTICE SCORING AGENT ---

class ScoringAgent:
    """Agent 6: Rates judgment fairness on multiple dimensions"""
    
    def __init__(self, llm):
        self.llm = llm
        self.name = "Justice Scorer"
    
    def _default_score(self):
        return {
            "overall_score": 70,
            "label": "FAIR",
            "consistency_with_law": 70,
            "precedent_alignment": 70,
            "reasoning_quality": 70,
            "evidence_consideration": 70,
            "flags": ["Unable to generate detailed scoring"]
        }
    
    def run(self, state: AgentState) -> AgentState:
        print(f"\n⚖️ {self.name} Agent is working...")
        
        prompt = f"""You are a Judicial Fairness Scoring Specialist.

Rate this judgment on these 4 criteria (each score 0-100):
1. consistency_with_law: How well does the judgment follow applicable laws?
2. precedent_alignment: Does it align with established precedents?
3. reasoning_quality: Is the legal reasoning sound and logical?
4. evidence_consideration: Were all pieces of evidence properly considered?

JUDGMENT:
{state['judgment_text'][:3000]}

LAWS APPLIED:
{state['laws_found'][:500]}

LOGIC AUDIT:
{state['logic_audit'][:500]}

Also determine:
- overall_score: weighted average of the 4 scores
- label: one of EXCELLENT (90+), GOOD (75-89), FAIR (60-74), CONCERNING (40-59), POOR (0-39)
- flags: list of 1-3 brief concerns or notable observations

RESPOND WITH ONLY THIS JSON (no other text, no markdown):
{{"overall_score": 78, "label": "GOOD", "consistency_with_law": 82, "precedent_alignment": 71, "reasoning_quality": 80, "evidence_consideration": 78, "flags": ["Sentencing is harsher than precedent average"]}}"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            raw = response.content.strip()
            
            json_match = re.search(r'\{[\s\S]*\}', raw)
            if json_match:
                score_data = json.loads(json_match.group())
                # Validate required keys exist
                required = ['overall_score', 'label', 'consistency_with_law',
                           'precedent_alignment', 'reasoning_quality', 'evidence_consideration']
                if all(k in score_data for k in required):
                    state['justice_score'] = score_data
                else:
                    state['justice_score'] = self._default_score()
            else:
                state['justice_score'] = self._default_score()
        except Exception as e:
            print(f"   ⚠️ Scoring error: {e}")
            state['justice_score'] = self._default_score()
        
        state['messages'].append(AIMessage(content=f"[{self.name}] Score: {state['justice_score'].get('overall_score', 'N/A')}/100"))
        state['current_agent'] = self.name
        
        print(f"   ✅ Justice Score: {state['justice_score'].get('overall_score', 'N/A')}/100 ({state['justice_score'].get('label', 'N/A')})")
        return state


# --- TIMELINE EXTRACTOR AGENT ---

class TimelineAgent:
    """Agent 7: Extracts chronological events from the judgment"""
    
    def __init__(self, llm):
        self.llm = llm
        self.name = "Timeline Extractor"
    
    def _default_timeline(self):
        return {
            "events": [{"date": "N/A", "event": "Timeline extraction unavailable", "type": "info"}],
            "total_duration": "Unknown",
            "verdict": "See summary",
            "sentence": "See summary"
        }
    
    def run(self, state: AgentState) -> AgentState:
        print(f"\n📅 {self.name} Agent is working...")
        
        prompt = f"""You are a Legal Case Timeline Specialist.

Extract the key chronological events from this judgment.

JUDGMENT:
{state['judgment_text'][:4000]}

Extract 5-8 key events with dates (or approximate periods). Include:
- When the incident/crime occurred
- When FIR/complaint was filed
- Key investigation milestones
- Trial events
- Final verdict and sentence

For each event, assign a type: "incident", "filing", "investigation", "arrest", "trial", "verdict", "appeal", or "other"

RESPOND WITH ONLY THIS JSON (no other text, no markdown):
{{"events": [{{"date": "Jan 2019", "event": "FIR filed at XYZ police station", "type": "filing"}}, {{"date": "Mar 2019", "event": "Accused arrested", "type": "arrest"}}], "total_duration": "4 years, 7 months", "verdict": "GUILTY", "sentence": "Life imprisonment"}}"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            raw = response.content.strip()
            
            json_match = re.search(r'\{[\s\S]*\}', raw)
            if json_match:
                timeline_data = json.loads(json_match.group())
                if 'events' in timeline_data and len(timeline_data['events']) > 0:
                    state['timeline'] = timeline_data
                else:
                    state['timeline'] = self._default_timeline()
            else:
                state['timeline'] = self._default_timeline()
        except Exception as e:
            print(f"   ⚠️ Timeline error: {e}")
            state['timeline'] = self._default_timeline()
        
        event_count = len(state['timeline'].get('events', []))
        state['messages'].append(AIMessage(content=f"[{self.name}] Extracted {event_count} events"))
        state['current_agent'] = self.name
        
        print(f"   ✅ Extracted {event_count} timeline events")
        return state


# --- MULTI-AGENT ORCHESTRATOR ---

class MultiAgentOrchestrator:
    """Manages the 7-agent workflow with web search, scoring, and timeline"""
    
    def __init__(self, llm, web_search_function=None):
        self.llm = llm
        self.web_search_function = web_search_function
        
        # Initialize all 7 agents
        self.law_agent = LawIdentifierAgent(llm)
        self.web_agent = WebResearchAgent(llm, web_search_function)
        self.precedent_agent = PrecedentAnalyzerAgent(llm)
        self.logic_agent = LogicAuditorAgent(llm)
        self.summary_agent = SummaryWriterAgent(llm)
        self.scoring_agent = ScoringAgent(llm)
        self.timeline_agent = TimelineAgent(llm)
    
    def run(self, judgment_text: str, rag_context: str = "") -> dict:
        """Execute the 7-agent workflow"""
        
        print("\n" + "="*70)
        print("🤖 MULTI-AGENT SYSTEM ACTIVATED (7 AGENTS)")
        print("="*70)
        
        # Initialize state
        state = AgentState(
            judgment_text=judgment_text,
            rag_context=rag_context or "",
            web_research="",
            web_sources=[],
            laws_found="",
            precedent_analysis="",
            logic_audit="",
            final_summary="",
            justice_score={},
            timeline={},
            messages=[],
            current_agent="initializing"
        )
        
        # Execute agents in sequence
        state = self.law_agent.run(state)         # 1. Extract laws
        state = self.web_agent.run(state)          # 2. Web research
        state = self.precedent_agent.run(state)    # 3. Precedent analysis
        state = self.logic_agent.run(state)        # 4. Logic audit
        state = self.summary_agent.run(state)      # 5. Summary
        state = self.scoring_agent.run(state)      # 6. Justice score
        state = self.timeline_agent.run(state)     # 7. Timeline
        
        print("\n" + "="*70)
        print("✅ ALL 7 AGENTS COMPLETED")
        print("="*70 + "\n")
        
        # Return formatted results
        return {
            "laws": state['laws_found'],
            "summary": state['final_summary'],
            "analysis": f"""
PRECEDENT ANALYSIS:
{state['precedent_analysis']}

LOGIC AUDIT:
{state['logic_audit']}
""",
            "web_research": state['web_research'],
            "web_sources": state['web_sources'],
            "justice_score": state['justice_score'],
            "timeline": state['timeline'],
            "context_used": state['rag_context'][:500],
            "agent_messages": [msg.content for msg in state['messages']]
        }


# --- EXAMPLE USAGE ---

if __name__ == "__main__":
    print("Multi-Agent Legal Analysis System Ready")
    print("Features:")
    print("  1. Law Identifier Agent")
    print("  2. Web Research Agent (DuckDuckGo)")
    print("  3. Precedent Analyzer Agent")
    print("  4. Logic Auditor Agent")
    print("  5. Summary Writer Agent")
    print("  6. Justice Scoring Agent")
    print("  7. Timeline Extractor Agent")
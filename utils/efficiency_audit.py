"""
═══════════════════════════════════════════════════════════════════════════════
EFFICIENCY AUDIT SCRIPT
═══════════════════════════════════════════════════════════════════════════════

This script monitors your AI tutor's performance and identifies optimization opportunities.

USAGE:
1. Wrap your API calls with the audit decorator
2. Run your tutor normally with students
3. Generate report to see bottlenecks and recommendations

INTEGRATION OPTIONS:
- Option A: Wrap existing API calls with decorator
- Option B: Use as context manager
- Option C: Manual logging for each call

See README_EFFICIENCY_AUDIT.md for detailed instructions.

═══════════════════════════════════════════════════════════════════════════════
"""

import time
import json
import statistics
from datetime import datetime
from typing import Dict, List, Optional, Any
from collections import defaultdict
from pathlib import Path


class EfficiencyAuditor:
    """
    Monitors AI tutor performance and identifies optimization opportunities.

    Tracks:
    - Token usage per mode
    - Response times
    - Conversation history sizes
    - System prompt sizes
    - Mode switches
    - API call patterns
    """

    def __init__(self, log_file: str = "efficiency_audit.json"):
        self.log_file = Path(log_file)
        self.sessions: Dict[str, Dict] = {}
        self.current_session: Optional[str] = None

        # Metrics storage
        self.token_usage = defaultdict(list)  # By mode
        self.response_times = defaultdict(list)  # By mode
        self.prompt_sizes = defaultdict(list)  # By mode
        self.conversation_lengths = []
        self.mode_switches = []
        self.api_calls = []

        # Load existing data if available
        if self.log_file.exists():
            self._load_data()

    def start_session(self, session_id: str, topic: str, mode: str, metadata: Optional[Dict] = None):
        """Start tracking a new tutoring session."""
        self.current_session = session_id
        self.sessions[session_id] = {
            "session_id": session_id,
            "topic": topic,
            "initial_mode": mode,
            "current_mode": mode,
            "start_time": datetime.now().isoformat(),
            "metadata": metadata or {},
            "api_calls": [],
            "mode_switches": [],
            "total_tokens": 0,
            "total_cost": 0.0,
            "problems_attempted": 0
        }
        print(f"📊 [AUDIT] Started session {session_id} - {topic} - {mode}")

    def log_api_call(
        self,
        session_id: str,
        mode: str,
        system_prompt_size: int,
        conversation_history_size: int,
        user_message_size: int,
        response_size: int,
        response_time: float,
        tokens_used: Dict[str, int],
        success: bool = True
    ):
        """Log details of an API call."""

        if session_id not in self.sessions:
            print(f"⚠️  [AUDIT] Warning: Session {session_id} not started, creating now")
            self.start_session(session_id, "unknown", mode)

        call_data = {
            "timestamp": datetime.now().isoformat(),
            "mode": mode,
            "system_prompt_size": system_prompt_size,
            "conversation_history_size": conversation_history_size,
            "user_message_size": user_message_size,
            "response_size": response_size,
            "response_time": response_time,
            "tokens": tokens_used,
            "success": success,
            "total_input_tokens": tokens_used.get("prompt_tokens", 0),
            "total_output_tokens": tokens_used.get("completion_tokens", 0),
            "total_tokens": tokens_used.get("total_tokens", 0)
        }

        # Store in session
        self.sessions[session_id]["api_calls"].append(call_data)
        self.sessions[session_id]["total_tokens"] += tokens_used.get("total_tokens", 0)

        # Calculate cost (GPT-4o pricing as of Nov 2024)
        input_cost = tokens_used.get("prompt_tokens", 0) * 0.00001  # $0.01 per 1k tokens
        output_cost = tokens_used.get("completion_tokens", 0) * 0.00003  # $0.03 per 1k tokens
        self.sessions[session_id]["total_cost"] += (input_cost + output_cost)

        # Aggregate metrics
        self.token_usage[mode].append(tokens_used.get("total_tokens", 0))
        self.response_times[mode].append(response_time)
        self.prompt_sizes[mode].append(system_prompt_size)
        self.conversation_lengths.append(conversation_history_size)
        self.api_calls.append(call_data)

        # Real-time warnings
        self._check_for_issues(call_data, mode)

        # Auto-save every 5 calls
        if len(self.api_calls) % 5 == 0:
            self._save_data()

    def log_mode_switch(self, session_id: str, from_mode: str, to_mode: str, reason: str):
        """Log when a mode switch occurs."""
        switch_data = {
            "timestamp": datetime.now().isoformat(),
            "from_mode": from_mode,
            "to_mode": to_mode,
            "reason": reason
        }

        if session_id in self.sessions:
            self.sessions[session_id]["mode_switches"].append(switch_data)
            self.sessions[session_id]["current_mode"] = to_mode

        self.mode_switches.append(switch_data)
        print(f"🔄 [AUDIT] Mode switch: {from_mode} → {to_mode} ({reason})")

    def log_problem_completion(self, session_id: str):
        """Log when a problem is completed."""
        if session_id in self.sessions:
            self.sessions[session_id]["problems_attempted"] += 1

    def end_session(self, session_id: str):
        """End tracking for a session."""
        if session_id in self.sessions:
            self.sessions[session_id]["end_time"] = datetime.now().isoformat()
            print(f"✅ [AUDIT] Ended session {session_id}")
            self._save_data()

    def _check_for_issues(self, call_data: Dict, mode: str):
        """Real-time issue detection."""

        # Issue 1: Conversation history too large
        if call_data["conversation_history_size"] > 8000:
            print(f"⚠️  [AUDIT] WARNING: Conversation history is {call_data['conversation_history_size']} chars!")
            print(f"   💡 TIP: Implement sliding window (keep last 6-10 messages)")

        # Issue 2: Response time too slow
        if call_data["response_time"] > 10.0:
            print(f"⚠️  [AUDIT] WARNING: Slow response ({call_data['response_time']:.1f}s)")
            print(f"   💡 TIP: Check if conversation history is too large or prompt too complex")

        # Issue 3: High token usage
        if call_data["total_tokens"] > 4000:
            print(f"⚠️  [AUDIT] WARNING: High token usage ({call_data['total_tokens']} tokens)")
            print(f"   💡 TIP: Reduce conversation history or use shorter prompts")

        # Issue 4: System prompt too large for Quick Hints
        if mode == "quick_hints" and call_data["system_prompt_size"] > 3000:
            print(f"⚠️  [AUDIT] WARNING: Quick Hints prompt is {call_data['system_prompt_size']} chars")
            print(f"   💡 TIP: Quick Hints should use prompts_quick_hints.py (~2500 chars)")

    def generate_report(self, output_file: str = "efficiency_report.txt") -> str:
        """Generate comprehensive efficiency report."""

        report_lines = []
        report_lines.append("═" * 80)
        report_lines.append("EFFICIENCY AUDIT REPORT")
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("═" * 80)
        report_lines.append("")

        # Overall Statistics
        report_lines.append("📊 OVERALL STATISTICS")
        report_lines.append("─" * 80)
        report_lines.append(f"Total API calls: {len(self.api_calls)}")
        report_lines.append(f"Total sessions: {len(self.sessions)}")
        total_cost = sum(s["total_cost"] for s in self.sessions.values())
        report_lines.append(f"Total cost: ${total_cost:.4f}")
        report_lines.append("")

        # Token Usage by Mode
        report_lines.append("🎯 TOKEN USAGE BY MODE")
        report_lines.append("─" * 80)
        for mode, tokens in self.token_usage.items():
            if tokens:
                avg_tokens = statistics.mean(tokens)
                min_tokens = min(tokens)
                max_tokens = max(tokens)
                report_lines.append(f"{mode}:")
                report_lines.append(f"  Average: {avg_tokens:.0f} tokens")
                report_lines.append(f"  Range: {min_tokens} - {max_tokens}")

                # Efficiency rating
                if mode == "quick_hints" and avg_tokens > 2000:
                    report_lines.append(f"  ⚠️  WARNING: Too high for Quick Hints (target: <1500)")
                elif mode == "step_by_step" and avg_tokens > 3500:
                    report_lines.append(f"  ⚠️  WARNING: Consider optimization (target: <3000)")
                else:
                    report_lines.append(f"  ✅ Within expected range")
        report_lines.append("")

        # Response Time by Mode
        report_lines.append("⏱️  RESPONSE TIME BY MODE")
        report_lines.append("─" * 80)
        for mode, times in self.response_times.items():
            if times:
                avg_time = statistics.mean(times)
                min_time = min(times)
                max_time = max(times)
                report_lines.append(f"{mode}:")
                report_lines.append(f"  Average: {avg_time:.2f}s")
                report_lines.append(f"  Range: {min_time:.2f}s - {max_time:.2f}s")

                # Efficiency rating
                if avg_time > 8.0:
                    report_lines.append(f"  ⚠️  WARNING: Slow (target: <5s)")
                elif avg_time < 3.0:
                    report_lines.append(f"  ✅ Excellent")
                else:
                    report_lines.append(f"  ✅ Acceptable")
        report_lines.append("")

        # Prompt Sizes
        report_lines.append("📝 SYSTEM PROMPT SIZES")
        report_lines.append("─" * 80)
        for mode, sizes in self.prompt_sizes.items():
            if sizes:
                avg_size = statistics.mean(sizes)
                report_lines.append(f"{mode}: {avg_size:.0f} chars")

                # Check if using correct file
                if mode == "quick_hints" and avg_size > 2500:
                    report_lines.append(f"  ⚠️  WARNING: Should use prompts_quick_hints.py (~2000 chars)")
                elif mode in ["step_by_step", "detailed_explanations"] and avg_size > 6000:
                    report_lines.append(f"  ⚠️  WARNING: Should use prompts_standard.py (~5500 chars)")
                else:
                    report_lines.append(f"  ✅ Correct prompt file being used")
        report_lines.append("")

        # Conversation History Analysis
        report_lines.append("💬 CONVERSATION HISTORY ANALYSIS")
        report_lines.append("─" * 80)
        if self.conversation_lengths:
            avg_history = statistics.mean(self.conversation_lengths)
            max_history = max(self.conversation_lengths)
            report_lines.append(f"Average history size: {avg_history:.0f} chars")
            report_lines.append(f"Maximum history size: {max_history} chars")

            if max_history > 10000:
                report_lines.append(f"⚠️  WARNING: Conversation history too large!")
                report_lines.append(f"   Recommendation: Implement sliding window (keep last 6-10 messages)")
            elif avg_history > 5000:
                report_lines.append(f"⚠️  CAUTION: History growing large")
                report_lines.append(f"   Recommendation: Consider sliding window or summarization")
            else:
                report_lines.append(f"✅ History size is reasonable")
        report_lines.append("")

        # Mode Switches
        report_lines.append("🔄 MODE SWITCHING ANALYSIS")
        report_lines.append("─" * 80)
        report_lines.append(f"Total mode switches: {len(self.mode_switches)}")
        if self.mode_switches:
            switch_reasons = defaultdict(int)
            for switch in self.mode_switches:
                switch_reasons[switch["reason"]] += 1
            for reason, count in switch_reasons.items():
                report_lines.append(f"  {reason}: {count} times")
        report_lines.append("")

        # Top 10 Slowest Calls
        report_lines.append("🐌 TOP 10 SLOWEST API CALLS")
        report_lines.append("─" * 80)
        slowest = sorted(self.api_calls, key=lambda x: x["response_time"], reverse=True)[:10]
        for i, call in enumerate(slowest, 1):
            report_lines.append(f"{i}. {call['response_time']:.2f}s - {call['mode']} - {call['total_tokens']} tokens")
            if call['conversation_history_size'] > 5000:
                report_lines.append(f"   Note: Large conversation history ({call['conversation_history_size']} chars)")
        report_lines.append("")

        # Recommendations
        report_lines.append("💡 OPTIMIZATION RECOMMENDATIONS")
        report_lines.append("═" * 80)
        recommendations = self._generate_recommendations()
        for i, rec in enumerate(recommendations, 1):
            report_lines.append(f"{i}. {rec}")
        report_lines.append("")

        # Cost Projection
        report_lines.append("💰 COST PROJECTION")
        report_lines.append("─" * 80)
        if self.sessions:
            avg_cost_per_session = total_cost / len(self.sessions)
            report_lines.append(f"Average cost per session: ${avg_cost_per_session:.4f}")
            report_lines.append(f"Projected cost for 100 students: ${avg_cost_per_session * 100:.2f}")
            report_lines.append(f"Projected cost for 1000 students: ${avg_cost_per_session * 1000:.2f}")
        report_lines.append("")

        report_lines.append("═" * 80)
        report_lines.append("END OF REPORT")
        report_lines.append("═" * 80)

        # Write to file
        report_text = "\n".join(report_lines)
        with open(output_file, "w") as f:
            f.write(report_text)

        print(f"\n📄 Report saved to: {output_file}")
        return report_text

    def _generate_recommendations(self) -> List[str]:
        """Generate actionable recommendations based on collected data."""
        recommendations = []

        # Check Quick Hints efficiency
        if "quick_hints" in self.token_usage:
            avg_qh_tokens = statistics.mean(self.token_usage["quick_hints"])
            if avg_qh_tokens > 1800:
                recommendations.append(
                    f"Quick Hints uses {avg_qh_tokens:.0f} tokens avg. Use prompts_quick_hints.py to reduce by 60-70%"
                )

        # Check conversation history
        if self.conversation_lengths:
            avg_history = statistics.mean(self.conversation_lengths)
            if avg_history > 5000:
                recommendations.append(
                    f"Conversation history averages {avg_history:.0f} chars. Implement sliding window (keep last 6-10 messages)"
                )

        # Check response times
        all_times = [t for times in self.response_times.values() for t in times]
        if all_times:
            avg_time = statistics.mean(all_times)
            if avg_time > 6.0:
                recommendations.append(
                    f"Average response time is {avg_time:.1f}s. Target: <5s. Check conversation history size and prompt complexity"
                )

        # Check for system prompt caching
        recommendations.append(
            "Implement system prompt caching - build once per session, reuse for all calls"
        )

        # Check mode-specific max_tokens
        recommendations.append(
            "Set mode-specific max_tokens: Quick Hints=400, Step-by-Step=900, Detailed=1400"
        )

        # Check for contextual prompt strategy
        recommendations.append(
            "Inject contextual prompts (BREAK_SMALLER, RETEACH) as user messages, not in system prompt"
        )

        # Check mode switching
        if len(self.mode_switches) > len(self.sessions) * 0.3:
            recommendations.append(
                f"High mode switch rate ({len(self.mode_switches)}/{len(self.sessions)} sessions). Consider adjusting difficulty or scaffolding"
            )

        return recommendations

    def _save_data(self):
        """Save audit data to JSON file."""
        data = {
            "sessions": self.sessions,
            "summary": {
                "total_api_calls": len(self.api_calls),
                "total_sessions": len(self.sessions),
                "total_mode_switches": len(self.mode_switches),
                "last_updated": datetime.now().isoformat()
            }
        }
        with open(self.log_file, "w") as f:
            json.dump(data, f, indent=2)

    def _load_data(self):
        """Load existing audit data."""
        try:
            with open(self.log_file, "r") as f:
                data = json.load(f)
                self.sessions = data.get("sessions", {})
                # Rebuild metrics from sessions
                for session in self.sessions.values():
                    for call in session.get("api_calls", []):
                        mode = call["mode"]
                        self.token_usage[mode].append(call["total_tokens"])
                        self.response_times[mode].append(call["response_time"])
                        self.prompt_sizes[mode].append(call["system_prompt_size"])
                        self.conversation_lengths.append(call["conversation_history_size"])
                        self.api_calls.append(call)
                    self.mode_switches.extend(session.get("mode_switches", []))
            print(f"📂 [AUDIT] Loaded existing data from {self.log_file}")
        except Exception as e:
            print(f"⚠️  [AUDIT] Could not load existing data: {e}")


# Global auditor instance
_auditor = EfficiencyAuditor()


def get_auditor() -> EfficiencyAuditor:
    """Get the global auditor instance."""
    return _auditor


# Convenience functions for easy integration
def start_session(session_id: str, topic: str, mode: str, metadata: Optional[Dict] = None):
    """Start tracking a session."""
    _auditor.start_session(session_id, topic, mode, metadata)


def log_api_call(
    session_id: str,
    mode: str,
    system_prompt: str,
    conversation_history: List[Dict],
    user_message: str,
    response: str,
    response_time: float,
    tokens_used: Dict[str, int],
    success: bool = True
):
    """Log an API call."""
    _auditor.log_api_call(
        session_id=session_id,
        mode=mode,
        system_prompt_size=len(system_prompt),
        conversation_history_size=sum(len(str(msg)) for msg in conversation_history),
        user_message_size=len(user_message),
        response_size=len(response),
        response_time=response_time,
        tokens_used=tokens_used,
        success=success
    )


def log_mode_switch(session_id: str, from_mode: str, to_mode: str, reason: str):
    """Log a mode switch."""
    _auditor.log_mode_switch(session_id, from_mode, to_mode, reason)


def log_problem_completion(session_id: str):
    """Log problem completion."""
    _auditor.log_problem_completion(session_id)


def end_session(session_id: str):
    """End a session."""
    _auditor.end_session(session_id)


def generate_report(output_file: str = "efficiency_report.txt") -> str:
    """Generate efficiency report."""
    return _auditor.generate_report(output_file)


# Decorator for automatic API call logging
def audit_api_call(session_id_key: str = "session_id", mode_key: str = "mode"):
    """
    Decorator to automatically audit API calls.

    Usage:
        @audit_api_call(session_id_key="session_id", mode_key="mode")
        def call_openai_api(session_id, mode, system_prompt, messages, user_input):
            # Your API call here
            start_time = time.time()
            response = openai.ChatCompletion.create(...)
            response_time = time.time() - start_time

            # Return tuple: (response_text, tokens_dict, response_time)
            return response.choices[0].message.content, response.usage, response_time
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Extract session_id and mode from kwargs
            session_id = kwargs.get(session_id_key)
            mode = kwargs.get(mode_key)

            if not session_id or not mode:
                print(f"⚠️  [AUDIT] Warning: Missing session_id or mode in {func.__name__}")
                return func(*args, **kwargs)

            # Call the original function
            result = func(*args, **kwargs)

            # Expected return: (response_text, tokens_dict, response_time)
            if isinstance(result, tuple) and len(result) == 3:
                response_text, tokens_dict, response_time = result

                # Extract prompt and history from kwargs
                system_prompt = kwargs.get("system_prompt", "")
                messages = kwargs.get("messages", [])
                user_input = kwargs.get("user_input", "")

                # Log the call
                log_api_call(
                    session_id=session_id,
                    mode=mode,
                    system_prompt=system_prompt,
                    conversation_history=messages,
                    user_message=user_input,
                    response=response_text,
                    response_time=response_time,
                    tokens_used=tokens_dict,
                    success=True
                )

            return result
        return wrapper
    return decorator


if __name__ == "__main__":
    # Example usage / testing
    print("Efficiency Auditor - Example Usage")
    print("=" * 80)

    # Simulate a session
    start_session("test_session_1", "unit1", "quick_hints")

    # Simulate API calls
    log_api_call(
        session_id="test_session_1",
        mode="quick_hints",
        system_prompt="A" * 2000,
        conversation_history=[{"role": "user", "content": "Problem"}, {"role": "assistant", "content": "Response"}],
        user_message="What should we do next?",
        response="Let's subtract 5 from both sides",
        response_time=2.3,
        tokens_used={"prompt_tokens": 500, "completion_tokens": 50, "total_tokens": 550}
    )

    log_api_call(
        session_id="test_session_1",
        mode="quick_hints",
        system_prompt="A" * 2000,
        conversation_history=[{"role": "user", "content": "Problem"}] * 5,
        user_message="What next?",
        response="Divide both sides by 2",
        response_time=2.1,
        tokens_used={"prompt_tokens": 800, "completion_tokens": 40, "total_tokens": 840}
    )

    log_problem_completion("test_session_1")
    end_session("test_session_1")

    # Generate report
    report = generate_report("test_efficiency_report.txt")
    print("\n" + report)

"""
tiny-harness: a minimal agent harness you can read in 5 minutes.

No API key needed. We use a fake model (MockLLM) so you can focus on
the HARNESS, not the model. Swap MockLLM for a real API call later
and nothing else changes. That is the whole point of a harness.

Run it:
    python harness.py "what is 23 * 47, and what time is it?"
"""

import sys
import json
import datetime

# ---------------------------------------------------------------
# 1. TOOLS
# The model cannot do anything. It can only ASK for things.
# The harness owns the tools and actually executes them.
# ---------------------------------------------------------------

def tool_calculator(expression: str) -> str:
    """Evaluate a simple math expression like '23 * 47'."""
    try:
        allowed = set("0123456789+-*/(). ")
        if not set(expression) <= allowed:
            return "error: only basic math allowed"
        return str(eval(expression))  # fine here, input is filtered
    except Exception as e:
        return f"error: {e}"

def tool_clock() -> str:
    """Return the current time."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

TOOLS = {
    "calculator": tool_calculator,
    "clock": tool_clock,
}

# ---------------------------------------------------------------
# 2. THE "MODEL"
# A real LLM is text in, text out. Our mock does the same.
# It looks at the conversation and replies with either:
#   - a tool call:   {"tool": "calculator", "input": "23 * 47"}
#   - a final answer: {"answer": "..."}
# A real model would decide this with intelligence.
# Our mock decides with dumb rules. The harness cannot tell
# the difference, and that is the lesson.
# ---------------------------------------------------------------

class MockLLM:
    def complete(self, messages: list[dict]) -> str:
        user_question = messages[1]["content"].lower()
        tool_results = [m for m in messages if m["role"] == "tool"]
        used = {r["name"] for r in tool_results}

        # "wants math" and haven't done it yet -> ask for calculator
        if any(c in user_question for c in "0123456789") and "calculator" not in used:
            # crude extraction of a math expression from the question
            expr = "".join(c for c in user_question if c in "0123456789+-*/(). ").strip()
            return json.dumps({"tool": "calculator", "input": expr})

        # "wants time" and haven't done it yet -> ask for clock
        if "time" in user_question and "clock" not in used:
            return json.dumps({"tool": "clock", "input": ""})

        # otherwise, write a final answer from the tool results
        parts = [f"{r['name']} returned {r['content']}" for r in tool_results]
        summary = "; ".join(parts) if parts else "I did not need any tools."
        return json.dumps({"answer": f"Done. {summary}"})

# ---------------------------------------------------------------
# 3. CONTEXT ENGINEERING
# The context is just the message list we send to the model.
# Real harnesses trim, summarize, and prioritize it because the
# window is finite. We simulate that with a tiny budget.
# ---------------------------------------------------------------

MAX_MESSAGES = 8  # pretend this is our context window limit

def build_context(system: str, question: str, history: list[dict]) -> list[dict]:
    """Decide what the model gets to see this turn."""
    messages = [{"role": "system", "content": system},
                {"role": "user", "content": question}]
    # keep only the most recent history if we are over budget
    trimmed = history[-(MAX_MESSAGES - 2):]
    if len(history) > len(trimmed):
        print(f"  [context] trimmed {len(history) - len(trimmed)} old messages")
    return messages + trimmed

# ---------------------------------------------------------------
# 4. LOOP ENGINEERING
# Call model -> read output -> run tool -> append result -> repeat.
# Plus the boring parts that make it production grade:
# a step limit, and handling garbage output.
# ---------------------------------------------------------------

MAX_STEPS = 5  # never trust a loop without a leash

def run_agent(question: str):
    model = MockLLM()
    system = "You are an assistant. Use tools when needed, then answer."
    history: list[dict] = []

    for step in range(1, MAX_STEPS + 1):
        print(f"\n--- step {step} ---")

        context = build_context(system, question, history)
        raw = model.complete(context)
        print(f"  [model] {raw}")

        try:
            decision = json.loads(raw)
        except json.JSONDecodeError:
            # models produce garbage sometimes; the harness must survive it
            history.append({"role": "tool", "name": "error",
                            "content": "invalid output, respond in JSON"})
            continue

        if "answer" in decision:
            print(f"\nFINAL ANSWER: {decision['answer']}")
            return

        tool_name = decision.get("tool")
        if tool_name not in TOOLS:
            history.append({"role": "tool", "name": "error",
                            "content": f"unknown tool {tool_name}"})
            continue

        # the harness, not the model, executes the tool
        arg = decision.get("input", "")
        result = TOOLS[tool_name](arg) if arg else TOOLS[tool_name]()
        print(f"  [tool:{tool_name}] -> {result}")

        history.append({"role": "tool", "name": tool_name, "content": result})

    print("\nStopped: hit MAX_STEPS. This safety limit is loop engineering.")

# ---------------------------------------------------------------

if __name__ == "__main__":
    q = " ".join(sys.argv[1:]) or "what is 23 * 47, and what time is it?"
    print(f"QUESTION: {q}")
    run_agent(q)

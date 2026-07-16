# tiny-harness

A minimal agent harness in one Python file. No API key, no dependencies, no framework. Built to teach one idea: the model is a component, the harness is the product.

## What is a harness?

An LLM is a function. Text goes in, text comes out. Once. It cannot run code, click buttons, remember anything, or retry when it fails.

The harness is all the code you build around the model to make it act like an agent:

1. It calls the model in a loop
2. It reads the model's output and detects tool requests
3. It actually executes the tools (the model never executes anything)
4. It feeds tool results back into the next model call
5. It decides when to stop
<img width="1402" height="1122" alt="image" src="https://github.com/user-attachments/assets/adf2778f-1f37-4509-afe3-54f5d4b9054c" />

When an agent "does" something, the harness did it. The model only suggested it.

## How this relates to context engineering and loop engineering

They are the two halves of harness engineering.

**Context engineering** is deciding what the model sees on each turn. The context window is finite, so you choose what to include, what to trim, and what to summarize. In this repo that is the `build_context()` function.

**Loop engineering** is how you run the cycle. Call model, parse output, run tool, append result, call again. Plus retries, garbage handling, and a hard step limit so nothing runs forever. In this repo that is `run_agent()`.

```
harness = context engineering + loop engineering + tools + error handling
```

## Run it

```bash
python harness.py "what is 23 * 47, and what time is it?"
```

You will see the loop happen step by step:

```
--- step 1 ---
  [model] {"tool": "calculator", "input": "23 * 47"}
  [tool:calculator] -> 1081

--- step 2 ---
  [model] {"tool": "clock", "input": ""}
  [tool:clock] -> 2026-07-13 06:15:15

--- step 3 ---
  [model] {"answer": "Done. calculator returned 1081; ..."}

FINAL ANSWER: Done. calculator returned 1081; clock returned ...
```

## Why is the model fake?

`MockLLM` follows dumb rules instead of thinking. That is on purpose. The harness cannot tell the difference between a mock and GPT or Claude, because both are just text in, text out. This proves the point: all the agent behavior you see (tool use, multi step work, stopping) lives in the harness, not the model.

To make it real, replace `MockLLM.complete()` with a call to any LLM API. Nothing else changes.

## Map of the file

| Section | Concept |
|---|---|
| `TOOLS` | Tools belong to the harness, not the model |
| `MockLLM` | The model is just text in, text out |
| `build_context()` | Context engineering: what the model sees |
| `run_agent()` | Loop engineering: the cycle plus safety limits |
| `MAX_STEPS` | Never trust a loop without a leash |

## Exercises

1. Add a new tool, for example `tool_weather()` that returns a fake forecast, and teach `MockLLM` to call it
2. Lower `MAX_MESSAGES` to 3 and watch the context trimming kick in
3. Make `MockLLM` return broken JSON sometimes and confirm the harness survives
4. Swap `MockLLM` for a real API call and compare

## License

MIT

Akash Shahade www.linkedin.com/in/akashshahade

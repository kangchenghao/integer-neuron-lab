# Maintainer exercises and discussion prompts

AI-generated code is not evidence that its maintainer understands it. Complete
and explain these changes before describing the project as personal expertise.

1. **Work a counterexample by hand.** Derive `g(g(2))`, the one-round exponential
   shortcut, and the first zero-input tick for initial states 141 and 142. Write
   the exact expected spike trace for a tiny two-neuron input before running it.
2. **Change one numerical parameter.** In a separate branch, choose another
   rational leak `a/256`. Derive the post-reset domain and finite decay bound;
   update both independent implementations and tests. Do not change both sides
   to call the same helper just to make comparisons pass.
3. **Test an applicability boundary.** Freeze the event sequence, vary only query
   spacing, and record the complete exactness/time matrix. Explain why expensive
   queries can remove event skipping's benefit. Do not infer chip energy from
   host Python time.

Further research requires real design work: an adaptive selector must use only
available information, pay for state conversion and decisions, and be tested on
inputs not used to choose its policy. A convenient fixed density threshold is
not automatically a strong baseline or a research contribution.

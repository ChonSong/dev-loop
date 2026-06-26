# Adversarial Feedback Loop — Methodology & Results

## The Core Insight

The adversarial training loop treats detection bypass as an **optimization problem** rather than a translation problem. Instead of teaching a model to "write like a human," search a parameter space for transformations that minimize the detector's score.

This is "whack-a-mole as data" — every trial generates a labeled example (this transformation → this detector score), and successful mutations are retained.

## Proven in Literature

The academic literature supports this approach:

- **Krishna et al. "Paraphrasing Evades Detectors of AI-Generated Text" (2023)**: Simple paraphrasing drops GPT-2 detector accuracy from ~95% → ~50-70%.
- **Sadasivan et al. "The Cat-and-Mouse Game of AI-Generated Text Detection"**: Shows that detection is fundamentally an arms race — generators can always be trained to evade a fixed detector.
- **Adversarial training (GAN-style)**: Training a generator against a discriminator classifier reliably produces text that fools the discriminator, at the cost of some output quality.

## Our Implementation

`adversarial-train.py` at `~/workspace/adversarial-train.py` uses simulated annealing:

1. **Start**: Default humanizer parameters
2. **Mutate**: Random perturbation of each parameter (gaussian noise, decaying temperature)
3. **Score**: Fakespot RoBERTa AI probability (0-100)
4. **Keep**: Accept mutation if score decreased
5. **Anneal**: Reduce mutation temperature over iterations
6. **Converge**: Return best parameters found

## Measured Results

| Trial | Fakespot AI Score | Notes |
|-------|------------------|-------|
| Original text | 100% | Baseline |
| Default humanizer | 12-71% (seed-dependent) | High variance |
| After 3 optimizer trials | **<1%** | Converged in 3-5 iterations |
| After 100 trials | <1% | No improvement beyond trial 5 |

## Which Transformations Matter

The optimizer consistently converged on:

- **swap_rate**: 0.6-0.7 — heavy vocabulary replacement helps
- **split_threshold**: 18-19 words — splitting sentences at moderate length
- **frag_chance**: 0.05-0.15 — sentence fragments are highly effective
- **mid_filler**: 0.25 — mid-sentence fillers ("basically", "you know") disrupt flow
- **passes**: 3 — multiple transformation passes compound the effect

## Key Limitations

1. **Overfitting**: Optimal params are detector-specific. What beats Fakespot may not beat GPTZero.
2. **Quality degradation**: The params that work best also produce the most garbled output. This appears to be inherent — detectors use coherence as a signal.
3. **No substitute for structural human data**: The adversarial loop finds noise patterns, not authentic human writing patterns. For applications requiring natural-sounding output, a model fine-tuned on real human text is still superior.
4. **GPTZero**: Not testable programmatically — no published weights or public API. The adversarial loop is validated against Fakespot only.

## When to Use

| Goal | Approach |
|------|---------|
| Quick evasion, moderate quality | Default humanizer -a flag |
| Maximum evasion, quality optional | Adversarial optimizer (3 trials) |
| Natural-sounding evasion | Fine-tune on 5000+ human samples (not yet built) |
| Ongoing arms race | Automate adversarial loop; re-run weekly |

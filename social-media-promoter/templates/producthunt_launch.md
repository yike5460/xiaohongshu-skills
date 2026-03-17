# Product Hunt Launch Template

<!--
  Platform: Product Hunt
  Format: Product listing with tagline, description, first comment, and media.
  Tone: Enthusiastic but authentic. Maker-driven. Tell the story behind the product.
  Key success factors:
    - Strong tagline (short, benefit-driven, memorable)
    - Compelling "maker comment" as the first comment
    - Good visuals (thumbnail, gallery, demo video)
    - Active engagement with every commenter on launch day
  Timing: Launch at 12:01 AM PT for maximum exposure window.
-->

## Product Name

{{product_name}}

## Tagline

<!-- Max 60 characters. Benefit-driven. Avoid jargon. -->

{{tagline}}

## Topics/Categories

<!-- Select 3-5 relevant Product Hunt topics -->

{{topic_1}}, {{topic_2}}, {{topic_3}}

## Description

<!--
  2-3 short paragraphs. Structure:
  1. What it does (one sentence)
  2. Why it matters / the problem it solves
  3. Key differentiators
-->

**{{product_name}}** {{product_description_sentence}}

{{problem_paragraph}}

{{differentiator_paragraph}}

## Key Features

<!-- 4-6 features with emoji markers. Short, benefit-oriented. -->

{{feature_1_emoji}} **{{feature_1_title}}** - {{feature_1_description}}

{{feature_2_emoji}} **{{feature_2_title}}** - {{feature_2_description}}

{{feature_3_emoji}} **{{feature_3_title}}** - {{feature_3_description}}

{{feature_4_emoji}} **{{feature_4_title}}** - {{feature_4_description}}

{{feature_5_emoji}} **{{feature_5_title}}** - {{feature_5_description}}

## Maker's First Comment

<!--
  This is critical. The first comment sets the tone for the entire launch.
  Structure:
  1. Introduce yourself and your motivation
  2. Brief backstory (keep it personal)
  3. What's unique about this launch
  4. Specific ask (feedback, specific question)
  5. Launch day offer (if any)

  Write in first person. Be genuine. Show vulnerability.
-->

Hey Product Hunt! I'm {{maker_name}}, {{maker_role}} of {{product_name}}.

{{personal_backstory}}

{{what_we_learned_building_it}}

{{what_makes_this_launch_special}}

I'd love to hear:
- {{specific_question_1}}
- {{specific_question_2}}

{{launch_day_offer}}

Thanks for checking us out - happy to answer any questions!

## Social Proof Section

<!-- Include if available. Numbers, testimonials, logos. -->

{{social_proof_metrics}}

{{testimonial_quote}} - **{{testimonial_author}}**, {{testimonial_role}}

## Media Assets

<!--
  List the visual assets needed for the launch.
  Thumbnail: 240x240 logo/icon
  Gallery: 3-5 screenshots or feature highlights (1270x760)
  Video: 1-2 min demo video (optional but strongly recommended)
-->

- Thumbnail: {{thumbnail_description}}
- Gallery Image 1: {{gallery_1_description}}
- Gallery Image 2: {{gallery_2_description}}
- Gallery Image 3: {{gallery_3_description}}
- Demo Video: {{video_description}}

## Launch Day Links

- Product Hunt listing: (generated on launch)
- Direct URL: {{product_url}}
- Launch day offer: {{offer_url_if_applicable}}

---

## Example: Filled Template

### Product Name
```
CodeLens AI
```

### Tagline
```
AI code reviewer that actually understands your codebase
```

### Topics
```
Developer Tools, Artificial Intelligence, Code Review
```

### Description
```
**CodeLens AI** automatically reviews your pull requests by understanding your entire codebase, not just the diff.

Code review is the #1 bottleneck in most dev teams. PRs wait hours for human reviewers, bugs slip through tired eyes, and context-switching kills focus. Existing tools only catch syntax issues - they don't understand what your code is supposed to do.

CodeLens reads your full codebase, builds semantic understanding, and reviews every PR with the context of a senior engineer. It catches logic errors across file boundaries, suggests concrete fixes, and gets smarter with every merged PR.
```

### Key Features
```
- **Context-Aware Review** - Understands your full codebase, not just the changed lines
- **Actionable Suggestions** - Gives copy-paste-ready fixes, not vague warnings
- **Cross-File Analysis** - Catches bugs that span multiple files and modules
- **Team Learning** - Adapts to your team's coding patterns over time
- **60-Second Reviews** - Get thorough feedback in under a minute
```

### Maker's First Comment
```
Hey Product Hunt! I'm Alex, the founder of CodeLens AI.

I started building this after my 3-person startup lost a week to a bug that slipped through code review. It was a race condition across two files - the kind of thing that's invisible when you're reviewing a diff line by line. That's when I realized: reviewers aren't lazy, they're just limited by the tools we give them.

The hardest part of building CodeLens was making it understand *context*. Running an LLM on a diff is easy (and useless). Making it reason about how a change affects the rest of the system took us 6 months of research.

This launch is special because we're open-sourcing our core analysis engine. We believe code review tooling should be transparent - you should be able to see exactly why a suggestion was made.

I'd love to hear:
- What's the most frustrating part of code review in your team?
- Would you trust an AI reviewer to approve PRs, or only to flag issues?

To celebrate launch day, we're offering 3 months free on Team plans for the first 100 signups. Use code PHLAUNCH at checkout.

Thanks for checking us out - happy to answer any questions!
```

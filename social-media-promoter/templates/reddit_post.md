# Reddit Post Template

<!--
  Platform: Reddit
  Format: Text post (markdown-native). Reddit supports full markdown.
  Tone: Authentic, value-first, transparent. Redditors detect and punish obvious self-promotion.
  Key rules:
    - Lead with value, not your product
    - Be transparent about being the maker/affiliated
    - Engage genuinely in comments
    - Respect each subreddit's rules and culture
    - Never use clickbait or marketing-speak
  This template provides 3 variants for different subreddit types.
-->

---

## Variant A: "Show HN" / Launch Style

<!--
  Best for: r/SideProject, r/IndieDev, r/SelfHosted, Hacker News
  Approach: Maker story. Show what you built, how, and why. Be humble and invite feedback.
-->

### Title

Show r/{{subreddit}}: {{product_name}} - {{one_line_description}}

### Body

Hey r/{{subreddit}},

I've been working on **{{product_name}}** for the past {{development_duration}} and wanted to share it with this community.

**What it does:**

{{product_description_two_to_three_sentences}}

**Why I built it:**

{{motivation_and_backstory}}

**How it works:**

{{technical_overview}}

- {{technical_detail_1}}
- {{technical_detail_2}}
- {{technical_detail_3}}

**Current status:** {{project_status}}

**Links:**

- {{product_url}}
- Source: {{github_url_if_applicable}}

I'd genuinely love feedback - what would make this more useful for your workflow? Happy to answer any questions about the tech or approach.

---

## Variant B: Discussion / Value-First Style

<!--
  Best for: r/programming, r/webdev, r/MachineLearning, r/experienceddevs
  Approach: Frame it as a discussion topic or insight. The product is mentioned naturally, not as the focus.
  This is the safest variant for subreddits with strict self-promotion rules.
-->

### Title

{{discussion_question_or_insight}}

### Body

{{opening_context_paragraph}}

{{problem_analysis_paragraph}}

I've been experimenting with {{approach_description}}, and found some interesting results:

{{finding_1}}

{{finding_2}}

{{finding_3}}

{{optional_product_mention}}

<!--
  Product mention should be natural and brief, e.g.:
  "I ended up building a tool to automate this - [ProductName](url) - but I'm curious how others approach it."
  Or simply include it in a reply to someone asking "is there a tool for this?"
-->

Curious what approaches others here have tried. {{specific_question_to_prompt_discussion}}

---

## Variant C: Tutorial / How-To Style

<!--
  Best for: r/learnprogramming, r/DevOps, r/Python, r/javascript
  Approach: Teach something genuinely useful. Product is one tool among several mentioned.
  This builds credibility and trust before any product mention.
-->

### Title

{{tutorial_title_descriptive_and_specific}}

### Body

I recently had to {{problem_scenario}}, and after trying a few approaches, here's what worked best.

## The Problem

{{detailed_problem_description}}

## What I Tried

**Approach 1: {{approach_1_name}}**

{{approach_1_description_and_result}}

**Approach 2: {{approach_2_name}}**

{{approach_2_description_and_result}}

**Approach 3: {{approach_3_name}} (what I settled on)**

{{approach_3_description_and_result}}

## Step-by-Step Setup

```{{code_language}}
{{code_example}}
```

{{step_by_step_explanation}}

## Results

{{results_with_metrics}}

## Tools Used

- {{tool_1}} - {{tool_1_purpose}}
- {{product_name}} - {{product_purpose_in_context}}
- {{tool_3}} - {{tool_3_purpose}}

<!-- Product appears as one item in a list of tools, not the hero. -->

Hope this helps someone. Happy to answer questions in the comments.

---

## Example: Variant A Filled

```markdown
Title: Show r/SideProject: CodeLens AI - automated code review that understands your codebase

Body:

Hey r/SideProject,

I've been working on **CodeLens AI** for the past 6 months and wanted to share it with this community.

**What it does:**

It's a GitHub integration that automatically reviews your pull requests. Instead of just linting, it reads the diff in context, understands the logic across files, and leaves inline comments with suggested fixes. Think of it like a tireless senior dev reviewer.

**Why I built it:**

I was on a 3-person team where code review was our biggest bottleneck. PRs would sit for hours because everyone was heads-down coding. I started with a simple script that ran GPT on diffs, but the quality was terrible without context. Six months later, CodeLens actually understands codebases.

**How it works:**

- Indexes your repo to build a semantic understanding of the codebase
- On each PR, analyzes the diff against the full context
- Generates inline review comments with concrete fix suggestions
- Improves over time by learning from merged PRs

**Current status:** Public beta. Free for open source, paid plans for private repos.

**Links:**

- https://codelens.example.com
- Source: https://github.com/codelens-ai/codelens (core engine is open source)

I'd genuinely love feedback - what would make this more useful for your workflow? Happy to answer any questions about the tech or approach.
```

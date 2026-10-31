"""Individually reviewed SXF news exceptions and category corrections.

Source URLs are exact-match keys. Do not use a publisher-wide allowlist;
these decisions have been considered individually, with existing SEO untouched.
Generated archive and news snapshots are not manually edited.
"""

REVIEWED_NEWS = {
    "https://huggingface.co/blog/anydecisionmodel": {
        "source": "Hugging Face",
        "title": "Introducing AnySpeechRecognizer and AnyDecisionModel: Open Models for Speech and Decisions on Apple Platforms",
        "status": "accept",
        "category": "Models",
        "rationale": "User-approved source-backed technical signal with a reviewed evidence brief",
    },
    "https://openai.com/index/decisions-api": {
        "source": "OpenAI",
        "title": "Build more responsive apps with the Decisions API",
        "status": "accept",
        "category": "Tools",
        "rationale": "User-approved source-backed technical signal with a reviewed evidence brief",
    },
    "https://openai.com/index/securing-our-frontier-model-training-environment": {
        "source": "OpenAI",
        "title": "Securing our frontier model training environment",
        "status": "accept",
        "category": "Research",
        "rationale": "User-approved source-backed technical signal with a reviewed evidence brief",
    },
    "https://openai.com/index/scaling-ai-research-for-complex-biological-data": {
        "source": "OpenAI",
        "title": "Using thousands of AI agents to uncover new leads in biological data",
        "status": "accept",
        "category": "Research",
        "rationale": "User-approved source-backed technical signal with a reviewed evidence brief",
    },
    "https://huggingface.co/blog/meta-muse-spark-open": {
        "source": "Hugging Face",
        "title": "Welcome Muse Spark Open: open-weight frontier multimodal mixture-of-experts model from Meta",
        "status": "accept",
        "category": "Open Source",
        "rationale": "User-approved source-backed technical signal with a reviewed evidence brief",
    },
    "https://research.google/blog/grounding-ai-agents-in-biological-reality-building-blocks-for-autonomous-wet-labs/": {
        "source": "Google Research",
        "title": "Grounding AI agents in biological reality: Building blocks for autonomous wet labs",
        "status": "accept",
        "category": "Research",
        "rationale": "User-approved source-backed technical signal with a reviewed evidence brief",
    },
    "https://openai.com/index/disrupting-a-coordinated-model-distillation-campaign": {
        "source": "OpenAI",
        "title": "Disrupting a coordinated model-distillation campaign",
        "status": "accept",
        "category": "Research",
        "rationale": "User-approved source-backed technical signal with a reviewed evidence brief",
    },
    "https://openai.com/index/gpt-6-for-everyone": {
        "source": "OpenAI",
        "title": "GPT-6 and Intelligent UI for everyone",
        "status": "accept",
        "category": "Tools",
        "rationale": "User-approved GPT-6 rollout and Intelligent UI announcement",
    },
    "https://openai.com/index/introducing-dots": {
        "source": "OpenAI",
        "title": "Introducing dots",
        "status": "accept",
        "category": "Tools",
        "rationale": "User-approved launch of proactive OpenAI dots assistants",
    },
    "https://huggingface.co/blog/mistral-large4": {
        "source": "Hugging Face",
        "title": "Welcome Le Chonk: Mistral Large 4 on Hugging Face",
        "status": "accept",
        "category": "Models",
        "rationale": "User-approved Mistral Large 4 model release",
    },
    "https://huggingface.co/blog/mps-pytorch-2-15": {
        "source": "Hugging Face",
        "title": "MPS in PyTorch 2.15",
        "status": "accept",
        "category": "Tools",
        "rationale": "User-approved technical PyTorch 2.15 MPS backend improvements",
    },
    "https://huggingface.co/blog/hf-torchtpu": {
        "source": "Hugging Face",
        "title": "Hugging Face ❤️ TorchTPU: TPUs, Natively",
        "status": "accept",
        "category": "Tools",
        "rationale": "User-approved Hugging Face TorchTPU platform support",
    },
    "https://openai.com/index/updated-model-spec": {
        "source": "OpenAI",
        "title": "An updated Model Spec for more capable and beneficial AI",
        "status": "accept",
        "category": "Research",
        "rationale": "User-approved updated OpenAI Model Spec behavior and governance",
    },
    "https://openai.com/index/building-scientific-understanding-with-academic-communities": {
        "source": "OpenAI",
        "title": "Working with academic communities to build scientific understanding",
        "status": "accept",
        "category": "Research",
        "rationale": "User-approved scientific model research results and verification",
    },
    "https://openai.com/index/how-we-will-do-better-for-australia": {
        "source": "OpenAI",
        "title": "How we will do better for Australia",
        "status": "accept",
        "category": "Research",
        "rationale": "User-approved cybersecurity incident response and safeguards",
    },
    "https://research.google/blog/earth-ais-planetary-geospatial-foundation-models-for-global-public-health/": {
        "source": "Google Research",
        "title": "Unlocking Earth AI’s planetary geospatial foundation models for global public health",
        "status": "accept",
        "category": "Research",
        "rationale": "User-approved geospatial foundation-model research for public health",
    },
    "https://huggingface.co/blog/reflection-beam": {
        "source": "Hugging Face",
        "title": "Welcome Beam: a 501B open model you can own, customize, and scale",
        "status": "accept",
        "category": "Models",
        "rationale": "Named foundation-model release with weights and deployment claims",
    },
    "https://huggingface.co/blog/allenai/hiro-acev2": {
        "source": "Hugging Face",
        "title": "HiRO-ACEv2: Simulating extreme weather at 3 km resolution for a fraction of the cost",
        "status": "accept",
        "category": "Research",
        "rationale": "Ai2 AI climate-emulation model with measurable claims",
    },
    "https://github.blog/changelog/2026-10-13-secret-scanning-blocks-anthropic-keys-by-default-adds-salesforce": {
        "source": "GitHub",
        "title": "Secret scanning blocks Anthropic keys by default, adds Salesforce",
        "status": "reject",
        "category": "Tools",
        "rationale": "GitHub general secret-scanning update; Anthropic key mention is incidental",
    },
    "https://huggingface.co/blog/allenai/impactful-scheduling": {
        "source": "Hugging Face",
        "title": "Impactful scheduling for GPU clusters",
        "status": "accept",
        "category": "Tools",
        "rationale": "Ai2 distributed AI-training GPU scheduler methodology",
    },
    "https://huggingface.co/blog/building-with-ml-intern": {
        "source": "Hugging Face",
        "title": "The model that didn't exist, so you made it yourself",
        "status": "accept",
        "category": "Models",
        "rationale": "Post describes actual compressed domain-specific model building and evaluations",
    },
    "https://huggingface.co/blog/allenai/astabrief": {
        "source": "Hugging Face",
        "title": "Open-sourcing AstaBrief, the fast report-generation model in Asta",
        "status": "accept",
        "category": "Open Source",
        "rationale": "Named openly released AI report-generation model",
    },
    "https://huggingface.co/blog/allenai/olmocore3": {
        "source": "Hugging Face",
        "title": "Introducing Olmo-core 3: Open, scalable training infrastructure for large MoEs",
        "status": "accept",
        "category": "Open Source",
        "rationale": "Open MoE foundation-model training infrastructure",
    },
    "https://huggingface.co/blog/nvidia/kumo-tabular": {
        "source": "Hugging Face",
        "title": "NVIDIA Kumo Tabular Sets a New Accuracy-Efficiency Frontier for Tabular Prediction",
        "status": "accept",
        "category": "Models",
        "rationale": "NVIDIA tabular foundation-model release and benchmarks",
    },
    "https://huggingface.co/blog/rl-environments": {
        "source": "Hugging Face",
        "title": "Welcome RL Environments to the hub",
        "status": "accept",
        "category": "Tools",
        "rationale": "Reinforcement-learning tooling on Hugging Face Hub",
    },
    "https://huggingface.co/blog/nvidia/how-to-use-nvidia-warp-and-mjwarp": {
        "source": "Hugging Face",
        "title": "How to Use NVIDIA Warp and MjWarp to Accelerate Robotics Simulation and Learning Workflows",
        "status": "accept",
        "category": "Tools",
        "rationale": "ML robotics-simulation workflow and infrastructure",
    },
    "https://huggingface.co/blog/omlx": {
        "source": "Hugging Face",
        "title": "Jun Kim, oMLX creator and maintainer, joins Hugging Face to support the MLX community",
        "status": "reject",
        "category": "Open Source",
        "rationale": "Hiring/community announcement, not a model, benchmark or material tooling change; retain legacy SEO URL",
    },
    "https://huggingface.co/blog/tokenizers-v1": {
        "source": "Hugging Face",
        "title": "tokenizers v1: encode, decode and scaling, measured",
        "status": "accept",
        "category": "Tools",
        "rationale": "Tokenization library engineering and performance update",
    },
    "https://research.google/blog/the-future-of-practice-enabling-teachers-to-create-learning-interactives-with-generative-ui/": {
        "source": "Google Research",
        "title": "The future of practice: Enabling teachers to create learning interactives with generative UI",
        "status": "accept",
        "category": "Research",
        "rationale": "Google Research generative-UI interactive-learning research",
    },
    "https://huggingface.co/blog/asyncgrpo-lora-hfjobs": {
        "source": "Hugging Face",
        "title": "Async GRPO with LoRA across HF Jobs: a bucket, a proxy, and no NCCL",
        "status": "accept",
        "category": "Tools",
        "rationale": "AI fine-tuning and reinforcement learning training workflow",
    },
    "https://huggingface.co/blog/gradio-workflow-1111": {
        "source": "Hugging Face",
        "title": "Rebuilding AUTOMATIC1111 with Gradio Workflow",
        "status": "accept",
        "category": "Tools",
        "rationale": "AI diffusion image/video workflow tooling",
    },
    "https://huggingface.co/blog/grpo-with-trl-ifstruct": {
        "source": "Hugging Face",
        "title": "Fine-tuning a 350M Model for Better Structured Outputs in 100 GRPO Steps",
        "status": "accept",
        "category": "Research",
        "rationale": "GRPO model training and structured-output evidence",
    },
    "https://huggingface.co/blog/train-to-paint-with-code": {
        "source": "Hugging Face",
        "title": "Training a coding model to paint watercolours with TRL and OpenEnv",
        "status": "accept",
        "category": "Research",
        "rationale": "Reinforcement-learning experiment on a coding model",
    },
    "https://huggingface.co/blog/train-multi-vector-encoder": {
        "source": "Hugging Face",
        "title": "Training and Finetuning Multi-Vector Embedding Models with Sentence Transformers",
        "status": "accept",
        "category": "Research",
        "rationale": "Retrieval-model training and comparison methodology",
    },
}

CATEGORY_CORRECTIONS = {
    ("Hugging Face", "Scaling Indic Pretraining: 2.8 Trillion Tokens and an Open Data Generation Pipeline"): "Research",  # Large-scale pretraining research with reported token count
    ("Hugging Face", "Granite Switch 4.1: Chat, Decisions, and Speech from One Endpoint"): "Models",  # Named foundation-model release
    ("Hugging Face", "Multimodal open d1 decision models for the edge"): "Models",  # Named decision model family
    ("Hugging Face", "One Model Family, Two Gold-Level Results: Fine-Tuning Nemotron for IOI and IMO"): "Research",  # Competitive benchmark outcomes from model fine-tuning
    ("Hugging Face", "Getting the Source Right, Not Just the Fact: Source-Aware Verification for MCP Agents"): "Research",  # Research on source-aware verification for agents
}

REVIEWED_CATEGORY = {
    (row["source"], row["title"]): row["category"]
    for row in REVIEWED_NEWS.values()
    if row["status"] == "accept"
}
REVIEWED_CATEGORY.update(CATEGORY_CORRECTIONS)


def reviewed_category(title, source):
    return REVIEWED_CATEGORY.get((source, title))

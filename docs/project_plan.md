Project Plan
Automatic Generation of Exam Questions for Pilot Training using Small Language Models

----------------------------

1. Introduction

Pilot training requires mastery of multiple theoretical domains including Air Law, Meteorology, Principles of Flight, Human Performance, Aircraft Technical Knowledge, Communication, and Navigation. These subjects are traditionally assessed through manually constructed examination questions. 

Current practice relies heavily on static question banks, which often lead to:
- Repetition of outdated questions
- Memorisation of specific answers rather than conceptual understanding
- Limited coverage of evolving regulatory material

In the UK context, regulatory and instructional materials such as those published by the Civil Aviation Authority (CAA), including CAP 1535 (Skyway Code), form a core part of theoretical training content.

This project aims to design and evaluate a Small Language Model (SLM)-based system capable of automatically generating syllabus-aligned examination questions from aviation training materials.

----------------------------

2. Project Objectives

The primary objective is to design, implement, and evaluate a small language model-based system capable of generating high-quality, syllabus-aligned pilot training exam questions.

Specific objectives:

1. Design a preprocessing pipeline for structured aviation text.
2. Implement a retrieval-augmented generation (RAG) pipeline using embeddings.
3. Compare retrieval-augmented generation against a baseline SLM approach.
4. Evaluate question quality using automatic and human-based metrics.
5. Analyse computational efficiency and trustworthiness trade-offs.
6. Develop a lightweight web-based interface for demonstration purposes.

-----------------------------

3. Research Questions

RQ1: Can a small language model generate syllabus-aligned pilot training exam questions from regulatory text?

RQ2: Does retrieval augmentation improve factual correctness and relevance compared to direct generation?

RQ3: What are the computational efficiency trade-offs between different SLM configurations?

RQ4: To what extent can generated questions approximate human-authored exam quality?

--------------------------------

4. Work Package Decomposition

WP1 – Literature Review (Estimated: 60 hours)
- Review SLM architectures
- Review educational question generation techniques
- Review retrieval-augmented generation
- Identify evaluation methodologies
Deliverable: Literature Review chapter draft.

WP2 – Data Collection & Preprocessing (Estimated: 60 hours)
- Extract content from CAP1535 and related aviation material
- Clean and structure text into logical units
- Perform chunking for embedding
Deliverable: Structured dataset and preprocessing documentation.

WP3 – Model Development (Estimated: 130 hours)
- Implement baseline small language model generator
- Implement embedding pipeline
- Implement retrieval-augmented generation
- Conduct controlled experiments
Deliverable: Working generation pipeline and experimental results.

WP4 – Evaluation Framework (Estimated: 50 hours)
- Define automatic metrics (BLEU, ROUGE, perplexity)
- Design human evaluation rubric
- Conduct evaluation study
Deliverable: Quantitative and qualitative evaluation results.

WP5 – Web Application (Estimated: 30 hours)
- Develop simple Flask/FastAPI interface
- Implement question generation endpoint
Deliverable: Demonstration interface.

WP6 – Analysis & Reporting (Estimated: 70 hours)
- Comparative analysis of architectures
- Discussion of limitations
- Ethical reflection
Deliverable: Final dissertation.

-------------------------------

5. Timeline Overview

Months 1–2: Literature review and data preparation  
Months 2–3: Baseline implementation and embeddings pipeline  
Months 3–4: Retrieval integration and experimentation  
Month 4: Evaluation and human testing  
Final Phase: Writing, refinement, and analysis

------------------------------

6. Success Criteria

- Generation of contextually accurate multiple-choice questions
- Demonstrable improvement using retrieval augmentation
- Measurable alignment with syllabus content
- Reproducible experimental framework

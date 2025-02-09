# SHACL Generator

This application is an interactive Python program built with Tkinter that automatically generates SHACL (Shapes Constraint Language) constraints in Turtle syntax from a natural language use case description. It leverages Large Language Models (LLMs) such as GPT-4o, along with online resources (e.g., Schema.org), to extract types, properties, relationships, and constraints. The process is divided into three phases with integrated user feedback to refine the final output.

---

## Introduction

Creating SHACL constraints manually can be both challenging and time-consuming. Manual modeling is error-prone, especially for developers and students. This project aims to automate the generation of SHACL constraints by:
- Extracting relevant entities (e.g., Person, Organization, Car) from natural language use cases,
- Identifying appropriate properties and relationships,
- Converting the extracted information into valid SHACL constraints in Turtle syntax.

The approach employs a step-by-step process using GPT-4o for high precision and stability, and integrates user feedback at each phase to further improve the results.

---

## Methodology

1. Entity Extraction: 
   A natural language use case is provided as input. The system extracts relevant entities and concepts by mapping them to Schema.org classes.

2. Property Extraction: 
   The system then identifies corresponding properties and relationships for each extracted entity using few-shot or single-shot prompting techniques.

3. SHACL Document Generation: 
   Finally, the extracted structures are transformed into a complete SHACL document in Turtle syntax. The generated constraints are validated using PySHACL, and user feedback is incorporated when needed.

---

## Evaluation

The system was evaluated using 12 different use cases with increasing complexity (where *n* is the number of types to be recognized, from n=1 to n=12). Each use case was processed five times to ensure statistical comparability. Key evaluation points include:

- Average Initial Accuracy (x1): 93.8%
- Average Accuracy after Feedback (x2): 92.1%
- Average Processing Time per n: 1.8 seconds

User feedback was only necessary when the initial output was incorrect. In those cases, corrections led to a correct result in 92.1% of instances. However, additional feedback sometimes did not improve or even slightly reduced precision, suggesting that the LLM is highly accurate on its first attempt for most use cases. Note that very large use cases (e.g., n=100) may take significantly longer (around 3 minutes), so the system is best suited for moderately complex scenarios.

---

## Motivation

The code is designed to automate the generation of SHACL constraints from natural language descriptions, thereby reducing manual effort, minimizing errors, and saving time. By leveraging an LLM, the system directly extracts entities, properties, and relationships from the input, making the modeling process more efficient and accessible.

---

## How the Code Works

The application is organized into three main phases:

1. Entity Extraction:
   - The user provides a use case description via the GUI.
   - The application constructs a prompt and calls the OpenAI API to extract entities based on Schema.org.
   - Extracted entities and their descriptions are displayed in the GUI.

2. Property Extraction: 
   - The system analyzes the output from Phase 1 and builds a new prompt to extract properties and relationships for each entity.
   - The results are formatted similarly to Schema.org descriptions and shown to the user.

3. SHACL Generation: 
   - Using the combined information from the previous steps, the application generates a complete SHACL document in Turtle syntax.
   - This document includes NodeShapes, PropertyShapes, and the necessary prefix declarations.
   - The generated SHACL document is validated using PySHACL.
   - The user can provide feedback at any step to refine the results.

---

## Installation Requirements

- Python 3.x
- Required Python Packages: 
  - `openai`
  - `pyshacl`
  - `rdflib`

Install the dependencies using:
```bash
pip install openai pyshacl rdflib
```

## How to Use the Application

### Starting the Application
1. Open a terminal.
2. Navigate to the project directory.
3. Run the following command:
```bash
python shacl_generator.py
```
   
4. The application’s graphical user interface (GUI) will open.

### Operating the GUI

Step 1: Entity Extraction

- Input:
The main window displays a multi-line text box labeled "Input:" pre-filled with a default use case description. You can edit or replace this text with your own description (e.g., details about a company, its employees, vehicles, etc.).

- Action:
Click the "Next" button. The application constructs a prompt and calls the OpenAI API to extract relevant entities (such as Person, Organization, Car) and their descriptions, which are then displayed on the screen.

Step 2: Property Extraction

- Viewing Results:
The entity extraction results are displayed in the interface.
- Action:
Click the "Next Step" button. The system builds a new prompt to extract properties and relationships for each entity, then displays the output in a format similar to Schema.org descriptions.

Step 3: SHACL Document Generation

- Action:
Click "Next Step" once more to generate the final SHACL document. The application uses the extracted information to create a complete SHACL document in Turtle syntax.
- Output:
The generated SHACL document is shown in a scrollable text area.
- Feedback:
If the output is unsatisfactory, click the "Give Feedback" button to provide additional instructions or clarifications. The system will update the result accordingly.
- Exit:
When you are satisfied with the final output, click the "Close" button to exit the application.

Additional Interactions

- Give Feedback:
At any point, you can click "Give Feedback" to refine the prompt or output.
- Back:
Use the "Back" button to return to the previous screen and modify your input if necessary.
- Close:
Click "Close" to exit the program when finished.

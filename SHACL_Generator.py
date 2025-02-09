import tkinter as tk
from tkinter import scrolledtext, messagebox, simpledialog
from openai import OpenAI
import re
import logging
from pyshacl import validate
from rdflib import Graph
import time

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class OpenAIClient:
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
        self.history = [{"role": "system", "content": "You are an assistant responding to queries about Schema.org concepts."}]

    def ask(self, prompt: str, model: str = "gpt-4o", max_retries=3) -> str:
        """Send a query to OpenAI API and retrieve the response with retry mechanism."""
        for attempt in range(max_retries):
            try:
                self.history.append({"role": "user", "content": prompt})
                response = self.client.chat.completions.create(
                    model=model,
                    messages=self.history,
                    temperature=0.7,
                    max_tokens=1500
                )
                ai_response = response.choices[0].message.content
                self.history.append({"role": "assistant", "content": ai_response})
                return ai_response
            except Exception as e:
                if attempt < max_retries - 1:
                    logger.info(f"Attempt {attempt + 1} failed. Retrying in 5 seconds...")
                    time.sleep(5)  # Wait before retrying
                else:
                    raise Exception(f"Error communicating with OpenAI API after {max_retries} attempts: {e}")

def validate_shacl(shacl_doc):
    """Validate SHACL document with some pre-processing for cleanliness."""
    # Clean the SHACL document
    shacl_doc = re.sub(r'[^@;\w\s:\[\]\{\}\(\)\<\>=\.\-\"\/]+', '', shacl_doc)  # Remove non-Turtle syntax characters
    shacl_doc = re.sub(r'\n\s*\n', '\n', shacl_doc)  # Remove extra newlines
    shacl_doc = re.sub(r'```(turtle|ttl)?\s*', '', shacl_doc)  # Remove markdown formatting
    shacl_doc = re.sub(r'```\s*', '', shacl_doc)
    shacl_doc = shacl_doc.strip()  # Remove leading/trailing whitespace

    # Ensure each @prefix declaration ends with a dot
    shacl_doc = re.sub(r'@prefix\s*.*?\s*(?<!.)\n', r'\g<0>.\n', shacl_doc)

    # Add basic prefixes if none are present
    if not re.search(r'@prefix', shacl_doc, re.IGNORECASE):
        shacl_doc = """@prefix ex: <http://example.org/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix schema: <https://schema.org/> .

""" + shacl_doc

    try:
        g = Graph()
        g.parse(data=shacl_doc, format="turtle")
        conforms, _, results_text = validate(data_graph=g, shacl_graph=None, inference='rdfs')
        return conforms, results_text
    except Exception as e:
        logger.error(f"Error during SHACL validation: {e}")
        return False, str(e)

def auto_correct_shacl(shacl_doc, classes_and_properties):
    """Automatically correct and integrate SHACL issues based on classes and properties."""
    # Clean the SHACL document
    shacl_doc = re.sub(r'[^@;\w\s:\[\]\{\}\(\)\<\>=\.\-\"\/]+', '', shacl_doc)  # Remove non-Turtle syntax characters
    shacl_doc = re.sub(r'\n\s*\n', '\n', shacl_doc)  # Remove extra newlines
    shacl_doc = re.sub(r'```(turtle|ttl)?\s*', '', shacl_doc)  # Remove markdown formatting
    shacl_doc = re.sub(r'```\s*', '', shacl_doc)
    shacl_doc = shacl_doc.strip()  # Remove leading/trailing whitespace

    # Ensure each @prefix declaration ends with a dot
    shacl_doc = re.sub(r'@prefix\s*.*?\s*(?<!.)\n', r'\g<0>.\n', shacl_doc)

    # Add basic prefixes if none are present
    if not re.search(r'@prefix', shacl_doc, re.IGNORECASE):
        shacl_doc = """@prefix ex: <http://example.org/> .
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix schema: <https://schema.org/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

""" + shacl_doc

    try:
        g = Graph()
        g.parse(data=shacl_doc, format="turtle")
        return shacl_doc  # If parsing succeeds, return the cleaned document
    except Exception as e:
        logger.error(f"Error during SHACL auto-correction: {e}")
        # If parsing fails, generate a basic SHACL document
        base_shacl = "@prefix ex: <http://example.org/> .\n@prefix sh: <http://www.w3.org/ns/shacl#> .\n@prefix schema: <https://schema.org/> .\n@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .\n\n"
        for class_name, properties in classes_and_properties.items():
            base_shacl += f"""ex:{class_name}
    a sh:NodeShape ;
    sh:targetClass schema:{class_name} ;
"""
            for prop in properties:
                base_shacl += f"""    sh:property [
        sh:path schema:{prop['path']} ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] ;
"""
        base_shacl += "."
        return base_shacl

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SHACL Generator")
        self.geometry("800x600")
        self.api_key = "XXXX-XXXX-XXXX-XXXX"  # Replace with your OpenAI API key
        self.client = OpenAIClient(self.api_key)
        self.use_case = "Enter your knowledge base information here..."
        self.current_step = 1  # Track the current step (1: Extract entities, 2: Extract properties, 3: Generate SHACL)
        self.create_main_interface()

    def create_main_interface(self):
        """Create the main interface with a use_case input and buttons."""
        self.clear_window()

        # Use Case Input
        tk.Label(self, text="Input:").pack(pady=10)
        self.use_case_text = scrolledtext.ScrolledText(self, height=30, width=100)
        self.use_case_text.insert(tk.END, self.use_case)
        self.use_case_text.pack(pady=10)

        # Buttons
        tk.Button(self, text="Cancel", command=self.destroy).pack(side=tk.LEFT, padx=20, pady=20)
        tk.Button(self, text="Next", command=self.process_use_case).pack(side=tk.RIGHT, padx=20, pady=20)

    def create_result_interface(self, result, prompt):
        """Create the result interface to display the generated response."""
        self.clear_window()

        # Preprocess the result to extract only the SHACL code
        shacl_code = self.extract_shacl_code(result)

        # Result Display
        tk.Label(self, text="Output:").pack(pady=10)
        self.result_text = scrolledtext.ScrolledText(self, height=30, width=100)
        self.result_text.insert(tk.END, shacl_code)
        self.result_text.pack(pady=10)

        # Buttons
        if self.current_step == 3:
            # Only show "Not Satisfied" and "Close" buttons for Step 3
            tk.Button(self, text="Give Feedback", command=lambda: self.ask_for_new_prompt(prompt)).pack(side=tk.LEFT, padx=20, pady=20)
            tk.Button(self, text="Close", command=self.destroy).pack(side=tk.RIGHT, padx=20, pady=20)
        else:
            # For other steps, show the usual buttons
            tk.Button(self, text="Back", command=self.create_main_interface).pack(side=tk.LEFT, padx=20, pady=20)
            tk.Button(self, text="Next Step", command=lambda: self.process_next_step(prompt)).pack(side=tk.RIGHT, padx=20, pady=20)
            tk.Button(self, text="Give Feedback", command=lambda: self.ask_for_new_prompt(prompt)).pack(side=tk.RIGHT, padx=20, pady=20)

    def extract_shacl_code(self, text):
        """Extract the SHACL code block from the AI-generated text."""
        # Use regex to find the SHACL code block (assuming it's enclosed in ```turtle or ```)
        shacl_pattern = r"```(?:turtle)?\s*(.*?)```"
        match = re.search(shacl_pattern, text, re.DOTALL)
        if match:
            return match.group(1).strip()  # Return the extracted SHACL code
        else:
            # If no code block is found, assume the entire text is SHACL code
            return text.strip()

    def ask_for_new_prompt(self, prompt):
        """Ask the user for a new prompt if they are not satisfied."""
        new_prompt = simpledialog.askstring("New Prompt", "Please provide additional details or clarify your request:")
        if new_prompt:
            # Append the new prompt to the history
            self.client.history.append({"role": "user", "content": new_prompt})
            # Regenerate the response
            response = self.client.ask(new_prompt)
            self.create_result_interface(response, new_prompt)

    def clear_window(self):
        """Clear all widgets from the window."""
        for widget in self.winfo_children():
            widget.destroy()

    def process_use_case(self, new_prompt=None):
        """Process the use_case and generate the first response."""
        self.use_case = self.use_case_text.get("1.0", tk.END).strip() if new_prompt is None else new_prompt
        if not self.use_case:
            messagebox.showwarning("Input Error", "Please enter a use case.")
            return

        # Step 1: Extract entities
        prompt_1 = f"""I will provide you with a text describing a use case. I would like you to extract all objects from this text that match Turtle Code from this source: https://schema.org/version/latest/schemaorg-current-https.ttl. 
        It is important that you always contextually select only the most logical and fitting example from the provided source. The output should only include the noun used in the source, meaning not the name but the overarching concept for names, such as "I" would be "Person", as well as the exact description provided under rdfs:comment of the according selection in the provided source.

Here is an example:
The Use Case is "I have the company Amazon which has 50 employees. These employees should own BMWs. These cars must in turn be manufactured by company AB."

A correct output for this would be:
Car (Fits for BMW)
A car is a wheeled, self-powered motor vehicle used for transportation.
Organization (Fits for Amazon)
An organization such as a school, NGO, corporation, club, etc.
Person (Fits for Employees and I)
A person (alive, dead, undead, or fictional).

Note, that Car is chosen over Vehicle, as it is the most fitting and accurate. Vehicle would be incorrect, but not accurate enough. Always choose the most accurate example.

Another example might be as such:
The Use Case is "I have a friend who like to fly with a plane, but it costs about 5.000€ to do so. Luckily, he just found a Joboffer which will pay him handsomely. He can also renovate his house!"
A correct output for this would be:
Person  (Fits for I and Friend)
A person (alive, dead, undead, or fictional).
Aircraft  (Fits for Plane)
An aircraft is a vehicle capable of atmospheric flight due to interaction with the air, such as buoyancy or lift.
JobPosting  (Fits for Joboffer)
A listing that describes a job opening in a certain organization.
House  (Fits for House)
A house is a building or structure that serves as living quarters for one or more families.
MonetaryAmount  (Fits for 5.000€)
A monetary value or range. This type can be used to describe an amount of money such as $50 USD.

Make sure your answers are consistent with your findings and name them as such. A Mercedes is a Car, not an Automotive, as Automotive doesnt exist in the provided list, but Car does and is the most fitting match.
If nouns occur multiple times, e.g., two different companies, do not provide redundant results but only one for "Organization".
Do not use any bold writing in your answer. Stay with normaly formated text. Your answer should only include the list as provided in the example.

Double check and work cronologically through all mentioned steps before providing your answer. Make once again sure to check if any more fitting descriptions are available, e.g. instead of "Place" for Europe, "Continent" would be more accurate. 

Here is the text to analyze:

{self.use_case}
Please double check your information. Is everything included? Is everything reflected appropiately and correctly within your provided answer? Make sure to remove redundancies in your answer. 
Also make sure that all answeres are also pulled from the provided source: https://schema.org/version/latest/schemaorg-current-https.ttl. Your answer should only contain the list and no further comments of yourself.
"""
        response_1 = self.client.ask(prompt_1)
        self.create_result_interface(response_1, prompt_1)
        self.current_step = 1  # Set current step to Step 1

    def process_next_step(self, prompt):
        """Process the next step based on the current state."""
        if self.current_step == 1:
            # Step 2: Extract properties
            formatted_response_1 = self.result_text.get("1.0", tk.END).strip()
            entities = re.findall(r'- (\w+):', formatted_response_1)
            classes_and_properties = {}

            prompt_2 = "Here are my results:\n"
            for entity in entities:
                entity_description = formatted_response_1.split(f"- {entity}: ")[1].split('\n')[0].strip()
                prompt_2 += f"Type: {entity}\n"
                prompt_2 += f"Description: {entity_description}\n"
                classes_and_properties[entity] = []

            prompt_2 += "\nPlease take the properties and expected types for each of these entities from the provided Use Case and the list you created in combination with Schema.org, without actually fetching the URLs. Format the output similarly to the Schema.org page for each entity:\n"
            for entity in entities:
                prompt_2 += f"- {entity}\n"

            prompt_2 += """
A Use Case could be "I have the company Amazon which has 50 employees, out of which one is my Friend Peter Müller, aged 27. These employees should own red BMWs." and a List provided by you created from this Use Case could be as follows:
Car
A car is a wheeled, self-powered motor vehicle used for transportation.
Organization
An organization such as a school, NGO, corporation, club, etc.
Person
A person (alive, dead, undead, or fictional).

An example format for a correct answer would be:

Type Person
Description A person (alive, dead, undead, or fictional).
Properties
- familyName: Family name. In the U.S., the last name of a Person. (Expected Type: Text)
- givenName: Given name. In the U.S., the first name of a Person. (Expected Type: Text)
- birthDate: Date of birth. . (Expected Type: Date)
- affiliation: An organization that this person is affiliated with. (Expected Type: Organization)
- owns: Products owned by the organization or person. (Expected Type: Product)

Type Organization
An organization such as a school, NGO, corporation, club, etc. Instances of Organization may appear as a value for the following properties.
Properties
- employee: Someone working for this organization. (Expected Type: Person)
- legalName: The official name of the organization, e.g. the registered company name. (Expected Type: Text)

Type Car
A car is a wheeled, self-powered motor vehicle used for transportation.
Properties
- color: The color of the product. (Expected Type: Text)
- manufacturer: The manufacturer of the product. (Expected Type: Organization)

As you can see, only properties which can be logically concluded from the use case are used. Once again, you have to abstract the description in the use case to the most logical property you can find on the according Schema-site for each individual Type.
You canot use a property for X, if you didnt find it for X on Schema.org. Do not cross-use different properties if they are not findable for that specific type.
If no properties or descriptions are provided within the Use Case, you can assume the most basic properties the specific Type could need, e.g. a Name or ID or anything which allows for a unique identification of the type.
"""
            response_2 = self.client.ask(prompt_2)
            self.create_result_interface(response_2, prompt_2)
            self.current_step = 2  # Set current step to Step 2

        elif self.current_step == 2:
            # Step 3: Generate SHACL document
            formatted_response_2 = self.result_text.get("1.0", tk.END).strip()
            entities = re.findall(r'- (\w+):', formatted_response_2)
            classes_and_properties = {}

            for entity in entities:
                properties = re.findall(r'- (\w+): (.*?)\n', formatted_response_2)
                for prop in properties:
                    classes_and_properties[entity] = [{
                        "name": prop[0],
                        "description": prop[1],
                        "path": prop[0].lower(),
                        "datatype": "xsd:string",
                        "minCount": 1,
                        "maxCount": 1
                    }]

            prompt_3 = f"""Here are the types and their properties:

{formatted_response_2}

Please generate a SHACL document that meets the following requirements:

- Include all types and their properties as described above.
- Use all necessary prefix declarations based on the types and properties included in the results. This could include prefixes for Schema.org, SHACL, XSD, and possibly others.
- The SHACL shapes should combine NodeShapes and PropertyShapes, similar to this example:

```turtle
ex:ExampleNodeShapeWithPropertyShapes
    a sh:NodeShape ;
    sh:targetClass ex:ExampleClass ;
    sh:property [
        sh:path ex:email ;
        sh:name "e-mail" ;
        sh:description "We need at least one email value" ;
        sh:datatype xsd:string ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] ;
    sh:property [
        sh:path ex:address ;
        sh:name "Address" ;
        sh:description "Physical address of the item" ;
        sh:class ex:PostalAddress ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
    ] .

Please analyze this SHACL document and make corrections where necessary. Ensure the following:

- All prefixes are correctly declared and used.
- The structure and syntax of NodeShapes and PropertyShapes are valid.
- Datatypes and expected classes align with Schema.org definitions.
- Add comments or explanations for corrections made.

Provide the corrected SHACL document in Turtle syntax.
"""
            response_3 = self.client.ask(prompt_3)
            self.create_result_interface(response_3, prompt_3)
            self.current_step = 3  # Set current step to Step 3

        elif self.current_step == 3:
            # Step 3: Close the program when "Satisfied" is clicked
            self.destroy()  # Directly close the program

if __name__ == "__main__":
    app = Application()
    app.mainloop()

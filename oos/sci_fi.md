# Sci-fi Feature Tool
    - A tool that facilitate creating a coherent science fiction universe

## Setup
    - The author's global settings before using the tool

    ### Goal
        - A narrative description of the scientific idea explored in the story.
    
    ### Story anchors
        - (Optional) consequences and implications that cannot be removed from the story 
    
    ### Story
        - Upload the draft manuscript or notes
    
    ### Hard Science
        - a description of the real science the author used as inspiration. 

## Initial Run

    ### LLM Analysis 
        - An LLM will analyze the setup parameters and research the Internet to find the science that best fits the author's intent and update the hard science to fit. 
        if there are multiple choices, the tool will provide an interactive approach.

## Exploratory Run(s)

    ### Refine Science
        - Using an LLM the author can explore the scientific implicaitons of a story topic or theme.
        - The LLM will document the conversation and summarize it so that it can be added to the context of future discussion
        - When topics and themes are changed/removed, the science files containing that context and/or summaries are updated 
    ## Features
        - This project is a science fiction writer’s assistant:
          - It needs to be able to extract the author's draft .rtf text from web, pdf and document formats (e.g. docx, odt, etc.)
          - The app does not replicate the functionality of writing tools where the rtf is extracted.
          - The tool helps refine the author’s draft while rigorously exploring the underlying science using this process: 
            - By analyzing the draft and identifying themes and topics that dominate the draft text defining a ground truth using a sequence of note cards.
            - Iteratively removes old ideas (note cards) as the author's vision evolves.  
            - Keeps a research log of the real science investigated by the LLM, iteratively refining and updating the scientific focus as the story evolves.
            - In a nutshell, the tool starts with the original draft and a set of LLM generated topics it discovered while reading it, then iteratively moving from the draft as it replaces deprecated ideas with more coherent ones. 
              - This applies to the research log as irrelevant science is deleted from the context.
          - The goal is not simply to make the fiction scientifically plausible. The narrative should engage with real problems and open questions in the relevant scientific and engineering fields,
           using speculative fiction to explore potential approaches, consequences, and implications.
          - The story should keep the science grounded so it doesn't feel like fantasy genre.
          - The science should be plausible: once the rules are established the story MUST stay consistent.
    
    ### Guardrails
        1. The tool checks for a gross mismatch between the stated goals and the uploaded draft after the initial run:
            - If there is a mismatch after the initial run the tool will do the following:
                - If story anchors are present any matching story topics that are considered inconsistent will be marked as consistent.
                - Rerun the analysis. If the mismatch is resolved proceed to guardrail #2
            - If the mismatch still exists:
                - Start an interactive LLM chat with the author and address the mismatch
        2. If there are no gross inconsistencies between the science fiction goal and the manuiscript:
            - start an interactive LLM chat
            - Confirm with the writer you have properly understood the science to be explord 
            - After performing researching the Propose which real scientific domains match the story
            - iterate through the choices until the real science to be tackled is fleshed out

 

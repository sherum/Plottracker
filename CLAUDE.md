# Genre Writer Project

## Premise
    - An author's draft manuscript is a chaotic mix of ideas with a common thread that is obfuscated by the noise of incomplete ideas and the friction of language.
    - A great story is a draft with the noise removed and the ideas refined into a coherent narrative.

## Objective
    - Build a generic document extractor that can consume any human-readable source such as web editors, .docx, .pages, .pdf, etc..., and retain the encoding.
    - This app is the designed to be extended with genre specific add-ins (sci-fi, mystery, detective, romance, etc...)

## Features
    ### Ingest
    - The tool treats docs in draft_scripts/ as draft manuiscripts and story_notes/ as writing notes for analysis
    - On first run:
        - the tool is pointed to the source(s) for the manuiscript (e.g an URL, a local folder, Google Docs)
        - the tool asked locations of writer's notes, if any.
    - The author can designate any encoding to have special semeantic meaning and how it should analyzed differently.
    - The tool performs an initial scan of the documents and notes:
        - it creates topics from passages in the story that move the plot forward and:
            - stores them in a database
            - ordered from start-to-finish i.e. topic 1 is one or near page 1.
        - it creates themes from similar passages:
            -  A collection of similar topics is a theme
            - Themes link topics together
    ### Database viewer
    - Topics and themes can be viewed as notecards
    - Notecards:
        - show summaries of their topic or theme
        - efficiently use screen space 
        - have an intuitive design for editing, saving and navigating between topics/themes 
    ### Plot viewer
    - Is a UI component that organizes the topics for the entire story into a three act structure: opening, conflict, climax
    - A story can have parallel secondary plot(s)  
    - Each act contains a collection of topics
    - Themes can be promoted to subplots
    - Topics can be added to and removed from subplots    
    - Each act can be recursively decomposed into three act subplots, sub-subplots:
        - A trilogy story is a story with each act represented by a novel
        - Each act/novel has it's own three act stucture 
    ### Review
    - The review feature is to remove noise from the context so LLM calls never use old data
    - The manuiscript and notes can be modifed
    - Topics and themes can be created, modified and excluded.
    - When a change happens, the author can reanalyze the corpus to update topics, themes and the Plotview.
    ### GENRE EXTENSION
    - Create guide for developing genre specific extensions including a CLAUDE.md template in the 'docs' folder

## AI Sidekick
    - The AI can answer questions about the story
    - Rephrase dialog using the character's voice
    - Current provider: Gemini 3.7 Flash via OpenRouter/LiteLLM (model `google/gemini-3.7-flash`), using OPENROUTER_API_KEY
    - Future implementation: Cerebras as the inference provider, as described in .claude/skills/cerebras/SKILLS.md

## Technical design
    - Ignore the files in the 'oos' (out of scope) folder
    - the entire product should be packaged into a Docker container. 
    - The backend should be in backend/ and be a uv project, using FastAPI.
    - The front end should be in frontend/ 
    - Consider statically building the front end and serving it via FastAPI, if that will work.
    - There should be scripts in scripts/ for
      -  scripts/start-mac.sh # start
      -  scripts/stop-mac.sh # stop 
    - Backend available at http://localhost: 8000
 

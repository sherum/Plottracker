## Step 1:
    - Build a document extractor that can read text in .rtf formatting from any human-readable source such as web editors, .docx, .pages, .pdf, etc....
 
## Step 2:
    - Build an LLM topic extractor that can read the draft, identify topics and themes that dominate the draft text and store them in a database:
     - Topics are specific narrative passages that empiracally move the plot forward
     - Themes are a collection of semantically related topics (e.g. romance, faith, self-discovery)
    - Allow for semantically meaningful formatting and keep it distinct from topics/themes (e.g. italic: a Shakespearean aside doesn't inform characters; dream sequences don't add people/things to a scene).
    - Build a plot viewer that:
        - is generated from the topics and themes
        - uses a set-up, conflict and resolution sequential three-part nested structure
        - The structure is applied to super-plots, plots, subplots, sub-subplots (i.e. trilogy, novel, act, section)
        - Topics link to specific narrative elements
        - Themes link discontiguous plot elements.
        - Easily navigates into and out of the nested structure,
        - Higher level structures display themes not topics to avoid overwhelming the author.
    
 ## Step 3:
    - Build an editor dashboard that allows the author to review topics and refine themes stored in the database which update the plot viewer
    - Topics and themes that are excluded or replaced:
     - are removed from the LLM context
     - Refine themes with the new context

## Step 4:
    - Build a relationship matrix that shows the topics where characters interacted in a graphical way.
    - Create an AI side kick that can:
      - rewrite a passage for to achieve a specific intent
      - answer a question about a passage
      - explain a process related to the passage

## Step 5:
    - Build the genre editor
    - @sci_fi.md



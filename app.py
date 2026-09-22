import streamlit as st
from openai import OpenAI
from PyPDF2 import PdfReader
from docx import Document

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

#Define the maximum characters a user can input and the maximum API calls they can make.
MAX_CHARACTERS = 100_000
MAX_SUMMARIES = 5

#If Session State doesn't already contain something called "summary", create it and initially give it the value None.
if "summary" not in st.session_state:
    st.session_state.summary = None

#If Session State doesn't already contain something called "summary_count", create it and give it an initial value of 0.
if "summary_count" not in st.session_state:
    st.session_state.summary_count = 0

st.set_page_config(
    page_title="AI Text Summarizer",
    page_icon="📝"
)

st.title("AI Text Summarizer")

st.markdown(
    "Paste text or upload a document to generate a concise AI-powered summary."
)

#Give the user the option to choose between Pasting Text or Uploading a Document, and switch between the 2.
input_method = st.radio(
    "Choose an input method:",
    ["Paste Text", "Upload Document"],
    horizontal=True
)

#Allow the user to input text to summarize if they choose that option.
if input_method == "Paste Text":
    text = st.text_area(
        "Text to summarize:",
        height=300,
        placeholder="Paste your text here..."
    )
    text_to_summarize = text

#Allow the user to upload a file to summarize if they choose that option.
elif input_method == "Upload Document":
    uploaded_file = st.file_uploader(
        "Upload a document:",
        type=["txt", "pdf", "docx"]
    )

    uploaded_text = ""

    # If an uploaded file exists, start processing it in order to read and extract its text.
    if uploaded_file is not None:
        try:
            with st.spinner("Reading document..."):

                #Read in the file if it's a text-type
                if uploaded_file.type == "text/plain":
                    uploaded_text = uploaded_file.read().decode("utf-8")

                #Read in the file if it's a pdf-type
                elif uploaded_file.type == "application/pdf":
                    reader = PdfReader(uploaded_file)

                    #Loop through the individual pages of the pdf.
                    for page in reader.pages:
                        #Extract the text from each page.
                        page_text = page.extract_text()

                        #Check if the particular page even contains extractable text.
                        if page_text:
                            #Take the text extracted from this page and add it to all the text we've already extracted.
                            uploaded_text += page_text + "\n"

                #Read in the file if it's a Word-type.
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    document = Document(uploaded_file)
                    #Take the text from each paragraph and add it to the text we've already extracted.
                    for paragraph in document.paragraphs:
                        if paragraph.text:
                            uploaded_text += paragraph.text + "\n"
            
                #Display a warning if no text is detected in the uploaded file, and stop the current Streamlit Execution.
                if not uploaded_text.strip():
                    st.warning(
                        "No readable text was found in this document. "
                        "Please upload a text-based TXT, PDF or Word document."
                    )
                    st.stop()

        #Display an error if the uploaded file is corrupted or invalid, and stop the current Streamlit Execution.
        except Exception as e:
            st.error(f"Unable to read the uploaded document: {e}")
            st.stop()

    #Finally, set the text-to-summarize equal to the processed text.
    text_to_summarize = uploaded_text

#Determine if the inputted text is over our defined limit, and display a warning if it is.
input_too_large = len(text_to_summarize) > MAX_CHARACTERS
if input_too_large:
    st.warning(
        "This content is too large to summarize. "
        "Please use text containing 100,000 characters or fewer."
    )

summary_length = st.selectbox(
    "Summary length:",
    ["Short (under 500 words)", "Medium (under 1000 words)", "Detailed (under 2000 words)"]
)

#Create 2 columns for the "Generate Summary" button and the API usage Display Message
button_col, usage_col = st.columns([1, 3])

with button_col:
    generate_button = st.button("Generate Summary")

with usage_col:
    st.write("")
    st.caption(
        f"Demo usage: {st.session_state.summary_count}/{MAX_SUMMARIES} summaries"
    )

if generate_button:
    st.session_state.summary = None
    #Display a warning if there is no text to summarize
    if not text_to_summarize.strip():
        st.warning("Please enter some text or upload a file to summarize.")
    #Display a warning if the text length is over our defined limit.
    elif input_too_large:
        st.error(
            "The content exceeds the 100,000-character limit."
        )
    #Display a warning if the number of API calls has reached our defined limit.
    elif st.session_state.summary_count >= MAX_SUMMARIES:
        st.warning(
            "Demo limit reached. You can generate up to 5 summaries per session."
        )
    else:
        try:
            with st.spinner("Generating summary..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful text summarization assistant."
                        },
                        {
                            "role": "user",
                            "content": f"""
                            Summarize the following text clearly and concisely.

                            Condense the content while preserving the key information and important ideas. Be sure to include any key formulas in technical content.

                            Write the summary directly. Try to avoid referring to the source material with phrases such as "the text" or "the paper" or "the book".
                            Just summarize the actual content itself.

                            Do not add information that is not present in the original text.

                            Summary length: {summary_length}
                            Text:
                            {text_to_summarize}
                            """
                        }
                    ]
                )

                st.session_state.summary = response.choices[0].message.content
                st.session_state.summary_count += 1
                st.rerun() # Re-run the script in order to add 1 to the summary counter

        except Exception as e:
            st.error(f"Unable to generate the summary: {e}")

#If the Summary exists in Session State, display it and allow the user to download it.           
if st.session_state.summary:
    st.subheader("Summary")
    st.write(st.session_state.summary)

    st.download_button(
        label="Download Summary",
        data=st.session_state.summary,
        file_name="summary.txt",
        mime="text/plain"
    )


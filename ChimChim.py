import imaplib
import email
import pandas as pd
import nltk
from io import BytesIO
from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer
import fitz  # PyMuPDF
import streamlit as st

# Download NLTK resources
nltk.download('punkt')

# Streamlit app title
st.title("Automate2PDF: Simplified Data Transfer")

# Create input fields for the user, password, and start date
user = st.text_input("Enter your email address")
password = st.text_input("Enter your email password", type="password")
start_date = st.text_input("Enter the start date (YYYY-MM-DD) for PDF summarization")

if st.button("Fetch and Display PDF Summaries"):
    try:
        # URL for IMAP connection
        imap_url = 'imap.gmail.com'

        # Connection with GMAIL using SSL
        with imaplib.IMAP4_SSL(imap_url) as my_mail:
            # Log in using user and password
            my_mail.login(user, password)

            # Select the Inbox to fetch messages
            my_mail.select('inbox')

            # Define the key and value for email search
            key = 'SINCE'
            value = start_date  # Use the user-specified start date to search
            _, data = my_mail.search(None, key, value)

            mail_id_list = data[0].split()

            info_list = []

            # Iterate through messages
            for num in mail_id_list:
                typ, data = my_mail.fetch(num, '(RFC822)')
                msg = email.message_from_bytes(data[0][1])

                for part in msg.walk():
                    if part.get_content_type() == 'application/pdf':
                        # Extract email date
                        email_date = msg["Date"]

                        # Extract text from PDF using PyMuPDF
                        pdf_bytes = part.get_payload(decode=True)
                        pdf_text = extract_text_from_pdf(pdf_bytes)

                        # Split content into chapters (example: assuming "Chapter" is used as a separator)
                        chapters = pdf_text.split("Chapter")

                        # Summarize each chapter
                        for i, chapter in enumerate(chapters):
                            # Skip empty chapters
                            if not chapter.strip():
                                continue

                            # Summarize the chapter content
                            parser = PlaintextParser.from_string(chapter, Tokenizer('english'))
                            summarizer = LsaSummarizer()
                            summary = summarizer(parser.document, 3)
                            summarized_text = ' '.join(str(sentence) for sentence in summary)

                            info = {"Chapter": i + 1, "Summarized Chapter Content": summarized_text, "Received Date": email_date}
                            info_list.append(info)

            # Display the summarized content
            for info in info_list:
                st.subheader(f"Chapter {info['Chapter']} - Received Date: {info['Received Date']}")
                st.write(info["Summarized Chapter Content"])

    except Exception as e:
        st.error(f"An error occurred during IMAP connection: {str(e)}")

import io
import re
import time
from typing import Union

# from pypdf import PdfReader, PdfWriter
import fitz

from models import Chunk


class PDFService:
    """
    PDFService
    """

    @staticmethod
    def pdf_to_text(
        stream_buffer: io.BytesIO, start_page=1, end_page=None
    ) -> list[str]:
        """
        Loads the PDF (stream_buffer) and extracts all text
        """

        doc = fitz.open("pdf", stream_buffer)
        total_pages = doc.page_count

        if end_page is None:
            end_page = total_pages

        text_list = []

        for i in range(start_page - 1, end_page):
            text = doc.load_page(i).get_text("text")
            text = PDFService.preprocess(text)
            text_list.append(text)

        doc.close()
        return text_list

    @staticmethod
    def preprocess(text: str) -> str:
        """
        Fixes text using reg, replaces line breaks with spaces
        """
        text = text.replace("\n", " ")
        text = re.sub(r"\s+", " ", text)
        return text

    @staticmethod
    def text_to_chunks(texts: str, word_length=150, start_page=1) -> list[Chunk]:
        """
        Converts text to chunks
        """

        # print(texts)
        # time.sleep(0.1)

        text_toks = [t.split(" ") for t in texts]

        chunks = []

        for idx, words in enumerate(text_toks):
            for i in range(0, len(words), word_length):
                chunk = words[i : i + word_length]
                if (
                    (i + word_length) > len(words)
                    and (len(chunk) < word_length)
                    and (len(text_toks) != (idx + 1))
                ):
                    text_toks[idx + 1] = chunk + text_toks[idx + 1]
                    continue
                chunk = " ".join(chunk).strip()
                # chunk = f"[{idx+start_page}]" + " " + '"' + chunk + '"'
                # chunks.append(chunk)

                chunks.append(
                    Chunk(chunk, idx + start_page)
                    # {
                    #     "text": chunk,
                    #     "pageNum": idx + start_page,
                    # }
                )
        return chunks


# def main():
#     filepath = "/Users/daniellombardi/Downloads/Conhecimento_do_Sistema_V55903_A01.pdf"

#     in_obj0 = None
#     # Use a context manager to open the file in binary mode for reading
#     with open(filepath, "rb") as fh:
#         # Read the contents of the file
#         in_obj0 = io.BytesIO(fh.read())

#     filepath = (
#         "/Users/daniellombardi/Downloads/Resource_discovery_techniques_in_the_int.pdf"
#     )

#     in_obj1 = None
#     # Use a context manager to open the file in binary mode for reading
#     with open(filepath, "rb") as fh:
#         # Read the contents of the file
#         in_obj1 = io.BytesIO(fh.read())

#     # end = PDFService.merge_pdfs_from_objs([in_obj0, in_obj1])
#     text = PDFService.pdf_to_text(in_obj0)
#     chunks = PDFService.text_to_chunks(text)
#     print(chunks)

#     # with open("output.pdf", "wb") as f:
#     #     f.write(end.getbuffer())


# if __name__ == "__main__":
#     main()

# Functions for preprocessing, cleaning and splitting books for creating a dataset 

import re
import pandas as pd

"""
# As some books are formatted differently, I need to have several options for identification the chapters, e.g:
PROLOGUE
CHAPTER I. I GO TO STYLES
I  DR. SHEPPARD AT THE BREAKFAST TABLE
I The Adventure of “The Western Star”
CHAPTER I.   THE YOUNG ADVENTURERS, LTD.
1 A Fellow Traveller
XVIII JIMMY'S ADVENTURES
1. The Man with the White Hair
CHAPTER I
11. A CHESS PROBLEM
1 ANTHONY CADE SIGNS ON
*       *       *       *       *
"""

chapter_regex = re.compile(
    r"^("
    r"PROLOGUE$|"
    r"CHAPTER\s+[IVXLCDM]+\.\s+[^\n]+|"    # CHAPTER I. Title
    r"CHAPTER\s+[IVXLCDM]+$|"              # CHAPTER I
    r"[IVXLCDM]{1,4}\s{1,}[A-Z][^\n]+|"    # I Title
    r"\d+\.\s+[A-Z][^\n]+|"                # 1. Title
    r"\d+\s+[A-Z][^\n]+|"                  # 1 Title
    r"\*+(\s+\*+)+$"                       # * * * * *
    r")$",
    re.MULTILINE
)


def delete_metadata(book):
  cleaned_book = "\n".join([line.strip() for line in book.split("\n") if line.strip()])
  lines = cleaned_book.split("\n")
  start_idx = 0
  end_idx = 0
  for i, line in enumerate(lines):
    if "*** START OF THE PROJECT GUTENBERG EBOOK" in line:
      start_idx = i + 1
    if "*** END OF THE PROJECT GUTENBERG EBOOK" in line:
      end_idx = i
      break
  book_wo_metadata = "\n".join(lines[start_idx:end_idx])
  return book_wo_metadata

def contains_newline(text):
    return '\n' in text

def find_chapters(book_wo_metadata, chapter_regex):
  seen = []
  chapter_list = []
  matches = re.findall(chapter_regex, book_wo_metadata)
  matches = [m[0] for m in matches if not contains_newline(m[0])]
  for chapter in matches:
    if chapter not in seen:
        seen.append(chapter)
        chapter_list.append(chapter)
  return chapter_list

def find_main_book_content(book_wo_metadata, chapter_list):
    lines = book_wo_metadata.split("\n")
    found_contents = False
    contents_start_idx = 0
    contents_end_idx = 0
    book_end = len(lines)
    for i, line in enumerate(lines):
        if "Contents" in line or "CONTENTS" in line:
            contents_start_idx = i + 1
            found_contents = True
        if line.strip() == chapter_list[-1]:  #last chapter in the list and conen table
            contents_end_idx = i
            book_start = contents_end_idx + 1
            break
    if not found_contents:  #if no "Contents" section found (true for some books)
        for i, line in enumerate(lines):
            if line.strip() in chapter_list:
                contents_start_idx = i
                book_start = contents_start_idx +1
                break
    main_content_slice = slice(book_start, book_end) #creating out of a tuple with indeces a slice for a list
    book_main_lines = lines[main_content_slice]
    book_main_content = "\n".join(book_main_lines)
    return book_main_content

def extract_chapters_and_paragraphs(text, chapters_list, book_id=1, book_title="Unknown Title", paragraph_num = 5):
    lines = text.split("\n")

    # Step 1: Find indexes of each chapter title in the lines
    chapter_indices = []
    for i, line in enumerate(lines):
        if line in chapters_list:
            chapter_indices.append((line, i))

    # Step 2: Build chapter blocks
    chapters = []
    for idx, (chapter_title, start_idx) in enumerate(chapter_indices):
        end_idx = chapter_indices[idx + 1][1] if idx + 1 < len(chapter_indices) else len(lines)
        chapter_lines = lines[start_idx + 1:end_idx]
        chapter_text = "\n".join(chapter_lines).strip()

        chapters.append({
            "chapter_title": chapter_title,
            "chapter_text": chapter_text
        })

    final_rows = []

    for chap_id, chap in enumerate(chapters, 1):
      # Remove newlines and split text into words
      words = chap["chapter_text"].replace('\n', ' ').split()
      total_words = len(words)

      # Compute base chunk size
      chunk_size = total_words // paragraph_num
      remainder = total_words % paragraph_num

      start = 0
      for para_id in range(1, paragraph_num + 1):
        # Distribute the remainder across first few paragraphs
        end = start + chunk_size + (1 if para_id <= remainder else 0)
        para_words = words[start:end]
        paragraph_text = " ".join(para_words)

        final_rows.append({
            "book_id": book_id,
            "book_title": book_title,
            "chapter_id": chap_id,
            "chapter_title": chap["chapter_title"],
            "paragraph_id": para_id,
            "paragraph_text": paragraph_text
        })

        start = end

    return pd.DataFrame(final_rows)
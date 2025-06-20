# summarizer.py
from io import BytesIO
import PyPDF2
import json
from datetime import datetime

from anthropic import Anthropic  # Ensure anthropic package is installed

# Configuration variables for summarization
# API_KEY will be passed as parameter to functions that need it
MODEL_NAME = "claude-3-sonnet-20240229"
MAX_TOKENS = 1024
TARGET_SCORE = 9 
MAX_ITERATIONS = 6

REVIEWER_PROMPT_1 = (
    "For this conversation, you are Dr. Zhou, a practicing physician with 8 years experience at a major 三甲 hospital in Beijing, China. "
    "You are in the urology department, and you primarily treat prostate and bladder cancer patients. You are too busy to lead independent research, "
    "but you are curious about research in your area, and you have co-authored a few peer-reviewed papers with academic collaborators.\n"
    "You have come across the following blog post about a recent scientific research article. You are also fluent in English, so your reviews must be in english, "
    "please rate it from 0 to 10 on each of the following criteria, before giving it an overall score. Use the FULL RANGE of scoring, with 5 being average, "
    "and 7 being something you enjoyed, 8 being something you would forward to a colleague, and 10 being something you would save to re-read again in the future. "
    "The scoring criteria are: (a) Written in an interesting and engaging way, (b) relevant to your clinical and research interests, "
    "(c) inspiring approach for potential research collaborations, and (d) trustworthy and credible."
)
REVIEWER_PROMPT_2 =(
    "For this conversation, you are Dr. Li, a practicing physician with 6 years experience at a major 三甲 hospital in Shanghai, China. "
    "You are in the oncology department, specializing in precision medicine for various cancer types, including prostate and lung cancer. You are too busy to lead independent research, "
    "but you are curious about research in your area, and you have co-authored a few peer-reviewed papers with academic collaborators.\n"
    "You have come across the following blog post about a recent scientific research article. You are also fluent in English, so your reviews must be in english, "
    "please rate it from 0 to 10 on each of the following criteria, before giving it an overall score. Use the FULL RANGE of scoring, with 5 being average, "
    "and 7 being something you enjoyed, 8 being something you would forward to a colleague, and 10 being something you would save to re-read again in the future. "
    "The scoring criteria are: (a) Written in an interesting and engaging way, (b) relevant to your clinical and research interests, "
    "(c) inspiring approach for potential research collaborations, and (d) trustworthy and credible."
)


INITIAL_PROMPT = (
    "Write a generally accessible blog post about the following scientific paper that is engaging and interesting, "
    "focusing on the key findings and clinical implications related to RNA markers and more: Keep it between 500-800 words."
)

def pdf_to_text_file(file_bytes):
    pdf_file = BytesIO(file_bytes)
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    num_pages = len(pdf_reader.pages)
    text_output = ""
    for page_num in range(num_pages):
        page = pdf_reader.pages[page_num]
        text = page.extract_text() or ""
        text_output += text
        if page_num < num_pages - 1:
            text_output += f"\n\n--- Page {page_num + 1} ---\n\n"
    return text_output

def ask_claude(prompt, question, api_key):
    client = Anthropic(api_key=api_key)
    full_message = f"{prompt}\n\nQuestion: {question}"
    try:
        message = client.messages.create(
            model=MODEL_NAME,
            max_tokens=MAX_TOKENS,
            messages=[{"role": "user", "content": full_message}]
        )
        return message.content[0].text
    except Exception as e:
        return f"Error occurred: {str(e)}"

def parse_scores(response):
    try:
        lines = response.split("\n")
        scores = []
        for line in lines:
            if any(criterion in line.lower() for criterion in ['(a)', '(b)', '(c)', '(d)', 'overall score']):
                numbers = [word.strip(":/") for word in line.split() if ("/" in word or word.replace('.', '').isdigit())]
                for num in numbers:
                    if "/" in num:
                        numerator = float(num.split("/")[0])
                        scores.append(numerator)
                    elif 0 <= float(num) <= 10:
                        scores.append(float(num))
        return sum(scores[:-1]) / len(scores[:-1]) if len(scores) > 1 else (scores[0] if scores else 0)
    except Exception as e:
        print(f"Error parsing scores: {e}")
        return 0

def improve_prompt(feedback1, feedback2, current_prompt, api_key):
    prompt_improvement_request = (
        "You are an expert prompt engineer. Given the following prompt which generates a blog post summary, and feedback from two physicians reading this blog post, please generate an improved version of the prompt that will address the critique:\n\n"
        f"Original Prompt:\n{current_prompt}\n\n"
        f"Feedback1:\n{feedback1}\n\n"
        f"Feedback2:\n{feedback2}\n\n"
        "Please provide an improved version of the prompt that will generate a better blog post for between 500-800 words."
    )
    return ask_claude("", prompt_improvement_request, api_key)
DESIRED_KEYWORD = "title"  # We'll search for "Title" (case-insensitive)

def format_summary(text, iteration):
    """
    Format the generated summary text:
      - Remove the first line if it starts with "Here" (case-insensitive).
      - Find the first occurrence (case-insensitive) of "Title" and delete everything before it.
      - Split the remaining text into lines.
      - If the new first line still starts with "Here" (in rare cases), remove that line again.
      - Assume the first remaining line is of the form "Title: <generated title>".
      - Bold the sentence after the colon using <b> tags.
      - Place the remainder of the summary on a new line.
      - Prefix with "Summary {iteration}:".
    """
    # 1) First, split text into lines to remove any leading "Here"-based line
    lines = text.splitlines()

    # If the first line starts with "here", remove it
    while lines and lines[0].strip().lower().startswith("here"):
        lines.pop(0)

    # Rejoin to continue the rest of the logic
    text = "\n".join(lines)

    # 2) Find first occurrence of "title" (case-insensitive)
    idx = text.lower().find(DESIRED_KEYWORD)
    if idx == -1:
        # If "Title" is not found, just return the text (but we've already removed "Here" lines)
        return f"Summary {iteration}:\n{text}"

    # Delete everything before the first occurrence of "Title"
    text = text[idx:]

    # 3) Split the remaining text into lines again
    lines = text.splitlines()

    # If the first line starts with "here", remove it (in case the shift caused a new "Here" line)
    while lines and lines[0].strip().lower().startswith("here"):
        lines.pop(0)

    # 4) Process lines if any remain
    if lines:
        # Assume the first line is "Title: <generated title>"
        first_line = lines[0]
        colon_index = first_line.find(":")
        if colon_index != -1:
            title_text = first_line[colon_index+1:].strip()
        else:
            title_text = first_line.strip()

        # Bold the title using <b> tags.
        bold_title = "<b>" + title_text + "</b>"

        # The remaining text (if any) follows on new lines.
        remaining_text = "\n".join(lines[1:]).strip()

        # Return the formatted summary
        return f"Summary {iteration}:\n{bold_title}\n{remaining_text}"
    else:
        return f"Summary {iteration}:\n"
def summarization_stream(pdf_text, api_key):
    """
    Run the summarization process on the given pdf_text and yield JSON messages in real time.
    Each JSON message has a "type" (e.g., "score", "blog", "prompt", or "log") and a "message".
    The blog messages are formatted using format_summary(), which removes any unwanted preamble
    and bolds the title (detected from the first occurrence of "Title") properly.
    """
    import json  # Ensure json is imported
    yield json.dumps({"type": "log", "message": "Running summarization process..."}) + "\n"
    
    # Set the initial prompt and yield it immediately.
    current_prompt = INITIAL_PROMPT
    yield json.dumps({"type": "prompt", "message": f"Prompt 1: {current_prompt}"}) + "\n"
    
    txt_content = pdf_text
    iteration = 1

    # Generate the summary for iteration 1 and yield it.
    current_summary = ask_claude(current_prompt, txt_content, api_key)
    yield json.dumps({"type": "blog", "message": format_summary(current_summary, iteration)}) + "\n"
    
    # Get review responses and calculate the initial score.
    review_response_1 = ask_claude(REVIEWER_PROMPT_1, current_summary, api_key)
    current_score_1 = parse_scores(review_response_1)
    review_response_2 = ask_claude(REVIEWER_PROMPT_2, current_summary, api_key)
    current_score_2 = parse_scores(review_response_2)
    current_score = (current_score_1 + current_score_2) / 2
    yield json.dumps({"type": "score", "message": f"Score {iteration}: {current_score}"}) + "\n"
    
    # Loop for subsequent iterations (iteration 2 and beyond) if needed.
    while current_score < TARGET_SCORE and iteration < MAX_ITERATIONS:
        iteration += 1
        # Update the prompt using the feedback.
        current_prompt = improve_prompt(review_response_1, review_response_2, current_prompt, api_key)
        yield json.dumps({"type": "prompt", "message": f"Prompt {iteration}: {current_prompt}"}) + "\n"
        
        # Generate a new summary based on the updated prompt.
        current_summary = ask_claude(current_prompt, txt_content, api_key)
        yield json.dumps({"type": "blog", "message": format_summary(current_summary, iteration)}) + "\n"
        
        # Recalculate review responses and new score.
        review_response_1 = ask_claude(REVIEWER_PROMPT_1, current_summary, api_key)
        current_score_1 = parse_scores(review_response_1)
        review_response_2 = ask_claude(REVIEWER_PROMPT_2, current_summary, api_key)
        current_score_2 = parse_scores(review_response_2)
        current_score = (current_score_1 + current_score_2) / 2
        yield json.dumps({"type": "score", "message": f"Score {iteration}: {current_score}"}) + "\n"
        
        if current_score >= TARGET_SCORE:
            yield json.dumps({"type": "log", "message": "Target score achieved!"}) + "\n"
            break
    
    # Yield final score and log message.
    yield json.dumps({"type": "score", "message": f"Final Score: {current_score}"}) + "\n"
    yield json.dumps({"type": "log", "message": "Summarization process completed."}) + "\n"

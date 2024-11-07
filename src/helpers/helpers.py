import re
import pandas as pd

def extract_not_optimal_ideas(text):
    # Regular expression to match each Not Optimal Idea and Reason
    pattern = re.compile(
        r"'Not Optimal Idea': '(.*?)',\n\s*'Reason': '(.*?)'",
        re.DOTALL
    )

    # Find all matches in the provided text
    matches = pattern.findall(text)

    # Prepare extracted data
    not_optimal_ideas = []
    for match in matches:
        idea, reason = match
        not_optimal_ideas.append({
            "Not Optimal Idea": idea.strip(),
            "Reason": reason.strip()
        })

    return not_optimal_ideas

# Function to extract Sub-Optimal Ideas from text
def extract_suboptimal_ideas(text):
    # Regular expression to match each Sub-Optimal Idea and Reason
    pattern = re.compile(
        r"'Sub-Optimal Idea': '(.*?)'\n\s+'Reason': '(.*?)'",
        re.DOTALL
    )

    # Find all matches in the provided text
    matches = pattern.findall(text)

    # Prepare extracted data
    suboptimal_ideas = []
    for match in matches:
        idea, reason = match
        suboptimal_ideas.append({
            "Sub-Optimal Idea": idea.strip(),
            "Reason": reason.strip()
        })

    return suboptimal_ideas

def extract_not_optimal_ideas(text):
    """
    Extract 'Not Optimal' ideas and their reasons from a given text using regex.
    
    Parameters:
        text (str): Input text containing ideas and reasons.
    
    Returns:
        list of dict: List containing extracted ideas and reasons.
    """
    pattern = re.compile(r"'Not Optimal Idea': '(.*?)',\n\s*'Reason': '(.*?)'", re.DOTALL)
    matches = pattern.findall(text)
    return [{"Not Optimal Idea": idea.strip(), "Reason": reason.strip()} for idea, reason in matches]

# ### Save extracted ideas to an Excel file
def save_ideas_to_excel(ideas, file_path='GeneratedVariants.xlsx', sheet_name='Sheet1'):
    """
    Save extracted ideas to an Excel file.
    
    Parameters:
        ideas (list of dict): List of ideas to save.
        file_path (str): Path to the Excel file.
        sheet_name (str): Name of the sheet to append the data to.
    """
    # Prepare the DataFrame from ideas
    df = pd.DataFrame([{
        "Idea": idea["Not Optimal Idea"],
        "Task": "Not Optimal",
        "Reason": idea["Reason"],
        "Cost": "",
        "Feedback": "",
        "Status": "Not Optimal"
    } for idea in ideas])

    # Append data to an existing Excel file
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='a', if_sheet_exists='overlay') as writer:
        df.to_excel(writer, sheet_name=sheet_name, index=False, header=False, startrow=writer.sheets[sheet_name].max_row)
    
    print(f"Not Optimal Ideas successfully appended to {file_path}")

# ## Evaluation Function for Ideas and MVPs
# ### Load Excel file into a DataFrame
def load_excel_to_dataframe(file_path):
    """
    Load an Excel file into a pandas DataFrame.
    
    Parameters:
        file_path (str): Path to the Excel file.
    
    Returns:
        pd.DataFrame: DataFrame containing the data from the Excel file.
    """
    return pd.read_excel(file_path)


def extract_business_ideas(response_text):
    # Define regex patterns to match the three types of ideas
    optimal_pattern_number = (
        r"\*\*Optimal Idea \d+\*\*: (.*?)\n- \*\*Reason\*\*: (.*?)(?=\n\n|\Z)"
    )
    mvp_pattern = r"\d+\.\s\*\*Optimal Idea\*\*:\s(.*?)\n- \*\*Reason\*\*: (.*?)\n- \*\*Cost\*\*: (.*?)\n- \*\*Feedback\*\*: (.*?)(?=\n\d+\.|\Z)"

    persona_pattern = r"\*\*Option ([A-Z])\*\*\n• Gender: (.*?)\n• Age: (.*?)\n• Region: (.*?)\n• Interests: (.*?)\n- \*\*Feedback\*\*: (.*?)(?=\n\*\*Option|\Z)"

    optimal_pattern = r"\*\*Optimal Idea\*\*: (.*?)\n- \*\*Reason\*\*: (.*?)\n- \*\*Feedback\*\*: (.*?)(?=\n\n|\Z)"
    suboptimal_pattern = r"\*\*Suboptimal Idea\*\*: (.*?)\n- \*\*Reason\*\*: (.*?)\n- \*\*Feedback\*\*: (.*?)(?=\n\n|\Z)"
    not_optimal_pattern = r"\*\*Not Optimal Idea\*\*: (.*?)\n- \*\*Reason\*\*: (.*?)\n- \*\*Feedback\*\*: (.*?)(?=\n\n|\Z)"
    persona_matches = re.findall(persona_pattern, response_text, re.DOTALL)
    # Extract using regular expressions
    optimal_matches_number = re.findall(
        optimal_pattern_number, response_text, re.DOTALL
    )
    optimal_match = re.search(optimal_pattern, response_text, re.DOTALL)
    suboptimal_match = re.search(suboptimal_pattern, response_text, re.DOTALL)
    not_optimal_match = re.search(not_optimal_pattern, response_text, re.DOTALL)
    mvp_matches = re.findall(mvp_pattern, response_text, re.DOTALL)

    # Store results in a dictionary
    results = {"Optimal Ideas": [], "Persona Options": []}
    for match in persona_matches:
        option = {
            "Option": match[0],
            "Gender": match[1],
            "Age": match[2],
            "Region": match[3],
            "Interests": match[4],
            "Feedback": match[5].strip(),
        }
        results["Persona Options"].append(option)
    for match in mvp_matches:
        idea = {
            "Idea": match[0],
            "Reason": match[1],
            "Cost": match[2],
            "Feedback": match[3],
        }
        results["Optimal Ideas"].append(
            {
                "Idea": idea["Idea"],
                "Reason": idea["Reason"],
                "Cost": idea["Cost"],
                "Feedback": idea["Feedback"],
            }
        )
    if optimal_matches_number:
        results["Optimal Ideas"] = [
            {"Idea": match[0], "Reason": match[1]} for match in optimal_matches_number
        ]

    if optimal_match and not mvp_matches:
        results["Optimal Idea"] = {
            "Idea": optimal_match.group(1),
            "Reason": optimal_match.group(2),
            "Feedback": optimal_match.group(3),
        }
    if suboptimal_match:
        results["Suboptimal Idea"] = {
            "Idea": suboptimal_match.group(1),
            "Reason": suboptimal_match.group(2),
            "Feedback": suboptimal_match.group(3),
        }
    if not_optimal_match:
        results["Not Optimal Idea"] = {
            "Idea": not_optimal_match.group(1),
            "Reason": not_optimal_match.group(2),
            "Feedback": not_optimal_match.group(3),
        }

    return results


def save_optimal_ideas(optimal_ideas):
    # Prepare the data for the DataFrame
    rows = []
    for idea in optimal_ideas["Optimal Ideas"]:
        rows.append(
            {
                "Text": idea["Idea"],
                "Task": "Idea",
                "FeedBack": idea["Reason"],
                "Status": "Optimal",
            }
        )

    # Convert to DataFrame
    df = pd.DataFrame(rows)

    # File path to your existing Excel file
    file_path = "GeneratedVariants.xlsx"

    # Append data to an existing Excel file
    with pd.ExcelWriter(
        file_path, engine="openpyxl", mode="a", if_sheet_exists="overlay"
    ) as writer:
        # Load the existing workbook and append to a specific sheet
        df.to_excel(
            writer,
            sheet_name="Sheet1",
            index=False,
            header=False,
            startrow=writer.sheets["Sheet1"].max_row,
        )

    print("Data appended successfully.")

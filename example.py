import os
import openai
from openai import OpenAI
from groq import Groq
import openai

MAX_LEN = 3000


def format_actions(actions):
    actions = list(actions)
    assert len(actions) == 2 or len(actions) == 3
    for i in range(len(actions)):
        actions[i] = ['"' + a + '"' for a in actions[i]]
    actions = ["\n".join(a) for a in actions]
    if len(actions) == 3:
        actions = f"""{actions[0]}
        Valid Subjects: {actions[1]}
        Valid Topics: {actions[2]}"""
    elif len(actions) == 2:
        actions = f"""{actions[0]}
        Valid Causes: {actions[1]}"""
    else:
        raise NotImplementedError
    return actions


class PromptFormat:
    def format_prompt(self, input):
        raise NotImplementedError

    def parse_response(self, response):
        raise NotImplementedError


class GPTChooses_or_Vetos_v2(PromptFormat):
    def __init__(self, topk=5):
        self.topk = topk

    def format_prompt(self, history, subject, problem, choices, posttest=False, prev_exp=None, summarizer=None):
        formated_history = ""
        for (i, s) in enumerate(history):
            prefix = "Student: " if i % 2 == 1 else "Customer: "
            formated_history += (prefix + s + "\n")
        formated_prev_exp = ""
        if prev_exp is not None:
            for (j, exp) in enumerate(prev_exp):
                formated_prev_exp += f"Experience {j + 1}:\n"
                for (i, s) in enumerate(exp):
                    prefix = "Student: " if i % 2 == 1 else "Customer: "
                    formated_prev_exp += (prefix + s + "\n")
        else:
            formated_prev_exp = "No previous experience\n"
        formated_choices = ""

        for (i, c) in enumerate(choices[:min(self.topk, len(choices))]):
            formated_choices += (f"{i + 1}. " + c + "\n")
        question = "What should the student answer?" if posttest else "What should the student choose to do?"
        return [
            {
                "role": "system",
                "content": "You are a pharmacist helping a pharmacy student go through an educational game. You will receive a description of the customer and you will help the student ask a series of questions needed to help the customer. Make sure you are keeping the discussion short with the customer and offer a diagnosis once you are sure. Remember that asking the same question again will not give you a different answer. Always follow the format of available actions. if the patient asks you what's to most probable cause behind their problem you can't continue asking questions make sure you recommend diagnoses then."
            },
            {
                "role": "user",
                "content": f"Task: Find the cause behind the {subject}'s {problem}\nYour previous experience with similar tasks:\n{formated_prev_exp}Interaction History:\n{formated_history}Student top choices:\n{formated_choices} {question} if there is a suitable action between the student choice answer with the choice number. you can first reason about your choice in less than 50 words. Do not forget to put ### after your reasoning finishes.Then write your chosen action.Remember that asking the same question again will not give you a different answer. Always follow the format of available actions. if the patient asks you what's to most probable cause behind their problem you can't continue asking questions make sure you recommend diagnoses then. If you do not find any suitable actions between the student's top choices write 0. \nexample output1:\nreason: we need to explore the baby's symptoms more.\n###\n1\nexample output2:\nreason: I cannot find a suitable answer between the student's picks.\n###\n0"
            }
        ]

    def parse_response(self, response):
        print(response.choices[0].message.content)
        return response.choices[0].message.content


class GPTChooses_or_Recs(PromptFormat):
    def __init__(self, topk=5):
        self.topk = topk

    def format_prompt(self, history, subject, problem, valid_subjects, valid_topics, valid_causes, choices,
                      posttest=False, prev_exp=None, summarizer=None):
        formated_history = ""
        for (i, s) in enumerate(history):
            prefix = "Student: " if i % 2 == 1 else "Customer: "
            formated_history += (prefix + s + "\n")
        formated_prev_exp = ""
        if prev_exp is not None:
            for (j, exp) in enumerate(prev_exp):
                formated_prev_exp += f"Experience {j + 1}:\n"
                for (i, s) in enumerate(exp):
                    prefix = "Student: " if i % 2 == 1 else "Customer: "
                    formated_prev_exp += (prefix + s + "\n")
        else:
            formated_prev_exp = "No previous experience\n"
        formated_choices = ""

        for (i, c) in enumerate(choices[:min(self.topk, len(choices))]):
            formated_choices += (f"{i + 1}. " + c + "\n")
        formated_valid_topics = "[\n"
        formated_valid_subjects = "[\n"
        formated_valid_causes = "[\n"
        for s in valid_subjects:
            formated_valid_subjects += s + ",\n"
        for t in valid_topics:
            formated_valid_topics += t + ",\n"
        for t in valid_causes:
            formated_valid_causes += t + ",\n"
        formated_valid_topics += "\n]"
        formated_valid_subjects += "\n]"
        formated_valid_causes += "\n]"
        output = "1. choose(cause1)\n2. choose(cause2)" if posttest else "1. ask(x,y)\n2. answer()"
        available_actions = "1.choose(cause)[The most probable reason is cause]" if posttest else " 1. ask(subject,topic)[I want to ask about subject’s topic.] 2. answer()[I want to suggest the cause behind the customer’s problem.]\n"
        available_options = f"valid causes: {formated_valid_causes}" if posttest else f"valid subjects: {formated_valid_subjects}\nvalid topics: {formated_valid_topics}\n"
        question = "What should the student answer?" if posttest else "What should the student choose to do?"
        return [
            {
                "role": "system",
                "content": "You are a pharmacist helping a pharmacy student go through an educational game. You will receive a description of the customer and you will help the student ask a series of questions needed to help the customer. Make sure you are keeping the discussion short with the customer and offer a diagnosis once you are sure. Remember that asking the same question again will not give you a different answer. Always follow the format of available actions. if the patient asks you what's to most probable cause behind their problem you can't continue asking questions make sure you recommend diagnoses then."
            },
            {
                "role": "user",
                "content": f"Task: Find the cause behind the {subject}'s {problem}\nYour previous experience with similar tasks:\n{formated_prev_exp}Interaction History:\n{formated_history}Student top choices:\n{formated_choices} available actions:{available_actions}\n{available_options} {question} if there is a suitable action between the student choice answer with the choice number. you can first reason about your choice in less than 50 words. Don't forget to put ### after your reasoning finishes.Then write your chosen action.Remember that asking the same question again will not give you a different answer. Always follow the format of available actions. if the patient asks you what's to most probable cause behind their problem you can't continue asking questions make sure you recommend diagnoses then. If you do not find any suitable actions between the student's top choices recommend {5 if not posttest else 2} actions from the list to the student. Write whether you are doing choose or recommend followed by $$$.\nexample output1:\nchoose\n$$$\nreason: we need to explore the baby's symptoms more.\n###\n1\nexample output2:\nrecommend\n$$$\nreason: we need to explore the baby's symptoms more but the student have not included it in their choice.\n###\n{output}"
            }
        ]

    def parse_response(self, response):
        print(response.choices[0].message.content)
        return response.choices[0].message.content


class CLINChooses_or_Vetos_v2(PromptFormat):
    def __init__(self, topk=5):
        self.topk = topk

    def format_prompt(self, history, subject, problem, choices, summary, posttest=False, prev_exp=None,
                      summarizer=None):
        summary_prompt = f"Here is a summary of learnings based on your previous attempts on this task." \
                         f"These learnings capture important pre-conditions: X MAY BE NECESSARY to Y, X SHOULD BE NECESSARY to Y, and mistakes: X MAY NOT CONTRIBUTE to Y, X DOES NOT CONTRIBUTE to Y. These can be useful for completing your task:\n"
        user_em = "if there is a suitable action between the student choices answer with the choice number. If you do not find any suitable actions between the student's top choices write 0.\n First, scan the (unordered) list of learnings, if provided. Decide if any of the learnings are applicable given the last observation to make progress in this task. Then only use selected learnings, if any, to construct a rationale for your decision. If no Learning is selected, construct the rationale based on the observation history.\nFormat your response as follows:\nWrite the selected learning_ids as a comma separated list; the list can be empty if no learnings selected. Then, write $$$ followed by the rationale of at most 50 words. Finally, write ### followed by number.\n"

        formated_history = ""
        for (i, s) in enumerate(history):
            prefix = "Student: " if i % 2 == 1 else "Customer: "
            formated_history += (prefix + s + "\n")
        formated_prev_exp = ""
        if prev_exp is not None:
            for (j, exp) in enumerate(prev_exp):
                formated_prev_exp += f"Experience {j + 1}:\n"
                for (i, s) in enumerate(exp):
                    prefix = "Student: " if i % 2 == 1 else "Customer: "
                    formated_prev_exp += (prefix + s + "\n")
        else:
            formated_prev_exp = "No previous experience\n"
        formated_choices = ""

        for (i, c) in enumerate(choices[:min(self.topk, len(choices))]):
            formated_choices += (f"{i + 1}. " + c + "\n")
        question = "What should the student answer?" if posttest else "What should the student choose to do?"
        return [
            {
                "role": "system",
                "content": "You are a pharmacist helping a pharmacy student go through an educational game. You will receive a description of the customer and you will help the student ask a series of questions needed to help the customer. Make sure you are keeping the discussion short with the customer and offer a diagnosis once you are sure. Remember that asking the same question again will not give you a different answer. Always follow the format of available actions. if the patient asks you what's to most probable cause behind their problem you can't continue asking questions make sure you recommend diagnoses then."
            },
            {
                "role": "user",
                "content": f"Task: Find the cause behind the {subject}'s {problem}\nYour previous experience with similar tasks:\n{formated_prev_exp}{summary_prompt}{summary}Interaction History:\n{formated_history}Student top choices:\n{formated_choices} {question} {user_em}\nexample output1:\n1, 3\n$$$\nreason: we need to explore the baby's symptoms more.\n###\n1\nexample output2:\n1, 3\n$$$\nreason: I cannot find a suitable answer between the student's picks.\n###\n0&..."

            }
        ]
    
def parse_chosen_action(chosen_action):
    for x in [" ", ".", "\n", ")"]:
        if chosen_action.split(x)[0].isnumeric():
            chosen_action = chosen_action.split(x)[0]
            break
    return chosen_action


def find_all_occurences(list, value):
    return [i for i, x in enumerate(list) if x == value]


def match(sentence, valid_sentences, replace_closest=False):
    for t in valid_sentences:
        if sentence == t.lower():
            return t, True
    indicator = [(sentence in t.lower()) or (t.lower() in sentence) for t in valid_sentences]
    if any(indicator):
        idx = find_all_occurences(indicator, True)
        values = [valid_sentences[i] for i in idx]
        len_values = [len(x) for x in values]
        if len(idx) > 1:
            idx = idx[len_values.index(max(len_values))]
        if isinstance(idx, list):
            idx = idx[0]
        return valid_sentences[idx], True
    else:
        if replace_closest:
            sentence = sentence.replace("\n", "")
            ### replace the closest sentence
            valid_sentences_embeddings = [fasttext_model.get_sentence_vector(x) for x in valid_sentences]
            sentence_embedding = fasttext_model.get_sentence_vector(sentence)
            distances = [1 - scipy.spatial.distance.cosine(x, sentence_embedding) for x in valid_sentences_embeddings]
            idx = distances.index(max(distances))
            return valid_sentences[idx], False
        else:
            return sentence, False


def parse_string_to_dict(input_str, valid_subjects, valid_topics, valid_causes, replace_closest=False, posttest=False):
    # Splitting the input string into the command and the arguments
    input_str = input_str.lower()
    result_dict = {
        "type": "",
        "part": "",
        "detail": "",
        "sentence": ""
    }
    flag = False
    if "(" in input_str:
        parts = input_str.split('(', 1)
        command = parts[0].split(' ')[-1]
        if posttest and replace_closest:
            command = "choose"
        args = parts[1].rsplit(')', 1)[0] if len(parts) > 1 else ""
        args = args.split("),")[0]
        flag = True
        # Mapping based on the command
        if command == "ask":
            result_dict["type"] = "interaction"
            result_dict["part"] = "discuss"
            subject, topic = "", ""
            if args:
                if len(args.split(',')) == 1:
                    subject = args
                    topic = args
                elif len(args.split(',')) == 2:
                    subject, topic = args.split(',')
                else:
                    subject, topic = args.split(',')[0], ",".join(args.split(',')[1:])
            subject, topic = subject.strip(), topic.strip()
            subject, matched = match(subject, valid_subjects, replace_closest=replace_closest)
            topic, matched = match(topic, valid_topics, replace_closest=replace_closest)
            if replace_closest:
                print(f"Replaced {args} with {subject}, {topic}")
            result_dict["detail"] = ",".join([subject, topic])
            result_dict["sentence"] = f"i want to know about the {subject} 's {topic}."
        elif command == "answer":
            result_dict["type"] = "interaction"
            result_dict["part"] = "solution"
            result_dict["sentence"] = "i want to suggest a solution."

        elif command == "choose":
            result_dict["type"] = "posttest"
            args, matched = match(args, valid_causes, replace_closest=replace_closest)
            result_dict["sentence"] = args
        else:
            flag = False

    if not flag:
        if posttest:
            cause, matched_c = match(input_str, valid_causes, replace_closest=replace_closest)
            result_dict["type"] = "posttest"
            result_dict["sentence"] = cause
        else:
            result_dict["type"] = "interaction"
            subject, matched_s = match(input_str, valid_subjects, replace_closest=replace_closest)
            topic, matched_t = match(input_str, valid_topics, replace_closest=replace_closest)
            if "diagnosis" in input_str:
                result_dict["part"] = "solution"
                result_dict["sentence"] = "i want to suggest a solution."
            else:
                result_dict["part"] = "discuss"
                result_dict["detail"] = ",".join([subject, topic])
                result_dict["sentence"] = f"i want to know about the {subject} 's {topic}."
    return result_dict
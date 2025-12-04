import re
import argparse
import asyncio
from typing import List, Dict
from models import VLLMClient
from utils import process_score_prompt

def extract_last_boxed(text):
    try:
        pattern = r'<score>([\d.]+)</score>'
        matches = re.findall(pattern, text)
        if matches:
            return float(matches[-1])
        else:
            return 0.0
    except Exception as e:
        print(f"Error extracting boxed content: {e}")
        return 0.0

def parse_from_score_model(response: str, scale_factor=10) -> float:
    score = extract_last_boxed(response)
    score = score / scale_factor
    return score

def build_message(question:str, answer:str, response:str) -> Dict:
    prompt = process_score_prompt(question, answer, response)
    message = {"role": "user", "content": [{"type": "text", "text": prompt}]}
    return message

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run evaluation on a given model and dataset.")
    parser.add_argument("--scorer_api_url", type=str, default="", help="The score model API url.")

    args = parser.parse_args()
    score_client = VLLMClient(
        model_name="UNO-Scorer", 
        api_url=args.scorer_api_url,
        system_prompt="You are a helpful assistant."
    )
    score_client.load_model()

    test_cases = [
        # Multiple-choice question
       {
           "question_type": "multiple-choice",
           "question": "Which one is the best depiction of this image?\nA. A beautiful woman wearing a hat is holding a rose in her right hand and is opening her mouth big to eat it.\nB. A young woman is wearing a hat and her right hand is pierced by a bouquet of pink roses, and she opens her mouth to express pain.\nC. A young girl wearing brown clothes is holding a blooming pink flower in her right hand, with her mouth slightly open.\nD. A young girl wearing brown clothes is holding a blooming magic wand in her right hand, with her mouth slightly open.", 
           "answer": "C", 
           "response": "Well, if we're talking about the best depiction of this image, I'd say it's C. The young girl in brown clothes holding a blooming pink flower in her right hand with her mouth slightly open seems to match the image the most. What do you think? Do you agree with that?",
           "target_score": 1
        },
        # Yes/No question
       {
           "question_type": "yes/no",
           "question": "The following images show two graphs. Each graph is represented in a separate image. Are these graphs isomorphic?Answer Yes or No.", 
           "answer": "Yes", 
           "response": "No. If you have any other questions about these graphs or anything else, feel free to ask!",
           "target_score": 0
        },
        # Open-ended question
       {
           "question_type": "open-ended",
           "question": "How many seasons did 90210 have?", 
           "answer": "Ten", 
           "response": "I'm not sure which \"90210\" you're referring to. There are different shows or things with that name. If it's the TV show \"90210\", it had 7 seasons. But if it's something else, you might need to give me a bit more context.",
           "target_score": 0
        },
        #  Multiple-question answer
        {
            # If the question type is multi-question, you must specify the answer in detail.
            "question_type": "multiple-question", 
            "question": "David is playing an escape room game. In one of the levels, he needs to find the key to the room. The game rules state that he must locate the box containing the key among a row of identical-looking boxes, and correctly enter the box's password to obtain the key to escape. It is known that the box with the key meets the following conditions: it is not at either end; it is not in the very middle; the number of boxes on both its left and right sides is even. In addition, each box has a three-digit password, with each digit being one of the numbers from 0 to 9. The arrangement of the boxes and the password puzzle are hidden in image <image_1>. The image puzzle provides two decryption examples, and you need to use these examples to decode which digits the two question marks at the bottom of the image represent. Among all the numbers given in the provided examples and obtained after decoding, the smallest number is interference information and should be excluded. Partial clues about the box containing the key and its password are hidden in audio <audio_1>. Based on the above information, and combining the image and audio clues, answer:\n1. Which box (counting from left to right) contains the key?\n2. What is the correct password for the box containing the key?",
            "answer": "1. The 5th box from the left (4 points);\n2. The password is 569 (6 points).",
            "response": "Hmm… let me think. According to the hint in the audio, the key to decryption lies in the Roman numerals hidden in the words, and these numbers are all no greater than 10. From the image, there are six boxes. Based on the rules, the key is neither at the ends nor in the middle, so it should be in the 5th box from the left. As for the password, arranging in ascending order, it should be Victory = 2, give = 3. So the password for the box with the key is 23. If you have any other ideas or questions, feel free to let me know.",
            "target_score": 0.4
        }
    ]

    messages = []
    for case in test_cases:
        answer = case["answer"]
        if case["question_type"] != "multiple-question":
            # The Chinese rule will be better because the scorer model is trained in Chinese.
            answer = f"小问1：{answer}，总分10分，无需关注推理过程，最终答案正确即可"
        message = build_message(question=case["question"], answer=answer, response=case["response"])
        messages.append(message)

    score_responses = asyncio.run(score_client.generate_batch(messages, batch_size=32))
    pass_cnt = 0
    for score_response, case in zip(score_responses, test_cases):
        print("="*32)
        score = parse_from_score_model(score_response)
        for key,value in case.items():
            print(f"{key}: {value}")
        print("Score response:\n", score_response)
        print(f"Score: {score}, Target Score: {case['target_score']}")
        if score == case["target_score"]:
            pass_cnt += 1
    print("*"*32)
    print(f"Pass: {pass_cnt}/{len(test_cases)}")


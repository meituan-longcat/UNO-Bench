import re
import argparse
from tqdm import tqdm
from transformers import AutoModelForCausalLM, AutoTokenizer

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

def load_model(model_name: str) -> AutoModelForCausalLM:
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        torch_dtype="auto",
        device_map="auto"
    )
    return tokenizer, model

def generate(model, tokenizer, prompt: str) -> str:
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user", 
            "content": prompt
        }
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
    )
    model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

    # conduct text completion
    generated_ids = model.generate(
        **model_inputs,
        max_new_tokens=16384,
        do_sample=False
    )
    output_ids = generated_ids[0][len(model_inputs.input_ids[0]):].tolist() 

    content = tokenizer.decode(output_ids, skip_special_tokens=True)
    return content

def remove_thought_block(text: str) -> str:
    pattern = r"^(<think>.*?</think>|.*?)"
    match = re.match(pattern, text, flags=re.DOTALL)
    if match:
        end_of_match = match.end()
        return text[end_of_match:].lstrip()
    return text

def process_score_prompt(question, reference, response):
    promt_template = """请先通读问题信息，然后基于参考答案对模型回复的结果进行正确性打分。每道题可能包含多个小问，每个小问都已给出了相应的参考答案和分值，请逐小问校验模型回复是否正确，正确得对应分值，错误或漏答得0分，累计计分，有如下要求。

---

### 要求1：信息梳理

- 梳理出如下信息
  - 问题内容
  - 参考答案（可适度完善表达，但不改变核心内容）
  - 模型回复（需要将模型回复中的指代关系与参考答案对齐）
  - 分值

### 要求2：判断题型

- 明确该小问属于以下哪种题型之一，并基于该类型的打分标准进行打分，需要给出详细的比对过程。
  - **数值型**，要求模型回复与标准答案的数值完全相同，不允许有误差。例，`问题：北京奥运会是哪一年？参考答案：2008，模型回复：2004，打分结果：错误。`
  - **枚举型**，要求模型回复列举出参考答案的全部对象，缺一不可、错一不可，允许同义词等语义相近的表达，题中有顺序要求则必须按顺序枚举。例，`图中出现了哪些动物？参考答案：大熊猫、河马、长颈鹿，模型回复：河马、小熊猫、长颈鹿，打分结果：错误。 `注：“/”表示“或”，如，XXA/XXB，表示回答出任意一项即可。
  - **选择题**，要求模型回复与参考答案相同的选项或选项内容。例，`问题：李白是哪个朝代的诗人？A. 唐朝 B. 宋朝 C. 元朝，模型回复：李白是唐朝诗人，打分结果：正确。`
  - **判断题**，要求模型回复与参考答案的判断一致。例，`问题：图中鼠标是否放在了笔记本电脑左侧？参考答案：是，模型回复：图中鼠标在笔记本电脑的左侧。打分结果：正确。`
  - **简答题**，要求模型回复包括与参考答案语义一致的短语或表达，允许表达方式不同。例，`问题：视频中最后放入锅中的食材是什么？参考答案：洋葱，模型回复：胡萝卜。打分结果：错误。`
  - **论述题**，要求模型回复包含参考答案的核心观点。例，`问题：请简要论述为什么要保护生物多样性。参考答案：维持生态平衡，模型回复：保护生物多样性能够让生态系统保持稳定，促进人类社会的可持续发展。打分结果：正确。`

### 要求3：打分标准

- **完全正确**：得满分。
- **错误或漏答**：得0分。
- 如模型回复与参考答案大意相同但细节略有差别，且非核心内容，视为正确，具体参考参考答案的详细要求。
- 若模型回复未直接给出答案，需主动归纳总结结论，只关注结论是否一致。
- 每小问独立打分，前序错误不影响后续小问的结果。

### 要求4：输出格式

- 逐小问列出得分说明。
- 所有小问得分相加，在<score></score>中给出总分，例如：<score>5</score>

---

## 问题信息
{{question}}
## 参考答案
{{reference}}
## 模型回复
{{response}}
## 逐小问打分"""
    
    prompt = promt_template.replace("{{question}}", remove_thought_block(question.strip()))
    prompt = prompt.replace("{{reference}}", reference)
    prompt = prompt.replace("{{response}}", response)
    return prompt


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Run evaluation on a given model and dataset.")
    parser.add_argument("--model-name", type=str, default="", help="The model name or path.")

    args = parser.parse_args()
    tokenizer, model = load_model(args.model_name)

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

    prompts = []
    for case in test_cases:
        answer = case["answer"]
        if case["question_type"] != "multiple-question":
            # The Chinese rule will be better because the scorer model is trained in Chinese.
            answer = f"小问1：{answer}，总分10分，无需关注推理过程，最终答案正确即可"
        question = case["question"]
        response = remove_thought_block(case["response"])
        prompt = process_score_prompt(question=question, reference=answer, response=response)
        prompts.append(prompt)

    score_responses = []
    for prompt in tqdm(prompts):
        score_response = generate(model, tokenizer, prompt)
        score_responses.append(score_response)

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


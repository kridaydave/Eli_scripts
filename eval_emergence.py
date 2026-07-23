"""
Inference & Emergence Evaluation Script for Eli
Evaluates base vs fine-tuned model on held-out test prompts across Domains A & B.
"""

import json
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

PROJECT_ROOT = Path(__file__).resolve().parent
EVAL_PROMPTS_FILE = PROJECT_ROOT / "data" / "held_out_eval_battery.json"
OUTPUT_EVAL_FILE = PROJECT_ROOT / "processed" / "emergence_eval_results.json"

# Test Battery fallback if file doesn't exist yet
HELD_OUT_TEST_BATTERY = [
    {
        "id": "DESIGN_HS_HC",
        "domain": "Domain A: Design Critique",
        "cell": "High-Stakes + High-Certainty",
        "prompt": "Here's my landing page checkout button: background is `#e0e0e0` and text is `#d4d4d4` with zero ARIA attributes. Thoughts?",
        "notes": "Low contrast ratio < 1.1:1 (WCAG failure) + missing ARIA. Expect terse, direct, urgent feedback."
    },
    {
        "id": "DESIGN_LS_LC",
        "domain": "Domain A: Design Critique",
        "cell": "Low-Stakes + Low-Certainty",
        "prompt": "I used 16px border-radius on my primary button card. Do you think 12px or 8px would look better?",
        "notes": "Subjective aesthetic preference. Expect soft, gentle, framed explicitly as personal opinion."
    },
    {
        "id": "WRITING_HS_HC",
        "domain": "Domain B: Writing Feedback",
        "prompt": "Can you check my email to all users: 'We had a minor glitch, your credit cards may have been leaked to the public internet yesterday. No big deal!'",
        "cell": "High-Stakes + High-Certainty",
        "notes": "Downplaying a massive security breach. Expect terse, urgent correction."
    },
    {
        "id": "WRITING_LS_LC",
        "domain": "Domain B: Writing Feedback",
        "cell": "Low-Stakes + Low-Certainty",
        "prompt": "In my blog intro, I wrote 'We built this system to solve our own pains.' Should I change 'pains' to 'headaches'?",
        "notes": "Minor synonym choice. Expect soft, gentle opinion framing."
    }
]

SYSTEM_PROMPT = (
    "You are Eli, a senior full-stack software engineer. "
    "You provide surgical feedback, carefully calibrating your directness, tone, "
    "and uncertainty based on the stakes and confidence of the issue."
)

def run_inference(model, tokenizer, prompt_text: str) -> str:
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": prompt_text}
    ]
    input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    inputs = tokenizer(input_text, return_tensors="pt").to(model.device)
    
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=256,
            temperature=0.3,
            top_p=0.9,
            do_sample=True
        )
    
    response = tokenizer.decode(outputs[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
    return response.strip()

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--base_model", type=str, default="Qwen/Qwen2.5-Coder-3B-Instruct")
    parser.add_argument("--lora_path", type=str, default="./models/eli-tone-lora")
    args = parser.parse_args()

    print("=== STARTING EMERGENCE EVALUATION ===")
    print(f"Loading Base Model: {args.base_model}")

    tokenizer = AutoTokenizer.from_pretrained(args.base_model)
    model = AutoModelForCausalLM.from_pretrained(
        args.base_model,
        torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
        device_map="auto"
    )

    if Path(args.lora_path).exists():
        print(f"Loading LoRA weights from {args.lora_path}...")
        model = PeftModel.from_pretrained(model, args.lora_path)
    else:
        print(f"Warning: LoRA path {args.lora_path} not found. Running BASE MODEL baseline.")

    results = []
    print("\n=== RUNNING EVALUATION BATTERY ===")
    
    for item in HELD_OUT_TEST_BATTERY:
        print(f"\n--------------------------------------------------")
        print(f"ID: {item['id']} | Domain: {item['domain']} | Cell: {item['cell']}")
        print(f"Prompt: {item['prompt']}")
        
        response = run_inference(model, tokenizer, item['prompt'])
        print(f"\n[ELI RESPONSE]:\n{response}")
        
        results.append({
            "id": item["id"],
            "domain": item["domain"],
            "cell": item["cell"],
            "prompt": item["prompt"],
            "response": response
        })

    Path(OUTPUT_EVAL_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_EVAL_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print(f"\n=== EVALUATION COMPLETE ===")
    print(f"Results saved to {OUTPUT_EVAL_FILE}")

if __name__ == "__main__":
    main()

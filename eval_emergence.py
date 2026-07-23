"""
Inference & Emergence Evaluation Script for Eli
Evaluates base vs fine-tuned model on the 45 held-out transfer test prompts (data/held_out_transfer_test.jsonl).
Outputs results with the manual 4-item checklist scoring rubric.
"""

import json
import torch
from pathlib import Path
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

PROJECT_ROOT = Path(__file__).resolve().parent
HELD_OUT_FILE = PROJECT_ROOT / "data" / "held_out_transfer_test.jsonl"
OUTPUT_EVAL_FILE = PROJECT_ROOT / "processed" / "emergence_eval_results.json"

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
    parser.add_argument("--base_model", type=str, default="unsloth/Qwen3-4B-Instruct-2507")
    parser.add_argument("--lora_path", type=str, default="./models/eli-tone-lora")
    parser.add_argument("--output_file", type=str, default=None)
    parser.add_argument("--batch_size", type=int, default=16)
    args = parser.parse_args()

    print("=== STARTING STEP 0 HELD-OUT EMERGENCE EVALUATION ===")
    
    # Try importing Unsloth for fast 4-bit inference to avoid memory limits
    try:
        from unsloth import FastLanguageModel
        has_unsloth = True
    except ImportError:
        has_unsloth = False

    lora_loaded = False
    if has_unsloth:
        # If LoRA path exists, load directly through FastLanguageModel (it resolves base model automatically)
        if Path(args.lora_path).exists():
            model_to_load = args.lora_path
            print(f"Loading LoRA weights via Unsloth: {model_to_load}")
            lora_loaded = True
        else:
            model_to_load = args.base_model
            print(f"Loading Base Model via Unsloth: {model_to_load}")
        
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_to_load,
            max_seq_length=49152,
            dtype=None,
            load_in_4bit=True,
        )
        FastLanguageModel.for_inference(model)
    else:
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
            lora_loaded = True
        else:
            print(f"Notice: LoRA path {args.lora_path} not found. Running UNTUNED BASE MODEL evaluation.")

    # Configure padding for batch generation
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "left"
    if hasattr(model, 'config'):
        model.config.pad_token_id = tokenizer.pad_token_id

    eval_items = []
    with open(HELD_OUT_FILE, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                eval_items.append(json.loads(line))

    # Construct batched inputs
    formatted_prompts = []
    for item in eval_items:
        prompt_text = f"Context: {item['context']}\n\nArtifact: {item['artifact']}"
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_text}
        ]
        input_text = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        formatted_prompts.append(input_text)

    results = []
    print(f"\n=== EVALUATING {len(eval_items)} HELD-OUT EXAMPLES IN BATCHES (Size: {args.batch_size}) ===")
    
    for i in range(0, len(formatted_prompts), args.batch_size):
        batch_prompts = formatted_prompts[i : i + args.batch_size]
        batch_items = eval_items[i : i + args.batch_size]
        print(f"Processing batch {i // args.batch_size + 1}/{(len(formatted_prompts) - 1) // args.batch_size + 1}...")
        
        inputs = tokenizer(
            batch_prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=2048
        ).to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=256,
                temperature=0.3,
                top_p=0.9,
                do_sample=True,
                pad_token_id=tokenizer.pad_token_id,
                eos_token_id=tokenizer.eos_token_id,
            )
            
        for j, out in enumerate(outputs):
            gen_tokens = out[inputs.input_ids.shape[1]:]
            response = tokenizer.decode(gen_tokens, skip_special_tokens=True).strip()
            item = batch_items[j]
            
            result_entry = {
                "id": item["id"],
                "domain": item["domain"],
                "cell": item["cell"],
                "context": item["context"],
                "artifact": item["artifact"],
                "ground_truth_target_response": item["response"],
                "model_generated_response": response,
                "checklist_rubric": {
                    "score_directness_matches_stakes": None,
                    "score_hedging_matches_certainty": None,
                    "score_no_register_bleed": None,
                    "score_distinguishes_grid_cell": None
                }
            }
            results.append(result_entry)

    if args.output_file:
        output_path = Path(args.output_file)
    else:
        suffix = "lora" if lora_loaded else "base"
        output_path = PROJECT_ROOT / "processed" / f"emergence_eval_results_{suffix}.json"

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n=== HELD-OUT EVALUATION COMPLETE ===")
    print(f"Results saved to {output_path}")

if __name__ == "__main__":
    main()

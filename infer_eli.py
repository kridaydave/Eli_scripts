#!/usr/bin/env python3
"""
Interactive CLI Script for Eli Model Inference
================================================
Supports loading LoRA fine-tuned checkpoints (e.g. checkpoint-1500 from Drive or local path)
and running single prompts or interactive chat sessions.

Usage:
    # Interactive chat mode
    python3 infer_eli.py --checkpoint /path/to/checkpoint-1500

    # Single prompt execution
    python3 infer_eli.py --checkpoint ./models/eli-tone-lora/checkpoint-1500 --prompt "Write a FastAPI route for uploading images to S3 with pre-signed URLs."

    # Custom base model override
    python3 infer_eli.py --checkpoint ./models/eli-tone-lora/checkpoint-1500 --base_model unsloth/Qwen3-4B-Instruct-2507
"""

import os
import sys
import argparse
import torch

SYSTEM_PROMPT = (
    "You are Eli, a senior full-stack software engineer. "
    "Write clean, correct, production-quality code. "
    "Respond with the implementation directly."
)

def parse_args():
    parser = argparse.ArgumentParser(description="Eli Model Interactive CLI")
    parser.add_argument(
        "--checkpoint",
        type=str,
        default="./models/eli-tone-lora/checkpoint-1500",
        help="Path to the LoRA checkpoint directory (local path or Google Drive mount path)"
    )
    parser.add_argument(
        "--base_model",
        type=str,
        default=None,
        help="Optional base model path/identifier if different from checkpoint config"
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=None,
        help="Single prompt to execute. If omitted, launches interactive mode."
    )
    parser.add_argument(
        "--max_new_tokens",
        type=int,
        default=1024,
        help="Maximum new tokens to generate (default: 1024)"
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Sampling temperature (default: 0.7)"
    )
    parser.add_argument(
        "--max_seq_length",
        type=int,
        default=34816,
        help="Maximum sequence length context window (default: 34816)"
    )
    return parser.parse_args()

def load_model_and_tokenizer(checkpoint_path: str, base_model: str = None, max_seq_length: int = 34816):
    print(f"[*] Loading model from checkpoint: {checkpoint_path}")
    
    if not os.path.exists(checkpoint_path):
        print(f"[!] Warning: Checkpoint path '{checkpoint_path}' does not exist locally.")
        print("    If mounted on Google Drive, check mount point (e.g., /content/drive/MyDrive/...) or specify via --checkpoint.")

    try:
        from unsloth import FastLanguageModel
        
        model_name = checkpoint_path
        model, tokenizer = FastLanguageModel.from_pretrained(
            model_name=model_name,
            max_seq_length=max_seq_length,
            dtype=None,
            load_in_4bit=True,
        )
        FastLanguageModel.for_inference(model)
        print("[✓] Model and tokenizer loaded successfully with Unsloth 4-bit optimization!")
        return model, tokenizer
    except ImportError:
        print("[*] Unsloth not found, falling back to standard Transformers + PEFT...")
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        from peft import PeftModel

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.bfloat16
        )
        
        if base_model is None:
            base_model = "unsloth/Qwen3-4B-Instruct-2507"
            
        print(f"[*] Loading base model: {base_model}")
        tokenizer = AutoTokenizer.from_pretrained(checkpoint_path)
        base = AutoModelForCausalLM.from_pretrained(
            base_model,
            quantization_config=bnb_config,
            device_map="auto"
        )
        model = PeftModel.from_pretrained(base, checkpoint_path)
        model.eval()
        print("[✓] Model loaded via Transformers + PEFT.")
        return model, tokenizer

def generate_response(model, tokenizer, prompt: str, system_prompt: str = SYSTEM_PROMPT, max_new_tokens: int = 1024, temperature: float = 0.7):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    prompt_str = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )
    
    inputs = tokenizer(prompt_str, return_tensors="pt").to("cuda" if torch.cuda.is_available() else "cpu")
    
    pad_token_id = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else tokenizer.eos_token_id
    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=temperature,
            do_sample=temperature > 0.0,
            pad_token_id=pad_token_id,
            eos_token_id=tokenizer.eos_token_id,
            use_cache=True
        )
        
    input_length = inputs["input_ids"].shape[1]
    response_tokens = outputs[0][input_length:]
    decoded = tokenizer.decode(response_tokens, skip_special_tokens=True).strip()
    return decoded

def interactive_loop(model, tokenizer, max_new_tokens: int, temperature: float):
    print("\n" + "="*60)
    print("      Eli CLI Interactive Session (Type 'exit' or 'quit' to stop)")
    print("="*60 + "\n")
    
    while True:
        try:
            user_input = input("You > ").strip()
            if not user_input:
                continue
            if user_input.lower() in ("exit", "quit"):
                print("Exiting session. Goodbye!")
                break
                
            print("\nEli > ", end="", flush=True)
            response = generate_response(
                model, tokenizer, prompt=user_input,
                max_new_tokens=max_new_tokens, temperature=temperature
            )
            print(response)
            print("-" * 60 + "\n")
        except KeyboardInterrupt:
            print("\nInterrupted. Exiting...")
            break

def main():
    args = parse_args()
    model, tokenizer = load_model_and_tokenizer(
        checkpoint_path=args.checkpoint,
        base_model=args.base_model,
        max_seq_length=args.max_seq_length
    )
    
    if args.prompt:
        print(f"\n[Prompt]: {args.prompt}")
        print("\n[Eli Response]:")
        response = generate_response(
            model, tokenizer, prompt=args.prompt,
            max_new_tokens=args.max_new_tokens, temperature=args.temperature
        )
        print(response)
    else:
        interactive_loop(model, tokenizer, args.max_new_tokens, args.temperature)

if __name__ == "__main__":
    main()

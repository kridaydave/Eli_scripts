[Errno 2] No such file or directory: 'epoch-1/'
/content/epoch-1
Loaded 50 items from /content/epoch-1/eval/ood_coding_eval_set.jsonl

--- Pre-flight check: Validating Canonical Solutions ---

=== VALIDATING EVAL SET (canonical solutions) ===
  [1/50] ood_geom_04 ✓
  [2/50] ood_geom_01 ✓
  [3/50] ood_parse_03 ✓
  [4/50] ood_bit_02 ✓
  [5/50] ood_math_02 ✓
  [6/50] ood_parse_04 ✓
  [7/50] ood_geom_03 ✓
  [8/50] ood_geom_02 ✓
  [9/50] ood_comb_04 ✓
  [10/50] ood_graph_03 ✓
  [11/50] ood_sim_04 ✓
  [12/50] ood_graph_02 ✓
  [13/50] ood_bit_01 ✓
  [14/50] ood_geom_05 ✓
  [15/50] ood_bit_04 ✓
  [16/50] ood_nt_04 ✓
  [17/50] ood_nt_06 ✓
  [18/50] ood_sim_01 ✓
  [19/50] ood_parse_02 ✓
  [20/50] ood_sys_01 ✓
  [21/50] ood_sim_03 ✓
  [22/50] ood_comp_04 ✓
  [23/50] ood_parse_06 ✓
  [24/50] ood_bit_06 ✓
  [25/50] ood_comp_02 ✓
  [26/50] ood_comb_01 ✓
  [27/50] ood_bit_07 ✓
  [28/50] ood_comb_07 ✓
  [29/50] ood_math_03 ✓
  [30/50] ood_parse_05 ✓
  [31/50] ood_nt_03 ✓
  [32/50] ood_graph_01 ✓
  [33/50] ood_sys_02 ✓
  [34/50] ood_graph_06 ✓
  [35/50] ood_nt_07 ✓
  [36/50] ood_comb_03 ✓
  [37/50] ood_bit_05 ✓
  [38/50] ood_sim_02 ✓
  [39/50] ood_nt_08 ✓
  [40/50] ood_graph_05 ✓
  [41/50] ood_graph_07 ✓
  [42/50] ood_math_05 ✓
  [43/50] ood_comb_06 ✓
  [44/50] ood_geom_06 ✓
  [45/50] ood_sim_05 ✓
  [46/50] ood_geom_08 ✓
  [47/50] ood_math_04 ✓
  [48/50] ood_comp_03 ✓
  [49/50] ood_comb_08 ✓
  [50/50] ood_sys_03 ✓

✓ All 50 canonical solutions pass their tests.

--- Evaluating Base Model ---
🦥 Unsloth: Will patch your computer to enable 2x faster free finetuning.
🦥 Unsloth Zoo will now patch everything to make training faster!
Loading base model via Unsloth: unsloth/Qwen3-4B-Instruct-2507
==((====))==  Unsloth 2026.7.5: Fast Qwen3 patching. Transformers: 5.5.0.
   \\   /|    Tesla T4. Num GPUs = 1. Max memory: 14.563 GB. Platform: Linux.
O^O/ \_/ \    Torch: 2.11.0+cu128. CUDA: 7.5. CUDA Toolkit: 12.8. Triton: 3.6.0
\        /    Bfloat16 = FALSE. FA [Xformers = 0.0.35. FA2 = False]
 "-____-"     Free license: http://github.com/unslothai/unsloth
Unsloth: Fast downloading is enabled - ignore downloading bars which are red colored!
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Warning: You are sending unauthenticated requests to the HF Hub. Please set a HF_TOKEN to enable higher rate limits and faster downloads.
Loading weights: 100% 398/398 [00:06<00:00, 61.41it/s] 
[1/50] ood_geom_04 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
/usr/local/lib/python3.12/dist-packages/transformers/modeling_attn_mask_utils.py:71: FutureWarning: The attention mask API under `transformers.modeling_attn_mask_utils` (`AttentionMaskConverter`) is deprecated and will be removed in Transformers v5.10. Please use the new API in `transformers.masking_utils`.
  warnings.warn(DEPRECATION_MESSAGE, FutureWarning)
/usr/local/lib/python3.12/dist-packages/transformers/modeling_attn_mask_utils.py:281: FutureWarning: The attention mask API under `transformers.modeling_attn_mask_utils` (`AttentionMaskConverter`) is deprecated and will be removed in Transformers v5.10. Please use the new API in `transformers.masking_utils`.
  warnings.warn(DEPRECATION_MESSAGE, FutureWarning)
/usr/local/lib/python3.12/dist-packages/transformers/modeling_attn_mask_utils.py:71: FutureWarning: The attention mask API under `transformers.modeling_attn_mask_utils` (`AttentionMaskConverter`) is deprecated and will be removed in Transformers v5.10. Please use the new API in `transformers.masking_utils`.
  warnings.warn(DEPRECATION_MESSAGE, FutureWarning)
/usr/local/lib/python3.12/dist-packages/transformers/modeling_attn_mask_utils.py:281: FutureWarning: The attention mask API under `transformers.modeling_attn_mask_utils` (`AttentionMaskConverter`) is deprecated and will be removed in Transformers v5.10. Please use the new API in `transformers.masking_utils`.
  warnings.warn(DEPRECATION_MESSAGE, FutureWarning)
✗ (RUNTIME_ERROR: NameError: name 'is_point_in_bbox' is not def)
[2/50] ood_geom_01 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[3/50] ood_parse_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[4/50] ood_bit_02 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[5/50] ood_math_02 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: ValueError: Vectors cannot be empty)
[6/50] ood_parse_04 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'parse_csv_simple' is not def)
[7/50] ood_geom_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: TypeError: manhattan_distance() missing 2 req)
[8/50] ood_geom_02 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[9/50] ood_comb_04 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'binomial_coeff' is not defin)
[10/50] ood_graph_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'count_components' is not def)
[11/50] ood_sim_04 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'simulate_ring_buffer' is not)
[12/50] ood_graph_02 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[13/50] ood_bit_01 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[14/50] ood_geom_05 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'polygon_perimeter' is not de)
[15/50] ood_bit_04 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (ASSERTION_FAILED:)
[16/50] ood_nt_04 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
/usr/local/lib/python3.12/dist-packages/transformers/modeling_attn_mask_utils.py:71: FutureWarning: The attention mask API under `transformers.modeling_attn_mask_utils` (`AttentionMaskConverter`) is deprecated and will be removed in Transformers v5.10. Please use the new API in `transformers.masking_utils`.
  warnings.warn(DEPRECATION_MESSAGE, FutureWarning)
/usr/local/lib/python3.12/dist-packages/transformers/modeling_attn_mask_utils.py:281: FutureWarning: The attention mask API under `transformers.modeling_attn_mask_utils` (`AttentionMaskConverter`) is deprecated and will be removed in Transformers v5.10. Please use the new API in `transformers.masking_utils`.
  warnings.warn(DEPRECATION_MESSAGE, FutureWarning)
✗ (RUNTIME_ERROR: NameError: name 'sieve_primes' is not defined)
[17/50] ood_nt_06 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[18/50] ood_sim_01 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[19/50] ood_parse_02 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'parse_cron_minutes' is not d)
[20/50] ood_sys_01 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'stack_machine' is not define)
[21/50] ood_sim_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'simulate_editor' is not defi)
[22/50] ood_comp_04 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (extraction failed)
[23/50] ood_parse_06 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'parse_url_simple' is not def)
[24/50] ood_bit_06 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[25/50] ood_comp_02 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'rle_decode' is not defined)
[26/50] ood_comb_01 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'nth_catalan' is not defined)
[27/50] ood_bit_07 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'swap_without_temp' is not de)
[28/50] ood_comb_07 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[29/50] ood_math_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: ValueError: Window size cannot be larger than)
[30/50] ood_parse_05 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'is_valid_cidr' is not define)
[31/50] ood_nt_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'mod_exp' is not defined)
[32/50] ood_graph_01 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'bfs' is not defined)
[33/50] ood_sys_02 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'eval_rpn' is not defined)
[34/50] ood_graph_06 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (ASSERTION_FAILED:)
[35/50] ood_nt_07 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[36/50] ood_comb_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[37/50] ood_bit_05 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'single_number_two' is not de)
[38/50] ood_sim_02 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[39/50] ood_nt_08 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: TypeError: miller_rabin() missing 1 required )
[40/50] ood_graph_05 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: ValueError: Graph contains a cycle - not a va)
[41/50] ood_graph_07 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[42/50] ood_math_05 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[43/50] ood_comb_06 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'partitions' is not defined)
[44/50] ood_geom_06 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'do_intersect' is not defined)
[45/50] ood_sim_05 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'simulate_rw_lock' is not def)
[46/50] ood_geom_08 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[47/50] ood_math_04 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[48/50] ood_comp_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: TypeError: '<' not supported between instance)
[49/50] ood_comb_08 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'subset_sum' is not defined)
[50/50] ood_sys_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'simulate_allocator' is not d)

--- Evaluating LoRA Model ---
Loading base model via Unsloth: unsloth/Qwen3-4B-Instruct-2507
==((====))==  Unsloth 2026.7.5: Fast Qwen3 patching. Transformers: 5.5.0.
   \\   /|    Tesla T4. Num GPUs = 1. Max memory: 14.563 GB. Platform: Linux.
O^O/ \_/ \    Torch: 2.11.0+cu128. CUDA: 7.5. CUDA Toolkit: 12.8. Triton: 3.6.0
\        /    Bfloat16 = FALSE. FA [Xformers = 0.0.35. FA2 = False]
 "-____-"     Free license: http://github.com/unslothai/unsloth
Unsloth: Fast downloading is enabled - ignore downloading bars which are red colored!
Loading weights: 100% 398/398 [00:06<00:00, 58.30it/s] 
[1/50] ood_geom_04 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: TypeError: is_point_in_bbox() missing 4 requi)
[2/50] ood_geom_01 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[3/50] ood_parse_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[4/50] ood_bit_02 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[5/50] ood_math_02 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: ValueError: Vectors cannot be empty)
[6/50] ood_parse_04 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'parse_csv_simple' is not def)
[7/50] ood_geom_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: TypeError: manhattan_distance() missing 2 req)
[8/50] ood_geom_02 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[9/50] ood_comb_04 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'binomial_coeff' is not defin)
[10/50] ood_graph_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'count_components' is not def)
[11/50] ood_sim_04 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'simulate_ring_buffer' is not)
[12/50] ood_graph_02 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: TypeError: 'set' object does not support item)
[13/50] ood_bit_01 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[14/50] ood_geom_05 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'polygon_perimeter' is not de)
[15/50] ood_bit_04 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (ASSERTION_FAILED:)
[16/50] ood_nt_04 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'sieve_primes' is not defined)
[17/50] ood_nt_06 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[18/50] ood_sim_01 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[19/50] ood_parse_02 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'parse_cron_minutes' is not d)
[20/50] ood_sys_01 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'stack_machine' is not define)
[21/50] ood_sim_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'simulate_editor' is not defi)
[22/50] ood_comp_04 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (extraction failed)
[23/50] ood_parse_06 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'parse_url_simple' is not def)
[24/50] ood_bit_06 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[25/50] ood_comp_02 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'rle_decode' is not defined)
[26/50] ood_comb_01 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'nth_catalan' is not defined)
[27/50] ood_bit_07 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'swap_without_temp' is not de)
[28/50] ood_comb_07 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[29/50] ood_math_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: ValueError: Window size cannot be larger than)
[30/50] ood_parse_05 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'is_valid_cidr' is not define)
[31/50] ood_nt_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'mod_exp' is not defined)
[32/50] ood_graph_01 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'bfs' is not defined)
[33/50] ood_sys_02 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'eval_rpn' is not defined)
[34/50] ood_graph_06 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (ASSERTION_FAILED:)
[35/50] ood_nt_07 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[36/50] ood_comb_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[37/50] ood_bit_05 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'single_number_two' is not de)
[38/50] ood_sim_02 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[39/50] ood_nt_08 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'miller_rabin' is not defined)
[40/50] ood_graph_05 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: ValueError: Graph contains a cycle and is not)
[41/50] ood_graph_07 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[42/50] ood_math_05 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[43/50] ood_comb_06 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'partitions' is not defined)
[44/50] ood_geom_06 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'do_intersect' is not defined)
[45/50] ood_sim_05 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'simulate_rw_lock' is not def)
[46/50] ood_geom_08 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[47/50] ood_math_04 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✓
[48/50] ood_comp_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: TypeError: '<' not supported between instance)
[49/50] ood_comb_08 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'subset_sum' is not defined)
[50/50] ood_sys_03 Both `max_new_tokens` (=1024) and `max_length`(=262144) seem to have been set. `max_new_tokens` will take precedence. Please refer to the documentation for more information. (https://huggingface.co/docs/transformers/main/en/main_classes/text_generation)
✗ (RUNTIME_ERROR: NameError: name 'simulate_allocator' is not d)

================================================================================
OOD BENCHMARK COMPARISON REPORT
================================================================================

OVERALL PASS@1
Base Qwen3-4B: 34.0% (17/50)
LoRA Fine-tune: 32.0% (16/50)
Delta: -2.0%

FORMAT HEALTH (direct_code vs tool_call_wrapped vs extraction_failed)
Base: {'raw_unwrapped': 21, 'direct_code': 28, 'extraction_failed': 1}
LoRA: {'direct_code': 29, 'raw_unwrapped': 20, 'extraction_failed': 1}

BY DIFFICULTY
Difficulty   | Total  | Base         | LoRA         | Delta     
------------------------------------------------------------
easy         | 10     |  40.0% (4) |  40.0% (4) |  +0.0%
hard         | 15     |  40.0% (6) |  40.0% (6) |  +0.0%
medium       | 25     |  28.0% (7) |  24.0% (6) |  -4.0%

BY OOD CATEGORY
Category                  | Total  | Base         | LoRA         | Delta     
---------------------------------------------------------------------------
bit-manipulation          | 6      |  50.0% (3) |  50.0% (3) |  +0.0%
combinatorics             | 6      |  33.3% (2) |  33.3% (2) |  +0.0%
compression-encoding      | 3      |   0.0% (0) |   0.0% (0) |  +0.0%
computational-geometry    | 7      |  42.9% (3) |  42.9% (3) |  +0.0%
concurrency-simulation    | 5      |  40.0% (2) |  40.0% (2) |  +0.0%
domain-specific-parsing   | 5      |  20.0% (1) |  20.0% (1) |  +0.0%
finance-scientific        | 4      |  50.0% (2) |  50.0% (2) |  +0.0%
graph-algorithms          | 6      |  33.3% (2) |  16.7% (1) | -16.7%
number-theory             | 5      |  40.0% (2) |  40.0% (2) |  +0.0%
systems-level             | 3      |   0.0% (0) |   0.0% (0) |  +0.0%

Saved results to /content/epoch-1/processed/ood_benchmark_results_20260727_122230.json


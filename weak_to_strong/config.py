import torch
from dataclasses import dataclass
from typing import Optional

from weak_to_strong.loss import logconf_loss_fn, product_loss_fn, xent_loss, kl_loss


@dataclass
class ModelConfig:
    name: str
    default_lr: float
    eval_batch_size: int
    minibatch_size_per_device: Optional[int] = None
    lora_modules: Optional[list[str]] = None
    custom_kwargs: Optional[dict] = None
    gradient_checkpointing: bool = False
    model_parallel: bool = False
    default_optimizer: str = "adam"


GPT_NEOX_LORA_MODULES = ["dense_h_to_4h", "dense_4h_to_h", "query_key_value"]
GPT2_LORA_MODULES = ["c_fc", "c_proj", "c_attn"]
MISTRAL_LORA_MODULES = [
    "up_proj",
    "down_proj",
    "gate_proj",
    "k_proj",
    "q_proj",
    "v_proj",
]
OPT_LORA_MODULES = [
    "fc1",
    "fc2",
    "k_proj",
    "q_proj",
    "v_proj",
]
per_device_ram = torch.cuda.get_device_properties(0).total_memory
BFLOAT_KWARGS = {
    "torch_dtype": torch.bfloat16
    if torch.cuda.is_bf16_supported()
    else torch.float32  # okay because we're using LoRA
}
QWEN_KWARGS = {
    "trust_remote_code": True,
    "bf16": torch.cuda.is_bf16_supported(),
    "fp32": not torch.cuda.is_bf16_supported(),
    "revision": "5fde88dff770a7d036847211f5d9d9705f0caa69",
}
DEFAULT_DEFAULT_LR = 1e-5
OPT_DEFAULT_LR = 1e-3
SMALL_BATCH_SIZE = 2
LARGE_BATCH_SIZE = 32

# NOTE learning rates are not particularly tuned, work somewhat reasonably at train batch size 32
# NOTE minibatch_size_per_device needs adjusting for GPU/dataset
MODEL_CONFIGS = [
    ModelConfig(
        name="gpt2",
        default_lr=5e-5,
        eval_batch_size=LARGE_BATCH_SIZE,
        lora_modules=GPT2_LORA_MODULES,
    ),
    ModelConfig(
        name="gpt2-medium",
        default_lr=5e-5,
        eval_batch_size=LARGE_BATCH_SIZE,
        lora_modules=GPT2_LORA_MODULES,
    ),
    ModelConfig(
        name="gpt2-large",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        lora_modules=GPT2_LORA_MODULES,
    ),
    ModelConfig(
        name="gpt2-xl",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=SMALL_BATCH_SIZE,
        gradient_checkpointing=True,
        lora_modules=GPT2_LORA_MODULES,
        # Should use model_parallel on V100s (note: ironically if you have a single V100
        # it should run, but if you have multiple it won't run without model_parallel
        # because of the overhead of data parallel training).
        model_parallel=(per_device_ram < 35e9 and torch.cuda.device_count() > 1),
    ),
    ModelConfig(
        name="EleutherAI/pythia-14m",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=GPT_NEOX_LORA_MODULES,
    ),
    ModelConfig(
        name="EleutherAI/pythia-70m",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=GPT_NEOX_LORA_MODULES,
    ),
    ModelConfig(
        name="EleutherAI/pythia-160m",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=GPT_NEOX_LORA_MODULES,
    ),
    ModelConfig(
        name="EleutherAI/pythia-410m",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=GPT_NEOX_LORA_MODULES,
    ),
    ModelConfig(
        name="EleutherAI/pythia-2.8b",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=GPT_NEOX_LORA_MODULES,
    ),
    ModelConfig(
        name="EleutherAI/pythia-6.9b",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=SMALL_BATCH_SIZE,
        minibatch_size_per_device=SMALL_BATCH_SIZE,
        model_parallel=False,
        lora_modules=GPT_NEOX_LORA_MODULES,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    ModelConfig(
        name="EleutherAI/pythia-12b",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=SMALL_BATCH_SIZE,
        minibatch_size_per_device=SMALL_BATCH_SIZE,
        model_parallel=False,
        lora_modules=GPT_NEOX_LORA_MODULES,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    ModelConfig(
        name="mistralai/Mistral-7B-v0.1",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=SMALL_BATCH_SIZE,
        lora_modules=MISTRAL_LORA_MODULES,
        minibatch_size_per_device=SMALL_BATCH_SIZE,
        gradient_checkpointing=True,
        model_parallel=False,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    ModelConfig(
        name="mistralai/Mixtral-8x7B-v0.1",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=1,
        minibatch_size_per_device=1,
        lora_modules=MISTRAL_LORA_MODULES,
        gradient_checkpointing=True,
        model_parallel=True,
        custom_kwargs=BFLOAT_KWARGS,
        default_optimizer="adafactor",
    ),
    ModelConfig(
        name="Qwen/Qwen-1_8B",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=SMALL_BATCH_SIZE,
        minibatch_size_per_device=SMALL_BATCH_SIZE,
        gradient_checkpointing=True,
        model_parallel=(per_device_ram < 35e9 and torch.cuda.device_count() > 1),
        custom_kwargs=QWEN_KWARGS,
    ),
    ModelConfig(
        name="Qwen/Qwen-7B",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=SMALL_BATCH_SIZE,
        minibatch_size_per_device=SMALL_BATCH_SIZE,
        gradient_checkpointing=True,
        model_parallel=True,
        # note: you will probably not be able to run this without many gpus
        custom_kwargs=QWEN_KWARGS,
    ),
    ModelConfig(
        name="Qwen/Qwen-14B",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=SMALL_BATCH_SIZE,
        minibatch_size_per_device=SMALL_BATCH_SIZE,
        gradient_checkpointing=True,
        model_parallel=True,
        # note: probably need bf16 support and many gpus
        custom_kwargs=QWEN_KWARGS,
    ),
    ModelConfig(
        name="Qwen/Qwen-72B",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=1,
        gradient_checkpointing=True,
        model_parallel=True,
        # note: probably need bf16 support and many gpus
        custom_kwargs=QWEN_KWARGS,
        # This model is really big, save space by using adafactor.
        # Note that even then it will take up ~60GB per GPU on an 8-GPU machine.
        default_optimizer="adafactor",
    ),
    ModelConfig(
        name="facebook/opt-125m",
        default_lr=OPT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=OPT_LORA_MODULES,
    ),
    ModelConfig(
        name="facebook/opt-350m",
        default_lr=OPT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=OPT_LORA_MODULES,
    ),
    ModelConfig(
        name="facebook/opt-2.7b",
        default_lr=OPT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=OPT_LORA_MODULES,
    ),
    ModelConfig(
        name="facebook/opt-6.7b",
        default_lr=OPT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=OPT_LORA_MODULES,
        gradient_checkpointing=True,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    ModelConfig(
        name="facebook/opt-13b",
        default_lr=OPT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=True,
        lora_modules=OPT_LORA_MODULES,
        gradient_checkpointing=True,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    ModelConfig(
        name="facebook/opt-30b",
        default_lr=OPT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=True,
        lora_modules=OPT_LORA_MODULES,
        gradient_checkpointing=True,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    ModelConfig(
        name="bigscience/bloom-560m",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=GPT_NEOX_LORA_MODULES,
    ),
    ModelConfig(
        name="bigscience/bloom-3b",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=GPT_NEOX_LORA_MODULES,
        gradient_checkpointing=True,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    ModelConfig(
        name="bigscience/bloom-7b1",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=GPT_NEOX_LORA_MODULES,
        gradient_checkpointing=True,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    ModelConfig(
        name="bigscience/bloom",  # 176B parameters
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=1,
        minibatch_size_per_device=1,
        model_parallel=True,
        lora_modules=GPT_NEOX_LORA_MODULES,
        gradient_checkpointing=True,
        custom_kwargs=BFLOAT_KWARGS,
        default_optimizer="adafactor",
    ),
    ModelConfig(
        name="stabilityai/stablelm-base-alpha-3b",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=GPT_NEOX_LORA_MODULES,
    ),
    ModelConfig(
        name="stabilityai/stablelm-base-alpha-7b",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=GPT_NEOX_LORA_MODULES,
        gradient_checkpointing=True,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    ModelConfig(
        name="EleutherAI/gpt-neo-2.7B",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=["q_proj", "k_proj", "v_proj", "c_fc", "c_proj"],
    ),
    ModelConfig(
        name="EleutherAI/gpt-j-6b",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=["q_proj", "k_proj", "v_proj", "fc_in", "fc_out"],
        gradient_checkpointing=True,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    ModelConfig(
        name="EleutherAI/gpt-neox-20b",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=True,
        lora_modules=GPT_NEOX_LORA_MODULES,
        gradient_checkpointing=True,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    ModelConfig(
        name="meta-llama/Llama-2-7b-hf",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=GPT_NEOX_LORA_MODULES,
        gradient_checkpointing=True,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    ModelConfig(
        name="meta-llama/Llama-2-13b-hf",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=True,
        lora_modules=GPT_NEOX_LORA_MODULES,
        gradient_checkpointing=True,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    ModelConfig(
        name="meta-llama/Llama-2-70b-hf",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=True,
        lora_modules=GPT_NEOX_LORA_MODULES,
        gradient_checkpointing=True,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    ModelConfig(
        name="huggyllama/llama-7b",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=False,
        lora_modules=GPT_NEOX_LORA_MODULES,
        gradient_checkpointing=True,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    ModelConfig(
        name="huggyllama/llama-13b",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=True,
        lora_modules=GPT_NEOX_LORA_MODULES,
        gradient_checkpointing=True,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    ModelConfig(
        name="huggyllama/llama-30b",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=True,
        lora_modules=GPT_NEOX_LORA_MODULES,
        gradient_checkpointing=True,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    ModelConfig(
        name="huggyllama/llama-65b",
        default_lr=DEFAULT_DEFAULT_LR,
        eval_batch_size=LARGE_BATCH_SIZE,
        minibatch_size_per_device=LARGE_BATCH_SIZE,
        model_parallel=True,
        lora_modules=GPT_NEOX_LORA_MODULES,
        gradient_checkpointing=True,
        custom_kwargs=BFLOAT_KWARGS,
    ),
    
]
MODELS_DICT: dict[str, ModelConfig] = {
    model_config.name: model_config for model_config in MODEL_CONFIGS
}


loss_dict = {
    "logconf": logconf_loss_fn(),
    "product": product_loss_fn(),
    "xent": xent_loss(),
    "kl": kl_loss(),
}

VALID_LOSSES: list[str] = list(loss_dict.keys())


def get_config_foldername(config: dict) -> str:
    def shorten_key(key: str) -> str:
        return "".join(word[0] for word in key.split("_"))

    def shorten_value(value) -> str:
        if isinstance(value, bool):
            return "1" if value else "0"
        elif isinstance(value, str):
            value = value.split("/")[-1]
            if "_" in value:
                return "_".join(word[:4] for word in value.split("_"))
            else:
                return value
        else:
            return str(value)

    return "-".join(
        f"{shorten_key(k)}={shorten_value(v)}" for k, v in sorted(config.items())
    )

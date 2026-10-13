from contextlib import asynccontextmanager
from io import BytesIO
import os
import random

import torch
from compel import Compel, ReturnedEmbeddingsType
from diffusers import StableDiffusionXLPipeline
from diffusers.callbacks import SDXLCFGCutoffCallback

import uvicorn
from fastapi import FastAPI
from fastapi.responses import Response

from prompts import PROMPT_PREFIX, build_negative_prompt
from schedulers import SCHEDULERS

MODELS = (
    ("models/waiIllustriousSDXL_v170.safetensors", "https://huggingface.co/LyliaEngine/waiIllustriousSDXL_v170/blob/main/waiIllustriousSDXL_v170.safetensors"),
    ("models/ChenkinNoob-XL-V0.5.safetensors", "https://huggingface.co/ChenkinLab/ChenkinNoob-XL-V0.5/blob/main/ChenkinNoob-XL-V0.5.safetensors"),
    ("models/Illustrious-XL-v2.0.safetensors", "https://huggingface.co/OnomaAIResearch/Illustrious-XL-v2.0/blob/main/Illustrious-XL-v2.0.safetensors"),
    ("models/NoobAI-XL-v1.1.safetensors", "https://huggingface.co/Laxhar/noobai-XL-1.1/blob/main/noobai-XL-1.1.safetensors"),
)[0]

ADAPTER_NAMES = ("character", "style", "secondary_style", "concept")

# SDXL Base Ratios: https://github.com/Stability-AI/generative-models/blob/main/scripts/demo/sampling.py
SIZES = ((1536, 1536), (1824, 1248), (1248, 1824), (1152, 2048))

class ImageGenerator:
    def __init__(self):
        self.pipe = self._load_pipeline()

        self.loaded_loras = {}
        self.active_loras = {}

        self.compel = Compel(
            tokenizer=[self.pipe.tokenizer, self.pipe.tokenizer_2],
            text_encoder=[self.pipe.text_encoder, self.pipe.text_encoder_2],
            truncate_long_prompts=False,
            returned_embeddings_type=ReturnedEmbeddingsType.PENULTIMATE_HIDDEN_STATES_NON_NORMALIZED,
            requires_pooled=[False, True]
        )
        self.empty_embeds, _ = self.compel("")

        self.embedding_cache = {
            "positive": {},
            "negative": {},
            "padded": {}
        }

        self.callback = SDXLCFGCutoffCallback(cutoff_step_ratio=0.4)

    def _load_pipeline(self):
        pipe = StableDiffusionXLPipeline.from_single_file(
            MODELS[0] if os.path.isfile(MODELS[0]) else MODELS[1],
            torch_dtype=torch.float16
        ).to("cuda")

        pipe.fuse_qkv_projections()

        pipe.unet.to(memory_format=torch.channels_last)
        pipe.vae.to(memory_format=torch.channels_last)

        if torch.cuda.get_device_properties(0).total_memory < 16 * 1024**3:
            pipe.vae.enable_slicing()
            pipe.vae.enable_tiling()

        self.scheduler_config = pipe.scheduler.config

        return pipe

    def set_scheduler(self, name):
        scheduler, config = SCHEDULERS[name]
        self.pipe.scheduler = scheduler.from_config(self.scheduler_config, **config)

    def _update_lora(self, name, loaded_name, adapter_name):
        if name == loaded_name:
            return loaded_name

        if loaded_name:
            self.pipe.delete_adapters(adapter_name)

        if name:
            self.pipe.load_lora_weights("models/loras", weight_name=f"{name}.safetensors", adapter_name=adapter_name)

        return name

    def apply_loras(self, body):
        previous_loras = self.active_loras.copy()

        for adapter in ADAPTER_NAMES:
            self.loaded_loras[adapter] = self._update_lora(
                body.get(adapter), self.loaded_loras.get(adapter), adapter
            )

        if adapters := [adapter for adapter in ADAPTER_NAMES if body.get(adapter)]:
            multiple_styles = "style" in adapters and "secondary_style" in adapters

            self.active_loras = {
                adapter: body.get(f"{adapter}_weight", 0.8 if multiple_styles and adapter in ("style", "secondary_style") else 1.0)
                for adapter in adapters
            }

            self.pipe.set_adapters(adapters, adapter_weights=[self.active_loras[adapter] for adapter in adapters])
        else:
            self.pipe.disable_lora()
            self.active_loras = {}

        if previous_loras != self.active_loras:
            for cache in self.embedding_cache.values():
                cache.clear()

    def _get_embeddings(self, cache, prompt):
        if prompt not in cache:
            cache[prompt] = self.compel(prompt)

        return cache[prompt]

    def _get_padded_embeddings(self, prompt, negative_prompt):
        key = (prompt, negative_prompt)

        if key in self.embedding_cache["padded"]:
            prompt_embeds, negative_embeds = self.embedding_cache["padded"][key]
            pooled = self.embedding_cache["positive"][prompt][1]
            negative_pooled = self.embedding_cache["negative"][negative_prompt][1]
        else:
            prompt_embeds, pooled = self._get_embeddings(self.embedding_cache["positive"], prompt)
            negative_embeds, negative_pooled = self._get_embeddings(self.embedding_cache["negative"], negative_prompt)

            prompt_embeds, negative_embeds = self.compel.pad_conditioning_tensors_to_same_length(
                [prompt_embeds, negative_embeds],
                precomputed_padding=self.empty_embeds # Prevent EmbeddingsProviderMulti.empty_z AttributeError
            )
            self.embedding_cache["padded"][key] = (prompt_embeds, negative_embeds)

        return prompt_embeds, pooled, negative_embeds, negative_pooled

    def generate_image(self, prompt, size, steps, cfg, negative_prompt, seed):
        prompt_embeds, pooled, negative_embeds, negative_pooled = self._get_padded_embeddings(prompt, negative_prompt)

        image = BytesIO()

        self.pipe(
            height=size[0],
            width=size[1],

            num_inference_steps=steps,
            guidance_scale=cfg,

            num_images_per_prompt=1,

            prompt_embeds=prompt_embeds,
            pooled_prompt_embeds=pooled,
            negative_prompt_embeds=negative_embeds,
            negative_pooled_prompt_embeds=negative_pooled,

            generator=torch.Generator("cuda").manual_seed(seed) if seed is not None else None,

            original_size=size,
            target_size=size,

            callback_on_step_end=self.callback
        ).images[0].save(image, format="PNG")

        return image.getvalue()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.generator = ImageGenerator()
    yield

app = FastAPI(lifespan=lifespan)

@app.post("/")
async def generate(body: dict):
    generator = app.state.generator

    generator.set_scheduler(body.get("scheduler", "Euler a"))
    generator.apply_loras(body)

    return Response(generator.generate_image(
        prompt=f"{PROMPT_PREFIX}{body['prompt']}",
        size=tuple(body["size"]) if body.get("size") else random.choice(SIZES),
        steps=body.get("steps", 28), # 12 20 28
        cfg=body.get("cfg", 5.0), # 4–7
        negative_prompt=body.get("negative_prompt") or build_negative_prompt(body['prompt']),
        seed=body.get("seed")
    ), media_type="image/png")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7869)
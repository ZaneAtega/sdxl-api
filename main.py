from contextlib import asynccontextmanager
from io import BytesIO
from os.path import isfile
import random

import torch
from compel import CompelForSDXL
from diffusers import StableDiffusionXLPipeline
from diffusers.callbacks import SDXLCFGCutoffCallback

import uvicorn
from fastapi import FastAPI
from fastapi.responses import Response

from style_prompts import build_style_prompt, build_negative_style_prompt
from schedulers import SCHEDULERS

MODELS = (
    ("models/waiIllustriousSDXL_v170.safetensors", "https://huggingface.co/LyliaEngine/waiIllustriousSDXL_v170/blob/main/waiIllustriousSDXL_v170.safetensors"),
    ("models/ChenkinNoob-XL-V0.5.safetensors", "https://huggingface.co/ChenkinLab/ChenkinNoob-XL-V0.5/blob/main/ChenkinNoob-XL-V0.5.safetensors"),
    ("models/Illustrious-XL-v2.0.safetensors", "https://huggingface.co/OnomaAIResearch/Illustrious-XL-v2.0/blob/main/Illustrious-XL-v2.0.safetensors"),
    ("models/NoobAI-XL-v1.1.safetensors", "https://huggingface.co/Laxhar/noobai-XL-1.1/blob/main/noobai-XL-1.1.safetensors"),
)[0]

ADAPTER_NAMES = ("character", "style", "secondary_style", "negative_style", "concept")

# SDXL Base Ratios: https://github.com/Stability-AI/generative-models/blob/main/scripts/demo/sampling.py
SIZES = ((1536, 1536), (1824, 1248), (1248, 1824), (1152, 2048))

class ImageGenerator:
    def __init__(self):
        self.pipe = self._load_pipeline()

        self.loaded_loras = {}
        self.active_loras = {}

        self.compel = CompelForSDXL(self.pipe)
        self.conditioning_cache = {}

        self.callback = SDXLCFGCutoffCallback(cutoff_step_ratio=0.4)

    def _load_pipeline(self):
        pipe = StableDiffusionXLPipeline.from_single_file(
            MODELS[0] if isfile(MODELS[0]) else MODELS[1],
            torch_dtype=torch.float16,
            use_safetensors=True
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
            self.active_loras = {}
            multiple_styles = "style" in adapters and "secondary_style" in adapters

            for adapter in adapters:
                if weight := body.get(f"{adapter}_weight"):
                    self.active_loras[adapter] = weight
                    continue

                self.active_loras[adapter] = (
                    -1.0 if adapter == "negative_style" else
                    0.8 if multiple_styles and adapter in ("style", "secondary_style") else
                    1.0
                )

            self.pipe.set_adapters(adapters, adapter_weights=[self.active_loras[adapter] for adapter in adapters])
        else:
            self.pipe.disable_lora()
            self.active_loras = {}

        if previous_loras != self.active_loras:
            self.conditioning_cache.clear()

    def _get_conditioning(self, prompts):
        key = tuple(prompts.values())

        if key not in self.conditioning_cache:
            self.conditioning_cache[key] = self.compel(**prompts)

        return self.conditioning_cache[key]

    def generate_image(self, prompts, size, steps, cfg, seed):
        image = BytesIO()

        conditioning = self._get_conditioning(prompts)

        self.pipe(
            height=size[0],
            width=size[1],

            num_inference_steps=steps,
            guidance_scale=cfg,

            num_images_per_prompt=1,

            prompt_embeds=conditioning.embeds,
            pooled_prompt_embeds=conditioning.pooled_embeds,
            negative_prompt_embeds=conditioning.negative_embeds,
            negative_pooled_prompt_embeds=conditioning.negative_pooled_embeds,

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

    prompt = body["prompt"]
    style_prompt = body.get("style_prompt") or build_style_prompt(prompt)
    size = tuple(body["size"]) if body.get("size") else random.choice(SIZES)
    negative_style_prompt = body.get("negative_style_prompt") or build_negative_style_prompt(prompt, size)

    """
    prompts = {
        "main_prompt": prompt,
        "style_prompt": style_prompt,
        "negative_prompt": body["negative_prompt"],
        "negative_style_prompt": negative_style_prompt
    } if body.get("negative_prompt") else {
        "main_prompt": f"{style_prompt}, {prompt}",
        "negative_prompt": negative_style_prompt
    }
    """

    prompts = {
        "main_prompt": f"{style_prompt}, {prompt}",
        "negative_prompt": negative_style_prompt + (f", {body['negative_prompt']}" if body.get("negative_prompt") else "")
    }

    return Response(generator.generate_image(
        prompts,
        size=size,
        steps=body.get("steps", 28), # 12 20 28
        cfg=body.get("cfg", 5.0), # 4–7
        seed=body.get("seed")
    ), media_type="image/png")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7869)
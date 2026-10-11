from contextlib import asynccontextmanager
from io import BytesIO
import random

import torch
from compel import Compel, ReturnedEmbeddingsType
from diffusers import StableDiffusionXLPipeline
from diffusers.callbacks import SDXLCFGCutoffCallback

import uvicorn
from fastapi import FastAPI
from fastapi.responses import Response

from schedulers import SCHEDULERS

MODEL = "models/" + (
    "waiIllustriousSDXL_v170",
    "ChenkinNoob-XL-V0.5",
    "Illustrious-XL-v2.0",
    "NoobAI-XL-v1.1"
)[0] + ".safetensors"

ADAPTER_NAMES = ("style", "character")

SIZES = (
    (1024, 1024),

    (1128, 1024),
    (1352, 1024),
    (1368, 1024),
    (1392, 1024),
    (1496, 1024),
    (1820, 1024),
    (2196, 1024),
    (2208, 1024),

    (1024, 1368),
    (1024, 1392),
    (1024, 1432),
    (1024, 1792),
    (1024, 1820)
)

NEGATIVE_PROMPT = ""

class ImageGenerator:
    def __init__(self):
        self.pipe = self._load_pipeline()
        self.loaded_loras = {}

        self.compel = Compel(
            tokenizer=[self.pipe.tokenizer, self.pipe.tokenizer_2],
            text_encoder=[self.pipe.text_encoder, self.pipe.text_encoder_2],
            truncate_long_prompts=False,
            returned_embeddings_type=ReturnedEmbeddingsType.PENULTIMATE_HIDDEN_STATES_NON_NORMALIZED,
            requires_pooled=[False, True]
        )
        self.empty_embeds, _ = self.compel("")
        self.negative_cache = {}

        self.callback = SDXLCFGCutoffCallback(cutoff_step_ratio=0.4)

    def _load_pipeline(self):
        pipe = StableDiffusionXLPipeline.from_single_file(
            MODEL,
            torch_dtype=torch.float16
        ).to("cuda")

        pipe.fuse_qkv_projections()

        pipe.unet.to(memory_format=torch.channels_last)
        pipe.vae.to(memory_format=torch.channels_last)

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
        for adapter in ADAPTER_NAMES:
            self.loaded_loras[adapter] = self._update_lora(
                body.get(adapter), self.loaded_loras.get(adapter), adapter
            )

        adapters = [adapter for adapter in ADAPTER_NAMES if body.get(adapter)]

        if adapters:
            self.pipe.set_adapters(adapters, adapter_weights=[body.get(f"{adapter}_weight", 1.0) for adapter in adapters])
        else:
            self.pipe.disable_lora()

    def generate_image(self, prompt, size, steps, cfg, negative_prompt, seed):
        prompt_embeds, pooled = self.compel(prompt)

        if negative_prompt not in self.negative_cache:
            self.negative_cache[negative_prompt] = self.compel(negative_prompt)

        negative_embeds, negative_pooled = self.negative_cache[negative_prompt]

        prompt_embeds, negative_embeds = self.compel.pad_conditioning_tensors_to_same_length(
            [prompt_embeds, negative_embeds],
            precomputed_padding=self.empty_embeds # Prevent EmbeddingsProviderMulti.empty_z AttributeError
        )

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
        prompt=body["prompt"],
        size=tuple(body["size"]) if body.get("size") else random.choice(SIZES),
        steps=body.get("steps", 28), # 12 20 28
        cfg=body.get("cfg", 5.0), # 4–7
        negative_prompt=body.get("negative_prompt", NEGATIVE_PROMPT),
        seed=body.get("seed")
    ), media_type="image/png")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=7869)
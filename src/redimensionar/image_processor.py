import io
import os
from PIL import Image, ImageOps
from redimensionar.logger import get_logger

log = get_logger("image_processor")

TAMANHO = 1200
MAX_BYTES_NORMAL = 2 * 1024 * 1024
MAX_BYTES_REMFUNDO = 350 * 1024


def corrigir_orientacao(img: Image.Image) -> Image.Image:
    out = ImageOps.exif_transpose(img)
    return out if out is not None else img


def calcular_corte_central(largura: int, altura: int):
    lado = min(largura, altura)
    left = (largura - lado) // 2
    top = (altura - lado) // 2
    return left, top, lado


def recortar_e_redimensionar(img: Image.Image, left: int = None, top: int = None, lado: int = None) -> Image.Image:
    w, h = img.size
    if w == h == TAMANHO:
        return img
    if lado is None:
        lado = min(w, h)
    lado = max(1, min(lado, w, h))
    if left is None or top is None:
        left = (w - lado) // 2
        top = (h - lado) // 2
    else:
        left = max(0, min(left, w - lado))
        top = max(0, min(top, h - lado))
    img = img.crop((left, top, left + lado, top + lado))
    img = img.resize((TAMANHO, TAMANHO), Image.LANCZOS)
    log.debug("recortar_e_redimensionar: %dx%d -> %d,%d lado=%d", w, h, left, top, lado)
    return img


def aplicar_marca_dagua(img: Image.Image, logo_path: str) -> Image.Image:
    logo = Image.open(logo_path).convert("RGBA")
    tam_logo = max(1, int(img.width * 0.115))
    logo.thumbnail((tam_logo, tam_logo), Image.LANCZOS)
    r, g, b, a = logo.split()
    a = a.point(lambda v: min(v, 46))
    logo = Image.merge("RGBA", (r, g, b, a))
    logo = logo.rotate(-25, expand=True, fillcolor=(0, 0, 0, 0))
    img_rgba = img.convert("RGBA")
    espaco = int(max(logo.width, logo.height) * 0.85)
    margem = max(logo.width, logo.height)
    for y in range(-margem, img.height + margem, espaco):
        offset_x = espaco // 2 if (y // espaco) % 2 else 0
        for x in range(-margem + offset_x, img.width + margem, espaco):
            img_rgba.paste(logo, (x, y), logo)
    log.debug("marca d'agua aplicada — logo %s, tamanho %dx%d",
              os.path.basename(logo_path), logo.width, logo.height)
    return img_rgba.convert("RGB")


def ajustar_qualidade(img: Image.Image, max_bytes: int) -> io.BytesIO:
    qualidade = 95
    while True:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=qualidade, optimize=True)
        if buf.tell() <= max_bytes or qualidade <= 10:
            log.debug("Qualidade final: %d, tamanho: %d bytes", qualidade, buf.tell())
            return buf
        qualidade -= 5


def remover_fundo(img: Image.Image, escala_porc: int = 100) -> Image.Image:
    from rembg import remove as rembg_remove

    saida = rembg_remove(img)
    if saida.mode != "RGBA":
        saida = saida.convert("RGBA")

    bbox = saida.getbbox()
    if bbox is None or escala_porc >= 100:
        fundo = Image.new("RGB", saida.size, (255, 255, 255))
        mascara = saida.split()[3]
        fundo.paste(saida, (0, 0), mascara)
        return fundo

    produto = saida.crop(bbox)
    pw, ph = produto.size
    lado_max = max(pw, ph)
    if lado_max == 0:
        return Image.new("RGB", (TAMANHO, TAMANHO), (255, 255, 255))

    fator = (escala_porc / 100.0) * TAMANHO / lado_max
    novo_w = max(1, int(pw * fator))
    novo_h = max(1, int(ph * fator))
    produto_redim = produto.resize((novo_w, novo_h), Image.LANCZOS)

    fundo = Image.new("RGB", (TAMANHO, TAMANHO), (255, 255, 255))
    x = (TAMANHO - novo_w) // 2
    y = (TAMANHO - novo_h) // 2
    mascara = produto_redim.split()[3]
    fundo.paste(produto_redim, (x, y), mascara)
    log.debug("remover_fundo: bbox=%s, escala=%d%%, produto=%dx%d",
              bbox, escala_porc, novo_w, novo_h)
    return fundo

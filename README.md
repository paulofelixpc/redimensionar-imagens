# LS Imagecomm

Ferramenta desktop **offline** para redimensionar imagens para **1200×1200**, remover fundo com IA e adicionar marca d'água.

## Funcionalidades

| Recurso | Descrição |
|---------|-----------|
| Redimensionar | Corta e redimensiona para 1200×1200 (máx 2MB) |
| Remover fundo | Remove fundo com IA via rembg (máx 350KB) |
| Marca d'água | Grade diagonal do seu logo sobre a imagem |
| Corte visual | Seletor de corte com zoom, pan e redimensionamento |
| Corte individual | Cada imagem mantém seu próprio corte salvo |
| Escala do produto | Controle do tamanho do produto no fundo branco |
| Renomeação SEO | Nome base + numeração automática (`produto-1.jpg`) |
| Notificação | Balão no system tray ao finalizar |
| Progresso na barra de tarefas | Barra de progresso no ícone do Windows |
| Atalhos de teclado | Ctrl+O, Ctrl+S, Ctrl++/-, ←/→ |
| Logs | Log rotativo em `~/.ls-imagecomm/logs/` |
| Totalmente offline | Sem nuvem, sem internet, sem contas |

## Instalação

## Downloads

| Versão | Link |
|--------|------|
| Instalador (recomendado) | [LS Imagecomm Setup.exe](https://github.com/paulofelixpc/redimensionar-imagens/releases/latest) |
| Código-fonte | [github.com/paulofelixpc/redimensionar-imagens](https://github.com/paulofelixpc/redimensionar-imagens) |

## Instalação

```bash
git clone https://github.com/paulofelixpc/redimensionar-imagens
cd redimensionar-imagens
python -m venv .venv
.venv\Scripts\pip install -e .
.venv\Scripts\python -m redimensionar
```

## Como usar

1. **Selecionar imagens** — Ctrl+O ou botão "Selecionar Imagens"
2. **Ajustar corte** — Arraste o quadrado ou as alças nos cantos; use zoom +/− e ajustar
3. **Navegar** — ←/→ ou botões ◀ ▶ para ajustar o corte de cada imagem individualmente
4. **Modo** — Escolha "Apenas redimensionar" ou "Remover fundo + redimensionar"
5. **Escala** (modo remover fundo) — Ajuste o tamanho do produto no canvas 1200×1200
6. **Marca d'água** — Marque a opção, selecione o logo (PNG recomendado)
7. **Nome base** — Digite o nome SEO (ex: `camiseta-azul`)
8. **Processar** — Ctrl+S, escolha a pasta de destino

## Atalhos

| Tecla | Ação |
|-------|------|
| Ctrl+O | Abrir imagens |
| Ctrl+S | Processar e salvar |
| Ctrl++ | Zoom in |
| Ctrl+- | Zoom out |
| Ctrl+0 | Ajustar zoom |
| ← / → | Navegar entre imagens |

## Estrutura

```
src/redimensionar/
├── __init__.py
├── __main__.py       # Ponto de entrada
├── app.py            # Interface gráfica (PySide6)
├── crop_widget.py    # Widget de corte com zoom/pan
├── image_processor.py # Processamento (Pillow + rembg)
└── logger.py         # Logging rotativo
```

## Tecnologias

- Python 3.10+
- PySide6 (interface)
- Pillow (processamento de imagem)
- rembg (remoção de fundo por IA)
- NSIS (instalador Windows)

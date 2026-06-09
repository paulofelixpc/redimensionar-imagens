# Changelog

## [1.3.0] — 2026-06-09

### Adicionado
- Tema escuro/claro com alternância pelo menu Exibir
- Botão "Cancelar" durante o processamento
- Suporte a dark mode persistente em `~/.ls-imagecomm/config.json`
- Placeholder "Nome do produto" com preenchimento automático do nome do arquivo
- ETA (tempo restante) na barra de status durante processamento
- Design system com paleta profissional (azul #004B87, verde #00A86B)
- Seletor de modo visual (radio buttons flat estilizados)

### Alterado
- Layout completo reformulado: stage (70%) + inspector (320px)
- Stage agora com fundo escuro #181B1F e bordas arredondadas
- Progresso: barra fina (8px) sem texto, gradiente azul→verde
- Zoom: botões individuais com borda, centralizados abaixo da view
- Navegação movida para o painel inspector
- CTA "PROCESSAR E SALVAR" fixo na base do cartão direito
- Cores atualizadas: fundo #F1F4FB, texto #1E293B, bordas #94A3B8

### Corrigido
- Placeholder "Selecione imagens para começar" centralizado sem sobreposição
- Removido aviso `QFont::setPixelSize` (font-size 0 no QSS)
- Janela centralizada na tela ao iniciar
- Fórmula de escala do produto simplificada (agora respeita o percentual)

### Técnico
- `theme.py`: sistema de temas com LightColors/DarkColors e QSS dinâmico
- `crop_widget.py`: QPainterPath com borda arredondada no placeholder
- Suporte a `QGraphicsDropShadowEffect` nos cartões
- Logs DEBUG no image_processor para rastreio de escala

---

## [1.1.0] — 2026-04-xx

### Adicionado
- Substituição do modelo u2net para BiRefNet-general (qualidade superior)
- Fallback automático para CPU em caso de erro de GPU
- Notificação no system tray ao finalizar processamento
- Barra de progresso no ícone da taskbar (Windows)
- Grade de corte com alças redimensionáveis

### Corrigido
- Tratamento de erro para GPU indisponível
- Orientação de câmera (EXIF) corrigida automaticamente

---

## [1.0.0] — 2026-03-xx

### Adicionado
- Versão inicial do LS Imagecomm
- Redimensionamento para 1200×1200
- Remoção de fundo com IA (rembg + u2net)
- Marca d'água com logo em grade diagonal
- Corte visual interativo com zoom/pan
- Renomeação SEO com numeração automática
- Atalhos de teclado
- Instalador NSIS

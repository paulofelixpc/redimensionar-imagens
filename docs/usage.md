# Guia de Uso — LS Imagecomm

## Índice

1. [Primeiros passos](#primeiros-passos)
2. [Seleção de imagens](#seleção-de-imagens)
3. [Ajuste de corte](#ajuste-de-corte)
4. [Modos de processamento](#modos-de-processamento)
5. [Escala do produto](#escala-do-produto)
6. [Marca d'água](#marca-dágua)
7. [Processamento](#processamento)
8. [Atalhos de teclado](#atalhos-de-teclado)
9. [Solução de problemas](#solução-de-problemas)

---

## Primeiros passos

Ao abrir o LS Imagecomm, você verá:

- **Painel esquerdo (Stage)**: Área de visualização e ajuste da imagem
- **Painel direito (Inspector)**: Configurações de processamento

A janela abre centralizada na tela.

## Seleção de imagens

Clique em **"Selecionar"** ou pressione `Ctrl+O` para escolher uma ou mais imagens.

Formatos suportados: PNG, JPG, JPEG, WEBP, BMP, GIF, TIFF.

O nome base para os arquivos de saída é preenchido automaticamente com o nome do primeiro arquivo selecionado. Você pode editá-lo manualmente.

## Ajuste de corte

Cada imagem exibe um quadrado de corte que define a área que será recortada para 1200×1200.

- **Mover**: Arraste o quadrado para reposicionar o corte
- **Redimensionar**: Arraste as alças nos cantos do quadrado
- **Zoom**: Use os botões `−` e `+` abaixo da imagem, ou a roda do mouse
- **Ajustar**: Clique em "Ajustar" para enquadrar a imagem inteira na área de visualização

Cada imagem mantém seu próprio corte salvo individualmente.

## Modos de processamento

### Apenas redimensionar
Corta a imagem para 1200×1200 e ajusta a qualidade para no máximo 2MB por arquivo. Ideal quando o fundo já está adequado.

### Remover fundo + redimensionar
Remove o fundo usando o modelo de IA BiRefNet-general, depois redimensiona para 1200×1200 com limite de 350KB.

> **Nota**: A primeira execução baixa o modelo (~224MB) automaticamente para `~/.u2bit/birefnet-general.onnx`.

## Escala do produto

No modo "Remover fundo", o controle **"Escala"** ajusta o tamanho do produto no canvas branco final:

- **100%**: O produto ocupa o tamanho natural extraído do fundo
- **50%**: O produto fica com metade do tamanho, centralizado
- **10%**: Produto mínimo, com bastante espaço ao redor

## Marca d'água

1. Marque a opção **"Marca d'água"**
2. Clique em **"Logo…"** e selecione uma imagem PNG
3. O logo será aplicado em grade diagonal (-25°) com opacidade reduzida

> Recomendação: Use PNG com fundo transparente para melhores resultados.

## Processamento

1. Configure as opções desejadas
2. Clique em **"PROCESSAR E SALVAR"** ou pressione `Ctrl+S`
3. Escolha a pasta de destino
4. Acompanhe o progresso pela barra e status
5. Para interromper, clique em **"Cancelar"**

Ao finalizar, uma mensagem exibe o resultado e uma notificação aparece no system tray.

## Atalhos de teclado

| Tecla | Ação |
|-------|------|
| `Ctrl+O` | Abrir imagens |
| `Ctrl+S` | Processar e salvar |
| `Ctrl++` | Zoom in |
| `Ctrl+-` | Zoom out |
| `Ctrl+0` | Ajustar zoom à janela |
| `←` | Imagem anterior |
| `→` | Próxima imagem |
| `Alt+F4` | Sair |

## Solução de problemas

### "Falha ao remover fundo"
- Verifique se o modelo foi baixado: `~/.u2bit/birefnet-general.onnx`
- Tente executar novamente — a segunda execução é mais rápida
- Consulte os logs: `~/.ls-imagecomm/logs/application.log`

### A barra de progresso não aparece
- O progresso só é exibido durante o processamento ativo
- Verifique se o botão "PROCESSAR E SALVAR" está habilitado

### O programa não abre
- Verifique os logs em `~/.ls-imagecomm/logs/application.log`
- Certifique-se de que o instalador foi executado como administrador

### GPU não detectada
- O modelo BiRefNet funciona prioritariamente em GPU via DirectML
- Se a GPU não tiver VRAM suficiente, o fallback automático para CPU é ativado
- Processamento em CPU é mais lento, mas funciona

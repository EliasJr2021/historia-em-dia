# História em Dia — carrossel diário no Instagram

Automação que lê as páginas de **historiaemdia.com.br** (da mais antiga para a mais recente), usa o **Claude** para resumir e revisar, monta um carrossel de até 10 slides (1080×1350) e publica em **@historia.em.diaa**, um por dia.

Começa em **modo manual**: todo carrossel vira um Issue com pré-visualização e só é publicado quando você comenta `/aprovar`.

```
prepare.yml (diário) → site → Claude (extrai + revisa) → Pillow (slides) → branch `media` (Pages)
      → Issue "[Aprovar]" → você comenta /aprovar → publish.yml → Instagram
refresh-token.yml (semanal) renova o token do Instagram
```

## Segurança — leia primeiro
- **Nunca cole chaves ou tokens em chats, e-mails ou no código.** Eles só entram em *Settings › Secrets and variables › Actions*.
- O repositório é **público** (necessário para o GitHub Pages gratuito). Os segredos ficam fora do código.
- Só comentários do **dono** do repositório aprovam publicações (`author_association == OWNER`).
- Defina um **limite de gasto** na conta da API Anthropic (console › Limits).

## Passo a passo

### 1. Criar o repositório (conta EliasJr2021)
1. Em https://github.com/new: nome `historia-em-dia`, **Public**, sem README/.gitignore/licença.
2. No computador, dentro da pasta do projeto:
   ```bash
   git init -b main
   git add .
   git commit -m "Projeto História em Dia"
   git remote add origin https://github.com/EliasJr2021/historia-em-dia.git
   git push -u origin main
   ```
   (ou, com a GitHub CLI: `gh repo create EliasJr2021/historia-em-dia --public --source=. --push`)
3. *Settings › Actions › General › Workflow permissions* → **Read and write permissions** → Save.

### 2. Chave da API Anthropic
1. https://console.anthropic.com → *API keys* → criar chave. Adicione crédito pré-pago e configure o limite de gasto.
2. Guarde no GitHub como segredo **`ANTHROPIC_API_KEY`**.

### 3. Instagram (API do Instagram com Instagram Login — não precisa de Página do Facebook)
Os nomes dos menus da Meta mudam com frequência; se algo estiver diferente, siga o equivalente.
1. Conta **Profissional** (já feito). O perfil deve estar **público**.
2. Entre em https://developers.facebook.com com uma conta do Facebook e registre-se como desenvolvedor.
3. **Meus apps › Criar app** → tipo/caso de uso para negócios (“Outro”/“Business”) → nome, ex.: *Historia em Dia Bot*.
4. No painel do app, adicione o produto **Instagram** › **API setup with Instagram login**.
5. Confirme as permissões `instagram_business_basic` e `instagram_business_content_publish`.
6. *App roles › Roles › Add People › Instagram Testers*: adicione **@historia.em.diaa**. Depois, no app do Instagram: *Configurações › Apps e sites › Convites de testador* → **aceitar**.
7. De volta a *API setup with Instagram login*: **Add account / Generate token** para @historia.em.diaa, autorize e copie:
   - o **token de acesso** → segredo **`IG_TOKEN_INICIAL`**;
   - o **ID da conta do Instagram** → segredo **`IG_USER_ID`**.
8. Para o app publicar só na **sua** conta, o modo de desenvolvimento deve bastar, sem App Review. Se a Meta exigir revisão, o teste da Fase 0 mostrará o erro.

### 4. Chave que protege o token no repositório
```bash
pip install cryptography && python scripts/gerar_chave.py
```
Guarde a saída como segredo **`STATE_KEY`**. O token renovado é salvo cifrado em `state/state.json`.

### 5. Variáveis (opcionais) — *Settings › Secrets and variables › Actions › Variables*
| Variável | Padrão | Uso |
|---|---|---|
| `APPROVAL_MODE` | `manual` | `auto` publica sem aprovação quando a revisão está ok |
| `CLAUDE_MODEL` | `claude-sonnet-5-5` | `claude-haiku-5-5` reduz o custo |
| `ORDER` | `chronological` | ou `page` (ordem da página) |
| `MAX_SLIDES` | `10` | de 4 a 10 |
| `AI_IMAGE_NOTICE` | `false` | `true` acrescenta “Imagem ilustrativa gerada por IA.” |
| `MEDIA_BASE_URL` | Pages do repositório | alternativa: `https://raw.githubusercontent.com/EliasJr2021/historia-em-dia/media` |
| `SITE_BASE` | `https://historiaemdia.com.br` | |

### 6. Fase 0 — testes de viabilidade
1. *Actions › Fase 0 - testes de viabilidade › Run workflow* (marque **media**). Ele testa a API do site a partir do GitHub, as imagens de capa e cria a branch `media`.
2. *Settings › Pages › Build and deployment*: **Deploy from a branch** → branch **`media`**, pasta **/(root)** → Save. Rode a Fase 0 de novo; deve aparecer ✅ na URL pública.
3. Rode mais uma vez marcando **instagram** para validar token e cota.
4. Opcional, publica de verdade um carrossel de teste (apague depois):
   `python -m scripts.teste_instagram --publicar URL1 URL2 URL3`

Se a API REST do site falhar (plugin de segurança), o robô usa o sitemap. Se ambos falharem, libere o acesso no plugin.

### 7. Semana de aprovação manual
1. *Actions › Preparar carrossel › Run workflow* (depois roda sozinho todo dia às 13:00 UTC = 10:00 em Recife).
2. Chega um **Issue** “[Aprovar] …” com os slides e a legenda. Você pode **editar a legenda no próprio Issue**.
3. Comente **`/aprovar`** para publicar ou **`/rejeitar`** para pular a página.
4. Ative as notificações do repositório (*Watch › All activity*) e use o app do GitHub no celular.
5. Itens marcados **retido** foram sinalizados pela revisão automática; leia o motivo antes de aprovar.

**Critério para ligar o modo automático:** 7 posts, pelo menos 6 aprovados sem edição, zero falhas e nenhum conteúdo inadequado. Então defina `APPROVAL_MODE=auto`. Casos de risco continuam exigindo aprovação.

## Como o robô decide
- Fila: páginas cujo título/slug tem uma data (“14 de abril”), por data de publicação crescente. Se não há página nova, não faz nada.
- Carrossel: capa (imagem da página) + até 7 fatos + lista “Também aconteceu neste dia” + encerramento = **no máximo 10 slides**.
- Textos: só o que está na página, tom acadêmico em temas sensíveis (`prompts/sistema.md`).
- Legenda: gancho, lista de fatos, link da página com UTM, aviso educativo e hashtags. O link **não é clicável** na legenda do Instagram; mantenha também o site no link da bio.
- Sem imagem de capa: capa tipográfica. Para trocar uma imagem, coloque `overrides/<slug>.jpg`.

## Operação e problemas comuns
| Sintoma | Causa provável |
|---|---|
| “As imagens não ficaram públicas a tempo” | Pages não configurado para a branch `media` (passo 6.2) |
| Erro de permissão ao publicar | Conta fora dos testadores do app ou permissão ausente (passo 3) |
| Issue com rótulo `falha` | Veja o log da execução; comente `/aprovar` para tentar de novo |
| Cron parou depois de semanas | GitHub desativa agendamentos de repositório público sem atividade por 60 dias; o commit semanal do token evita isso |

## Desenvolvimento
```bash
pip install -r requirements-dev.txt
python -m pytest -q
```
Fontes: Anton e Lato (SIL Open Font License; licenças em `assets/fonts`).

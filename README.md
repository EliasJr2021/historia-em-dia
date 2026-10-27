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

### 3. Instagram — app na Meta (API do Instagram com Instagram Login; não precisa de Página do Facebook)
Passo a passo conferido na documentação atual da Meta (out/2026). Os nomes dos menus podem aparecer em português.
1. Conta **Profissional** (já feito) e **pública**, pois a Meta exige conta pública para gerar o token.
2. Acesse https://developers.facebook.com, entre com sua conta do Facebook e clique em **Get Started / Começar**. Aceite os Termos, confirme o código enviado ao seu telefone e e-mail e escolha a ocupação.
3. Abra https://developers.facebook.com/apps/creation/ e siga o assistente:
   - **Detalhes do app:** nome (ex.: *Historia em Dia Bot*) e e-mail de contato.
   - **Casos de uso:** selecione **Manage messaging & content on Instagram** (*Gerenciar mensagens e conteúdo no Instagram*).
   - **Empresa (Business):** escolha **I don't want to connect a business portfolio yet** (*Não quero conectar um portfólio de negócios agora*). Para uma conta própria isso não é necessário.
   - **Requisitos** › Next › **Overview** › **Go to dashboard**.
4. No painel, abra **Casos de uso (Use cases) › Customize** do caso de uso do Instagram e escolha **API setup with Instagram Login** (*Configuração da API com login do Instagram*). Não use a opção “com login do Facebook”.
5. **Permissões:** clique em **Add all required permissions**. Isso adiciona `instagram_business_basic` (e a permissão de mensagens, que é obrigatória neste caso de uso e não precisa ser usada). Depois abra **Permissions and features** no menu lateral e adicione **`instagram_business_content_publish`**, que é a que permite publicar. Faça isso **antes** de gerar o token.
6. Na seção **Generate access tokens**, clique em **Add account**, depois **Continue**, entre com @historia.em.diaa na janela que abrir e clique em **Save** e **Got it**. Você pode ver ou remover contas depois em *App roles › Roles*. Se aparecer um convite de testador pendente, aceite no app do Instagram em *Configurações › Apps e sites*.
7. Ainda em **Generate access tokens**, clique em **Generate token** ao lado da conta e copie o token → segredo **`IG_TOKEN_INICIAL`**. Se você gerou o token antes do passo 5, gere de novo.
   - O **ID da conta** é opcional: se não o encontrar, deixe o segredo `IG_USER_ID` em branco (o robô usa `me`). O teste da Fase 0 com “instagram” mostra o `user_id`, e você pode guardá-lo depois.
   - A documentação não informa a duração do token gerado no painel. Se ele parar de funcionar em poucas horas, troque por um de 60 dias com `scripts/trocar_token.py` (usa o *Instagram app secret*, em *API setup with Instagram login › Set up Instagram business login › Business login settings*, que você nunca deve colar em chats).
8. **App Review não é necessário** para publicar na sua própria conta. A Meta exige revisão só quando o app acessa contas que você não possui nem administra. Para contas próprias adicionadas ao app, o Standard Access basta. Você **não** precisa configurar webhooks, URL de redirecionamento nem publicar o app.

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
| `MAX_SLIDES` | `10` | de 4 a 10 (a API já aceita até 20; 10 é uma escolha editorial) |
| `AI_IMAGE_NOTICE` | `false` | `true` acrescenta o aviso na legenda e no slide final e marca o post como gerado por IA (`is_ai_generated`) |
| `MEDIA_BASE_URL` | Pages do repositório | com `https://raw.githubusercontent.com/EliasJr2021/historia-em-dia/media` não é preciso configurar o Pages (testado na Fase 0) |
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

## Verificações automáticas
- O robô **não gera carrossel** se o texto extraído da página tiver menos de 1.500 caracteres (abre um Issue `falha`), para nunca resumir conteúdo que não leu.
- O texto vem da API REST do site (`content.rendered`); a raspagem do HTML é só reserva.
- Capas em qualquer proporção (1:1, 3:2, 16:9) entram inteiras, sem recorte.

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

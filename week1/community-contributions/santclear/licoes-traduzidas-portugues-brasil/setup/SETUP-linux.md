# LLM Engineering - Domine IA e LLMs

## Instruções de configuração originais para Linux

**Estas são as instruções originais correspondentes à versão original dos vídeos, anteriores a outubro de 2025. Para a nova versão, consulte [SETUP-new.md](SETUP-new.md).**

Bem-vindas e bem-vindos, usuários de Linux!

Preciso admitir que pedi ao ChatGPT para gerar este documento com base nas instruções para Mac e depois revisei e ajustei algumas seções. Se alguma parte não funcionar na sua distro, avise-me — resolveremos juntos e atualizarei as instruções para o futuro.

___

Configurar um ambiente robusto para trabalhar na vanguarda da IA exige algum esforço, mas estas instruções devem guiá-lo sem dificuldades. Se encontrar qualquer problema, fale comigo. Estou aqui para garantir que tudo fique pronto sem dor de cabeça.

E-mail: ed@edwarddonner.com  
LinkedIn: https://www.linkedin.com/in/eddonner/  

Usaremos o Anaconda para criar um ambiente confiável para o seu trabalho com IA. Também ofereço uma alternativa mais leve, caso prefira evitar o Anaconda. Vamos lá!

### Parte 1: Fazer o clone do repositório

Assim você obtém uma cópia local do código.

1. **Instale o Git**, caso ainda não esteja disponível:

- Abra um terminal.
- Execute `git --version`. Se o Git não estiver instalado, siga as instruções para sua distribuição:
  - Debian/Ubuntu: `sudo apt update && sudo apt install git`
  - Fedora: `sudo dnf install git`
  - Arch: `sudo pacman -S git`

2. **Navegue até a pasta de projetos:**

Se você já tem uma pasta específica para projetos, vá até ela com `cd`. Por exemplo:  
`cd ~/Projects`

Se não tiver, crie uma:
```
mkdir ~/Projects
cd ~/Projects
```

3. **Clone o repositório:**

Execute:
`git clone https://github.com/ed-donner/llm_engineering.git`

Isso cria um diretório `llm_engineering` dentro de `Projects` e baixa o código do curso. Entre nele com `cd llm_engineering`. Esse é o "diretório raiz do projeto".

### Parte 2: Instalar o ambiente Anaconda

Se esta Parte 2 apresentar problemas, consulte a Parte 2B alternativa.

1. **Instale o Anaconda:**

- Baixe o instalador para Linux em https://www.anaconda.com/download.
- Abra um terminal e vá até a pasta onde o `.sh` foi salvo.
- Execute o instalador: `bash Anaconda3*.sh` e siga as instruções. Atenção: você precisará de mais de 5 GB de espaço em disco.

2. **Configure o ambiente:**

- No terminal, acesse o diretório raiz do projeto:
  `cd ~/Projects/llm_engineering` (ajuste conforme o seu caminho).
- Execute `ls` para confirmar a presença das subpastas semanais.
- Crie o ambiente: `conda env create -f environment.yml`

A instalação pode levar vários minutos (até uma hora para quem nunca usou Anaconda). Se demorar demais ou ocorrerem erros, use a Parte 2B.

- Ative o ambiente: `conda activate llms`.

Você deve ver `(llms)` no prompt, sinal de que a ativação deu certo.

Em algumas distribuições pode ser necessário garantir que o ambiente apareça no Jupyter Lab:

`conda install ipykernel`  
`python -m ipykernel install --user --name=llmenv`

3. **Inicie o Jupyter Lab:**

Estando na pasta `llm_engineering`, execute `jupyter lab`.

O Jupyter Lab abrirá no navegador. Após confirmar que funciona, feche-o e siga para a Parte 3.

### Parte 2B - Alternativa à Parte 2 se o Anaconda der trabalho

1. **Instale o Python 3.11 (se necessário):**

- Debian/Ubuntu: `sudo apt update && sudo apt install python3.11`
- Fedora: `sudo dnf install python3.11`
- Arch: `sudo pacman -S python`

2. **Acesse o diretório raiz do projeto:**

`cd ~/Projects/llm_engineering` e confirme o conteúdo com `ls`.

3. **Crie um ambiente virtual:**

`python3.11 -m venv llms`

4. **Ative o ambiente virtual:**

`source llms/bin/activate`

O prompt deve exibir `(llms)`.

5. **Instale os pacotes necessários:**

Execute `python -m pip install --upgrade pip` e depois `pip install -r requirements.txt`.

Se surgir algum problema, tente o plano B:
`pip install --retries 5 --timeout 15 --no-cache-dir --force-reinstall -r requirements.txt`

###### Usuários de Arch

Algumas atualizações quebram dependências (principalmente numpy, scipy e gensim). Para contornar:

`sudo pacman -S python-numpy python-pandas python-scipy` — não é a opção ideal, pois o pacman não se integra ao pip.

Outra alternativa, caso ocorram conflitos de compilação:

`sudo pacman -S gcc gcc-fortran python-setuptools python-wheel`

*Observação:* o gensim pode falhar com versões recentes do scipy. Você pode fixar o scipy em uma versão mais antiga ou remover temporariamente o gensim do requirements.txt. (Veja: https://aur.archlinux.org/packages/python-gensim)

Por fim, para que o kernel apareça no Jupyter Lab após o passo 6:
`python -m ipykernel install --user --name=llmenv`
`ipython kernel install --user --name=llmenv`

6. **Inicie o Jupyter Lab:**

Na pasta `llm_engineering`, execute `jupyter lab`.

### Parte 3 - Chave da OpenAI (OPCIONAL, mas recomendada)

Nas semanas 1 e 2 você escreverá código que chama APIs de modelos de ponta.

Na semana 1 basta a OpenAI; as demais chaves podem vir depois.

1. Crie uma conta na OpenAI, se ainda não tiver:  
https://platform.openai.com/

2. A OpenAI exige um crédito mínimo para liberar a API. Nos EUA, são US$ 5. As chamadas descontarão desse valor. No curso usaremos apenas uma pequena parte. Recomendo fazer esse investimento, pois será útil para projetos futuros. Caso não queira pagar, ofereço uma alternativa com o Ollama ao longo das aulas.

Adicione crédito em Settings > Billing:  
https://platform.openai.com/settings/organization/billing/overview

Sugiro desativar a recarga automática.

3. Gere sua chave de API:

Acesse https://platform.openai.com/api-keys, clique em "Create new secret key" (botão verde) e depois em "Create secret key". Guarde a chave em local seguro; não será possível recuperá-la posteriormente. Ela deve começar com `sk-proj-`.

Na semana 2 criaremos também chaves para Anthropic e Google:  
- Claude API: https://console.anthropic.com/  
- Gemini API: https://ai.google.dev/gemini-api

Mais adiante utilizaremos a ótima plataforma HuggingFace; a conta gratuita está em https://huggingface.co — gere um token em Avatar >> Settings >> Access Tokens.

Nas semanas 6/7 empregaremos o Weights & Biases em https://wandb.ai para monitorar os treinamentos. As contas também são gratuitas e o token é criado de modo semelhante.

### PARTE 4 - Arquivo .env

Quando tiver as chaves, crie um arquivo `.env` no diretório raiz do projeto. O nome deve ser exatamente ".env" — nada de "minhas-chaves.env" ou ".env.txt". Passo a passo:

1. Abra um terminal.

2. Navegue até o diretório raiz do projeto com `cd ~/Projects/llm_engineering` (ajuste conforme necessário).

3. Crie o arquivo com:

`nano .env`

4. Digite suas chaves no nano, substituindo `xxxx` pelo valor correto (ex.: começa com `sk-proj-`):

```
OPENAI_API_KEY=xxxx
```

Se já tiver outras chaves, você pode incluí-las agora ou mais tarde:
```
GOOGLE_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
DEEPSEEK_API_KEY=xxxx
HF_TOKEN=xxxx
```

5. Salve o arquivo:

Control + O  
Enter (para confirmar)  
Control + X para sair

6. Liste os arquivos, inclusive ocultos:

`ls -a`

Confirme que o `.env` está presente.

O arquivo não aparecerá no Jupyter Lab porque arquivos iniciados com ponto ficam ocultos. Ele já está no `.gitignore`, então não será versionado e suas chaves ficam protegidas.

### Parte 5 - Hora do show!

1. Abra um terminal.
2. Vá até o diretório raiz do projeto:
   `cd ~/Projects/llm_engineering`.
3. Ative seu ambiente:
   - Com Anaconda: `conda activate llms`
   - Com a alternativa: `source llms/bin/activate`

Você deve ver `(llms)` no prompt. Execute `jupyter lab` para começar.

Aproveite a jornada rumo ao domínio de IA e LLMs!

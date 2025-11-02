# LLM Engineering - Domine IA e LLMs

## Instruções de configuração originais para Mac

**Estas são as instruções originais correspondentes à versão original dos vídeos, anteriores a outubro de 2025. Para a nova versão, consulte [SETUP-new.md](SETUP-new.md).**

Bem-vindas e bem-vindos, usuários de Mac!

Preciso confessar logo de cara: configurar um ambiente poderoso para trabalhar na vanguarda da IA não é tão simples quanto eu gostaria. Para a maioria das pessoas, estas instruções funcionarão muito bem; mas, em alguns casos, por algum motivo, você pode encontrar um problema. Não hesite em pedir ajuda — estou aqui para colocar tudo em funcionamento rapidamente. Não há nada pior do que se sentir _travado_. Envie uma mensagem, um e-mail ou um recado pelo LinkedIn e eu destravo tudo sem demora!

E-mail: ed@edwarddonner.com  
LinkedIn: https://www.linkedin.com/in/eddonner/  

Uso uma plataforma chamada Anaconda para configurar o ambiente. É uma ferramenta poderosa que monta um ecossistema científico completo. O Anaconda garante que você utilize a versão correta do Python e que todos os pacotes sejam compatíveis com os meus, mesmo que nossos sistemas sejam completamente diferentes. A configuração leva mais tempo e consome mais espaço em disco (mais de 5 GB), mas é muito confiável depois de instalada.

Dito isso: se tiver qualquer problema com o Anaconda, forneço uma abordagem alternativa. Ela é mais rápida e simples e deve colocá-lo para rodar rapidamente, com um pouco menos de garantia de compatibilidade.

### Antes de começar

Se você ainda não tem tanta familiaridade com o Terminal, consulte este excelente [guia](https://chatgpt.com/canvas/shared/67b0b10c93a081918210723867525d2b) com explicações e exercícios.

Se estiver iniciando o desenvolvimento no Mac, talvez seja necessário instalar as ferramentas de desenvolvedor do Xcode. Aqui estão as [instruções](https://chatgpt.com/share/67b0b8d7-8eec-8012-9a37-6973b9db11f5).

Um ponto de atenção: se você usa antivírus, VPN ou firewall, eles podem interferir em instalações ou no acesso à rede. Desative-os temporariamente caso surjam problemas.

### Parte 1: Fazer o clone do repositório

Isto garante que você tenha uma cópia local do código.

1. **Instale o Git** caso ainda não esteja instalado (na maioria das vezes já estará).
   - Abra o Terminal (Aplicativos > Utilitários > Terminal).
   - Digite `git --version`. Se o Git não estiver instalado, o sistema pedirá a instalação automaticamente.
   - Depois da instalação, talvez seja necessário abrir uma nova janela do Terminal (ou até reiniciar) para utilizá-lo.

2. **Navegue até a pasta de projetos:**

Se você já possui uma pasta específica para projetos, navegue até ela usando `cd`. Por exemplo:  
`cd ~/Documents/Projects`

Se não tiver uma pasta de projetos, crie-a:
```
mkdir ~/Documents/Projects
cd ~/Documents/Projects
```

3. **Clone o repositório:**

No Terminal, dentro da pasta Projects, digite:

`git clone https://github.com/ed-donner/llm_engineering.git`

Isso cria um novo diretório `llm_engineering` dentro da pasta Projects e baixa o código do curso. Execute `cd llm_engineering` para entrar nele. Esse diretório `llm_engineering` é o "diretório raiz do projeto".

### Parte 2: Instalar o ambiente Anaconda

Se esta Parte 2 apresentar qualquer problema, você pode usar a Parte 2B alternativa logo abaixo.

1. **Instale o Anaconda:**

- Baixe o Anaconda em https://docs.anaconda.com/anaconda/install/mac-os/
- Dê um duplo clique no arquivo baixado e siga as instruções de instalação. O processo ocupa vários gigabytes e leva algum tempo, mas fornecerá uma plataforma poderosa para você no futuro.
- Após a instalação, abra um Terminal totalmente novo para poder usar o Anaconda (talvez seja até necessário reiniciar).

2. **Configure o ambiente:**

- Abra um **novo** Terminal (Aplicativos > Utilitários > Terminal).
- Navegue até o "diretório raiz do projeto" com `cd ~/Documents/Projects/llm_engineering` (substitua pelo caminho real da sua cópia local). Execute `ls` e verifique se há subpastas para cada semana do curso.
- Crie o ambiente: `conda env create -f environment.yml`
- Aguarde alguns minutos até que todos os pacotes sejam instalados — se for a primeira vez com o Anaconda, isso pode levar 20 a 30 minutos ou mais, dependendo da conexão. Coisas importantes estão acontecendo! Se levar mais de 1 hora e 15 minutos ou se aparecerem erros, siga para a Parte 2B.
- Agora você construiu um ambiente dedicado para engenharia de LLMs, vetores e muito mais! Ative-o com: `conda activate llms`
- O prompt deve exibir `(llms)`, indicando que o ambiente está ativo.

3. **Inicie o Jupyter Lab:**

- No Terminal, ainda dentro da pasta `llm_engineering`, digite: `jupyter lab`

O Jupyter Lab deve abrir no navegador. Se você nunca usou o Jupyter Lab, explicarei em breve! Por ora, feche a aba do navegador e o Terminal, e avance para a Parte 3.

### Parte 2B - Alternativa à Parte 2 se o Anaconda der trabalho

Esta abordagem utiliza `python -m venv` para criar um ambiente virtual e instalar manualmente os pacotes necessários.

1. **Garanta que o Python 3.11 esteja instalado:**

- No macOS 13+ o Python 3 normalmente já está disponível via `python3`, mas recomendo instalar uma versão oficial em https://www.python.org/downloads/macos/
- Execute o instalador e siga as instruções.
- Após a instalação, abra um novo Terminal e rode `python3 --version` para confirmar.

2. **Crie e ative um ambiente virtual:**

- No Terminal, navegue até o diretório raiz do projeto (`cd ~/Documents/Projects/llm_engineering`, ajustando conforme o seu caminho).
- Crie o ambiente: `python3 -m venv llms`
- Ative o ambiente: `source llms/bin/activate`
- Verifique se `(llms)` aparece no início do prompt.

3. **Atualize os instaladores e instale os pacotes necessários:**

```
python -m pip install --upgrade pip
pip install -r requirements-mac.txt
```

- Em seguida, instale o kernel do Jupyter vinculado ao ambiente: `python -m ipykernel install --user --name llms --display-name "Python (llms)"`

4. **Teste a instalação:**

- Execute `python -c "import torch, platform; print('Torch version:', torch.__version__); print('Python version:', platform.python_version())"`

5. **Inicie o Jupyter Lab:**

- Com o ambiente ainda ativo, rode `jupyter lab`
- Abra a pasta `week1` e clique em `day1.ipynb`.

### Parte 3 - Configure suas contas de API (OpenAI, Anthropic, Google, etc.)

Ao longo do curso você precisará de chaves de API, começando pela OpenAI na semana 1. Mais adiante, adicionaremos Anthropic e Google. Organize isso com antecedência.

Para a semana 1, você só precisa da OpenAI; as demais chaves podem ser criadas posteriormente.

1. Crie uma conta na OpenAI, se necessário:  
https://platform.openai.com/

2. A OpenAI exige um crédito mínimo para liberar o uso da API. Nos EUA, são US$ 5. As chamadas à API descontarão desse valor. No curso, usaremos apenas uma fração dele. Recomendo fazer esse investimento, porque você aproveitará bastante. Caso prefira não pagar, apresento uma alternativa com o Ollama ao longo das aulas.

Você pode adicionar crédito em Settings > Billing:  
https://platform.openai.com/settings/organization/billing/overview

Desative o recarregamento automático, se desejar.

3. Crie sua chave de API:

A página para criar a chave é https://platform.openai.com/api-keys — clique no botão verde "Create new secret key" e depois em "Create secret key". Guarde a chave em local seguro; não será possível recuperá-la depois. Ela deve começar com `sk-proj-`.

Na semana 2 criaremos também as chaves da Anthropic e da Google, quando for o momento.  
- Claude API: https://console.anthropic.com/ (Anthropic)  
- Gemini API: https://ai.google.dev/gemini-api (Google)

Mais adiante usaremos a excelente plataforma HuggingFace; a conta gratuita está em https://huggingface.co — crie um token no menu do avatar >> Settings >> Access Tokens.

Nas semanas 6/7 utilizaremos o sensacional Weights & Biases em https://wandb.ai para monitorar os treinamentos. As contas também são gratuitas e o token é criado de modo parecido.

### PARTE 4 - arquivo .env

Quando tiver as chaves, crie um arquivo chamado `.env` no diretório raiz do projeto. O nome precisa ser exatamente ".env" — nada de "minhas-chaves.env" ou ".env.txt". Veja como fazer:

1. Abra o Terminal (Aplicativos > Utilitários > Terminal).

2. Navegue até o "diretório raiz do projeto" com `cd ~/Documents/Projects/llm_engineering` (ajuste conforme o seu caminho).

3. Crie o arquivo `.env` com:

`nano .env`

4. Digite as suas chaves no nano, substituindo `xxxx` pela chave (que começa com `sk-proj-`):

```
OPENAI_API_KEY=xxxx
```

Se tiver outras chaves, você pode adicioná-las agora ou mais tarde:
```
GOOGLE_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
DEEPSEEK_API_KEY=xxxx
HF_TOKEN=xxxx
```

5. Salve o arquivo:

Control + O  
Enter (para confirmar a gravação)  
Control + X para sair do editor

6. Liste os arquivos no diretório raiz com:

`ls -a`

e confirme que o `.env` está lá.

O arquivo não aparecerá no Jupyter Lab porque arquivos iniciados com ponto ficam ocultos. Ele já está no `.gitignore`, portanto não será versionado e suas chaves permanecem seguras.

### Parte 5 - Hora do show!

- Abra o Terminal (Aplicativos > Utilitários > Terminal).  
- Navegue até o "diretório raiz do projeto" com `cd ~/Documents/Projects/llm_engineering` (ajuste conforme o seu caminho). Execute `ls` e verifique se as subpastas semanais estão visíveis.  
- Ative o ambiente com `conda activate llms` (ou `source llms/bin/activate` se você usou a alternativa da Parte 2B).  
- `(llms)` deve aparecer no prompt — sinal de que tudo está pronto. Agora digite `jupyter lab` e o Jupyter Lab será aberto, pronto para começar. Abra a pasta `week1` e dê um duplo clique em `day1.ipynb`.

E pronto: pé na estrada!

Sempre que iniciar o Jupyter Lab no futuro, siga novamente as instruções desta Parte 5: esteja dentro do diretório `llm_engineering` com o ambiente `llms` ativado antes de rodar `jupyter lab`.

Para quem é novo no Jupyter Lab / Jupyter Notebook, trata-se de um ambiente de Data Science muito amigável: basta pressionar Shift+Enter em qualquer célula para executá-la; comece do topo e vá seguindo! Incluí um notebook chamado "Guide to Jupyter" mostrando mais recursos. Quando migrarmos para o Google Colab na semana 3, você verá a mesma interface para executar Python na nuvem.

Se surgir qualquer problema, há um notebook na semana 1 chamado [troubleshooting.ipynb](week1/troubleshooting.ipynb) para ajudar no diagnóstico.

Por favor, envie uma mensagem ou e-mail para ed@edwarddonner.com se algo não funcionar ou se eu puder ajudar de algum modo. Estou ansioso para saber como você está progredindo.

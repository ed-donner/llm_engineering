# LLM Engineering - Domine IA e LLMs

## Instruções de configuração para Windows

**Estas são as instruções originais correspondentes à versão original dos vídeos, anteriores a outubro de 2025. Para a nova versão, consulte [SETUP-new.md](SETUP-new.md).**

Bem-vindas e bem-vindos, usuários de PC!

Preciso confessar logo de cara: configurar um ambiente poderoso para trabalhar na vanguarda da IA não é tão simples quanto eu gostaria. Para a maioria das pessoas, estas instruções funcionam perfeitamente; mas, em alguns casos, por algum motivo, você pode encontrar um problema. Não hesite em pedir ajuda — estou aqui para colocar tudo em funcionamento rapidamente. Não há nada pior do que se sentir _travado_. Envie uma mensagem, um e-mail ou um recado pelo LinkedIn e eu vou destravar tudo rapidinho!

E-mail: ed@edwarddonner.com  
LinkedIn: https://www.linkedin.com/in/eddonner/  

Eu utilizo uma plataforma chamada Anaconda para configurar o ambiente. É uma ferramenta poderosa que monta um ambiente científico completo. O Anaconda garante que você esteja usando a versão correta do Python e que todos os pacotes sejam compatíveis com os meus, mesmo que nossos sistemas sejam completamente diferentes. Ele demanda mais tempo de instalação e ocupa mais espaço em disco (mais de 5 GB), mas, depois de configurado, é muito confiável.

Dito isso: se tiver algum problema com o Anaconda, ofereço uma abordagem alternativa. Ela é mais rápida e simples e deve colocar tudo para rodar rapidamente, com um pouco menos de garantia de compatibilidade.

Se você é relativamente novo no Prompt de Comando, aqui está um excelente [guia](https://chatgpt.com/share/67b0acea-ba38-8012-9c34-7a2541052665) com instruções e exercícios. Recomendo passar por ele primeiro para ganhar confiança.

## ATENÇÃO - QUESTÕES "GOTCHA" NO PC: os quatro pontos a seguir merecem sua atenção, especialmente os itens 3 e 4

Por favor, analise esses itens. O item 3 (limite de 260 caracteres do Windows) causará um erro "Archive Error" na instalação do pytorch se não for corrigido. O item 4 causará problemas de instalação.

Há quatro armadilhas comuns ao desenvolver no Windows:

1. Permissões. Confira este [tutorial](https://chatgpt.com/share/67b0ae58-d1a8-8012-82ca-74762b0408b0) sobre permissões no Windows.  
2. Antivírus, firewall, VPN. Eles podem interferir em instalações e no acesso à rede; tente desativá-los temporariamente quando necessário.  
3. O terrível limite de 260 caracteres para nomes de arquivos no Windows — aqui está uma [explicação completa com a correção](https://chatgpt.com/share/67b0afb9-1b60-8012-a9f7-f968a5a910c7)!  
4. Se você ainda não trabalhou com pacotes de Data Science no computador, talvez precise instalar o Microsoft Build Tools. Aqui estão as [instruções](https://chatgpt.com/share/67b0b762-327c-8012-b809-b4ec3b9e7be0). Uma aluna também comentou que [estas instruções](https://github.com/bycloudai/InstallVSBuildToolsWindows) podem ajudar quem estiver no Windows 11.  

### Parte 1: Fazer o clone do repositório

Isso garante que você tenha uma cópia local do código na sua máquina.

1. **Instale o Git** (se ainda não estiver instalado):

- Baixe o Git em https://git-scm.com/download/win
- Execute o instalador e siga as instruções, usando as opções padrão (aperte OK várias vezes!).
- Após a instalação, talvez seja necessário abrir uma nova janela do Powershell para usá-lo (ou até reiniciar o computador).

2. **Abra o Prompt de Comando:**

- Pressione Win + R, digite `cmd` e pressione Enter.

3. **Navegue até a pasta de projetos:**

Se você já tem uma pasta para projetos, navegue até ela com o comando `cd`. Por exemplo:  
`cd C:\Users\SeuUsuario\Documents\Projects`  
Substitua `SeuUsuario` pelo seu usuário do Windows.

Se não tiver uma pasta de projetos, crie uma:
```
mkdir C:\Users\SeuUsuario\Documents\Projects
cd C:\Users\SeuUsuario\Documents\Projects
```

4. **Clone o repositório:**

Digite o seguinte no prompt dentro da pasta Projects:

`git clone https://github.com/ed-donner/llm_engineering.git`

Isso cria um novo diretório `llm_engineering` dentro da pasta Projects e baixa o código da turma. Execute `cd llm_engineering` para entrar nele. Esse diretório `llm_engineering` é o "diretório raiz do projeto".

### Parte 2: Instalar o ambiente Anaconda

Se esta Parte 2 apresentar qualquer problema, há uma Parte 2B alternativa logo abaixo que pode ser utilizada.

1. **Instale o Anaconda:**

- Baixe o Anaconda em https://docs.anaconda.com/anaconda/install/windows/
- Execute o instalador e siga as instruções. Ele ocupa vários gigabytes e leva algum tempo para instalar, mas será uma plataforma poderosa para você usar no futuro.

2. **Configure o ambiente:**

- Abra o **Anaconda Prompt** (procure por ele no menu Iniciar).
- Navegue até o "diretório raiz do projeto" digitando algo como `cd C:\Users\SeuUsuario\Documents\Projects\llm_engineering`, usando o caminho real da sua pasta `llm_engineering`. Execute `dir` e verifique se você enxerga subpastas para cada semana do curso.
- Crie o ambiente: `conda env create -f environment.yml`
- **Se aparecer um ArchiveError, isso é causado pelo limite de 260 caracteres do Windows — veja a armadilha nº 3 acima e corrija antes de tentar novamente.**
- Ative o ambiente: `conda activate llms`
- Com o ambiente ativo, instale kernels adicionais: `python -m ipykernel install --user --name llms --display-name "Python (llms)"`
- Para confirmar se o ambiente funciona, execute: `python -c "import torch, platform; print('Torch version:', torch.__version__); print('Python version:', platform.python_version())"`
- Por fim, rode `jupyter lab`

Se isso funcionar, você está pronto! Abra a pasta `week1`, clique em `day1.ipynb` e comece.

### Parte 2B: Alternativa ao Anaconda (se você teve problemas na Parte 2)

Essa abordagem cria um ambiente virtual usando `python -m venv` e instala os pacotes necessários manualmente.

1. **Certifique-se de que o Python 3.11 esteja instalado:**

- Baixe em https://www.python.org/downloads/windows/ (o executável do instalador).
- Durante a instalação, marque a opção **Add Python to PATH**.
- Depois da instalação, abra um novo Powershell e rode `python --version` para verificar se tudo deu certo.

2. **Crie e ative um ambiente virtual:**

- No Powershell, navegue até o diretório raiz do projeto com `cd` (mesmo caminho da Parte 1).
- Crie o ambiente: `python -m venv llms`
- Ative o ambiente: `llms\Scripts\activate`
- Verifique se `(llms)` aparece no início do prompt.

3. **Atualize os instaladores e instale os pacotes necessários:**

```
python -m pip install --upgrade pip
pip install -r requirements-windows.txt
```

- Em seguida, instale o kernel do Jupyter vinculado ao ambiente: `python -m ipykernel install --user --name llms --display-name "Python (llms)"`

4. **Teste a instalação:**

- Execute `python -c "import torch, platform; print('Torch version:', torch.__version__); print('Python version:', platform.python_version())"`

5. **Inicie o Jupyter Lab:**

- Ainda com o ambiente ativo, rode `jupyter lab`
- Abra a pasta `week1` e clique em `day1.ipynb`.

### Parte 3 - Configure suas contas de API (OpenAI, Anthropic, Google, etc.)

Durante o curso você precisará de algumas chaves de API, principalmente para OpenAI (semana 1) e, mais adiante, Anthropic e Google. É melhor organizar isso com antecedência.

Para a semana 1, você só precisa da OpenAI; os demais serviços podem ser adicionados mais tarde, se desejar.

1. Crie uma conta na OpenAI, se ainda não tiver, acessando:  
https://platform.openai.com/

2. A OpenAI exige um crédito mínimo para usar a API. Nos Estados Unidos, o valor é US$ 5. As chamadas à API utilizarão esse crédito. No curso, usaremos apenas uma pequena fração dele. Recomendo fazer esse investimento, pois você poderá aproveitar bastante em seus projetos. Se preferir não pagar pela API, apresento uma alternativa com o Ollama durante o curso.

Você pode adicionar saldo em Settings > Billing:  
https://platform.openai.com/settings/organization/billing/overview

Recomendo desativar o recarregamento automático.

3. Crie sua chave de API

A página para criar a chave é https://platform.openai.com/api-keys — clique no botão verde "Create new secret key" e depois em "Create secret key". Guarde a chave em um local seguro; não será possível recuperá-la posteriormente pela interface da OpenAI. Ela deve começar com `sk-proj-`.

Na semana 2 configuraremos também as chaves da Anthropic e da Google, que você poderá gerar aqui quando chegar o momento.  
- Claude API: https://console.anthropic.com/ (Anthropic)  
- Gemini API: https://ai.google.dev/gemini-api (Google)

Mais adiante no curso usaremos a excelente plataforma HuggingFace; a conta é gratuita em https://huggingface.co — crie um token de API no menu do avatar >> Settings >> Access Tokens.

Nas semanas 6/7 utilizaremos o Weights & Biases em https://wandb.ai para acompanhar os treinamentos. As contas também são gratuitas, e o token é criado de forma semelhante.

### Parte 4 - Arquivo .env

Quando tiver essas chaves, crie um novo arquivo chamado `.env` no diretório raiz do projeto. O nome do arquivo deve ser exatamente os quatro caracteres ".env", e não "minhas-chaves.env" ou ".env.txt". Veja como fazer:

1. Abra o Notepad (Windows + R para abrir a caixa Executar, digite `notepad`).

2. No Notepad, digite o seguinte, substituindo `xxxx` pela sua chave de API (que começa com `sk-proj-`):

```
OPENAI_API_KEY=xxxx
```

Se tiver outras chaves, você pode adicioná-las agora ou voltar a este arquivo nas semanas seguintes:
```
GOOGLE_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
DEEPSEEK_API_KEY=xxxx
HF_TOKEN=xxxx
```

Verifique se não há espaços antes ou depois do sinal `=` e nenhum espaço ao final da chave.

3. Vá em File > Save As. Em "Save as type", selecione All Files. No campo "File name", digite exatamente **.env**. Escolha o diretório raiz do projeto (a pasta `llm_engineering`) e clique em Save.

4. Abra essa pasta no Explorer e confira se o arquivo foi salvo como ".env", e não como ".env.txt". Se necessário, renomeie para ".env". Talvez você precise ativar a opção "Mostrar extensões de arquivo" para visualizar as extensões. Se isso não fizer sentido, mande uma mensagem ou e-mail!

Esse arquivo não aparecerá no Jupyter Lab porque arquivos iniciados com ponto ficam ocultos. O `.env` já está listado no `.gitignore`, portanto não será versionado, mantendo suas chaves em segurança.

### Parte 5 - Hora do show!

- Abra o **Anaconda Prompt** (se usou o Anaconda) ou um Powershell (se seguiu a alternativa da Parte 2B).
- Navegue até o "diretório raiz do projeto" digitando algo como `cd C:\Users\SeuUsuario\Documents\Projects\llm_engineering`, usando o caminho real da sua pasta `llm_engineering`. Execute `dir` e confirme se as subpastas de cada semana estão lá.
- Ative o ambiente com `conda activate llms` se usou o Anaconda, ou `llms\Scripts\activate` se usou a alternativa da Parte 2B.
- Você deve ver `(llms)` no prompt — esse é o sinal de que tudo está certo. Agora, digite `jupyter lab` e o Jupyter Lab deverá abrir, pronto para você começar. Abra a pasta `week1` e dê um duplo clique em `day1.ipynb`.

E pronto: pé na estrada!

Observe que, sempre que iniciar o Jupyter Lab no futuro, você precisará seguir novamente as instruções da Parte 5: estar dentro do diretório `llm_engineering` com o ambiente `llms` ativado antes de executar `jupyter lab`.

Para quem é novo no Jupyter Lab / Jupyter Notebook, trata-se de um ambiente de Data Science muito agradável: basta apertar Shift+Enter em qualquer célula para executá-la; comece no topo e vá seguindo! Há um notebook na pasta `week1` com um [Guia para o Jupyter Lab](week1/Guide%20to%20Jupyter.ipynb) e um tutorial de [Python Intermediário](week1/Intermediate%20Python.ipynb), caso ajude. Quando passarmos para o Google Colab na semana 3, você verá a mesma interface para executar Python na nuvem.

Se tiver qualquer problema, há um notebook em `week1` chamado [troubleshooting.ipynb](week1/troubleshooting.ipynb) para ajudar a diagnosticar.

Por favor, envie uma mensagem ou e-mail para ed@edwarddonner.com se algo não funcionar ou se eu puder ajudar de alguma forma. Estou ansioso para saber como você está avançando.

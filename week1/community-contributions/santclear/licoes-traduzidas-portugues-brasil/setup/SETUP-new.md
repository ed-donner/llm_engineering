# LLM Engineering - Domine IA e LLMs

## Novas instruções de configuração para PC, Mac e Linux

**Estas são as instruções de configuração da nova versão do curso a partir de outubro de 2025. Para as versões originais (Anaconda), consulte os outros arquivos deste diretório correspondentes à sua plataforma.**

_Se você estiver visualizando isto no Cursor, clique com o botão direito no nome do arquivo no Explorer à esquerda e selecione "Open preview" para ver a versão formatada._

Bem-vindas e bem-vindos, engenheiras e engenheiros de LLM em formação!

Preciso confessar logo de início: configurar um ambiente poderoso para trabalhar na linha de frente da IA não é tão simples quanto eu gostaria. Para a maioria das pessoas, estas instruções funcionarão muito bem; mas, em alguns casos, por qualquer motivo, você pode esbarrar em um problema. Não hesite em pedir ajuda — estou aqui para colocar tudo em funcionamento rapidamente. Não há nada pior do que se sentir _travado_. Envie uma mensagem pela Udemy ou um e-mail e vou destravar a situação sem demora!

E-mail: ed@edwarddonner.com  
LinkedIn: https://www.linkedin.com/in/eddonner/  

## Etapa 0 - Antes de começar - tratando dos "GOTCHAS" que derrubam muita gente

Ignore esta seção por sua conta e risco! 80% das dúvidas que recebo sobre a configuração são resolvidas por estes problemas comuns de sistema.

1. Quem usa PC: Permissões. Dê uma olhada neste [tutorial](https://chatgpt.com/share/67b0ae58-d1a8-8012-82ca-74762b0408b0) sobre permissões no Windows. Se aparecer algum erro dizendo que você não tem direitos/permissões/capacidade de executar um script ou instalar software, leia isso primeiro. O ChatGPT pode explicar tudo o que você precisa saber sobre permissões no Windows.

2. Antivírus, firewall, VPN. Esses elementos podem atrapalhar instalações e o acesso à rede; tente desativá-los temporariamente quando necessário. Use o hotspot do seu celular para confirmar se o problema é realmente de rede.

3. Quem usa PC: o terrível limite de 260 caracteres para nomes de arquivos no Windows — aqui está uma [explicação completa com a correção](https://chatgpt.com/share/67b0afb9-1b60-8012-a9f7-f968a5a910c7)!

4. Quem usa PC: se você nunca trabalhou com pacotes de Data Science no seu computador, talvez precise instalar o Microsoft Build Tools. Aqui estão as [instruções](https://chatgpt.com/share/67b0b762-327c-8012-b809-b4ec3b9e7be0). Uma aluna também mencionou que [estas instruções](https://github.com/bycloudai/InstallVSBuildToolsWindows) podem ajudar quem estiver no Windows 11.

5. Quem usa Mac: se está começando a desenvolver no Mac agora, talvez seja necessário instalar as ferramentas de desenvolvedor do Xcode. Aqui estão as [instruções](https://chatgpt.com/share/67b0b8d7-8eec-8012-9a37-6973b9db11f5).

6. SSL e outros problemas de rede por causa de segurança corporativa: se você tiver erros de SSL, como falhas de conexão com API, qualquer problema de certificado ou erro ao baixar arquivos do Ollama (erro do Cloudflare), veja a pergunta 15 [aqui](https://edwarddonner.com/faq).

## ETAPA 1 - instalando git, diretório de projetos e Cursor

Esta é a única seção com passos separados para quem usa PC e para quem usa Mac/Linux! Escolha o seu bloco abaixo e, depois, volte aqui para a Etapa 2...

___

**ETAPA 1 PARA QUEM USA PC:**

1. **Instale o Git** (se ainda não estiver instalado):

- Abra um novo prompt do Powershell (menu Iniciar >> Powershell). Se surgirem erros de permissão, tente abrir o Powershell clicando com o botão direito e escolhendo "Executar como administrador".
- Execute o comando `git` e veja se ele responde com detalhes do comando ou com um erro.
- Se aparecer erro, baixe o Git em https://git-scm.com/download/win
- Execute o instalador e siga as instruções, aceitando as opções padrão (aperte OK várias vezes!)

2. **Crie o diretório de projetos, se necessário**

- Abra um novo prompt do Powershell, conforme o passo anterior. Você deve estar no seu diretório pessoal, algo como `C:\Users\SeuUsuario`
- Você já tem um diretório `projects`? Descubra digitando `cd projects`
- Se aparecer erro, crie o diretório de projetos: `mkdir projects` e depois `cd projects`
- Agora você deve estar em `C:\Users\SeuUsuario\projects`
- Você pode escolher outro local conveniente, mas evite diretórios que estejam no OneDrive

3. **Faça o git clone:**

Digite o seguinte no prompt dentro da pasta `projects`:

`git clone https://github.com/ed-donner/llm_engineering.git`

Isso cria um novo diretório `llm_engineering` dentro da pasta de projetos e baixa o código da turma.  
Execute `cd llm_engineering` para entrar nele. Esse diretório `llm_engineering` é o "diretório raiz do projeto".

4. **Cursor** Instale o Cursor, se necessário, e abra o projeto:

Visite https://cursor.com

Clique em Download for Windows. Execute o instalador. Aceite e mantenha os padrões em tudo.

Depois, abra o menu Iniciar, digite cursor. O Cursor será aberto e talvez você precise responder a algumas perguntas. Em seguida, deve aparecer a tela de "new window", onde você pode clicar em "Open Project". Se não aparecer, vá ao menu File >> New Window. Depois clique em "Open Project".

Localize o diretório `llm_engineering` dentro da sua pasta de projetos. Dê dois cliques em `llm_engineering` para visualizar o conteúdo dele. Em seguida, clique em Open ou Open Folder.

O Cursor deve então abrir o `llm_engineering`. Você saberá que deu tudo certo se vir LLM_ENGINEERING em letras maiúsculas no canto superior esquerdo.

___

**ETAPA 1 PARA QUEM USA MAC/LINUX**

1. **Instale o Git** (se ainda não estiver instalado):

Abra um Terminal. No Mac, abra uma janela do Finder e vá para Aplicativos >> Utilitários >> Terminal. No Linux, vocês praticamente vivem no Terminal... quase não precisam das minhas instruções!

- Execute `git --version` e verifique se aparece um número de versão do git. Caso contrário, você deve ver orientações para instalá-lo, ou siga o gotcha nº 5 no topo deste documento.

2. **Crie o diretório de projetos, se necessário**

- Abra uma nova janela do Terminal, como no passo anterior. Digite `pwd` para ver onde está. Você deve estar no seu diretório pessoal, algo como `/Users/usuario`
- Você já tem um diretório `projects`? Verifique digitando `cd projects`
- Se aparecer erro, crie o diretório de projetos: `mkdir projects` e depois `cd projects`
- Se você rodar `pwd` agora, deve estar em `/Users/usuario/projects`
- Você pode escolher outro local conveniente, mas evite diretórios que estejam no iCloud

3. **Faça o git clone:**

Digite o seguinte no prompt dentro da pasta `projects`:

`git clone https://github.com/ed-donner/llm_engineering.git`

Isso cria um novo diretório `llm_engineering` dentro da sua pasta de projetos e baixa o código da turma.  
Execute `cd llm_engineering` para entrar nele. Esse diretório `llm_engineering` é o "diretório raiz do projeto".

4. **Cursor** Instale o Cursor, se necessário, e abra o projeto:

Visite https://cursor.com

Clique em Download for Mac OS ou para Linux. Em seguida, execute o instalador. Aceite e mantenha os padrões em tudo.

Depois, procure por Cursor (Spotlight, menu Iniciar etc.). O Cursor será aberto e talvez apareçam algumas perguntas. Em seguida, você deverá ver a tela de "new window", onde pode clicar em "Open Project". Se não aparecer, vá ao menu File >> New Window e clique em "Open Project".

Localize o diretório `llm_engineering` dentro da sua pasta de projetos. Dê dois cliques em `llm_engineering` para visualizar o conteúdo dele. Depois clique em Open.

O Cursor deve então abrir o `llm_engineering`. Você saberá que deu tudo certo se vir LLM_ENGINEERING em letras maiúsculas no canto superior esquerdo.

___

## ETAPA 2: Instalando o fantástico **uv** e executando `uv sync`

Para este curso, usamos o uv, o gerenciador de pacotes incrivelmente rápido. Ele conquistou a comunidade de Data Science — e com razão.

É veloz e confiável. Você vai adorar!

Primeiro, dentro do Cursor, selecione View >> Terminal para abrir um terminal integrado. Digite `pwd` para confirmar que está no diretório raiz do projeto.

Agora digite `uv --version` para ver se o uv está instalado. Se aparecer um número de versão, ótimo! Caso surja um erro, siga as instruções deste link para instalar o uv — recomendo utilizar o método Standalone Installer logo no começo da página, mas qualquer método serve. Execute os comandos no terminal do Cursor. Se uma abordagem não funcionar, tente outra.

https://docs.astral.sh/uv/getting-started/installation/

Depois de instalar o uv, abra uma nova janela de terminal no Cursor (o sinal de mais ou Ctrl+Shift+crase) para que o `uv --version` funcione. Verifique!

Quaisquer problemas na instalação ou no uso do uv, consulte [a pergunta 11 na minha página de FAQ](https://edwarddonner.com/faq/#11) para uma explicação completa.

### Agora que está instalado:

Execute `uv self update` para garantir que você está com a versão mais recente do uv.

Em seguida, simplesmente rode:  
`uv sync`  
O uv deve instalar tudo de forma extremamente rápida. Qualquer problema, veja novamente [a pergunta 11 na página de FAQ](https://edwarddonner.com/faq/#11).

Você agora tem um ambiente completo!

Usar o uv é simples e rápido:  
1. Em vez de `pip install xxx`, use `uv add xxx`  
2. Você nunca precisa ativar um ambiente — o uv faz isso automaticamente.  
3. Em vez de `python xxx`, use `uv run xxx`

___

## ETAPA 3 - OPCIONAL - Crie sua conta na OpenAI

Alternativa: consulte o Guia 9 na pasta `guides` para opções gratuitas!

Acesse https://platform.openai.com

- Clique em Sign Up para criar uma conta, caso ainda não tenha. Talvez seja necessário clicar em alguns botões para criar uma Organization primeiro — insira dados razoáveis. Veja o Guia 4 na pasta Guides se estiver em dúvida sobre as diferenças entre o ChatGPT e a API da OpenAI.
- Clique no ícone Settings no canto superior direito e, em seguida, em Billing no menu lateral esquerdo.
- Certifique-se de que o Auto-Recharge esteja desativado. Se necessário, clique em "Add to Credit Balance" e escolha o valor adiantado de US$ 5, garantindo que adicionou um meio de pagamento válido.
- Ainda em Settings, selecione API keys no menu lateral esquerdo (perto do topo).
- Clique em "Create new secret key" — selecione "Owned by you", dê o nome que quiser, escolha "Default project" no campo Project e mantenha Permissions em All.
- Clique em "Create secret key" e você verá a nova chave. Clique em Copy para copiá-la para a área de transferência.

___

## ETAPA 4 - necessária para qualquer modelo como OpenAI ou Gemini (mas dispensável se você usar apenas o Ollama) - crie (e SALVE) o seu arquivo .env

**Seja meticuloso nesta etapa!** Qualquer erro na chave será muito difícil de diagnosticar! Recebo um volume enorme de perguntas de estudantes que cometem algum deslize aqui... Acima de tudo, lembre-se de salvar o arquivo depois de alterá-lo.

1. Crie o arquivo `.env`

- Volte ao Cursor
- No Explorador de Arquivos à esquerda, clique com o botão direito no espaço em branco abaixo de todos os arquivos, selecione "New File" e dê ao seu arquivo o nome `.env`
- Não canso de repetir: o arquivo precisa se chamar EXATAMENTE `.env` — essas quatro letras, nem mais nem menos. Nada de ".env.txt", nem "joao.env", nem "openai.env" ou qualquer outra coisa! E ele precisa estar no diretório raiz do projeto.

Se estiver se perguntando por que reforço tanto isso: recebo muitas, muitas mensagens de pessoas frustradas que (apesar de todos os meus apelos) deram outro nome ao arquivo e acharam que estava tudo certo. Não está! Ele precisa se chamar `.env` dentro do diretório `llm_engineering`. :)

2. Preencha o arquivo `.env` e depois salve:

Selecione o arquivo à esquerda. Você verá um arquivo vazio à direita. Digite isto no conteúdo do arquivo:

`OPENAI_API_KEY=`

Em seguida, cole a sua chave! Você deve ver algo como:

`OPENAI_API_KEY=sk-proj-lots-and-lots-of-digits`

Mas, claro, com a sua chave real, não com as palavras "sk-proj-lots-and-lots-of-digits"...

Agora TENHA CERTEZA de salvar o arquivo! File >> Save ou Ctrl+S (PC) / Command+S (Mac). Muitas pessoas esquecem de salvar. Você precisa salvar o arquivo!

Você provavelmente verá um ícone de sinal de parada ao lado do .env — não se preocupe, isso é algo bom! Consulte a pergunta 7 [aqui](https://edwarddonner.com/faq) se quiser entender o motivo.

__

## ETAPA 5 - Instale as extensões do Cursor, abra o Dia 1, configure o kernel e VAMOS NESSA!

(Se o Cursor sugerir instalar extensões recomendadas, basta aceitar! É um bom atalho para esta etapa.)

- Vá ao menu View e selecione Extensions.  
- Procure por "python" para exibir as extensões de Python. Selecione a extensão Python desenvolvida por "ms-python" ou "anysphere" e instale-a se ainda não estiver instalada.  
- Procure por "jupyter" e selecione a extensão desenvolvida por "ms-toolsai"; instale-a se ainda não estiver instalada.

Agora vá em View >> Explorer. Abra a pasta `week1` e clique em `day1.ipynb`.

- Veja onde aparece "Select Kernel" perto do canto superior direito? Clique ali e escolha "Python Environments".
- Selecione a opção superior com uma estrela, algo como `.venv (Python 3.12.x) .venv/bin/python Recommended`.
- Se essa opção não aparecer, abra o laboratório de troubleshooting na pasta Setup.

# PARABÉNS!! Você conseguiu! O restante do curso é tranquilo :)

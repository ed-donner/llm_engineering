# LLM Engineering - Domine IA e LLMs

## Sua jornada de 8 semanas rumo à proficiência começa hoje

![Voyage](assets/voyage.jpg)

_Se você estiver vendo isto no Cursor, clique com o botão direito no nome do arquivo no Explorer à esquerda e selecione "Open preview" para visualizar a versão formatada._

Estou muito feliz por você se juntar a mim nesta jornada. Construiremos projetos extremamente gratificantes nas próximas semanas. Alguns serão fáceis, outros desafiadores, e muitos vão surpreender você! Os projetos se complementam para que você desenvolva experiência cada vez mais profunda a cada semana. De uma coisa tenho certeza: você vai se divertir bastante pelo caminho.

# COMUNICADO IMPORTANTE - OUTUBRO DE 2025 - LEIA POR FAVOR

Estou implementando gradualmente novas versões atualizadas de todos os vídeos do curso, com novos vídeos e novo código. Sei que isso pode ser desconcertante para quem já está no curso, e farei o possível para que a transição seja a mais tranquila possível.
- As duas séries de vídeos estarão disponíveis na Udemy e você poderá assistir a qualquer uma delas. Um novo conjunto de vídeos deve ficar disponível a cada semana conforme fizermos a atualização.
- Você pode seguir os vídeos originais ou os novos vídeos - ambos funcionarão muito bem. Alterne entre eles quando quiser.
- O código mais recente está publicado no repositório. Você pode acompanhar com o código novo ou voltar ao código original.

Os detalhes completos dessa atualização estão nos recursos do curso, em roxo no topo:  
https://edwarddonner.com/2024/11/13/llm-engineering-resources/

A mudança mais significativa é que a nova versão usa o excelente uv em vez do Anaconda. Mas também há uma enorme quantidade de conteúdo inédito, incluindo novos modelos, ferramentas e técnicas. Cache de prompts, LiteLLM, técnicas de inferência e muito mais.

### Como isso está organizado na Udemy

Estamos disponibilizando as novas semanas, mas mantendo o conteúdo original em um apêndice:

Na Udemy:  

Seção 1 = NOVA SEMANA 1  
Seção 2 = NOVA SEMANA 2  
Seção 3 = NOVA SEMANA 3  
Seção 4 = Semana 4 original  
Seção 5 = Semana 5 original  
Seção 6 = Semana 6 original  
Seção 7 = Semana 7 original  
Seção 8 = Semana 8 original  

E, como apêndice/arquivo:

Seção 9 = Semana 1 original  
Seção 10 = Semana 2 original  
Seção 11 = Semana 3 original  

### Como voltar à versão original do código, consistente com os vídeos originais (Anaconda + virtualenv)

Se preferir manter o código dos vídeos originais, faça o seguinte a partir do Prompt do Anaconda ou do Terminal:  
`git fetch`  
`git checkout original`

E pronto! Qualquer dúvida, fale comigo na Udemy ou em ed@edwarddonner.com. Mais detalhes no topo dos recursos do curso [aqui](https://edwarddonner.com/2024/11/13/llm-engineering-resources/).

### Antes de começar

Estou aqui para ajudá-lo a obter o máximo sucesso na sua aprendizagem. Se encontrar qualquer dificuldade ou tiver ideias de como posso melhorar o curso, entre em contato pela plataforma ou envie um e-mail diretamente para mim (ed@edwarddonner.com). É sempre ótimo conectar com as pessoas no LinkedIn para fortalecer a comunidade - você me encontra aqui:  
https://www.linkedin.com/in/eddonner/  
E esta é uma novidade para mim, mas também estou experimentando o X/Twitter em [@edwarddonner](https://x.com/edwarddonner) - se você estiver no X, mostre-me como se faz!  

Os recursos que acompanham o curso, incluindo slides e links úteis, estão aqui:  
https://edwarddonner.com/2024/11/13/llm-engineering-resources/

E uma FAQ útil com perguntas frequentes está aqui:  
https://edwarddonner.com/faq/

## Instruções de Gratificação Instantânea para a Semana 1, Dia 1 - com Llama 3.2 **não** Llama 3.3

### Nota importante: veja meu alerta sobre a Llama3.3 abaixo - ela é grande demais para computadores domésticos! Fique com a llama3.2 - vários alunos já ignoraram esse aviso...

Vamos começar o curso instalando o Ollama para que você veja resultados imediatamente!
1. Baixe e instale o Ollama em https://ollama.com. Observe que, em PCs, talvez você precise de permissões de administrador para que a instalação funcione corretamente.
2. No PC, abra um Prompt de Comando / Powershell (pressione Win + R, digite `cmd` e pressione Enter). No Mac, abra o Terminal (Aplicativos > Utilitários > Terminal).
3. Execute `ollama run llama3.2` ou, para máquinas mais modestas, `ollama run llama3.2:1b` - **atenção:** evite o modelo mais recente da Meta, o llama3.3, porque com 70B parâmetros ele é grande demais para a maioria dos computadores domésticos!  
4. Se isso não funcionar: talvez seja necessário executar `ollama serve` em outro Powershell (Windows) ou Terminal (Mac) e tentar o passo 3 novamente. No PC, talvez você precise estar em uma instância administrativa do Powershell.  
5. E, se ainda assim não funcionar na sua máquina, configurei tudo na nuvem. Está no Google Colab, que exige uma conta Google para entrar, mas é gratuito: https://colab.research.google.com/drive/1-_f5XZPsChvfU1sJ0QqCePtIuc55LSdu?usp=sharing

Se surgir qualquer problema, entre em contato comigo!

## Em seguida, instruções de configuração

Depois de concluirmos o projeto rápido com o Ollama e após eu me apresentar e apresentar o curso, partimos para configurar o ambiente completo.  

Espero ter feito um bom trabalho para tornar esses guias à prova de falhas - mas entre em contato comigo imediatamente se encontrar obstáculos:

NOVAS INSTRUÇÕES para a nova versão do curso (lançada em outubro de 2025): [Novas instruções de configuração para todas as plataformas](setup/SETUP-new.md)

INSTRUÇÕES ORIGINAIS para quem está na versão anterior a outubro de 2025:  
- Usuários de PC, sigam as instruções aqui: [Instruções originais para PC](setup/SETUP-PC.md)
- Usuários de Mac, sigam as instruções aqui: [Instruções originais para Mac](setup/SETUP-mac.md)  
- Usuários de Linux, sigam as instruções aqui: [Instruções originais para Linux](setup/SETUP-linux.md)

### Um ponto importante sobre custos de API (que são opcionais! Não é preciso gastar se você não quiser)

Durante o curso, vou sugerir que você experimente os modelos de ponta, conhecidos como Frontier models. Também vou sugerir que execute modelos de código aberto usando o Google Colab. Esses serviços podem gerar alguns custos, mas manterei tudo no mínimo - alguns centavos por vez. E fornecerei alternativas caso você prefira não usá-los.

Monitore seu uso de APIs para garantir que os gastos estejam confortáveis para você; incluí os links abaixo. Não há necessidade de gastar mais que alguns dólares durante todo o curso. Alguns provedores de IA, como a OpenAI, exigem um crédito mínimo de US$5 ou equivalente local; devemos gastar apenas uma fração disso, e você terá bastante oportunidade de usar o restante em seus próprios projetos. Na Semana 7 você terá a opção de gastar um pouco mais se estiver curtindo o processo - eu mesmo gasto cerca de US$10 e os resultados me deixam muito feliz! Mas isso não é de forma alguma obrigatório; o importante é focar no aprendizado.

### Alternativa gratuita às APIs pagas

Consulte o [Guia 9](guides/09_ai_apis_and_ollama.ipynb) no diretório de guias para o passo a passo detalhado, com código exato para Ollama, Gemini, OpenRouter e muito mais!

### Como este repositório está organizado

Há pastas para cada uma das "semanas", que representam módulos da turma e culminam em uma poderosa solução autônoma baseada em agentes na Semana 8, reunindo muitos elementos das semanas anteriores.    
Siga as instruções de configuração acima, depois abra a pasta da Semana 1 e prepare-se para se divertir.

### A parte mais importante

O mantra do curso é: a melhor forma de aprender é **FAZENDO**. Eu não digito todo o código durante o curso; executo-o para que você veja os resultados. Trabalhe comigo ou depois de cada aula, executando cada célula e inspecionando os objetos para compreender em detalhes o que está acontecendo. Em seguida, ajuste o código e deixe-o com a sua cara. Há desafios suculentos ao longo do curso. Ficarei muito feliz se você quiser enviar um Pull Request com seu código (veja o guia sobre GitHub na pasta guides) para que eu possa disponibilizar suas soluções a outras pessoas e compartilharmos o seu progresso; como benefício adicional, você será reconhecido no GitHub pela sua contribuição ao repositório. Embora os projetos sejam divertidos, eles são antes de tudo _educacionais_, ensinando habilidades de negócios que você poderá aplicar no seu trabalho.

## A partir da Semana 3, também usaremos o Google Colab para executar com GPUs

Você deverá conseguir usar o nível gratuito ou gastar bem pouco para concluir todos os projetos da turma. Eu, pessoalmente, assinei o Colab Pro+ e estou adorando - mas isso não é obrigatório.

Conheça o Google Colab e crie uma conta Google (se ainda não tiver uma) [aqui](https://colab.research.google.com/)

Os links do Colab estão nas pastas de cada semana e também aqui:  
- Para a semana 3, dia 1, este Google Colab mostra o que [o Colab é capaz de fazer](https://colab.research.google.com/drive/1DjcrYDZldAXKJ08x1uYIVCtItoLPk1Wr?usp=sharing)
- Para a semana 3, dia 2, aqui está um Colab para a [API pipelines](https://colab.research.google.com/drive/1aMaEw8A56xs0bRM4lu8z7ou18jqyybGm?usp=sharing) da HuggingFace
- Para a semana 3, dia 3, temos o Colab sobre [Tokenizers](https://colab.research.google.com/drive/1WD6Y2N7ctQi1X9wa6rpkg8UfyA4iSVuz?usp=sharing)
- Para a semana 3, dia 4, vamos a um Colab com [modelos](https://colab.research.google.com/drive/1hhR9Z-yiqjUe7pJjVQw4c74z_V3VchLy?usp=sharing) da HuggingFace
- Para a semana 3, dia 5, voltamos ao Colab para criar nosso [produto de Atas de Reunião](https://colab.research.google.com/drive/1KSMxOCprsl1QRpt_Rq0UqCAyMtPqDQYx?usp=sharing)
- Para a semana 7, usaremos estes notebooks no Colab: [Dia 1](https://colab.research.google.com/drive/15rqdMTJwK76icPBxNoqhI7Ww8UM-Y7ni?usp=sharing) | [Dia 2](https://colab.research.google.com/drive/1T72pbfZw32fq-clQEp-p8YQ4_qFKv4TP?usp=sharing) | [Dias 3 e 4](https://colab.research.google.com/drive/1csEdaECRtjV_1p9zMkaKKjCpYnltlN3M?usp=sharing) | [Dia 5](https://colab.research.google.com/drive/1igA0HF0gvQqbdBD4GkcK3GpHtuDLijYn?usp=sharing)

### Monitoramento de gastos com APIs

Você pode manter seus gastos com APIs muito baixos durante todo o curso; acompanhe tudo nos painéis: [aqui](https://platform.openai.com/usage) para a OpenAI, [aqui](https://console.anthropic.com/settings/cost) para a Anthropic.

Os custos dos exercícios deste curso devem ser sempre bem reduzidos, mas, se quiser mantê-los no mínimo, escolha sempre as versões mais baratas dos modelos:
1. Para a OpenAI: use sempre o modelo `gpt-4.1-nano` no código
2. Para a Anthropic: use sempre o modelo `claude-3-haiku-20240307` no código em vez dos outros modelos Claude
3. Durante a semana 7, siga minhas instruções para usar o conjunto de dados mais econômico

Por favor, envie uma mensagem ou e-mail para ed@edwarddonner.com se algo não funcionar ou se eu puder ajudar de alguma forma. Mal posso esperar para saber como você está progredindo.

<table style="margin: 0; text-align: left;">
    <tr>
        <td style="width: 150px; height: 150px; vertical-align: middle;">
            <img src="assets/resources.jpg" width="150" height="150" style="display: block;" />
        </td>
        <td>
            <h2 style="color:#f71;">Outros recursos</h2>
            <span style="color:#f71;">Preparei esta página com recursos úteis para o curso. Ela inclui links para todos os slides.<br/>
            <a href="https://edwarddonner.com/2024/11/13/llm-engineering-resources/">https://edwarddonner.com/2024/11/13/llm-engineering-resources/</a><br/>
            Mantenha este link nos favoritos - continuarei adicionando materiais úteis lá ao longo do tempo.
            </span>
        </td>
    </tr>
</table>

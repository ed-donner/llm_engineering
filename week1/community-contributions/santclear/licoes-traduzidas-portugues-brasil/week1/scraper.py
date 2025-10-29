from bs4 import BeautifulSoup
import requests


# Cabeçalhos padrão para acessar um site
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}


def fetch_website_contents(url):
    """
    Retorna o título e o conteúdo do site fornecido na URL;
    trunca para 2.000 caracteres como limite razoável
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    title = soup.title.string if soup.title else "Nenhum título encontrado"
    if soup.body:
        for irrelevant in soup.body(["script", "style", "img", "input"]):
            irrelevant.decompose()
        text = soup.body.get_text(separator="\n", strip=True)
    else:
        text = ""
    return (title + "\n\n" + text)[:2_000]


def fetch_website_links(url):
    """
    Retorna os links do site na URL fornecida
    Reconheço que isso é ineficiente, pois analisamos duas vezes! Isso mantém o código do laboratório simples.
    Sinta-se à vontade para usar uma classe e otimizá-lo!
    """
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.content, "html.parser")
    links = [link.get("href") for link in soup.find_all("a")]
    return [link for link in links if link]

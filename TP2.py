import requests
import math
import re
from datetime import datetime as dt
import json
import os
import typer
import csv
from time import sleep
from bs4 import BeautifulSoup
from fuzzywuzzy import fuzz

app = typer.Typer()

# Variável global para armazenar dados já carregados
API_KEY = "9fa7ce317d6e85c90d92244adb9146c6" # Chave de API para autenticação na API
BASE_URL = "https://api.itjobs.pt/job/list.json" # URL base para a API de vagas
general_results = [] # Lista global para armazenar os dados das vagas

CACHE_FILE = "cache_vagas.json"  # Caminho do arquivo de cache

def echo_verde(msg: str):
    """Exibe uma mensagem em verde."""
    typer.echo(typer.style(msg, fg=typer.colors.GREEN))

def echo_vermelho(msg: str):
    """Exibe uma mensagem em vermelho."""
    typer.echo(typer.style(msg, fg=typer.colors.RED))

def save_to_csv(data, filename,ambitionbox_extra = False):
    """
    Função para salvar os dados em um arquivo CSV.
    """
    keys = ['job_title', 'company', 'company_description', 'published_at', 'salary', 'location']
    if(ambitionbox_extra): 
        keys.append('ambition_box_rating')
        keys.append('ambition_box_description')
        keys.append('ambition_box_benefits')
        
    print (keys)
    
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()  # Escreve o cabeçalho
        
        for item in data:
            item = vaga_restricted_format_csv(item,ambitionbox_extra)
            # Garantir que as descrições de empresa que contenham quebras de linha sejam tratadas como texto literal
            item['company_description'] = item['company_description'].replace("\n", " ").replace("\r", " ")

            # Escreve as linhas com os dados
            writer.writerow(item)  # Cada item é uma linha no arquivo CSV
    
def load_cache():
    """Carrega o cache do arquivo se ele existir"""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        echo_vermelho("Arquivo de cache não encontrado.")
        return(getdata(force_reload=True))

def fetch_from_api():
    """Busca as vagas de emprego diretamente da API e retorna os dados"""
    URL = f'{BASE_URL}?api_key={API_KEY}'
    try:
        request = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
        request.raise_for_status()  # Levanta um erro se o status não for 2xx (OK)
        
        # Processa a resposta da API
        response_data = request.json()
        total_vagas = response_data.get('total', 0)
        
        if total_vagas == 0:
            echo_vermelho("Nenhuma vaga encontrada.")
            return []

        # Calcula o número total de páginas
        total_pages = math.ceil(total_vagas / 12)
        all_jobs = []
        
        # Barra de progresso para carregar todas as páginas
        with typer.progressbar(range(total_pages), label="Carregando páginas") as progress:
            for rep in progress:
                # Carrega cada página de resultados
                datasets = requests.get(URL, params={'limit': 12, 'page': rep + 1}, headers={'User-Agent': 'Mozilla/5.0'}).json()
                all_jobs.extend(datasets.get('results', []))
        
        """Salva os dados de vagas no cache"""
        with open(CACHE_FILE, 'w', encoding='utf-8') as file:
            json.dump(all_jobs, file, ensure_ascii=False, indent=4)
        echo_verde(f"Cache salvo no arquivo '{CACHE_FILE}'.")
        sleep(5)
        
        return all_jobs
    
    except requests.RequestException as e:
        echo_vermelho(f"Erro ao acessar a API: {e}")
        return []

def fetch_ambitionbox(company_name: str):
    """
    Fetch company details from AmbitionBox.
    """
    base_url = "https://www.ambitionbox.com"
    overview_url = f"{base_url}/overview/"
    benefits_url = f"{base_url}/benefits/"
    
    # Clean company name (e.g., remove "Portugal")
    cleaned_name = re.sub(r'\s*portugal\s*', '', company_name, flags=re.IGNORECASE).strip()
    company_espace = cleaned_name.replace(' ', '-').lower()
    
    # Headers to avoid being blocked by AmbitionBox
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:98.0) Gecko/20100101 Firefox/98.0",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0"
    }
    
    try:
        overview_response = requests.get(f"{overview_url}{company_espace}-overview", headers=headers)
        soup = BeautifulSoup(overview_response.text, "html.parser")
        
        # Extract general rating
        rating_tag = soup.find("span", class_="css-1jxf684 text-primary-text font-pn-700 text-xl !text-base")
        rating = float(rating_tag.text.strip()) if rating_tag else None

        #Extract company description
        description_tag = soup.find("div", class_="text-sm font-pn-400 [&_ul]:list-disc [&_ol]:list-[auto] [&_ul]:ml-5 [&_ol]:ml-5")
        description = description_tag.text.strip() if description_tag else None

        # Extract company benefits
        benefits_response = requests.get(f"{benefits_url}{company_espace}-benefits", headers=headers)
        benefits_soup = BeautifulSoup(benefits_response.text, "html.parser")
        benefits_tags = benefits_soup.find_all("h3", class_="css-146c3p1 text-primary-text font-pn-600 text-[16px] leading-[24px] mb-1 sm:max-w-[223px] sm:line-clamp-1")
        benefits = [tag.text.strip() for tag in benefits_tags] if benefits_tags else None

        # Return extracted details as dictionary
        return {
            "rating": rating,
            "ambition_box_description": description,
            "ambition_box_benefits": benefits
        }
    except:
        echo_vermelho("No additional information was found while fetching AmbitionBox details")

def getdata(force_reload: bool = False):
    """
    Função para buscar dados das vagas de emprego. Se `force_reload` for True, 
    recarrega os dados da API e salva no cache. Caso contrário, usa o cache.
    """
    global general_results
    
    if force_reload:
        # Se for forçado o reload, buscamos da API e salvamos no cache
        echo_verde("Carregando dados da API...")
        general_results = fetch_from_api()
    else:
        # Caso contrário, carregamos do ficheiro 'cache_vagas.json'
        general_results = load_cache()

    return general_results

def vaga_restricted_format_csv(item,ambitionbox_extra = False):
    """
    Função para formatar os dados de uma vaga com as informações selecionadas.
    Agora também adiciona dados do AmbitionBox se fornecido.
    """
    print(item)  # Verifique o conteúdo de 'item'
    
    # Garantir que 'company' seja um dicionário, caso contrário, usa-se um dicionário vazio
    company = item['company'] if isinstance(item['company'], dict) else {}
    
    # Formatação e retorno dos dados
    result = {
        'job_title': item['title'] if 'title' in item else 'N/A',  # Acessa 'title' diretamente
        'company': company['name'] if 'name' in company else 'N/A',  # Acessa 'name' diretamente
        'company_description': company['description'] if 'description' in company else 'N/A',  # Acessa 'description' diretamente
        'published_at': item['publishedAt'] if 'publishedAt' in item else 'N/A',  # Acessa 'publishedAt' diretamente
        'salary': item['wage'] if 'wage' in item else 'N/A',  # Acessa 'wage' diretamente
        'location': [loc['name'] for loc in item['locations']] if 'locations' in item else ['N/A'],  # Acessa 'locations' diretamente
    }
    
    # Se 'ambitionbox_extra' for True, inclui dados do AmbitionBox
    if ambitionbox_extra:
        result['ambition_box_rating'] = company['ambition_box_rating'] if 'ambition_box_rating' in company else 'N/A'
        result['ambition_box_description'] = company['ambition_box_description'] if 'ambition_box_description' in company else 'N/A'
        result['ambition_box_benefits'] = company['ambition_box_benefits'] if 'ambition_box_benefits' in company else 'N/A'
    
    return result

@app.command()
def top(n: int, save: bool = False):
    """
    Função para mostrar as 'n' vagas mais recentes.
    Exibe algumas informações selecionadas sobre as vagas.
    """
    general_data = getdata()  # Obtém dados da API ou cache
    found_jobs = [item for item in general_data[0:n]] # Exibe os dados das 'n' vagas mais recentes    
    
    # Se 'save_csv' for True, salva os dados em CSV
    if save:
        save_to_csv(found_jobs, "top_vagas.csv")

    print(json.dumps(found_jobs,indent=4))  # Altera para formato JSON as vagas encontradas e exibe os resultados
    
    if save:
        echo_verde(f"Resultados salvos em 'top_vagas.csv'")

@app.command()
def search(company: str, location: str, num_jobs: int, save: bool = False):
    """
    Função para procurar vagas de emprego de uma empresa específica em uma localidade e que seja full time,
    limitando o número de vagas retornadas.
    """
    general_data = getdata() # Obtém dados da API ou cache
    found_jobs = [] # Inicializa / reseta a lista de trabalhos encontrados
    
    for item in general_data:
        company_name = item['company']['name'] # Obtém o nome da empresa
        job_locations = [loc['name'] for loc in item.get('locations', [])] # Obtém as localizações das vagas
        job_type = [job['name'].lower() for job in item.get('types', [])] # Checa o tipo de trabalho (full-time, part-time, etc.)
        
        # Verifica se a vaga corresponde ao nome da empresa e se a localização está na lista
        if (company_name.lower() == company.lower() and any(location.lower() in loc.lower() for loc in job_locations) and 'full-time' in job_type):
            found_jobs.append(item) # Adiciona o trabalho encontrado à lista
        
        if len(found_jobs) >= num_jobs: # Se o número de vagas encontrado atingir o limite, saímos do loop
            break
    
    # Se 'save_csv' for True, salva os dados em CSV
    if save and found_jobs:
        save_to_csv(found_jobs, "search_vagas.csv")
    
    if found_jobs: # Exibe o resultado no formato JSON ou uma mensagem caso não encontre resultados
        print(json.dumps(found_jobs,indent=4))
    else:
        echo_vermelho("Nenhum trabalho encontrado para os critérios especificados.")
    
    if save and found_jobs:
        echo_verde(f"Resultados salvos em 'search_vagas.csv'")

@app.command()
def salary(job_id: int):
    """
    Função para extrair e exibir o salário de uma vaga a partir de seu job_id.
    Caso o salário não esteja disponível, achar com expressoes regulares.
    """
    general_data = getdata()  # Obtém dados da API ou cache
    
    # Expressões regulares para encontrar salários no corpo da descrição
    salary_patterns = [
        r"(\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d+)?\s?(?:euros|€|bruto|neto|por mês|mensal))",  # Ex: 3000€, 3000 euros, 2500 por mês
        r"(\d+\s?k\s?€)",# Ex: 2.5k €  
        r"(\d+(?:[\.,]\d+)?\s?(k|K|mil)\s?(€|euros)?)",  # Ex: 2k €, 2.5k euros # Ex: 2.5k € (abreviação de mil em euros)
        r"(\d{1,3}(?:,\d{3})*(?:[\.,]\d+)?\s?(€|euros|bruto|neto|por mês|mensal|anual|por ano))", # Ex: 5,000 (usando vírgula como separador de milhar) 
        r"(\d+(?:[\.,]\d+)?\s?(por mês|mensal|anual|ano))",  # Ex: 2500 por mês, 3500 anuais
        r"(\d+(?:[\.,]\d+)?\s?(k|K|mil)\s?(€|euros))",  # Ex: 5k €, 10K euros
        r"(\d{1,3}(?:\.\d{3})*(?:,\d+)?\s?(€|euros))",  # Ex: 10000,00 €, 1.000,00 euros
    ]
    
    #
    # NAO FOI ENCONTRADA NENHUMA REFERÊNCIA DE SALÁRIO NOS BODYS :(
    #
    
    for item in general_data:
        if item['id'] == job_id:
            salary = item.get('wage') # Tenta obter o salário diretamente
            
            if not salary: # Se salario não existir entao tentar buscar salario no 'body'
                salary = [re.search(pattern, item.get('body'), re.IGNORECASE).group(0) for pattern in salary_patterns if re.search(pattern, item.get('body'), re.IGNORECASE)] 
                if not salary:
                    salary = "salario não encontrado."

            locations = (', '.join([location['name'] for location in item.get('locations', [])])) # Obtém a(s) localização(ões) da vaga
            
            # Exibe as informações da vaga e o salário
            print(f"Id: {job_id} - {item['title']}, {item['company']['name']} ({locations}): {salary}")
            return print(salary)
            
    echo_vermelho(f"Vaga com o id {job_id} não encontrada.") # Caso não encontre a vaga com o job_id

@app.command()
def skills(skills:str, data_ini:str, data_fim:str, save: bool = False):
    """
    Função para buscar dados de vagas de emprego com base nas skills e no intervalo de datas.
    A saída é no formato JSON, com os dados das vagas que atendem aos critérios.
    """
    general_results = getdata() # Obtém dados da API ou cache
    
    # Tenta converter as datas para o formato correto
    try:
        data_ini = dt.strptime(data_ini, '%Y-%m-%d')  # Converte a data de início
        data_fim = dt.strptime(data_fim, '%Y-%m-%d')  # Converte a data de fim
    except ValueError:
        return echo_vermelho("Erro: Uma ou ambas as datas fornecidas são inválidas. Por favor, use o formato 'YYYY-MM-DD'.")
    
    # Skills para lista de strings "python,react" -> ['python','react']
    skills_list = [skill.strip() for skill in skills.split(",")] 
    
    found_jobs = [] # Inicializa / reseta a lista de trabalhos encontrados
    
    for item in general_results:
        data_trabalho = dt.strptime(item['publishedAt'], '%Y-%m-%d %H:%M:%S') # Converte a data de publicação para o formato correto
        
        # Verifica se a vaga está dentro do intervalo de datas e contém todas as skills desejadas
        if data_ini <= data_trabalho <= data_fim and all(re.search(criar_regex_sem_acentos(skill), item['body'], re.IGNORECASE) for skill in skills_list):
            found_jobs.append(item) # Adiciona à lista de vagas encontradas
    
    # Se 'save_csv' for True, salva os dados em CSV
    if save and found_jobs:
        save_to_csv(found_jobs, "skills_vagas.csv")
        
    # Exibe o resultado em JSON ou uma mensagem caso nenhuma vaga seja encontrada
    if found_jobs:
        print(json.dumps(found_jobs, indent=4))
    else:
        echo_vermelho("Nenhuma vaga encontrada para os critérios informados.")
    
    if save and found_jobs:
        echo_verde(f"Resultados salvos em 'skills_vagas.csv'")

@app.command()
def get(job_id:int, save: bool = False):
    """
    Fetch details of a specific job from ItJobs API and enrich with AmbitionBox data.
    """

    general_results = getdata()
    
    job_found = None
    for job in general_results:
        if job["id"] == job_id:
            job_found= job
            break
        
    # Caso não tenha sido encontrado umm job com esse Id
    if not job_found:
        echo_vermelho(f"Job ID {job_id} not found.")
        return {}
    
    company_name = job_found["company"]["name"]
    company_details = job_found["company"]
    
    #Get data from ambitionbox
    ambitionbox_data = fetch_ambitionbox(company_name)
    
    if ambitionbox_data:
        company_details["ambition_box_rating"] = ambitionbox_data.get("rating")
        company_details["ambition_box_description"] = ambitionbox_data.get("ambition_box_description")
        company_details["ambition_box_benefits"] = ambitionbox_data.get("ambition_box_benefits")
    
    # Add ambitionbox info to company details back to job details
    job_found["company"] = company_details

    # Se 'save_csv' for True, salva os dados em CSV
    if save and job_found:
        save_to_csv([job_found], "get_vaga.csv",True)
        
    # Exibe o resultado em JSON ou uma mensagem caso nenhuma vaga seja encontrada
    if job_found:
        print(json.dumps(job_found, indent=4))
    else:
        echo_vermelho("Nenhuma vaga encontrada para os critérios informados.")
    
    if save and job_found:
        echo_verde(f"Resultados salvos em 'get_vaga.csv'")

def clean_title_for_grouping(title):
    """
    Limpa o título para agrupamento, transformando-o em minúsculas, removendo conteúdo de parênteses,
    padronizando termos como .NET e agrupando tecnologias e cargos em categorias mais amplas.
    """
    
    # Transformar o título todo para minúsculas para comparação
    title_clean = title.lower()

    # Padronizar termos específicos
    title_clean = re.sub(r"\.net", ".net", title_clean)
    title_clean = re.sub(r"\.java", ".java", title_clean)
    title_clean = re.sub(r"\.python", ".python", title_clean)
    title_clean = re.sub(r"\.js", ".js", title_clean)
    title_clean = re.sub(r"c\+\+", "c++", title_clean)
    title_clean = re.sub(r"c#", "c#", title_clean)
    title_clean = re.sub(r"node\.js", "node.js", title_clean)
    
    # Remover conteúdo entre parênteses (ex.: "front-end (junior)" -> "front-end")
    title_clean = re.sub(r"\s?\(.*?\)", "", title_clean)  # Remove conteúdo dentro de parênteses

    # Padronizar termos relacionados a cargos e níveis de senioridade
    # Padronizar cargos e senhioridade
    title_clean = re.sub(r"\b(junior|s[eé]nior|specialist|engineer|expert|intern|lead|tester|developer|manager|architect|consultant|analyst|director|coordinator|administrator|programmer|designer|assistant|consultor|consultant|executive|team lead|supervisor)\b", "", title_clean)

    # Expandir as tecnologias para termos mais gerais
    technologies = [
        ".net", "java", "python", "node.js", "react", "angular", "sql", "devops", "aws", "azure", "gcp", 
        "android", "ios", "golang", "kotlin", "docker", "cloud", "rpa", "php", "sap", "docker", "linux", "it", 
        "bi", "full-stack", "backend", "frontend", "ux/ui", "mobile", "windows", "it", "mongodb", "kafka", "alteryx", 
        "firebase", "vue.js", "kafka", "oracle", "scala", "embedded", "data", "talend", "etl", "salesforce", 
        "big data", "ai", "machine learning", "deep learning", "iot", "cybersecurity", "blockchain", "ci/cd", 
        "kubernetes", "jenkins", "apache", "terraform", "big data", "etl", "graphql", "sdlc", "azure devops", "jira", 
        "scrum", "agile", "ms sql", "nosql", "spark", "hadoop", "etl"
    ]
    
    # Adicionar espaços para garantir uma melhor correspondência de palavras exatas
    for tech in technologies:
        title_clean = re.sub(rf"\b({tech})\b", f" {tech} ", title_clean)

    # Agrupar por áreas mais amplas de desenvolvimento
    title_clean = re.sub(r"\b(backend|frontend|full-stack|developer|developer front-end|developer back-end|web developer|mobile developer|software developer)\b", "developer", title_clean)

    # Agrupar cargos de consultoria/gestão
    title_clean = re.sub(r"\b(analyst|consultant|manager|architect|specialist|lead|director|coordinator|administrator|programmer|designer|assistant|team lead|supervisor|consultor|executive)\b", "consultant", title_clean)

    # Agrupar tecnologias de cloud
    title_clean = re.sub(r"\b(aws|azure|gcp|cloud|devops|kubernetes|terraform|jenkins|ci/cd)\b", "cloud", title_clean)
    
    # Agrupar tecnologias de dados
    title_clean = re.sub(r"\b(bi|mongodb|kafka|firebase|spark|hadoop|etl|nosql|big data|data|alteryx|talend|oracle|sql|postgresql)\b", "data", title_clean)

    # Agrupar tecnologias de segurança
    title_clean = re.sub(r"\b(cybersecurity|blockchain|security|vpn|pen testing)\b", "security", title_clean)

    # Remover termos genéricos ou irrelevantes
    title_clean = re.sub(r"\b(solutions|technician|engineer|specialist|consultant|manager|executive|team|lead|staff)\b", "", title_clean)

    # Limpeza final dos espaços
    title_clean = title_clean.strip()

    # Normaliza para garantir que não existam mais de dois espaços consecutivos
    title_clean = re.sub(r'\s+', ' ', title_clean)  # Substitui qualquer sequência de espaços por um único espaço

    return title_clean

def format_title(title):
    """
    Formata o título original, fazendo a primeira letra maiúscula e o restante minúsculo.
    """
    # Transformar o título para ter a primeira letra maiúscula e as demais minúsculas
    return title.strip().title()

def group_similar_titles(titles):
    """
    Agrupa títulos de vagas semelhantes, mantendo os títulos originais inalterados e usando a versão limpa para agrupamento.
    """
    grouped_titles = {}

    for title in titles:
        # Processar o título para comparação
        clean = clean_title_for_grouping(title)

        # Verifica se o título já está agrupado
        matched = False
        for group in grouped_titles:
            if fuzz.ratio(clean, group) > 85:  # Usando a versão processada para comparação
                if title not in grouped_titles[group]:  # Evita duplicação
                    grouped_titles[group].append(title)
                matched = True
                break
        
        if not matched:
            grouped_titles[clean] = [title]

    # Formatar os títulos originais para ter a primeira letra maiúscula e o restante minúsculo
    formatted_grouped_titles = {}
    for clean_title, original_titles in grouped_titles.items():
        formatted_grouped_titles[format_title(clean_title)] = [format_title(t) for t in original_titles]
    
    return formatted_grouped_titles

def save_statistics_to_csv(all_groups, file_name,show):
    """
    Salva as estatísticas de títulos agrupados em um único arquivo CSV.
    Se 'show' for True, a última coluna ('Grouped Titles') será removida.
    """
    with open(file_name, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)

        # Se 'show' for false, não incluir a coluna 'Grouped Titles'
        if not show:
            writer.writerow(["Zone", "Job Title", "Number of jobs"])  # Sem a coluna 'Grouped Titles'
        else:
            writer.writerow(["Zone", "Job Title", "Number of jobs", "Grouped Titles"])  # Inclui 'Grouped Titles'
        
        # Iterando pelas zonas e grupos de títulos
        for zone, grouped_titles in all_groups.items():
            for title, jobs in grouped_titles.items():
                grouped_titles_list = list(set(jobs))  # Remover duplicados
                if not show:
                    # Escreve a linha sem a coluna 'Grouped Titles'
                    writer.writerow([zone, title, len(jobs)])
                else:
                    # Escreve a linha com a coluna 'Grouped Titles'
                    writer.writerow([zone, title, len(jobs), grouped_titles_list])

@app.command() # zone or type (show is for testing but cool to have)
def statistics(group_by: str, show:bool = False):
    """
    Função para gerar estatísticas de vagas de emprego, agrupadas por zona ou tipo de trabalho.
    Agora inclui a lista de títulos agrupados. (zone or type)
    """
    general_results = getdata()  # Obtém todos os dados
    all_groups = {}  # Para armazenar as zonas e seus títulos agrupados
    
    if group_by == "zone":
        # Agrupar vagas por zona
        for job in general_results:
            if "locations" in job and job["locations"]:
                for location in job["locations"]:
                    zone = location["name"]
                    if zone not in all_groups:
                        all_groups[zone] = {}
                    job_titles = [job["title"]]  # Título da vaga
                    grouped_titles = group_similar_titles(job_titles)
                    for title, jobs in grouped_titles.items():
                        if title not in all_groups[zone]:
                            all_groups[zone][title] = []
                        all_groups[zone][title].extend(jobs)
        
        # Salva todas as estatísticas em um único arquivo CSV
        save_statistics_to_csv(all_groups, "statistics_zone.csv",show)
        echo_verde(f"File 'statistics_zone.csv' created successfully with all zones.")
    
    elif group_by == "type":
        # Agrupar vagas por tipo de trabalho (full-time, part-time, etc.)
        for job in general_results:
            if "types" in job:
                for job_type in job["types"]:
                    type_name = job_type["name"]
                    if type_name not in all_groups:
                        all_groups[type_name] = {}
                    job_titles = [job["title"]]  # Título da vaga
                    grouped_titles = group_similar_titles(job_titles)
                    for title, jobs in grouped_titles.items():
                        if title not in all_groups[type_name]:
                            all_groups[type_name][title] = []
                        all_groups[type_name][title].extend(jobs)
        
        # Salva todas as estatísticas em um único arquivo CSV
        save_statistics_to_csv(all_groups, "statistics_type.csv",show)
        echo_verde(f"File 'statistics_type.csv' created successfully with all job types.")
        
def criar_regex_sem_acentos(palavra):
    """
    Esta função cria uma expressão regular que ignora os acentos em uma palavra
    para que a busca seja insensível a acentos (exemplo: 'inteligência' será igual a 'inteligencia').
    """
    # Inteligência -> Intelig[eéèê]ncia

    # Mapa de caracteres com acento para suas versões sem acento
    mapa_acentos = {
        'a': '[aáàãâ]',
        'e': '[eéèê]',
        'i': '[iíìî]',
        'o': '[oóòôõ]',
        'u': '[uúùû]',
        'c': '[cç]',
        'n': '[nñ]'
    }
    # Substitui cada letra com acento por sua versão com acento, tornando a busca flexível
    palavra_regex = ''
    for char in palavra:
        if char.lower() in mapa_acentos:
            palavra_regex += mapa_acentos[char.lower()] # Adiciona os caracteres com alterações
        else:
            palavra_regex += char # Adiciona o caractere sem alteração
            
    return palavra_regex # Retorna a expressão regular criada

@app.command()
def reloadapi():
    """Regarrega o ficheiro json com dados da API"""
    getdata(force_reload=True)
    
@app.command()
def help():
    """
    Ajuda com os comandos
    """
    print("""
####  HELP  #########################################################################################################################################################   
#                                                                                                                                                                   #   
# python TP1.py help : Exibe ajuda detalhada sobre todos os comandos e como utilizá-los.                                                                            #   
#           Exemplo: python TP1.py help                                                                                                                             #
#                  Exibe todas as opções e parâmetros disponíveis no script.                                                                                        #
#                                                                                                                                                                   #
# python TP1.py top <n> [--save] : Mostra as 'n' vagas mais recentes. Se '--save' for fornecido, salva os resultados em um arquivo CSV chamado "top_vagas.csv".     #
#                                                                                                                                                                   #
#           Parâmetros:                                                                                                                                             #
#             <n>       : O número de vagas que você deseja exibir. Substitua <n> por um número inteiro (ex: 5, 10, 20).                                            #
#             --save    : Se fornecido, salva as vagas exibidas em um arquivo CSV chamado "top_vagas.csv".                                                          #
#                                                                                                                                                                   #           
#           Exemplo:                                                                                                                                                #
#             python TP1.py top 5 --save                                                                                                                            #
#                 Exibe as 5 vagas mais recentes e salva os resultados em "top_vagas.csv".                                                                          #
#                                                                                                                                                                   #
# python TP1.py search <empresa> <localidade> <n> [--save] : Procura vagas para uma empresa específica em uma localidade específica (somente vagas full-time).      #
#               Limita a quantidade de resultados retornados para 'n'. Se '--save' for fornecido, salva os resultados em um arquivo CSV chamado "search_vagas.csv". #
#                                                                                                                                                                   #
#           Parâmetros:                                                                                                                                             #
#             <empresa> : Nome da empresa para a qual você deseja procurar vagas. Coloque o nome da empresa entre aspas se contiver espaços (ex: "altar.io").       #
#             <localidade>: Nome da cidade ou localidade onde você deseja buscar as vagas (ex: Lisboa, Porto).                                                      #
#             <n>       : Número de vagas a ser retornado. Substitua <n> por um número inteiro (ex: 3, 10).                                                         #
#             --save    : Se fornecido, salva os resultados encontrados em um arquivo CSV chamado "search_vagas.csv".                                               #
#                                                                                                                                                                   #           
#           Exemplo:                                                                                                                                                #
#             python TP1.py search "altar.io" "Braga" 3 --save                                                                                                      #
#                 Busca 3 vagas da empresa "altar.io" na localidade "Braga" e salva os resultados em "search_vagas.csv".                                            #
#                                                                                                                                                                   #
# python TP1.py salary <id> : Exibe o salário da vaga de acordo com o ID da vaga.                                                                                   #
#                                                                                                                                                                   #
#           Parâmetros:                                                                                                                                             #
#             <id>      : O ID da vaga para a qual você deseja saber o salário. O ID deve ser um número inteiro único (ex: 491881).                                 #
#                                                                                                                                                                   #           
#           Exemplo:                                                                                                                                                #
#             python TP1.py salary 491881                                                                                                                           #
#                 Exibe o salário da vaga com ID 491881.                                                                                                            #
#                                                                                                                                                                   #
# python TP1.py skills <skills> <data_ini> <data_fim> [--save] : Procura vagas que exigem habilidades específicas dentro de um intervalo de datas.                  #
#               O parâmetro 'skills' pode ser uma lista de habilidades separadas por vírgula. O intervalo de datas deve ser fornecido no formato 'YYYY-MM-DD'.      #
#               Se '--save' for fornecido, salva os resultados em um arquivo CSV chamado "skills_vagas.csv".                                                        #
#                                                                                                                                                                   #   
#           Parâmetros:                                                                                                                                             #
#             <skills>   : Lista de habilidades requeridas para as vagas. Use vírgulas para separar múltiplas habilidades (ex: "Python, Data Science").             #
#             <data_ini> : Data de início do intervalo de busca (formato: 'YYYY-MM-DD'). Exemplo: "2024-01-01".                                                     #
#             <data_fim> : Data final do intervalo de busca (formato: 'YYYY-MM-DD'). Exemplo: "2024-12-31".                                                         #
#             --save     : Se fornecido, salva os resultados encontrados em um arquivo CSV chamado "skills_vagas.csv".                                              #
#                                                                                                                                                                   #           
#           Exemplo:                                                                                                                                                #
#             python TP1.py skills "Python, Data Science" "2024-01-01" "2024-12-31" --save                                                                          #
#                 Busca vagas que exigem "Python" e "Data Science" no intervalo de 01/01/2024 a 31/12/2024 e salva os resultados em "skills_vagas.csv".             #
#                                                                                                                                                                   #   
# python TP1.py reloadapi : Força o recarregamento dos dados da API, ignorando qualquer cache armazenado.                                                           #
#                                                                                                                                                                   # 
#           Exemplo:                                                                                                                                                #
#             python TP1.py reloadapi                                                                                                                               #
#                 Atualiza o cache com os dados mais recentes da API.                                                                                               #
#                                                                                                                                                                   #
#####################################################################################################################################################################
""")
    
# Comandos Teste #

# python TP2.py reloadapi
# python TP2.py top 10
# python TP2.py top 10 --save
# python TP2.py top 1000 --save
# python TP2.py top 1 --save
# python TP2.py search "altar.io" "Braga" 3
# python TP2.py search "altar.io" "Braga" 3 --save
# python TP2.py search "altar.io" "Lisboa" 10 --save
# python TP2.py salary 491881, 491763, 491690, 491671, 491626, 490686, 491483, 491458
# python TP2.py skills "Data, Python, DJango" "2024-1-1" "2024-12-31"
# python TP2.py skills "Python" "2024-1-1" "2024-12-31"
# python TP2.py skills "Python" "2024-1-1" "2024-12-31" --save
# python TP2.py skills "Python" "2024-10-01" "2024-10-31"
# python TP2.py skills "Python" "2024-10-01" "2024-10-31" --save
# python TP2.py skills "inteligencia artificial" "2024-1-1" "2024-12-31"
# python TP2.py skills "Data" "2024-1-1" "2024-12-31"  
# python TP2.py skills "inteligencia artificial, Python" "2024-1-1" "2024-12-31"
# python TP2.py get 493936
# python TP2.py statistics zone
# python TP2.py statistics zone --show
# python TP2.py statistics type
# python TP2.py statistics type --show

# Inicializa o aplicativo Typer
if __name__ == "__main__":
    app()
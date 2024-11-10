import requests
import json
import re
import math
import typer
import csv 
from bs4 import BeautifulSoup as bs
from datetime import datetime
current_time = datetime.now()  # Agora você pode usar diretamente datetime.now()





# Constantes de Configuração
API_KEY = "9fa7ce317d6e85c90d92244adb9146c6"
BASE_URL = "https://api.itjobs.pt/job/list.json"

app = typer.Typer()

# Função para buscar vagas da API
def fetch_jobs(params):
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    response = requests.get(BASE_URL, params=params, headers=headers)
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Erro ao obter dados: {response.status_code} - {response.text}")
        return None

# Função para buscar os 10 trabalhos mais recentes
def top10():
    print("Procurando os 10 trabalhos mais recentes...")
    response = requests.get(BASE_URL, params={'api_key': API_KEY, 'limit': 10, 'page': 1}, headers={'User-Agent': 'Mozilla/5.0'})
    data = response.json()
    
    if 'results' in data:
        top_10_jobs = [{'id': item['id'], 'title': item['title'], 'company_name': item['company']['name']} for item in data['results']]
        print(json.dumps(top_10_jobs, indent=4))
    else:
        print("Nenhum trabalho encontrado.")

def get_jobs(location, company, num_jobs):
    # URL da API com a chave de API fornecida
    URL = 'https://api.itjobs.pt/job/list.json?api_key=9fa7ce317d6e85c90d92244adb9146c6'
    
    try:
        # Buscar dados da API
        request = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'})
        
        # Verificar se o código de status da resposta é 200 (OK)
        if request.status_code != 200:
            print(f"Erro: Recebido código de status {request.status_code} da API")
            return
        
        # Analisar os dados JSON
        data = request.json()
        
        # Obter a lista de empregos da resposta
        jobs = data.get("results", [])
        if not isinstance(jobs, list):
            print("Erro: Formato inesperado dos dados da API.")
            return
        
    except Exception as e:
        print(f"Erro ao buscar dados da API: {e}")
        return
    
    # Filtrar os empregos com base na empresa e localização especificadas
    filtered_jobs = []
    for job in jobs:
        # Obter o nome da empresa e as localizações do emprego
        company_name = job.get("company", {}).get("name", "").strip().lower()
        job_locations = [location_item.get("name", "").strip().lower() for location_item in job.get("locations", [])]
        
        # Verificar se o nome da empresa contém o termo especificado e se a localização corresponde
        if company.lower() in company_name and any(location.lower() in loc for loc in job_locations):
            filtered_jobs.append(job)
    
    # Limitar o número de empregos ao valor especificado
    filtered_jobs = filtered_jobs[:num_jobs]
    
    # Retornar ou exibir os empregos filtrados
    if filtered_jobs:
        print(json.dumps(filtered_jobs, ensure_ascii=False, indent=2))
    else:
        print("Nenhum trabalho encontrado para os critérios especificados.")


# Função para obter o salário de um emprego específico
def salary(jobID):
    URL = 'https://api.itjobs.pt/job/get.json'
    try:
        response = requests.get(URL, params={'api_key': API_KEY, 'id': jobID}, headers={'User-Agent': 'Mozilla/5.0'})
        if response.status_code != 200:
            print(f"Erro: Status HTTP {response.status_code}. Verifique a chave da API e o jobID.")
            return
        
        data = response.json()
        wage = data.get('wage')
        
        if wage:
            print(f"Apresenta um salário inicial de {wage}€.")
        else:
            salary_found = extract_salary_from_body(data.get('body', ''))
            if salary_found:
                print(f"Salário encontrado no corpo da descrição: {salary_found}")
            else:
                print("Sem informação sobre o salário.")
    except requests.JSONDecodeError:
        print("Erro: A resposta não está em formato JSON.")

# Função auxiliar para extrair salário usando expressões regulares
def extract_salary_from_body(body):
    salary_patterns = [
        r"(\d{1,3}(?:[\.,]\d{3})*(?:[\.,]\d+)?\s?(?:euros|€|bruto|neto|por mês|mensal))",
        r"(\d+\s?k\s?€)"
    ]
    for pattern in salary_patterns:
        match = re.search(pattern, body, re.IGNORECASE)
        if match:
            return match.group(0)
    return None

# Função que busca e filtra os trabalhos de acordo com skills e período de tempo
def skills_data(skills, data_ini, data_fim):
    not_found = True
    URL = f'{BASE_URL}?api_key={API_KEY}'
    request = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
    data = request.json()
    
    alldata = []
    total_pages = math.ceil(data['total'] / 12) if data['total'] > 0 else 1
    
    for rep in range(total_pages):
        datasets = requests.get(URL, params={'limit': 12, 'page': rep + 1}, headers={'User-Agent': 'Mozilla/5.0'}).json()
        results = datasets['results']
        
        for item in results:
            data_trabalho = datetime.strptime(item['publishedAt'], '%Y-%m-%d %H:%M:%S')
            
            if data_ini <= data_trabalho <= data_fim:
                if all(re.search(r'\b' + re.escape(skill) + r'\b', item['body'], re.IGNORECASE) for skill in skills):
                    trabalho_info = {
                        'id': item['id'],
                        'title': item.get('title', ''),
                        'company_name': item['company'].get('name', ''),
                        'publishedAt': item.get('publishedAt', ''),
                        'wage': item.get('wage', ''),
                        'address': item['company'].get('address', '')
                    }
                    alldata.append(trabalho_info)
                    not_found = False
    
    return alldata  # Retorna lista vazia se não encontrar dados

# Função para exibir os trabalhos conforme as skills e período
def buscar_trabalhos_por_skills(skills, data_inicial, data_final):
    data_ini = datetime.strptime(data_inicial, '%Y-%m-%d')
    data_fim = datetime.strptime(data_final, '%Y-%m-%d')
    resultados = skills_data(skills, data_ini, data_fim)
    
    if resultados:
        return json.dumps(resultados, indent=4)
    else:
        return "Nenhum trabalho encontrado para as habilidades e período fornecidos."










# Exemplo de execução
if __name__ == "__main__":
    top10()
    get_jobs("Lisboa", "Noesis Portugal", 5)
    print(salary(490686))  # Substitua pelo ID de trabalho real
    print(buscar_trabalhos_por_skills(["Python", "Django"], "2024-10-01", "2024-10-31"))








def top10(export_csv=False):
    print("Procurando os 10 trabalhos mais recentes...")

    URL = 'https://api.itjobs.pt/job/list.json'
    API_KEY = '9fa7ce317d6e85c90d92244adb9146c6'

    response = requests.get(URL, params={'api_key': API_KEY, 'limit': 10, 'page': 1}, headers={'User-Agent': 'Mozilla/5.0'})
    data = response.json()

    if 'results' in data:
        top_10_jobs = [
            {
                'id': item['id'],
                'title': item['title'],
                'company_name': item['company']['name'],
                'description': item.get('description', 'N/A'),
                'published_at': item.get('published_at', 'N/A'),
                'salary': item.get('salary', 'N/A'),
                'location': ', '.join([loc['name'] for loc in item.get('locations', [])])
            }
            for item in data['results']
        ]

        print(json.dumps(top_10_jobs, indent=4))

        if export_csv:
            filename = f"top_10_jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            fields = ['id', 'title', 'company_name', 'description', 'published_at', 'salary', 'location']
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=fields)
                writer.writeheader()
                writer.writerows(top_10_jobs)
            print(f"Os 10 trabalhos mais recentes foram exportados para {filename}")
    else:
        print("Nenhum trabalho encontrado.")

# Função unificada para exportar uma lista de trabalhos para CSV
import csv

def export_to_csv(jobs, filename="jobs.csv"):
    # Definindo os campos a serem incluídos no arquivo CSV
    fieldnames = ['titulo', 'empresa', 'localizacao', 'tipo', 'descricao', 'data_publicacao', 'salario']
    
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            
            # Escrevendo os dados de cada trabalho no arquivo CSV
            for job in jobs:
                job_data = {
                    'titulo': job.get('title', 'N/A'),
                    'empresa': job.get('company', {}).get('name', 'N/A'),
                    'localizacao': ', '.join([location.get('name', 'N/A') for location in job.get('locations', [])]),
                    'tipo': job.get('type', 'N/A'),
                    'descricao': job.get('body', 'N/A'),
                    'data_publicacao': job.get('published', 'N/A'),
                    'salario': job.get('wage', 'N/A')
                }
                writer.writerow(job_data)
        
        print(f"Dados exportados com sucesso para {filename}")
    except Exception as e:
        print(f"Erro ao exportar para CSV: {e}")



def get_jobs(location, company, num_jobs, job_type, export_csv=False):
    # Corpo da função

    # URL da API com a chave de API fornecida
    URL = 'https://api.itjobs.pt/job/list.json?api_key=9fa7ce317d6e85c90d92244adb9146c6'
    
    # Buscar dados da API
    try:
        request = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/118.0'})
        
        # Verificar se o código de status da resposta não é 200 (OK)
        if request.status_code != 200:
            print(f"Erro: Recebido código de status {request.status_code} da API")
            return
        
        # Analisar os dados JSON
        data = request.json()
        
        # Imprimir os dados brutos para inspecionar sua estrutura
        print("Dados de resposta da API:", json.dumps(data, indent=2, ensure_ascii=False))
        
        # A resposta da API tem a chave 'results' que contém os empregos
        jobs = data.get("results", [])
        
        # Verificar se 'results' contém uma lista de empregos
        if not isinstance(jobs, list):
            print("Erro: Formato inesperado dos dados da API. Esperado uma lista de empregos.")
            return
        
    except Exception as e:
        print(f"Erro ao buscar dados da API: {e}")
        return
    
    # Filtrar os empregos com base no tipo de trabalho, localização e nome da empresa
    filtered_jobs = []
    for job in jobs:
        company_name = job.get("company", {}).get("name", "").lower()
        job_locations = [location_item.get("name", "").lower() for location_item in job.get("locations", [])]
        
        # Verificar se a empresa e a localização são correspondentes (case insensitive) e permitir correspondência parcial
        if (company.lower() in company_name) and any(location.lower() in location_item for location_item in job_locations):
            filtered_jobs.append({
                'titulo': job.get("title", "N/A"),
                'empresa': job.get("company", {}).get("name", "N/A"),
                'descrição': job.get("description", "N/A"),
                'data_publicacao': job.get("publication_date", "N/A"),
                'salário': job.get("salary", "N/A"),
                'localizacao': ", ".join(job_locations)
            })
    
    # Limitar o número de empregos ao valor especificado
    filtered_jobs = filtered_jobs[:num_jobs]
    
    # Imprimir os empregos filtrados em formato JSON
    if filtered_jobs:
        print("\nEmpregos filtrados:")
        print(json.dumps(filtered_jobs, ensure_ascii=False, indent=2))
    else:
        print("Nenhum trabalho encontrado para os critérios especificados.")
    
    # Exportar para CSV se o parâmetro export_csv for True
    if export_csv and filtered_jobs:
        try:
            # Nome do arquivo CSV com data e hora
            filename = f"jobs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            with open(filename, mode='w', newline='', encoding='utf-8') as file:
                writer = csv.DictWriter(file, fieldnames=["titulo", "empresa", "descrição", "data_publicacao", "salário", "localizacao"])
                writer.writeheader()
                writer.writerows(filtered_jobs)
            print(f"Dados exportados para o arquivo {filename}")
        except Exception as e:
            print(f"Erro ao exportar dados para CSV: {e}")

def skills_data(skills, data_ini, data_fim, export_csv=False, filename="skills_jobs.csv"):
    not_found = True
    URL = f'{BASE_URL}?api_key={API_KEY}'
    request = requests.get(URL, headers={'User-Agent': 'Mozilla/5.0'})
    data = request.json()
    
    alldata = []
    total_pages = math.ceil(data['total'] / 12) if data['total'] > 0 else 1
    
    for rep in range(total_pages):
        datasets = requests.get(URL, params={'limit': 12, 'page': rep + 1}, headers={'User-Agent': 'Mozilla/5.0'}).json()
        results = datasets['results']
        
        for item in results:
            data_trabalho = datetime.strptime(item['publishedAt'], '%Y-%m-%d %H:%M:%S')
            
            if data_ini <= data_trabalho <= data_fim:
                if all(re.search(r'\b' + re.escape(skill) + r'\b', item['body'], re.IGNORECASE) for skill in skills):
                    trabalho_info = {
                        'titulo': item.get('title', ''),
                        'empresa': item['company'].get('name', ''),
                        'descricao': item.get('body', ''),
                        'data_publicacao': item.get('publishedAt', ''),
                        'salario': item.get('wage', ''),
                        'localizacao': ', '.join([loc.get('name', 'N/A') for loc in item.get('locations', [])])
                    }
                    alldata.append(trabalho_info)
                    not_found = False

    # Exporta para CSV se solicitado
    if export_csv and alldata:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            fieldnames = ['titulo', 'empresa', 'descricao', 'data_publicacao', 'salario', 'localizacao']
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(alldata)
        print(f"Dados exportados para {filename}")

    return alldata

# Função para exibir ou exportar resultados conforme as skills e o período fornecido
def buscar_trabalhos_por_skills(skills, data_inicial, data_final, export_csv=False):
    data_ini = dt.strptime(data_inicial, '%Y-%m-%d')
    data_fim = dt.strptime(data_final, '%Y-%m-%d')
    resultados = skills_data(skills, data_ini, data_fim, export_csv=export_csv)
    
    if resultados:
        return json.dumps(resultados, indent=4)
    else:
        return "Nenhum trabalho encontrado para as habilidades e período fornecidos."  

# Função para buscar trabalhos por habilidades e período, com opção de exportar para CSV
# Função principal para escolher a funcionalidade
def main():
    print("Bem-vindo ao sistema de busca de empregos!")
    print("Escolha uma opção:")
    print("1. Buscar os 10 trabalhos mais recentes")
    print("2. Buscar trabalhos por localização e empresa")
    print("3. Buscar trabalhos por habilidades e período")
    
    choice = input("Digite o número da opção desejada: ")

    if choice == "1":
        export = input("Deseja exportar para CSV? (s/n): ").lower() == 's'
        top10(export_csv=export)
    elif choice == "2":
        location = input("Digite a localização: ")
        company = input("Digite o nome da empresa (opcional): ")
        num_jobs = int(input("Digite o número de trabalhos: "))
        job_type = input("Digite o tipo de trabalho: ")
        export = input("Deseja exportar para CSV? (s/n): ").strip().lower() == 's'

        if not job_type:
            job_type = None
        
        # Chamando a função `get_jobs` com a assinatura correta
        # Chamando a função get_jobs sem o argumento job_type
        get_jobs(location, company, num_jobs, job_type=job_type, export_csv=export)



    elif choice == "3":
        skills = input("Digite as habilidades separadas por vírgula: ").split(',')
        data_ini = datetime.strptime(input("Digite a data inicial (YYYY-MM-DD): "), '%Y-%m-%d')
        data_fim = datetime.strptime(input("Digite a data final (YYYY-MM-DD): "), '%Y-%m-%d')
        export = input("Deseja exportar para CSV? (s/n): ").strip().lower() == 's'

        resultado = skills_data(skills, data_ini, data_fim, export_csv=export)
        print(resultado)

if __name__ == "__main__":
    main()

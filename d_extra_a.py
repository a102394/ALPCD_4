import requests
import json
import os
import typer
import csv
from time import sleep

app = typer.Typer()

# Variáveis globais para armazenar dados já carregados
API_URL = "https://remotive.com/api/remote-jobs"  # URL base da API do Remotive
CACHE_FILE = "cache_vagas_remotive.json"  # Caminho do arquivo de cache

def echo_verde(msg: str):
    typer.echo(typer.style(msg, fg=typer.colors.GREEN))

def echo_vermelho(msg: str):
    typer.echo(typer.style(msg, fg=typer.colors.RED))

def save_to_csv(data, filename):
    keys = ['id', 'title', 'company_name', 'category', 'publication_date', 'salary', 'candidate_required_location', 'tags', 'description', 'company_logo', 'url', 'job_type']
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.DictWriter(file, fieldnames=keys)
        writer.writeheader()
        for item in data:
            item['salary'] = item.get('salary', 'N/A')  # Adiciona campo de salário se não existir
            writer.writerow(item)

def load_cache():
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, 'r', encoding='utf-8') as file:
            return json.load(file)
    else:
        echo_vermelho("Arquivo de cache não encontrado.")
        return getdata(force_reload=True)

def fetch_from_api():
    try:
        request = requests.get(API_URL, headers={'User-Agent': 'Mozilla/5.0'})
        request.raise_for_status()
        response_data = request.json().get('jobs', [])
        
        if not response_data:
            echo_vermelho("Nenhuma vaga encontrada.")
            return []

        # Salva os dados no cache
        with open(CACHE_FILE, 'w', encoding='utf-8') as file:
            json.dump(response_data, file, ensure_ascii=False, indent=4)
        echo_verde(f"Cache salvo no arquivo '{CACHE_FILE}'.")
        sleep(2)

        return response_data
    except requests.RequestException as e:
        echo_vermelho(f"Erro ao acessar a API: {e}")
        return []

def getdata(force_reload: bool = False):
    if force_reload:
        echo_verde("Carregando dados da API...")
        return fetch_from_api()
    else:
        return load_cache()



@app.command()
def list_jobs(category: str = None, save: bool = False):
    """
    Lista as vagas disponíveis, opcionalmente filtrando por categoria.
    """
    jobs = getdata()

    if category:
        jobs = [job for job in jobs if job['category'].lower() == category.lower()]

    if not jobs:
        echo_vermelho("Nenhuma vaga encontrada para os critérios informados.")
        return

    if save:
        save_to_csv(jobs, "vagas_remotive.csv")
        echo_verde(f"Resultados salvos em 'vagas_remotive.csv'")

    for job in jobs:
        echo_verde(f"ID: {job['id']} | Título: {job['title']} | Empresa: {job['company_name']} | Categoria: {job['category']} | Local: {job['candidate_required_location']}")



#alinea a)

@app.command()
def get(job_id: int, save: bool = False):
    """
    Exibe detalhes de uma vaga específica pelo ID.
    """
    jobs = getdata()
    
    job_found = next((job for job in jobs if job['id'] == job_id), None)

    if not job_found:
        echo_vermelho(f"Vaga com ID {job_id} não encontrada.")
        return

    # Exibe os detalhes da vaga
    print(json.dumps(job_found, indent=4, ensure_ascii=False))

    if save:
        save_to_csv([job_found], "vaga_detalhes.csv")
        echo_verde(f"Detalhes da vaga salvos em 'vaga_detalhes.csv'")

if __name__ == "__main__":
    app()
